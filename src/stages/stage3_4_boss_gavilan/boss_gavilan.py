"""
Module: boss_gavilan
System: framework/entities (student boss assignment)
Academic Unit: Unit II (vectors, parametric circular motion)

T3-FINALIZATION — Fase 1 (órbita) + DIVE con cuerpo + FEATHER_STORM con
proyectiles reutilizados (`enemy_shooter.Projectile`), telegrafía con el
anillo rojo base (estado TELEGRAPHING) y SFX propios ya en disco
(`sfx_bosses_gavilan_dive`). La fase 2 es velocidad ×1.4 + plumas; el
cambio de fase usa el protocolo base a 7 HP. Sin IA nueva.
"""
from __future__ import annotations

import math

import pygame

from src.engine.core.events import Events
from src.engine.utils.math_utils import vec2_distance, vec2_normalize
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.enemy_base import EnemyState
from src.framework.entities.enemy_shooter import Projectile


class BossGavilan(BossBase):
    ORBIT_RADIUS = 80.0
    ORBIT_SPEED = 0.6  # rad/s — 17_BOSS_SPEC.md §5.3, Phase 1
    # GAME-100: telegraph para grade + feedback
    _telegraph = ""
    _telegraph_timer = 0.0
    TELEGRAPH_DURATION = 0.4

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=42.0,
            damage_on_contact=0.75,
        )
        self.set_boss_name("EL GAVILAN")
        self.rect.width = 56
        self.rect.height = 40
        self._orbit_angle: float = 0.0
        # Centro de la órbita: la posición real del BossSpawn en el mapa,
        # NO un valor fijo — el arena no está en x=0 del mundo.
        self._center: pygame.Vector2 = pygame.Vector2(spawn_position)
        # T3 — planificador y cuerpos de ataque (mismos patrones que ya
        # declaraban las fases; antes sólo se emitían eventos).
        self._attack_cooldown: float = 2.5
        self._dive_timer: float = 0.0
        self._dive_vel: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self._objetivo: pygame.Vector2 = pygame.Vector2(spawn_position)
        self._plumas: list[Projectile] = []
        self._telegraph_duration = 0.4

        self._load_boss_sprites("boss_gavilan", 56, 40)
        self.set_phases([
            BossPhase(
                phase_index=0,
                health_threshold=30.0,
                attack_patterns=["DIVE", "FEATHER_STORM"],
                movement_type="orbit",
                speed_multiplier=1.0,
            ),
            BossPhase(
                phase_index=1,
                health_threshold=15.0,
                attack_patterns=["DIVE", "FEATHER_STORM", "ORBIT_SHRINK"],
                movement_type="orbit",
                speed_multiplier=1.4,
            ),
        ])
        self.on_enter_stage()

    def on_enter_stage(self) -> None:
        self._orbit_angle = 0.0

    def _patrol_behavior(self, dt: float) -> None:
        self._actualizar_plumas(dt)
        self._update_orbit(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._actualizar_plumas(dt)
        # En picado manda la velocidad del picado, no la órbita.
        if self._dive_timer > 0:
            self._dive_timer -= dt
            self.position.x += self._dive_vel.x * dt
            self.position.y += self._dive_vel.y * dt
            self.rect.x = int(self.position.x)
            self.rect.y = int(self.position.y)
            self.clamp_to_arena()
            self._face_player()
            if self._dive_timer <= 0:
                self.state = EnemyState.CHASE
            return
        if self._telegraph:
            # Reafirmar cada fotograma: la máquina base pone ALERT al ver al
            # jugador y taparía el anillo rojo del telegrafiado.
            self.state = EnemyState.TELEGRAPHING
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0:
                self._execute_telegraphed_attack()
                self._telegraph = ""
            return
        self._update_orbit(dt)
        self._attack_cooldown -= dt
        if self._attack_cooldown <= 0:
            self._programar_ataque()
        self._check_phase_transition()

    # AUD-761 — concede coraza (mitiga daño) para que las 4 habilidades
    # condicionables tengan dueño y el BossRush pueda soltar algo aquí.
    skill_drop = "skill_coraza"  # type: ignore[assignment]

    def _check_phase_transition(self) -> None:
        """Phase 2 a 7 HP — delega al protocolo base (AUD-761)."""
        if self.current_phase == 0 and self.current_health <= 7.0:
            try:
                self._start_phase_transition()  # type: ignore[attr-defined]
            except Exception:
                if self._event_bus:
                    self._event_bus.emit(Events.BOSS_PHASE_CHANGED, phase=1)
                self._event_bus.emit(Events.BOSS_ATTACK, pattern="PHASE_CHANGE", rect=self.rect)

    def _programar_ataque(self) -> None:
        """Elige patrón de los declarados en la fase y lo telegrafía.

        El anillo rojo lo pinta `EnemyBase.draw` con el estado
        TELEGRAPHING: reutilizar, no duplicar feedback.
        """
        patrones = ["DIVE"]
        if self.current_phase >= 1:
            patrones.append("FEATHER_STORM")
            self._attack_cooldown = 2.2
        else:
            self._attack_cooldown = 3.0
        self._telegraph = patrones[int(self._orbit_angle) % len(patrones)]
        if self._player_ref is not None:
            self._objetivo = pygame.Vector2(
                self._player_ref.centerx, self._player_ref.centery
            )
        self._telegraph_timer = self.TELEGRAPH_DURATION
        self.state = EnemyState.TELEGRAPHING
        self._event_bus.emit(
            Events.BOSS_ATTACK, pattern=self._telegraph + "_TELEGRAPH",
            rect=self.rect,
        )

    def _execute_telegraphed_attack(self) -> None:
        if self._telegraph == "DIVE":
            self._do_dive()
        elif self._telegraph == "FEATHER_STORM":
            self._do_feather_storm()

    def _do_dive(self) -> None:
        direccion = self._objetivo - pygame.Vector2(self.rect.center)
        if direccion.length_squared() < 1e-6:
            direccion = pygame.Vector2(1.0, 0.0)
        self._dive_vel = direccion.normalize() * 280.0
        self._dive_timer = 0.5
        self.state = EnemyState.CHASE
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="DIVE", rect=self.rect)
        self._event_bus.emit(
            Events.SFX_BOSSES_GAVILAN_DIVE,
            pos=(self.position.x, self.position.y),
        )

    def _do_feather_storm(self) -> None:
        base = self._objetivo - pygame.Vector2(self.rect.center)
        if base.length_squared() < 1e-6:
            base = pygame.Vector2(1.0, 0.0)
        for desvio in (-0.2, 0.0, 0.2):
            vel = base.normalize().rotate(desvio * 57.3) * 150.0
            pluma = Projectile(
                pygame.Vector2(self.rect.centerx, self.rect.centery),
                vel, damage=0.5, lifetime=2.5,
            )
            pluma._event_bus = self._event_bus
            self._plumas.append(pluma)
        self.state = EnemyState.CHASE
        self._event_bus.emit(
            Events.BOSS_ATTACK, pattern="FEATHER_STORM", rect=self.rect
        )
        self._event_bus.emit(
            Events.SFX_PROJECTILE_FIRE,
            pos=(self.rect.centerx, self.rect.centery),
        )

    def _do_orbit_shrink(self) -> None:
        # ORBIT_SHRINK es velocidad de fase (×1.4 aplicado en _update_orbit
        # vía speed_multiplier del protocolo base), no un ataque aparte.
        self._event_bus.emit(
            Events.BOSS_ATTACK, pattern="ORBIT_SHRINK", rect=self.rect
        )

    def _actualizar_plumas(self, dt: float) -> None:
        for pluma in self._plumas:
            pluma.update(dt)
        self._plumas = [p for p in self._plumas if p.is_active]

    def _check_player_contact(self, player) -> None:
        super()._check_player_contact(player)
        player_hurtbox = (
            player.hurtbox if hasattr(player, "hurtbox") else player.rect
        )
        for p in list(self._plumas):
            if p.is_active and p.rect.colliderect(player_hurtbox):
                if getattr(player, "_parry_active", False) and getattr(
                    player, "_parry_window", 0
                ) > 0:
                    p._expired = True
                    p.is_active = False
                    player._parry_success = True
                    player._parry_active = False
                    player._parry_window = 0.0
                    self._event_bus.emit(
                        Events.VFX_PARRY, pos=(p.position.x, p.position.y)
                    )
                    self.stun(self.PARRY_STUN_DURATION)
                else:
                    player.apply_damage(p.damage, (self.position.x, self.position.y))
                    p.on_collision()

    def draw(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2
    ) -> None:
        super().draw(surface, camera_offset)
        for pluma in self._plumas:
            pluma.draw(surface, camera_offset)

    def _update_orbit(self, dt: float) -> None:
        # La fase 2 corre ×1.4: lo aplica el protocolo base en
        # `speed_multiplier` al terminar la transición (AUD-053).
        self._orbit_angle += self.ORBIT_SPEED * float(self.speed_multiplier) * dt
        self.position.x = self._center.x + math.cos(self._orbit_angle) * self.ORBIT_RADIUS
        self.position.y = self._center.y + math.sin(self._orbit_angle) * self.ORBIT_RADIUS
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
        # AUD-761: el vuelo orbital se salía del arena si el spawn quedaba
        # cerca del borde (órbita sin clamp). El jugador no lo alcanzaba.
        self.clamp_to_arena()
        self._face_player()

    def _face_player(self) -> None:
        """Orienta el sprite hacia el jugador con vectores explícitos
        (Unidad II — math_utils.vec2_normalize / vec2_distance)."""
        player_ref = self._player_ref
        if player_ref is None:
            return
        boss_pos = pygame.Vector2(self.rect.center)
        player_pos = pygame.Vector2(player_ref.center)
        distance = vec2_distance(boss_pos, player_pos)
        if distance < 1e-6:
            return
        direction = vec2_normalize(player_pos - boss_pos)
        self.facing_direction = 1 if direction.x >= 0 else -1

    def _get_animation_key(self) -> str:
        return "drift"

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(8, 6, 40, 28)

    def _build_hurtbox(self) -> pygame.Rect:
        ox = (self.rect.width - 40) // 2
        oy = (self.rect.height - 28) // 2
        return pygame.Rect(ox, oy, 40, 28)
