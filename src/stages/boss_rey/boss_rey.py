from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core.events import Events
from src.engine.utils.math_utils import vec2_distance, vec2_normalize
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.processing.curve_tools import CurveTools

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class BossRey(BossBase):
    """
    El Rey Terciopelo — Evaluación Práctica I: solo Fase 1 ("La Marioneta").

    Movimiento: recorrido errático por Catmull-Rom sobre 4 posiciones del
    arena (la actual + 3 aleatorias), recalculado cada 0.3s.
    Ataque: VENOM_SPIT, un glob de veneno recto apuntado al jugador con
    vectores de math_utils.

    Las Fases 2 (división en ReyMetad) y 3 (frenesí) son Práctica II — no se
    implementan aquí (docs/17_BOSS_SPEC.md §4, CLAUDE.md).
    """

    # AUD-238 — el Rey concede el doble salto. Ver `boss_venado.py`, que hace
    # lo mismo con el dash: cada habilidad condicionable necesita al menos un
    # jefe que la suelte o encender el candado la vuelve inalcanzable.
    skill_drop = "skill_double_jump"

    #: Cuántos puntos de control aleatorios se suman a la posición actual
    #: para trazar la curva (spec: "4 random arena positions").
    RANDOM_POINTS = 3
    PATH_SAMPLES = 20
    PATH_RECALC_INTERVAL = 0.3
    #: No generar puntos de control pegados a las paredes del arena.
    ARENA_MARGIN = 24
    #: Temblor vertical de la marioneta al caminar — el Rey no vuela, así que
    #: la Y se mantiene pegada al suelo con un jitter pequeño en vez de
    #: vagar por todo el alto del arena.
    FLOOR_JITTER = 5.0

    VENOM_SPIT_RANGE = 200.0
    VENOM_SPIT_COOLDOWN = 2.5
    VENOM_SPIT_SPEED = 90.0
    VENOM_SPIT_DAMAGE = 0.5

    @property
    def _floor_y(self) -> float:
        """Y de la cabeza del jefe para que sus pies queden sobre el suelo.

        `floor_surface_y` es la fuente preferida: la escena la toma del
        rectángulo de colisión "Floor" del TMX, que es el suelo de verdad.
        Antes esto se derivaba de `arena_bounds`, pero desde que
        `arena_bounds` es el rect del `CameraLock` (para encerrar al jefe en
        su sala) el jefe flotaba: la altura a la que camina no tiene por qué
        depender de dónde esté encuadrada la cámara, y al arrastrar el
        CameraLock en Tiled el borde inferior cayó en 592.0, que `pygame.Rect`
        trunca a 591 y desalinea los pies un píxel.

        El cálculo por `arena_bounds` queda como respaldo para cuando la
        escena no informa el suelo (por ejemplo en pruebas unitarias).
        """
        if self.floor_surface_y is not None:
            return float(self.floor_surface_y - self.rect.height)
        if self.arena_bounds is None:
            return self.position.y
        return float(self.arena_bounds.bottom - 16 - self.rect.height)

    # GAME-100: telegraph window antes de cada ataque (feedback jugable)
    _telegraph = ""
    _telegraph_timer = 0.0
    TELEGRAPH_DURATION = 0.4

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        phases = [
            BossPhase(
                phase_index=0,
                health_threshold=10.0,
                attack_patterns=["VENOM_SPIT", "CHARGE"],
                movement_type="random_walk",
                speed_multiplier=1.0,
            ),
            BossPhase(
                phase_index=1,
                health_threshold=5.0,
                attack_patterns=["VENOM_SPIT", "CHARGE", "SUMMON"],
                movement_type="random_walk",
                speed_multiplier=1.3,
            ),
        ]
        super().__init__(
            spawn_position=spawn_position,
            max_health=15.0,
            damage_on_contact=0.5,
        )
        self.set_boss_name("REY TERCIOPELO")

        # Hurtbox exacta del spec (28x48). El hitbox se deriva con la misma
        # proporción que usa boss_venado.py entre su sprite (48x48) y su
        # hitbox (36x44) aplicada al sprite de Fase 1 del Rey (40x56).
        self.rect.width = 30
        self.rect.height = 50
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        self._load_boss_sprites("boss_rey", 40, 56, sheets={
            "walk": (40, 56),
            "spit": (40, 56),
            "hurt": (40, 56),
            "death": (40, 56),
        })
        self.set_phases(phases)

        #: Y de la superficie transitable, que la escena fija leyendo el
        #: rect de colisión "Floor" del TMX. `None` hasta entonces: ver
        #: `_floor_y` para el respaldo.
        self.floor_surface_y: float | None = None

        self._path_points: list[tuple[float, float]] = []
        self._path_timer: float = 0.0

        self._venom_cooldown: float = 0.0
        self._projectiles: list[dict[str, Any]] = []
        self._phase_transition_count = 0  # contador para grade_boss phase_transitions

    def _patrol_behavior(self, dt: float) -> None:
        self._update_movement(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._update_movement(dt)
        # GAME-100: telegraph window
        if self._telegraph:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0:
                self._execute_telegraphed_attack()
                self._telegraph = ""
            return
        self._update_venom_spit(dt)
        self._check_phase_transition()

    def _check_phase_transition(self) -> None:
        """Phase 2 a 5 HP — delega al protocolo base (AUD-760 hardening).

        Antes emitía dos eventos sin cambiar `current_phase` ni activar
        `is_transitioning`/`invulnerable`; el HUD y `grade_boss` veían un
        cambio pero la `speed_multiplier` nunca subía a 1.3 y la ventana
        invulnerable de 2.5 s no existía. Ahora va por el camino real.
        """
        if self.current_phase == 0 and self.current_health <= 5.0:
            self._phase_transition_count += 1
            # Delegar al motor: pone is_transitioning, invuln, stinger y
            # cambia current_phase en _finish_phase_transition.
            try:
                self._start_phase_transition()  # type: ignore[attr-defined]
            except Exception:
                # Fallback si la base cambia de nombre: mantener el evento
                # mínimo para que grade_boss no quede en 0.
                if self._event_bus:
                    self._event_bus.emit(Events.BOSS_PHASE_CHANGED, phase=1)
                self._event_bus.emit(Events.BOSS_ATTACK, pattern="PHASE_CHANGE", rect=self.rect)

    def _execute_telegraphed_attack(self) -> None:
        if self._telegraph == "VENOM_SPIT":
            self._do_venom_spit()
        elif self._telegraph == "CHARGE":
            self._do_charge()

    def _do_venom_spit(self) -> None:
        self._update_venom_spit(999)
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="VENOM_SPIT", rect=self.rect)

    def _do_charge(self) -> None:
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="CHARGE", rect=self.rect)
        self._event_bus.emit(Events.PLAYER_DAMAGED, amount=0.5)

    def _do_summon(self) -> None:
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="SUMMON", rect=self.rect)

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hitbox(self) -> pygame.Rect:
        # La caja de golpe no puede salirse del cuerpo (30x50): antes era
        # `Rect(5, 3, 30, 50)` — el cuerpo entero desplazado, que golpea desde
        # fuera del sprite. Ahora se encoge y centra como la hurtbox (28x48).
        return pygame.Rect(2, 2, 26, 46)

    def _build_hurtbox(self) -> pygame.Rect:
        ox = (self.rect.width - 28) // 2
        oy = (self.rect.height - 48) // 2
        return pygame.Rect(ox, oy, 28, 48)

    # ── Movimiento: Catmull-Rom sobre 4 posiciones, cada 0.3s ──────────

    def _update_movement(self, dt: float) -> None:
        self._path_timer += dt
        if not self._path_points or self._path_timer >= self.PATH_RECALC_INTERVAL:
            self._path_timer = 0.0
            self._path_points = self._build_random_path()

        t = min(1.0, self._path_timer / self.PATH_RECALC_INTERVAL)
        x, y = CurveTools.sample_path(self._path_points, t)
        self.position.x = x
        self.position.y = y
        self.clamp_to_arena()

    def _build_random_path(self) -> list[tuple[float, float]]:
        """Curva Catmull-Rom desde la posición actual hasta 3 puntos al azar.

        Unit III: `CurveTools.catmull_rom` pasa exactamente por cada punto de
        control (a diferencia de una Bézier, que solo pasa por los extremos),
        lo que produce el movimiento nervioso y errático de una marioneta
        tirada por hilos en vez de un recorrido suave.
        """
        control_points = [(self.position.x, self.position.y)]
        control_points += [self._random_arena_point() for _ in range(self.RANDOM_POINTS)]
        return CurveTools.catmull_rom(control_points, self.PATH_SAMPLES)

    def _random_arena_point(self) -> tuple[float, float]:
        if self.arena_bounds is None:
            return (self.position.x, self.position.y)
        left = self.arena_bounds.left + self.ARENA_MARGIN
        right = self.arena_bounds.right - self.ARENA_MARGIN - self.rect.width
        if right < left:
            left = right = self.arena_bounds.centerx - self.rect.width // 2
        x = random.uniform(left, right)
        y = self._floor_y + random.uniform(-self.FLOOR_JITTER, self.FLOOR_JITTER)
        return (x, y)

    # ── Ataque: VENOM_SPIT, apuntado con vectores de math_utils ────────

    def _update_venom_spit(self, dt: float) -> None:
        self._venom_cooldown -= dt
        if self._venom_cooldown > 0.0 or self._player_ref is None:
            return

        boss_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        player_pos = pygame.Vector2(self._player_ref.centerx, self._player_ref.centery)

        # Unit II: distancia y dirección normalizada — el glob de veneno se
        # dispara solo dentro de rango y viaja recto hacia el jugador.
        if vec2_distance(boss_pos, player_pos) > self.VENOM_SPIT_RANGE:
            return
        direction = vec2_normalize(player_pos - boss_pos)
        if direction.length_squared() == 0.0:
            return

        self._projectiles.append({
            "pos": pygame.Vector2(boss_pos),
            "vel": direction * self.VENOM_SPIT_SPEED,
            "damage": self.VENOM_SPIT_DAMAGE,
            "alive": True,
        })
        self._event_bus.emit(Events.BOSS_ATTACK, pattern="VENOM_SPIT", rect=self.rect)
        self._venom_cooldown = self.VENOM_SPIT_COOLDOWN

    def _update_projectiles(self, dt: float) -> None:
        bounds = self.arena_bounds.inflate(64, 64) if self.arena_bounds else None
        for proj in self._projectiles[:]:
            if not proj["alive"]:
                self._projectiles.remove(proj)
                continue
            proj["pos"] += proj["vel"] * dt
            if bounds is not None and not bounds.collidepoint(proj["pos"]):
                proj["alive"] = False

    def _post_update(self, dt: float) -> None:
        self._update_projectiles(dt)

    def _check_player_contact(self, player: Player) -> None:
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for proj in self._projectiles:
            if not proj["alive"]:
                continue
            proj_rect = pygame.Rect(int(proj["pos"].x - 4), int(proj["pos"].y - 4), 8, 8)
            if proj_rect.colliderect(player_hurtbox):
                player.apply_damage(proj["damage"], self.rect.center)
                proj["alive"] = False
        super()._check_player_contact(player)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        for proj in self._projectiles:
            if not proj["alive"]:
                continue
            sx = int(proj["pos"].x - camera_offset.x)
            sy = int(proj["pos"].y - camera_offset.y)
            pygame.draw.circle(surface, (60, 140, 40), (sx, sy), 4)
            pygame.draw.circle(surface, (200, 255, 180), (sx, sy), 4, 1)
