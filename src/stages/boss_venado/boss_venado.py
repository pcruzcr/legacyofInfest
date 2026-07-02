from __future__ import annotations

import math

import pygame

from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.enemy_base import EnemyState
from src.framework.processing.curve_tools import CurveTools


class BossVenado(BossBase):
    """
    El Venado Sagrado — Phase 1: sinusoidal drift + stomp/charge/vine_toss.
    Phase 2: Bézier path + vine_sweep/mushroom_spore.
    Uses FilterTools for edge-glow aura and CurveTools for Bézier projectiles.
    """

    ARENA_W = 320
    ARENA_H = 224
    ARENA_CENTER_X = ARENA_W // 2

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=12.0,
            damage_on_contact=0.75,
        )
        self.set_boss_name("VENADO SAGRADO")
        self.rect.width = 36
        self.rect.height = 44
        self._elapsed: float = 0.0
        self._base_y: float = spawn_position.y

        self._projectiles: list[dict] = []

        self._attack_timers: dict[str, float] = {
            "STOMP": 0.0,
            "CHARGE": 0.0,
            "VINE_TOSS": 0.0,
            "VINE_SWEEP": 0.0,
            "MUSHROOM_SPORE": 0.0,
        }
        self._attack_cooldowns: dict[str, float] = {
            "STOMP": 3.0,
            "CHARGE": 6.0,
            "VINE_TOSS": 8.0,
            "VINE_SWEEP": 5.0,
            "MUSHROOM_SPORE": 10.0,
        }

        self._bezier_path: list[pygame.Vector2] = []
        self._bezier_t: float = 0.0
        self._bezier_speed: float = 0.15

        self._charge_active: bool = False
        self._charge_target_x: float = 0.0
        self._charge_direction: int = 0

        self._sweep_active: bool = False
        self._sweep_timer: float = 0.0

        self._stomp_rect: pygame.Rect | None = None
        self._defeat_stage: int = -1

        self._load_boss_sprites("boss_venado", 48, 48)
        self.set_phases()
        self.on_enter_stage()

    def set_phases(self, phases: list[BossPhase] | None = None) -> None:
        if phases is None:
            phases = [
                BossPhase(phase_index=0, health_threshold=12.0,
                          attack_patterns=["STOMP", "CHARGE", "VINE_TOSS"],
                          movement_type="sine", speed_multiplier=1.0,
                          filter_effect="sobel"),
                BossPhase(phase_index=1, health_threshold=6.0,
                          attack_patterns=["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"],
                          movement_type="bezier", speed_multiplier=1.5,
                          filter_effect="sobel_x"),
            ]
        super().set_phases(phases)

    def on_enter_stage(self) -> None:
        self._elapsed = 0.0
        self._projectiles.clear()
        self._attack_timers = {k: 0.0 for k in self._attack_timers}
        self._bezier_path = self._build_figure8_path()
        self._bezier_t = 0.0
        self._charge_active = False
        self._sweep_active = False
        self._stomp_rect = None
        self._filter_frame = 0

    def _build_figure8_path(self) -> list[pygame.Vector2]:
        cx = self.ARENA_CENTER_X
        cy = self.ARENA_H // 2 - 20
        r = 80
        return [
            pygame.Vector2(cx - r, cy),
            pygame.Vector2(cx, cy - r // 2),
            pygame.Vector2(cx + r, cy),
            pygame.Vector2(cx, cy + r // 2),
            pygame.Vector2(cx - r, cy),
        ]

    def _patrol_behavior(self, dt: float) -> None:
        self._update_movement(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._update_movement(dt)
        self._tick_attack_timers(dt)
        phase = self.phases[self.current_phase] if self.phases else None
        if phase is None:
            return
        for pattern in phase.attack_patterns:
            self._try_attack(pattern, dt)

    def _get_animation_key(self) -> str:
        """Drift animation for patrol; charge/stomp are attack-specific."""
        return "drift"

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(6, 4, 36, 44)

    def _build_hurtbox(self) -> pygame.Rect:
        ox = (self.rect.width - 30) // 2
        oy = (self.rect.height - 40) // 2
        return pygame.Rect(ox, oy, 30, 40)

    def _update_movement(self, dt: float) -> None:
        if not self.phases or self.current_phase >= len(self.phases):
            return
        phase = self.phases[self.current_phase]
        speed = 60.0 * phase.speed_multiplier

        if phase.movement_type == "sine":
            self._elapsed += dt
            self.position.x += speed * dt * self.facing_direction
            amplitude = 40.0
            freq = 0.4
            self.position.y = self._base_y + amplitude * math.sin(2 * math.pi * freq * self._elapsed)
            if self.position.x < 32:
                self.position.x = 32
                self.facing_direction = 1
            elif self.position.x > self.ARENA_W - 32:
                self.position.x = self.ARENA_W - 32
                self.facing_direction = -1

        elif phase.movement_type == "bezier" and self._bezier_path:
            self._bezier_t += self._bezier_speed * dt * phase.speed_multiplier
            if self._bezier_t >= 1.0:
                self._bezier_t = 0.0
            pos = CurveTools.sample_path(self._bezier_path, self._bezier_t)
            if isinstance(pos, (tuple, list)):
                self.position.x = pos[0]
                self.position.y = pos[1]
            else:
                self.position.x = pos.x
                self.position.y = pos.y

    def _tick_attack_timers(self, dt: float) -> None:
        for k in self._attack_timers:
            self._attack_timers[k] = max(0.0, self._attack_timers[k] - dt)

    def _try_attack(self, pattern: str, dt: float) -> None:
        if self._attack_timers.get(pattern, 0) > 0:
            return
        player_ref = self._player_ref
        if player_ref is None:
            return
        dx = abs(player_ref.centerx - self.rect.centerx)
        if pattern == "STOMP" and dx <= 96:
            self._do_stomp()
        elif pattern == "CHARGE" and dx >= self.ARENA_W // 2:
            self._do_charge(player_ref)
        elif pattern == "VINE_TOSS" and dx <= 200:
            self._do_vine_toss(player_ref)
        elif pattern == "VINE_SWEEP":
            self._do_vine_sweep()
        elif pattern == "MUSHROOM_SPORE" and dx <= 200:
            self._do_mushroom_spore()

    def _do_stomp(self) -> None:
        self._attack_timers["STOMP"] = self._attack_cooldowns["STOMP"]
        self._stomp_rect = pygame.Rect(
            self.rect.centerx - 48, self.rect.bottom - 8, 96, 8,
        )
        emit(Events.BOSS_ATTACK, pattern="STOMP", rect=self._stomp_rect)

    def _do_charge(self, player_ref: pygame.Rect) -> None:
        self._attack_timers["CHARGE"] = self._attack_cooldowns["CHARGE"]
        self._charge_active = True
        self._charge_direction = 1 if player_ref.centerx > self.rect.centerx else -1
        self._charge_target_x = self.rect.centerx + self._charge_direction * 160

    def _do_vine_toss(self, player_ref: pygame.Rect) -> None:
        self._attack_timers["VINE_TOSS"] = self._attack_cooldowns["VINE_TOSS"]
        muzzle = pygame.Vector2(self.rect.centerx, self.rect.top)
        predicted = pygame.Vector2(
            player_ref.centerx,
            player_ref.centery,
        )
        midpoint = pygame.Vector2(
            (muzzle.x + predicted.x) / 2,
            min(muzzle.y, predicted.y) - 80,
        )
        self._projectiles.append({
            "type": "vine",
            "control_points": [muzzle, midpoint, predicted],
            "t": 0.0,
            "speed": 0.5,
            "damage": 0.5,
            "alive": True,
        })

    def _do_vine_sweep(self) -> None:
        self._attack_timers["VINE_SWEEP"] = self._attack_cooldowns["VINE_SWEEP"]
        self._sweep_active = True
        self._sweep_timer = 0.5

    def _do_mushroom_spore(self) -> None:
        self._attack_timers["MUSHROOM_SPORE"] = self._attack_cooldowns["MUSHROOM_SPORE"]
        for angle_offset in [-15, 0, 15]:
            rad = math.radians(angle_offset)
            self._projectiles.append({
                "type": "spore",
                "pos": pygame.Vector2(self.rect.centerx, self.rect.centery),
                "vel": pygame.Vector2(
                    math.cos(rad) * 80,
                    math.sin(rad) * 80,
                ),
                "damage": 0.25,
                "alive": True,
                "lifetime": 3.0,
            })

    def _update_charge(self, dt: float) -> None:
        charge_speed = 220.0 if self.current_phase == 0 else 280.0
        self.position.x += self._charge_direction * charge_speed * dt
        if (self._charge_direction > 0 and self.position.x >= self._charge_target_x) or \
           (self._charge_direction < 0 and self.position.x <= self._charge_target_x):
            self._charge_active = False

    def _update_projectiles(self, dt: float) -> None:
        for proj in self._projectiles[:]:
            if not proj.get("alive", False):
                continue
            if proj["type"] == "vine":
                proj["t"] += proj["speed"] * dt
                if proj["t"] >= 1.0:
                    proj["alive"] = False
                    continue
                sampled = CurveTools.sample_path(proj["control_points"], proj["t"])
                if isinstance(sampled, (tuple, list)):
                    proj["pos"] = pygame.Vector2(sampled[0], sampled[1])
                else:
                    proj["pos"] = sampled
            elif proj["type"] == "spore":
                proj["pos"] += proj["vel"] * dt
                proj["lifetime"] -= dt
                if proj["lifetime"] <= 0:
                    proj["alive"] = False
            if not proj["alive"]:
                self._projectiles.remove(proj)

    def on_defeated(self) -> None:
        """Defeat sequence: death anim → particles → skull → relic → STAGE_COMPLETE."""
        self.state = EnemyState.DYING
        self._death_timer = 12.0 / 8.0  # 12 frames at 8 FPS = 1.5s
        self._defeat_stage = 0  # 0=dying, 1=skull, 2=done

    def update(self, dt: float) -> None:
        if not self.is_alive:
            return
        if self.state == EnemyState.DYING:
            self._death_timer -= dt
            if self._death_timer <= 0:
                if self._defeat_stage == 0:
                    self._defeat_stage = 1
                    self._death_timer = 2.0  # skull remains 2s
                elif self._defeat_stage == 1:
                    self._defeat_stage = 2
                    self._death_timer = 0
                    emit(Events.ENEMY_DIED,
                         entity_id=f"BossVenado_{id(self)}",
                         position=(self.position.x, self.position.y))
                    emit(Events.STAGE_COMPLETE, stage_id="")
                    self.is_alive = False
                    self.is_active = False
            return
        self._filter_frame += 1
        super().update(dt)
        self._update_projectiles(dt)
        if self._charge_active:
            self._update_charge(dt)
        if self._sweep_active:
            self._sweep_timer -= dt
            if self._sweep_timer <= 0:
                self._sweep_active = False
        if self._stomp_rect is not None and self._stomp_rect.y < self.rect.bottom:
            self._stomp_rect = None

    def check_player_contact(self, player) -> None:
        super().check_player_contact(player)
        for proj in self._projectiles:
            if not proj.get("alive", False) or "pos" not in proj:
                continue
            proj_rect = pygame.Rect(int(proj["pos"].x - 4), int(proj["pos"].y - 4), 8, 8)
            if proj_rect.colliderect(player.rect):
                player.apply_damage(proj.get("damage", 0.5), self.rect.center)
                proj["alive"] = False
        if self._stomp_rect and self._stomp_rect.colliderect(player.rect):
            player.apply_damage(1.0, self.rect.center)
            self._stomp_rect = None
        if self._sweep_active:
            sweep_rect = pygame.Rect(0, self.rect.bottom - 12, self.ARENA_W, 24)
            if sweep_rect.colliderect(player.rect):
                player.apply_damage(0.5, self.rect.center)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        for proj in self._projectiles:
            if not proj.get("alive", False) or "pos" not in proj:
                continue
            sx = int(proj["pos"].x - camera_offset.x)
            sy = int(proj["pos"].y - camera_offset.y)
            color = (100, 200, 100) if proj["type"] == "vine" else (180, 120, 80)
            pygame.draw.circle(surface, color, (sx, sy), 4)
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 4, 1)
        if self._stomp_rect:
            sx = int(self._stomp_rect.x - camera_offset.x)
            sy = int(self._stomp_rect.y - camera_offset.y)
            pygame.draw.rect(surface, (180, 100, 60), (sx, sy, self._stomp_rect.width, self._stomp_rect.height))
        if self._sweep_active:
            sx = int(0 - camera_offset.x)
            sy = int(self.rect.bottom - 12 - camera_offset.y)
            pygame.draw.rect(surface, (80, 180, 60), (sx, sy, self.ARENA_W, 24), 2)

    def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
        if not self.is_alive or self.is_transitioning:
            return
        if self._invincibility_timer > 0:
            return
        super().apply_hit(damage, source_position)
        if self.current_health <= 0:
            self.on_defeated()
            return
        self._check_phase_transition()
