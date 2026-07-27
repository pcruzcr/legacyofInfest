from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core.events import Events
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.boss_kit import (
    AttackScheduler,
    BossAttack,
    SummonTracker,
    SummonWave,
    WeakPoint,
)
from src.framework.entities.enemy_base import EnemyState
from src.framework.processing.curve_tools import CurveTools

if TYPE_CHECKING:
    from src.framework.entities.player import Player


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
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)
        self._elapsed: float = 0.0
        self._base_y: float = spawn_position.y

        self._projectiles: list[dict[str, Any]] = []

        # Los tiempos de ataque los lleva `self.attacks` (AttackScheduler), no
        # diccionarios paralelos aquí. Antes existían `_attack_timers` y
        # `_attack_cooldowns` locales: al añadir el planificador habría habido
        # dos sistemas de enfriamiento decidiendo lo mismo, y el que ganara
        # dependería del orden de llamadas — el peor tipo de error, porque el
        # jefe atacaría distinto según por dónde entrara la actualización.

        self._bezier_path: list[pygame.Vector2] = []
        self._bezier_t: float = 0.0
        self._bezier_speed: float = 0.15

        self._charge_active: bool = False
        self._charge_target_x: float = 0.0
        self._charge_direction: int = 0

        self._sweep_active: bool = False
        self._sweep_timer: float = 0.0

        self._stomp_rect: pygame.Rect | None = None
        self._stomp_timer: float = 0.0
        self._defeat_stage: int = -1

        self._combo_queue: list[str] = []
        self._combo_timer: float = 0.0

        # `frenzy_drift` no está en las claves por defecto de `_load_boss_sprites`,
        # así que la hoja existía en disco sin cargarse nunca.
        self._load_boss_sprites("boss_venado", 48, 48, sheets={
            "drift": (48, 48),
            "frenzy_drift": (48, 48),
            "hurt": (48, 48),
            "charge": (48, 48),
            "stomp": (48, 48),
            "vine": (48, 48),
            "death": (48, 48),
            "skull": (48, 48),
        })
        self.set_phases()
        self.on_enter_stage()

    def set_phases(self, phases: list[BossPhase] | None = None) -> None:
        if phases is None:
            phases = [
                BossPhase(phase_index=0, health_threshold=12.0,
                          attack_patterns=["STOMP", "CHARGE", "VINE_TOSS"],
                          movement_type="sine", speed_multiplier=1.0,
                          filter_effect="sobel",
                          combos={"STOMP": ["COMBO_STOMP_CHARGE"]}),
                BossPhase(phase_index=1, health_threshold=6.0,
                          attack_patterns=["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"],
                          movement_type="bezier", speed_multiplier=1.5,
                          filter_effect="sobel_x",
                          combos={"VINE_SWEEP": ["COMBO_SWEEP_SPORE"]}),
            ]
        super().set_phases(phases)
        self._declare_encounter()

    def _declare_encounter(self) -> None:
        """Ataques telegrafiados, puntos débiles e invocaciones (AUD-053).

        Antes, `attack_patterns` era una lista de cadenas que nada consumía: el
        Venado declaraba cinco ataques y ejecutaba siempre el mismo. Aquí se
        convierten en ataques reales con aviso, golpe y ventana de castigo.

        Los tiempos son decisiones de diseño explícitas:

        * ``STOMP`` es el ataque de base — aviso corto (0,5 s) porque es de
          corto alcance y el jugador ya está cerca leyendo al jefe.
        * ``CHARGE`` cruza la arena, así que avisa 0,9 s: hay que darle tiempo
          a decidir si salta o se aparta, no sólo a reaccionar.
        * ``VINE_TOSS`` es a distancia y castiga quedarse lejos, cerrando la
          estrategia de esperar fuera de rango.
        * ``MUSHROOM_SPORE`` sólo existe en la fase 2 y tiene la recuperación
          más larga: es el momento de mayor castigo del encuentro.
        """
        self.attacks = AttackScheduler([
            BossAttack("STOMP", windup=0.5, active=0.18, recover=0.7,
                       damage=0.75, reach=56.0, max_range=90.0, cooldown=2.4),
            BossAttack("CHARGE", windup=0.9, active=0.45, recover=1.1,
                       damage=1.0, reach=40.0, min_range=60.0, max_range=320.0,
                       cooldown=5.0),
            BossAttack("VINE_TOSS", windup=0.7, active=0.2, recover=0.9,
                       damage=0.5, reach=200.0, min_range=100.0, cooldown=4.0,
                       phases=(0,)),
            BossAttack("VINE_SWEEP", windup=0.75, active=0.3, recover=0.85,
                       damage=0.75, reach=110.0, max_range=140.0, cooldown=3.5,
                       phases=(1,)),
            BossAttack("MUSHROOM_SPORE", windup=1.0, active=0.25, recover=1.4,
                       damage=0.5, reach=160.0, cooldown=7.0, phases=(1,)),
        ])

        # Los cuernos son el punto débil: obligan a atacar por delante, que es
        # justo donde el jefe embiste. Esa tensión — el sitio que más daño hace
        # es el más peligroso — es lo que convierte el combate en una decisión.
        self.weak_points = [
            WeakPoint(offset=(6, 0), size=(24, 12), multiplier=2.5,
                      label="cuernos"),
            # Los flancos sólo quedan expuestos en la fase 2, cuando el jefe se
            # mueve por trayectoria Bézier y se le puede rodear.
            WeakPoint(offset=(-4, 20), size=(10, 18), multiplier=1.8,
                      phases=(1,), label="flanco"),
        ]

        # Invoca esporas en la fase 2. El tope de 4 vivos evita que el
        # encuentro deje de ser sobre el jefe y pase a ser sobre la multitud.
        self.summons = SummonTracker(waves=[
            SummonWave("FlyingCucaracha", count=2, max_alive=4,
                       cooldown=9.0, phases=(1,)),
        ])

    def on_enter_stage(self) -> None:
        self._elapsed = 0.0
        self._projectiles.clear()
        self.attacks.reset()
        self.summons.reset()
        self._bezier_path = self._build_figure8_path()
        self._bezier_t = 0.0
        self._charge_active = False
        self._sweep_active = False
        self._stomp_rect = None
        self._stomp_timer = 0.0
        self._filter_frame = 0
        self._combo_queue.clear()
        self._combo_timer = 0.0

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
        """Movimiento y combos. Los ataques los lanza el planificador.

        Ya no se recorre `phase.attack_patterns` disparando lo primero que
        quede en rango: eso hacía que el Venado ejecutase siempre STOMP —
        primero de la lista, rango más permisivo— y que los otros cuatro
        patrones declarados no llegaran a verse. `BossBase._update_encounter`
        elige el ataque y avisa aquí por `on_attack_fired`.
        """
        self._update_movement(dt)
        self._advance_combo(dt)

    def _get_animation_key(self) -> str:
        """La animación sigue al ataque en curso, no al estado.

        `boss_venado_charge.png` y `boss_venado_stomp.png` existen en disco
        desde el principio y **nunca se mostraban**: este método devolvía
        siempre `"drift"`. Un ataque telegrafiado que se ve igual que caminar
        no está telegrafiado, así que aquí es donde el aviso se hace visible.
        """
        current = self.attacks.current
        if current is not None:
            if current.name == "CHARGE":
                return "charge"
            if current.name == "STOMP":
                return "stomp"
            if current.name in ("VINE_TOSS", "VINE_SWEEP"):
                return "vine"
        # La fase 2 tiene su propia hoja de deriva, más agitada.
        if self.current_phase >= 1 and "frenzy_drift" in self._sprite_frames:
            return "frenzy_drift"
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

    def on_attack_fired(self, attack_name: str) -> None:
        """El aviso terminó: ejecuta el golpe.

        Gancho de `BossBase`. Se llama una sola vez, en el instante en que el
        ataque pasa de WINDUP a ACTIVE, así que aquí no hay que comprobar
        enfriamientos ni rangos: el planificador ya decidió que este ataque era
        posible y el jugador ya vio el aviso.
        """
        player_ref = self._player_ref
        phase = self.phases[self.current_phase] if self.phases else None
        phase_combos = phase.combos if phase else {}

        if attack_name == "STOMP":
            self._do_stomp()
        elif attack_name == "CHARGE" and player_ref is not None:
            self._do_charge(player_ref)
        elif attack_name == "VINE_TOSS" and player_ref is not None:
            self._do_vine_toss(player_ref)
        elif attack_name == "VINE_SWEEP":
            self._do_vine_sweep()
        elif attack_name == "MUSHROOM_SPORE":
            self._do_mushroom_spore()
        else:
            return

        if attack_name in phase_combos:
            self._queue_combo(phase_combos[attack_name])

    def on_summon(self, species_id: str, count: int) -> None:
        """Anuncia la invocación para que el HUD y el audio reaccionen."""
        self._event_bus.emit(
            Events.BOSS_ATTACK, pattern=f"SUMMON_{species_id}", rect=self.rect,
        )

    def _advance_combo(self, dt: float) -> None:
        """Encadena el siguiente golpe del combo tras su pausa."""
        if not self._combo_queue or self._combo_timer <= 0.0:
            return
        self._combo_timer -= dt
        if self._combo_timer > 0.0:
            return
        next_combo = self._combo_queue.pop(0)
        combo_method = getattr(self, f"_do_{next_combo.lower()}", None)
        if combo_method:
            combo_method()
        # Sólo se reencola si queda combo; si no, el temporizador se apaga.
        self._combo_timer = 0.5 if self._combo_queue else 0.0

    def _queue_combo(self, combo_names: list[str]) -> None:
        self._combo_queue = list(combo_names)
        self._combo_timer = 0.5

    def _do_combo_stomp_charge(self) -> None:
        player_ref = self._player_ref
        if player_ref is None:
            return
        self._do_charge(player_ref)
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="COMBO_STOMP_CHARGE", rect=self.rect)

    def _do_combo_sweep_spore(self) -> None:
        self._do_mushroom_spore()
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="COMBO_SWEEP_SPORE", rect=self.rect)

    def _do_stomp(self) -> None:
        # El rectángulo vive el tiempo activo del ataque, no un frame. Antes se
        # borraba con `if self._stomp_rect.y < self.rect.bottom`, condición que
        # es cierta en el mismo frame en que se crea (se coloca en
        # `bottom - 8`), así que el pisotón se destruía antes de poder golpear:
        # el ataque se veía y no hacía nada.
        self._stomp_timer = 0.18
        self._stomp_rect = pygame.Rect(
            self.rect.centerx - 48, self.rect.bottom - 8, 96, 8,
        )
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="STOMP", rect=self._stomp_rect)

    def _do_charge(self, player_ref: pygame.Rect) -> None:
        self._charge_active = True
        self._charge_direction = 1 if player_ref.centerx > self.rect.centerx else -1
        self._charge_target_x = self.rect.centerx + self._charge_direction * 160

    def _do_vine_toss(self, player_ref: pygame.Rect) -> None:
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
        self._sweep_active = True
        self._sweep_timer = 0.5

    def _do_mushroom_spore(self) -> None:
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
            if self.current_phase == 0:
                self._do_stomp()
                self._event_bus.emit(Events.BOSS_ATTACK, pattern="CHARGE_STOMP", rect=self.rect)

    def _update_projectiles(self, dt: float) -> None:
        for proj in self._projectiles[:]:
            if not proj.get("alive", False):
                continue
            if proj["type"] == "vine":
                proj["t"] += proj["speed"] * dt
                if proj["t"] >= 1.0:
                    proj["alive"] = False
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
                    # Stage scene handles STAGE_COMPLETE with 2s banner
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
        if self._stomp_rect is not None:
            self._stomp_timer -= dt
            if self._stomp_timer <= 0.0:
                self._stomp_rect = None

    def _check_player_contact(self, player: Player) -> None:
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for proj in self._projectiles:
            if not proj.get("alive", False) or "pos" not in proj:
                continue
            proj_rect = pygame.Rect(int(proj["pos"].x - 4), int(proj["pos"].y - 4), 8, 8)
            if proj_rect.colliderect(player_hurtbox):
                player.apply_damage(proj.get("damage", 0.5), self.rect.center)
                proj["alive"] = False
        if self._stomp_rect and self._stomp_rect.colliderect(player_hurtbox):
            player.apply_damage(1.0, self.rect.center)
            self._stomp_rect = None
        if self._sweep_active:
            sweep_rect = pygame.Rect(0, self.rect.bottom - 12, self.ARENA_W, 24)
            if sweep_rect.colliderect(player_hurtbox):
                player.apply_damage(0.5, self.rect.center)
        super()._check_player_contact(player)

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
        super().apply_hit(damage, source_position)
        if self.current_health <= 0 and self.is_alive:
            self.on_defeated()
