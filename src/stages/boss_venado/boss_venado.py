"""
Module: boss_venado
System: Stage 1-4 boss — El Venado Sagrado (student rewrite, Evaluación Práctica I)
Academic Unit: II, III, IV, V — see README.md front-matter for units_demonstrated
Description: Official 17_BOSS_SPEC §3 design reimplemented from
    student_templates/boss_template.py. Unit II: vec2_* math for spores/charge;
    Unit III: CurveTools.bezier for vine arc and figure-8 flight; Unit IV:
    explicit painter's draw order; Unit V: ColorTools glow/HSV effects.
"""
from __future__ import annotations

import logging
import math
from typing import Any

import pygame

from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import vec2_distance, vec2_normalize
from src.framework.entities.boss_base import BossBase, BossPhase
from src.framework.entities.boss_kit import WeakPoint, resolve_weak_point_damage
from src.framework.entities.enemy_base import EnemyState
from src.framework.processing.color_tools import ColorTools
from src.framework.processing.curve_tools import CurveTools

# New arena (map "Residencias al Crepusculo", 205x38 tiles)
ARENA_X0 = 2480.0        # CameraLock_01 left edge; keep in sync with boss_venado_scene.ARENA_X0
ARENA_X1 = 3264.0        # RightWall_Arena
ARENA_CX = (ARENA_X0 + ARENA_X1) / 2.0
FLOOR_Y = 560.0          # Collision Floor top
BASE_Y = 460.0           # sine center: rect.bottom peaks at 548 (melee-reachable)

SINE_AMPLITUDE = 40.0    # 17_BOSS_SPEC §3.3 (official)
SINE_FREQ = 0.4
DRIFT_SPEED = 60.0
CHARGE_SPEED_P1 = 220.0
CHARGE_SPEED_P2 = 280.0
CHARGE_TELEGRAPH = 0.35
CHARGE_WALL_PAUSE = 1.0  # wall-crash stagger: must outlast a full-height dodge-jump round trip (~0.95s) so skilled players can land and punish (FINDINGS H-12/E)
STOMP_TELEGRAPH = 0.4
STOMP_WINDOW = 0.35
STOMP_RECOVER = 0.6      # Hallazgo C fix: grounded punish window after the shockwave clears
SWEEP_TELEGRAPH = 0.6
SWEEP_WINDOW = 0.4
SPORE_SPEED = 80.0
SPORE_RANGE = 420.0      # expiry by vec2_distance (Unit II)
SPORE_LIFETIME = 6.0     # generous: distance expiry (5.25 s) binds first
PROJECTILE_HIT_RADIUS = 5.0  # vine/spore contact box half-size (Task 8 review carry-over)
VINE_PREDICT = 0.5       # s of player-velocity lead (official §3.5)
VINE_SPEED = 0.9         # vine projectile: path progress in t/s
VINE_ARC_HEIGHT = 80.0   # vine projectile: arc apex offset, official §3.5

# H-04/H-08 design fix: attack verticality (17_BOSS_SPEC §5 completeness).
GROUND_Y = FLOOR_Y - 48.0    # top y when slamming: rect.bottom == floor (H-04 punish window)
CHARGE_BAND_Y = 500.0        # top y during dash: rect.bottom 548 == sine trough (H-08 melee band)
VERTICAL_ATTACK_SPEED = 200.0  # px/s descend/rise for attack verticality

AGGRO_X = ARENA_X0 - 96.0  # the deer only fights on its sacred ground: aggro once the player nears the arena mouth

# Weak points (Feature C, adopted from the reference boss's boss_kit.WeakPoint --
# spec 2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §3). Enrichment
# only: not part of the official 17_BOSS_SPEC §3 rubric.
#
# Offsets are declared in CANONICAL space: the unflipped sprite frame as it
# sits on disk (facing_direction >= 0, no pygame.transform.flip applied --
# see BossVenado._mirror_weak_point below for the facing_direction < 0 case).
#
# A naive translation of the reference boss's own numbers (offset + (6,4), to
# go from its 36x44 rect to our 48x48 canvas -- see the spec) does NOT land
# on this sprite's antlers: it was checked pixel-by-pixel against
# assets/sprites/bosses/boss_venado_drift.png (and cross-checked against
# _charge.png/_frenzy_drift.png, same pose) with a 4px-grid overlay. On that
# 48x48 frame the deer faces right: antler tips cluster at x 34-42/y 0-6,
# fading into the skull crown down to about y 9; the readable "horns" target
# is x 32-46/y 0-10. The rear haunch (opposite the head, the flank a player
# rounds the boss to reach) sits at roughly x 9-21/y 18-34 -- the naive
# translation (x 2-12/y 24-42) mostly missed the body into background/legs.
CUERNOS_OFFSET = (32, 0)
CUERNOS_SIZE = (14, 10)
CUERNOS_MULTIPLIER = 2.5
FLANCO_OFFSET = (9, 18)
FLANCO_SIZE = (12, 16)
FLANCO_MULTIPLIER = 1.8
WEAK_POINT_FLASH_DURATION = 0.12  # brief crit confirmation, not a lingering VFX


class BossVenado(BossBase):
    """Two official phases: El Bosque Duerme (sine) / El Bosque Despierta (bezier)."""

    # AUD-238 — el primer jefe concede el dash.
    #
    # Una línea, y es el ejemplo que los estudiantes copian para su propio
    # jefe. Sin al menos un jefe que suelte cada habilidad condicionable,
    # encender `PLAYER_SKILLS_REQUIRE_UNLOCK` dejaría el dash inalcanzable
    # para siempre — mecánica borrada, no progresión. Lo exige
    # `test_habilidades_que_sueltan_los_jefes.py`.
    # AUD-263: dos, no una. `skill_parry` llevaba meses en el catálogo sin que
    # ningún jefe lo soltara —contenido inalcanzable— porque `skill_drop` era un
    # solo `str` y quitarle el dash al venado habría borrado una mecánica. Ahora
    # el motor acepta las dos formas y aquí se declaran las dos habilidades.
    skill_drop = ["skill_dash", "skill_parry"]

    # AUD-606 — las cajas de este jefe son CONSTANTES del sprite base 48×48
    # (`_build_hitbox`/`_build_hurtbox` más abajo), así que sin esta bandera
    # quedaban con el tamaño de la fase 1 cuando la fase 2 crece ×1.25. Con
    # ella, el motor escala hitbox/hurtbox ancladas abajo-centro y espeja los
    # puntos débiles según el facing — por eso `_mirror_weak_point` ya no
    # existe: el espejo a mano era la compensación por su ausencia.
    cajas_siguen_al_cuerpo = True

    _TELEGRAPH_WARN_COLOR = (230, 90, 60)   # STOMP/CHARGE/VINE_SWEEP warning tint
    _WEAK_POINT_FLASH_HUE = 48.0            # amber/gold crit confirmation, distinct
                                             # from the warning color above and the
                                             # green phase-transition pulse below

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=12.0,
            damage_on_contact=0.75,
        )
        self.set_boss_name("VENADO SAGRADO")
        # AUD-263 — `EnjambreDeBalas` tenía 0 usos fuera de su módulo (GAP-032).
        # Aquí es la nube de esporas de la fase 2: el patrón dense-bullet que el
        # bestiario no tenía y que un estudiante puede copiar tal cual. Medido
        # en su día: 2.000 balas de 12,94 ms a 0,072 ms.
        from src.framework.ecs.bullet_swarm import EnjambreDeBalas
        self.esporas = EnjambreDeBalas(capacidad=256)
        #: Quien reproduce las líneas de voz. Lo inyecta la escena; sin él, el
        #: jefe calla y no revienta — una entrega puede construirlo sin audio.
        self.audio_de_voz: object | None = None
        self._load_boss_sprites("boss_venado", 48, 48)
        self._load_extra_sprites()

        # Universal engine pattern (enemy_walker.py:54-57): TMX spawn Y is the
        # feet line; position is top-left, so shift up by the sprite height.
        self.rect.width = 48
        self.rect.height = 48
        self.position.y -= self.rect.height
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

        self._elapsed = 0.0
        self._base_y = BASE_Y
        self._attack_cooldowns = {
            "STOMP": 3.0, "CHARGE": 6.0, "VINE_TOSS": 8.0,
            "VINE_SWEEP": 5.0, "MUSHROOM_SPORE": 10.0,
        }
        self._attack_timers = {k: 0.0 for k in self._attack_cooldowns}
        # VINE_TOSS/MUSHROOM_SPORE start on cooldown: the fight opens with
        # melee pressure, not projectiles.
        self._attack_timers["VINE_TOSS"] = self._attack_cooldowns["VINE_TOSS"]
        self._attack_timers["MUSHROOM_SPORE"] = self._attack_cooldowns["MUSHROOM_SPORE"]

        self._telegraph = ""             # "" | "STOMP" | "CHARGE" | "VINE_SWEEP"
        self._telegraph_timer = 0.0
        self._charge_active = False
        self._charge_direction = 1
        self._charge_recover = 0.0       # Hallazgo C fix: stationary punish window after the wall-stop
        self._stomp_rect: pygame.Rect | None = None
        self._stomp_window = 0.0
        self._stomp_recover = 0.0        # Hallazgo C fix: grounded punish window after the shockwave clears
        self._y_recovering = False       # H-04/H-08: seamless y catch-up after an attack ends
        self._sweep_window = 0.0
        self._sweep_rect: pygame.Rect | None = None
        self._projectiles: list[dict[str, Any]] = []
        self._last_player_velocity = pygame.Vector2(0.0, 0.0)

        self._bezier_path: list[tuple[float, float]] = []
        self._bezier_t = 0.0
        self._bezier_dir = 1             # ping-pong traversal of the figure-8

        self._defeat_stage = 0
        self._defeated = False
        self._spore_glow = self._build_spore_glow()

        # Weak points (Feature C, enrichment -- see module-level comment above
        # CUERNOS_OFFSET for how these were measured). BossBase.__init__
        # already set self.weak_points=[] / self.last_weak_point=None; this
        # just populates the list. Declared in canonical (facing-right) space
        # -- _mirror_weak_point() reflects them when the sprite is drawn
        # flipped (facing_direction < 0).
        self.weak_points = [
            WeakPoint(offset=CUERNOS_OFFSET, size=CUERNOS_SIZE,
                      multiplier=CUERNOS_MULTIPLIER, label="cuernos"),
            # Only exposed in phase index 1 (the figure-8/bezier phase) --
            # mirrors the reference boss's own design (adoption spec §3.1).
            WeakPoint(offset=FLANCO_OFFSET, size=FLANCO_SIZE,
                      multiplier=FLANCO_MULTIPLIER, phases=(1,), label="flanco"),
        ]
        self._weak_point_flash_timer = 0.0
        self._weak_point_flash_point: WeakPoint | None = None

        self.set_phases()

    def set_phases(self, phases: list[BossPhase] | None = None) -> None:
        if phases is not None:
            super().set_phases(phases)
            return
        super().set_phases([
            BossPhase(phase_index=0, health_threshold=12.0,
                      attack_patterns=["STOMP", "CHARGE", "VINE_TOSS"],
                      movement_type="sine", speed_multiplier=1.0),
            # AUD-257 — la segunda fase declara `escala`. El campo existía en
            # `BossPhase` desde F5.7 y **ningún jefe lo usaba**, así que el
            # motor lo leía y lo tiraba (GAP-032). Éste es el jefe de
            # referencia: si el patrón no está aquí, no está en el material
            # que los estudiantes copian.
            #
            # 1,25 y no 2: el venado enloquecido tiene que caber en su cenador
            # y seguir siendo esquivable. La escala se nota en la silueta y en
            # el alcance, no en volver el combate imposible.
            BossPhase(phase_index=1, health_threshold=6.0,
                      attack_patterns=["VINE_SWEEP", "MUSHROOM_SPORE", "CHARGE"],
                      movement_type="bezier", speed_multiplier=1.5,
                      escala=1.25),
        ])

    def _load_extra_sprites(self) -> None:
        """frenzy_drift/skull are not in BossBase's 6 fixed keys — load manually."""
        from pathlib import Path
        base = Path("assets/sprites/bosses")
        for key in ("frenzy_drift", "skull"):
            path = base / f"boss_venado_{key}.png"
            try:
                self._sprite_frames[key] = AssetLoader.load_sprite_sheet(path, 48, 48)
            except (pygame.error, FileNotFoundError, PermissionError):
                logging.warning("boss_venado: failed to load sprite %s", path)

    def _check_detection_range(self) -> bool:
        """Design fix: guards the whole ARENA, not the whole map. The
        loader/CollisionSystem set player_ref from frame 1 (long before the
        player ever reaches the arena), so a bare `player_ref is not None`
        check kept the boss permanently ALERT and let range-less VINE_TOSS
        (a ~2500px Bezier arc) snipe the player across the entire corridor.
        Aggro now only engages once the player nears the arena mouth."""
        return self._player_ref is not None and self._player_ref.centerx >= AGGRO_X

    def _should_retreat(self) -> bool:
        """ENGINE V2 compatibility fix: EnemyBase._should_retreat (enemy_base.py
        ~L841-843) forces state=RETREAT once current_health drops to
        RETREAT_HEALTH_FRACTION (25%) of max_health -- with max_health=12.0 that
        is current_health<=3.0, deep in phase 2 -- and hands control to the
        generic _retreat_behavior (~L882-890), which walks the boss away from
        the player with no notion of ARENA_X0/X1 and can push it clean out of
        the arena. The Venado's official design (17_BOSS_SPEC §3) has no
        retreat state: phase 2's figure-8 pattern and the arena clamp must stay
        authoritative for the whole fight, so this override opts the boss out
        entirely."""
        return False

    # ──────────────────────────────────────────────
    # Template contract (5 methods)
    # ──────────────────────────────────────────────
    def _patrol_behavior(self, dt: float) -> None:
        self._update_movement(dt)

    def _alert_behavior(self, dt: float) -> None:
        self._update_movement(dt)
        # Hallazgo C fix: neither punish recover (STOMP grounded, CHARGE wall
        # pause) may be interrupted by a new attack starting mid-window.
        if (self.is_transitioning or self._telegraph or self._charge_active
                or self._stomp_recover > 0 or self._charge_recover > 0):
            return
        phase = self.phases[self.current_phase]
        for pattern in phase.attack_patterns:
            if self._attack_timers.get(pattern, 0.0) <= 0.0:
                self._try_attack(pattern)

    def _get_animation_key(self) -> str:
        if self._charge_active or self._telegraph == "CHARGE" or self._charge_recover > 0:
            return "charge"
        if self._telegraph == "STOMP" or self._stomp_window > 0 or self._stomp_recover > 0:
            return "stomp"
        if self._telegraph == "VINE_SWEEP" or self._sweep_window > 0:
            return "vine"
        if self.current_phase >= 1 and "frenzy_drift" in self._sprite_frames:
            return "frenzy_drift"
        return "drift"

    def _build_hitbox(self) -> pygame.Rect:
        return pygame.Rect(6, 4, 36, 44)          # 17_BOSS_SPEC §3.2 (local space)

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(9, 4, 30, 40)          # 30x40 centered in 48x48 (local)

    # AUD-606 — `_mirror_weak_point` retirado: el espejado por facing vive
    # ahora en `WeakPoint.rect_for(facing=...)`, activado por la bandera de
    # clase `cajas_siguen_al_cuerpo`. Mantener los dos habría producido un
    # doble espejo — el punto de vuelta al lado equivocado.

    # ──────────────────────────────────────────────
    # Movement
    # ──────────────────────────────────────────────
    def _approach_y(self, target: float, dt: float) -> bool:
        """H-04/H-08 design fix: move position.y toward target, clamped to
        VERTICAL_ATTACK_SPEED*dt per frame. Reused by STOMP's ground-plant,
        CHARGE's melee-band sweep, and the post-attack y-recovery below — no
        instant teleport in any of the three cases. Returns True once
        position.y has landed exactly on target (the remaining gap fit
        inside this frame's step budget) so callers can tell recovery is
        done WITHOUT a second, separately-thresholded snap on top of this
        one — an earlier version re-checked the post-step distance against
        its own ~2px tolerance and stamped again when under it, which could
        add up to ~2px on top of the already-clamped step in the same frame
        (caught by test_y_recovery_after_attack_is_bounded_no_teleport)."""
        delta = target - self.position.y
        step = VERTICAL_ATTACK_SPEED * dt
        if abs(delta) <= step:
            self.position.y = target
            return True
        self.position.y += step if delta > 0 else -step
        return False

    def _update_movement(self, dt: float) -> None:
        if not self.phases or self.current_phase >= len(self.phases):
            return
        if self._charge_active:
            return                        # charge overrides the base pattern (_update_charge owns y too)
        # Hallazgo C fix: freeze X for the whole STOMP telegraph+window+
        # recover cycle and for the CHARGE wall pause -- the old sine drift
        # kept nudging position.x throughout STOMP, undermining the bots'
        # assumption of a quasi-static punish target (FINDINGS.md Hallazgo
        # C, point 1). STOMP still plants to the floor via _approach_y (now
        # covering the recover too, not just the telegraph+window) so the
        # punish window stays grounded; CHARGE's wall pause needs no extra Y
        # handling -- _update_charge already swept it into the melee band
        # right before the dash stopped, and this early return just leaves
        # that position alone. _y_recovering is armed later, by
        # _update_attack_state, once the relevant recover timer expires --
        # not here anymore (see that method).
        grounded_punish = (self._telegraph == "STOMP" or self._stomp_window > 0
                            or self._stomp_recover > 0)
        if grounded_punish or self._charge_recover > 0:
            if grounded_punish:
                self._approach_y(GROUND_Y, dt)
            return
        phase = self.phases[self.current_phase]
        speed = DRIFT_SPEED * phase.speed_multiplier

        if phase.movement_type == "sine":
            self._elapsed += dt
            self.position.x += speed * dt * self.facing_direction
            target_y = self._base_y + SINE_AMPLITUDE * math.sin(
                2 * math.pi * SINE_FREQ * self._elapsed)
            if self._y_recovering:
                # H-04/H-08 recovery: no snap back to the sine formula --
                # ease toward it at the same clamped speed, then re-lock the
                # instant _approach_y itself lands exactly on target_y.
                if self._approach_y(target_y, dt):
                    self._y_recovering = False
            else:
                self.position.y = target_y
            if self.position.x < ARENA_X0 + 32:   # left clamp margin keeps the boss clear of the wall
                self.position.x = ARENA_X0 + 32
                self.facing_direction = 1
            elif self.position.x > ARENA_X1 - 80:  # right margin: 48px sprite + 32px melee gap
                self.position.x = ARENA_X1 - 80
                self.facing_direction = -1
        elif phase.movement_type == "bezier" and self._bezier_path:
            self._bezier_t += 0.12 * dt * phase.speed_multiplier * self._bezier_dir  # ~8.3 s per figure-8 leg at 1x speed
            # Ping-pong at the ends: reverses direction instead of jumping back to
            # t=0, which avoids a visual teleport across the whole figure-8.
            if self._bezier_t >= 1.0:
                self._bezier_t, self._bezier_dir = 1.0, -1
            elif self._bezier_t <= 0.0:
                self._bezier_t, self._bezier_dir = 0.0, 1
            px, py = CurveTools.sample_path(self._bezier_path, self._bezier_t)
            self.position.x = px
            if self._y_recovering:
                # Same H-08 recovery technique as the sine branch, but easing
                # toward the figure-8 path's y instead of the sine formula.
                if self._approach_y(py, dt):
                    self._y_recovering = False
            else:
                self.position.y = py

    def _build_figure8_path(self) -> list[tuple[float, float]]:
        """Official §3.5: pre-computed figure-8, 6 control points, degree-5 Bezier.

        P5 (the endpoint, which the curve passes through exactly) carries the
        +-45 dip; interior points only attract. At the nominal +-70 the
        endpoint (cy+70=530) put the deer's feet past the floor
        (530+48=578 > FLOOR_Y=560). +-45 keeps the endpoint at y=505
        (505+48=553), inside the arena and the melee-reachable window
        (test_figure8_path_inside_arena_and_reachable: [500, 560]).
        """
        cy = self._base_y
        pts = [
            (ARENA_X0 + 60.0,  cy),
            (ARENA_CX - 120.0, cy - 45.0),
            (ARENA_CX + 120.0, cy + 45.0),
            (ARENA_X1 - 110.0, cy),
            (ARENA_CX + 120.0, cy - 45.0),
            (ARENA_CX - 120.0, cy + 45.0),
        ]
        return CurveTools.bezier(pts, 64)              # Unit III

    # ──────────────────────────────────────────────
    # Attacks
    # ──────────────────────────────────────────────
    def _try_attack(self, pattern: str) -> None:
        pr = self._player_ref
        if pr is None:
            return
        if pattern == "STOMP":
            if abs(pr.centerx - self.rect.centerx) <= 96:
                self._telegraph, self._telegraph_timer = "STOMP", STOMP_TELEGRAPH
                self._attack_timers[pattern] = self._attack_cooldowns[pattern]
        elif pattern == "CHARGE":
            if (pr.centerx < ARENA_CX) != (self.rect.centerx < ARENA_CX):
                self._telegraph, self._telegraph_timer = "CHARGE", CHARGE_TELEGRAPH
                self._attack_timers[pattern] = self._attack_cooldowns[pattern]
        elif pattern == "VINE_TOSS":
            self._do_vine_toss(pr)
            self._attack_timers[pattern] = self._attack_cooldowns[pattern]
        elif pattern == "VINE_SWEEP":
            self._telegraph, self._telegraph_timer = "VINE_SWEEP", SWEEP_TELEGRAPH
            self._attack_timers[pattern] = self._attack_cooldowns[pattern]
        elif pattern == "MUSHROOM_SPORE":
            self._do_mushroom_spore(pr)
            self._attack_timers[pattern] = self._attack_cooldowns[pattern]

    def _update_attack_state(self, dt: float) -> None:
        if self.is_transitioning:
            return
        for k in self._attack_timers:
            if self._attack_timers[k] > 0:
                self._attack_timers[k] -= dt
        if self._telegraph:
            self._telegraph_timer -= dt
            if self._telegraph_timer <= 0:
                pattern, self._telegraph = self._telegraph, ""
                if pattern == "STOMP":
                    self._do_stomp()
                elif pattern == "CHARGE":
                    self._do_charge()
                elif pattern == "VINE_SWEEP":
                    self._sweep_window = SWEEP_WINDOW
                    self._sweep_rect = pygame.Rect(
                        int(ARENA_X0), int(FLOOR_Y) - 24,
                        int(ARENA_X1 - ARENA_X0), 24)
                    if self._event_bus is not None:
                        # SFX only -- NOT Events.BOSS_ATTACK here (Hallazgo D
                        # candado, dodger regression guard; see FINDINGS.md).
                        self._event_bus.emit(Events.SFX_BOSSES_VENADO_VINE)
                # freshly opened windows must not decay on the same tick (unclamped dt hitches)
                return
        if self._stomp_window > 0:
            self._stomp_window -= dt
            if self._stomp_window <= 0:
                self._stomp_rect = None
                # Hallazgo C fix: hand off to a grounded, harmless punish
                # recover instead of arming _y_recovering directly here (see
                # test_stomp_has_grounded_punish_recover). The `elif` below
                # can't fire in this same call -- we only entered this `if`
                # because _stomp_window was already >0 before the decrement
                # -- so the freshly-armed recover doesn't lose a tick, same
                # spirit as the telegraph's own early `return` above.
                self._stomp_recover = STOMP_RECOVER
        elif self._stomp_recover > 0:
            self._stomp_recover -= dt
            if self._stomp_recover <= 0:
                self._y_recovering = True
        if self._charge_recover > 0:
            # Hallazgo C fix: CHARGE's own stationary wall-pause punish
            # window (armed by _update_charge on wall-stop).
            self._charge_recover -= dt
            if self._charge_recover <= 0:
                self._y_recovering = True
        if self._sweep_window > 0:
            self._sweep_window -= dt
            if self._sweep_window <= 0:
                self._sweep_rect = None

    def _do_stomp(self) -> None:
        self._stomp_rect = pygame.Rect(
            self.rect.centerx - 48, int(FLOOR_Y) - 8, 96, 8)
        self._stomp_window = STOMP_WINDOW
        if self._event_bus is not None:
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="STOMP", rect=self._stomp_rect)
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_STOMP)

    def _do_charge(self) -> None:
        pr = self._player_ref
        if pr is None:
            return
        to_player = pygame.Vector2(pr.centerx - self.rect.centerx, 0.0)
        if to_player.length_squared() == 0:
            to_player = pygame.Vector2(float(self.facing_direction), 0.0)
        direction = vec2_normalize(to_player)               # Unit II: vec2_normalize
        self._charge_direction = 1 if direction.x >= 0 else -1
        self.facing_direction = self._charge_direction
        self._charge_active = True
        if self._event_bus is not None:
            # H-08 parity with _do_stomp: without this, CHARGE executes (the
            # boss dashes) but nothing observable ever announces it.
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="CHARGE", rect=self.rect)
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_CHARGE)

    def _update_charge(self, dt: float) -> None:
        if not self.phases or self.current_phase >= len(self.phases):
            return
        # dash stops closer to the wall than the sine margins (32/80) above — keep
        # 16<32 and 64<80 or facing_direction can point into the wall after a
        # wall-stop (sine re-clamp self-corrects in 1 frame)
        speed = CHARGE_SPEED_P1 if self.current_phase == 0 else CHARGE_SPEED_P2
        self.position.x += self._charge_direction * speed * dt
        self._approach_y(CHARGE_BAND_Y, dt)   # H-08: sweep down into the melee band while dashing
        if self.position.x <= ARENA_X0 + 16 or self.position.x >= ARENA_X1 - 64:
            self.position.x = max(ARENA_X0 + 16, min(self.position.x, ARENA_X1 - 64))
            self._charge_active = False
            # Hallazgo C fix: pause at the wall for CHARGE_WALL_PAUSE seconds
            # (a stationary punish window -- see
            # test_charge_wall_pause_is_stationary_punish_window) instead of
            # handing off straight to _y_recovering; _update_attack_state
            # arms that once the pause itself expires.
            self._charge_recover = CHARGE_WALL_PAUSE

    def _do_vine_toss(self, pr: pygame.Rect) -> None:
        # 18.0/-6.0: student's visual choice, approx. deer muzzle position
        # (slightly ahead of center, a bit above the vertical midline).
        muzzle = (self.rect.centerx + 18.0 * self.facing_direction,
                  self.rect.centery - 6.0)
        predicted_vec = (pygame.Vector2(pr.centerx, pr.centery)
                         + self._last_player_velocity * VINE_PREDICT)   # Unit II
        # 16.0: half player height — keeps the target at the player's
        # center (not their feet) when they are grounded.
        predicted = (predicted_vec.x, min(predicted_vec.y, FLOOR_Y - 16.0))
        midpoint = ((muzzle[0] + predicted[0]) / 2.0,
                    min(muzzle[1], predicted[1]) - VINE_ARC_HEIGHT)     # §3.5 arc
        path = CurveTools.bezier([muzzle, midpoint, predicted], 32)     # Unit III
        self._projectiles.append({
            "type": "vine", "path": path, "t": 0.0, "speed": VINE_SPEED,
            "pos": pygame.Vector2(muzzle), "damage": 0.5, "alive": True,
        })
        if self._event_bus is not None:
            # Hallazgo D fix: STOMP/CHARGE already announce themselves --
            # projectiles didn't, leaving the dodger structurally blind to
            # this attack (measured: 0 frames of warning, FINDINGS.md
            # Hallazgo D). Muzzle-sized rect, in parity with _do_stomp's own
            # attack-shaped rect (not the boss's full body).
            muzzle_rect = pygame.Rect(int(muzzle[0] - 5), int(muzzle[1] - 5), 10, 10)
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="VINE_TOSS", rect=muzzle_rect)
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_VINE)

    def _do_mushroom_spore(self, pr: pygame.Rect) -> None:
        origin = pygame.Vector2(self.rect.centerx, self.rect.centery)
        to_player = pygame.Vector2(pr.centerx, pr.centery) - origin
        if to_player.length_squared() == 0:
            to_player = pygame.Vector2(0.0, 1.0)
        center_dir = vec2_normalize(to_player)          # Unit II: aim at cast
        for angle in (-15.0, 0.0, 15.0):                # official spread L/C/R
            self._projectiles.append({
                "type": "spore",
                "pos": pygame.Vector2(origin),
                "origin": pygame.Vector2(origin),
                "vel": center_dir.rotate(angle) * SPORE_SPEED,
                "damage": 0.25, "alive": True, "age": 0.0,
            })
        if self._event_bus is not None:
            # Hallazgo D fix: same parity as _do_vine_toss above. Uses the
            # boss's own rect (the cast point, not a single spore) since the
            # attack is a 3-way fan, not one point-source projectile.
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="MUSHROOM_SPORE", rect=self.rect)
            # Only 3 Venado wavs exist (no dedicated spore sound) -- reuse VINE.
            # Deliberate deviation from the reference boss, which leaves this
            # attack silent (spec 2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §1.1).
            self._event_bus.emit(Events.SFX_BOSSES_VENADO_VINE)

    # ──────────────────────────────────────────────
    # Projectiles
    # ──────────────────────────────────────────────
    def _update_projectiles(self, dt: float) -> None:
        for proj in self._projectiles:
            if not proj["alive"]:
                continue
            if proj["type"] == "vine":
                proj["t"] += proj["speed"] * dt
                if proj["t"] >= 1.0:
                    proj["alive"] = False
                    continue
                px, py = CurveTools.sample_path(proj["path"], proj["t"])
                proj["pos"] = pygame.Vector2(px, py)
            elif proj["type"] == "spore":
                proj["age"] += dt
                proj["pos"] += proj["vel"] * dt
                if (proj["age"] >= SPORE_LIFETIME
                        or vec2_distance(proj["pos"], proj["origin"]) > SPORE_RANGE):
                    proj["alive"] = False                               # Unit II
        self._projectiles = [p for p in self._projectiles if p["alive"]]

    # ──────────────────────────────────────────────
    # Player interaction
    # ──────────────────────────────────────────────
    def _check_player_contact(self, player) -> None:
        """Engine hook (CollisionSystem.update_enemies calls this every frame
        before entity.update()): adds projectile/stomp/sweep damage on top of
        EnemyBase's body-contact check, then delegates to super() for the
        latter."""
        self._last_player_velocity = pygame.Vector2(player.velocity)  # feeds VINE_TOSS prediction
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for proj in self._projectiles:
            if not proj.get("alive") or "pos" not in proj:
                continue
            r = pygame.Rect(int(proj["pos"].x - PROJECTILE_HIT_RADIUS),
                            int(proj["pos"].y - PROJECTILE_HIT_RADIUS),
                            int(PROJECTILE_HIT_RADIUS * 2), int(PROJECTILE_HIT_RADIUS * 2))
            if r.colliderect(player_hurtbox):
                player.apply_damage(proj["damage"], self.rect.center)
                proj["alive"] = False
        if self._stomp_rect is not None and self._stomp_rect.colliderect(player_hurtbox):
            # hardcoded like the professor's reference boss (vine/spore carry damage in their dicts instead)
            player.apply_damage(1.0, self.rect.center)          # official STOMP dmg
            self._stomp_rect = None
            self._stomp_window = 0.0
        if self._sweep_window > 0 and self._sweep_rect is not None:
            if self._sweep_rect.colliderect(player_hurtbox):
                # hardcoded like the professor's reference boss (vine/spore carry damage in their dicts instead)
                player.apply_damage(0.5, self.rect.center)      # official SWEEP dmg
                self._sweep_window = 0.0
                self._sweep_rect = None
        super()._check_player_contact(player)

    # ──────────────────────────────────────────────
    # Lifecycle / engine wiring
    # ──────────────────────────────────────────────
    def _finish_phase_transition(self) -> None:
        """Engine hook: on top of the base's phase advance + event/VFX/stinger,
        (re)build the figure-8 flight path when entering a bezier-movement phase."""
        super()._finish_phase_transition()
        # AUD-263 — el venado habla. `play_voz` existía desde los buses de
        # AUD-144 y **no la llamaba nadie**: el motor sabía reproducir voz y no
        # había un solo fichero (GAP-031). Las líneas se sintetizan con el mismo
        # generador que produce todos los demás sonidos del proyecto.
        self._decir(f"sfx_voz_venado_fase{self.current_phase + 1}")
        # Y la fase 2 abre su nube de esporas nada más entrar, para que el
        # cambio se vea además de oírse.
        if self.current_phase >= 1:
            self._soltar_abanico_de_esporas()
        if self.phases[self.current_phase].movement_type == "bezier":
            self._bezier_path = self._build_figure8_path()
            self._bezier_t, self._bezier_dir = 0.0, 1
        # AUD-257 — `teletransportar` no tenía **ni un solo llamante** en todo
        # el repositorio (GAP-032). Su sitio natural es éste: el jefe
        # desaparece del punto donde el jugador lo tenía acorralado y reaparece
        # en el centro de la arena, que es lo que hace legible un cambio de
        # fase —y lo que impide encerrar al venado contra una pared durante
        # toda la pelea—. Sin arena declarada no se mueve: teletransportar a
        # ciegas podría dejarlo fuera del mapa.
        if self.arena_bounds is not None:
            self.teletransportar(
                float(self.arena_bounds.centerx - self.rect.width // 2),
                float(self.position.y),
            )
            self.clamp_to_arena()

    def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
        """EnemyBase.apply_hit (enemy_base.py:390-391) calls _die() synchronously
        when health drops to 0, and _die() (enemy_base.py:402-418) sets
        state=DYING itself before control returns here — so a `state != DYING`
        guard would be unreachable (verified: it is already DYING by this
        point). is_alive is left untouched by _die() (comment at
        enemy_base.py:410-411: it stays True until the scripted death
        sequence finishes), so the guard mirrors the professor's reference
        boss (backups/boss_venado_original_src/boss_venado.py:388-391): only
        current_health<=0 and is_alive, no state check.

        Weak points (Feature C, spec
        2026-07-29-adopcion-v2-sfx-luces-weakpoints-design.md §3.3) are
        resolved HERE, before delegating to super(), by calling
        resolve_weak_point_damage() directly -- deliberately NOT
        apply_hit_at(). apply_hit_at() (boss_base.py) is the "official" API
        for this, but nothing in the real damage flow ever calls it: the one
        real melee call site (collision_system.py process_attack) discards
        the player's swing hitbox and calls the plain
        apply_hit(damage, source_position) -- verified by grep, zero call
        sites outside boss_base.py/boss_kit.py themselves. self._player_ref
        (the player's own rect, kept live every frame by
        StageScene._update_gameplay -> enemy.set_player_ref, same object,
        not a copy) is the best available proxy for "where the hit landed"
        without touching that engine file. Calling super().apply_hit()
        afterwards (not apply_hit_at()) keeps this a single, non-recursive
        chain and preserves every existing i-frame/transition-invulnerable
        check already living in that chain -- the multiplier only changes
        the `damage` argument, never bypasses how it's applied.
        """
        final_damage = damage
        hit_point: WeakPoint | None = None
        if self._player_ref is not None and self.weak_points:
            # AUD-606 — sin pre-espejo: `cajas_siguen_al_cuerpo = True` hace
            # que resolve_weak_point_damage espeje por facing y escale con la
            # fase dentro del propio motor. Antes este jefe armaba la lista
            # espejada a mano, que era la compensación mientras el motor no
            # supiera hacerlo.
            final_damage, hit_point = resolve_weak_point_damage(
                self, self._player_ref, damage, self.weak_points,
                self.current_phase,
            )
        self.last_weak_point = hit_point
        if hit_point is not None:
            self._weak_point_flash_timer = WEAK_POINT_FLASH_DURATION
            self._weak_point_flash_point = hit_point

        super().apply_hit(final_damage, source_position)
        # one-shot: the reference boss restarts its death sequence when hit while dying;
        # the flag keeps the defeat timeline monotonic (QA gate stage_complete_on_death relies on it)
        if self.current_health <= 0 and self.is_alive and not self._defeated:
            self.on_defeated()

    def _decir(self, linea: str) -> None:
        """Una línea de voz, si hay quien la reproduzca (AUD-263).

        `play_voz` aparta la música al 35 % por su cuenta —es el único método
        del mezclador que lo hace solo— así que aquí no hay que pedir el
        ducking: pedirlo aparte es lo que garantiza olvidarlo en la mitad de
        las líneas.
        """
        audio = self.audio_de_voz
        if audio is not None and hasattr(audio, "play_voz"):
            audio.play_voz(linea)

    #: Esporas por abanico y su alcance. Doce y no cien: la nube tiene que
    #: leerse como un patrón que se esquiva, no como una pared.
    _ESPORAS_POR_ABANICO = 12
    _VELOCIDAD_ESPORA = 70.0

    def _soltar_abanico_de_esporas(self) -> None:
        """La nube de la fase 2 (AUD-263).

        Un abanico completo desde el centro del jefe: `EnjambreDeBalas.abanico`
        calcula los ángulos con NumPy de una vez, que es la razón por la que
        este patrón cabe en el fotograma.
        """
        self.esporas.abanico(
            float(self.rect.centerx), float(self.rect.centery),
            cuantas=self._ESPORAS_POR_ABANICO,
            velocidad=self._VELOCIDAD_ESPORA,
            vida=3.0, dano=0.5, radio=3.0,
        )

    def update(self, dt: float) -> None:
        """DYING short-circuits before touching any engine machinery: the death
        sequence (Task 9's _update_defeat) is scripted by hand, same as the
        professor's reference boss, so it must not race EnemyBase's own
        tick_cooldowns/state-machine DYING branch. Charge is skipped while
        is_transitioning (BossBase._pre_update freezes the state machine for
        the phase-change overlay) so the dash cannot reposition the boss
        during a frame the player sees as frozen. _filter_frame is the counter
        BossBase._apply_filter reads to throttle the phase filter_effect to
        once every 5 frames (_APPLY_FILTER_EVERY_N_FRAMES). update() is
        overridden wholesale — instead of the usual _pre_update/_post_update
        hooks — for the same reason: parity with how the reference boss wires
        its own attack/projectile pipeline around the DYING branch.
        """
        if self.state == EnemyState.DYING:
            self._update_defeat(dt)
            return
        if self._charge_active and not self.is_transitioning:
            self._update_charge(dt)
        self._update_attack_state(dt)
        self._update_projectiles(dt)
        self.esporas.update(dt)
        if self._weak_point_flash_timer > 0:
            self._weak_point_flash_timer = max(0.0, self._weak_point_flash_timer - dt)
        # ENGINE V2: BossBase._apply_filter now increments self._filter_frame
        # itself (boss_base.py ~L426); incrementing it here too was doubling
        # the phase-2 filter_effect cadence.
        super().update(dt)

    # ── Defeat sequence ──
    def on_defeated(self) -> None:
        self._decir("sfx_voz_venado_muerte")          # AUD-263
        self._defeated = True
        # state is already DYING here — _die() (enemy_base.py) set it before apply_hit() returned.
        self._death_timer = 1.5                       # death anim (12f @ 8fps)
        self._defeat_stage = 0
        self._projectiles.clear()
        self._charge_active = False
        self._charge_recover = 0.0
        self._telegraph = ""
        self._stomp_rect = None
        self._stomp_window = 0.0
        self._stomp_recover = 0.0
        self._y_recovering = False
        self._sweep_window = 0.0
        self._sweep_rect = None
        self._weak_point_flash_timer = 0.0
        self._weak_point_flash_point = None

    def _update_defeat(self, dt: float) -> None:
        self._death_timer -= dt
        self._advance_animation(dt)
        if self._death_timer <= 0:
            if self._defeat_stage == 0:
                self._defeat_stage, self._death_timer = 1, 2.0   # skull 2s (§3.6)
            elif self._defeat_stage == 1:
                self._defeat_stage = 2
                self._death_timer = 0.0
                self.is_alive = False
                self.is_active = False

    # ── Rendering (Unit IV: explicit painter's order) ──
    def _build_spore_glow(self) -> pygame.Surface:
        """Cached ONCE: ColorTools.alpha_blend halo+core (Unit V, perf-safe)."""
        core = pygame.Surface((16, 16))
        halo = pygame.Surface((16, 16))
        pygame.draw.circle(core, (240, 250, 200), (8, 8), 4)
        pygame.draw.circle(halo, (120, 220, 140), (8, 8), 8)
        glow = ColorTools.alpha_blend(halo, core, 0.55)          # Unit V
        glow.set_colorkey((0, 0, 0))
        return glow

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)          # 1) body (BossBase sprite)
        self._draw_telegraphs(surface, camera_offset) # 2) warnings
        self._draw_projectiles(surface, camera_offset)# 3) projectiles
        self.esporas.draw(surface, camera_offset)     # 3b) esporas (AUD-263)
        self._draw_transition_pulse(surface, camera_offset)  # 4) color VFX
        self._draw_weak_point_flash(surface, camera_offset)  # 5) crit confirmation
        if self._defeat_stage == 1:
            self._draw_skull(surface, camera_offset)

    def _draw_telegraphs(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        ox, oy = camera_offset.x, camera_offset.y
        if self._telegraph == "STOMP":
            r = pygame.Rect(int(self.rect.centerx - 48 - ox), int(FLOOR_Y - 6 - oy), 96, 4)
            pygame.draw.rect(surface, self._TELEGRAPH_WARN_COLOR, r)
        elif self._telegraph == "CHARGE":
            cx = int(self.rect.centerx - ox)
            cy = int(self.rect.centery - oy)
            tip = cx + self._sign_to_player() * 34
            pygame.draw.polygon(surface, self._TELEGRAPH_WARN_COLOR,
                                [(tip, cy), (tip - 10 * self._sign_to_player(), cy - 6),
                                 (tip - 10 * self._sign_to_player(), cy + 6)])
        elif self._telegraph == "VINE_SWEEP":
            r = pygame.Rect(int(ARENA_X0 - ox), int(FLOOR_Y - 24 - oy),
                            int(ARENA_X1 - ARENA_X0), 3)
            pygame.draw.rect(surface, self._TELEGRAPH_WARN_COLOR, r)
        if self._stomp_window > 0 and self._stomp_rect is not None:
            r = self._stomp_rect.move(int(-ox), int(-oy))
            pygame.draw.rect(surface, (250, 220, 120), r)
        if self._sweep_window > 0 and self._sweep_rect is not None:
            r = self._sweep_rect.move(int(-ox), int(-oy))
            pygame.draw.rect(surface, (140, 200, 110), r, 2)

    def _sign_to_player(self) -> int:
        pr = self._player_ref
        if pr is None:
            return self.facing_direction
        return 1 if pr.centerx >= self.rect.centerx else -1

    def _draw_projectiles(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        ox, oy = camera_offset.x, camera_offset.y
        for proj in self._projectiles:
            if not proj.get("alive") or "pos" not in proj:
                continue
            sx, sy = int(proj["pos"].x - ox), int(proj["pos"].y - oy)
            surface.blit(self._spore_glow, (sx - 8, sy - 8))     # Unit V visible
            if proj["type"] == "vine":
                pygame.draw.circle(surface, (110, 170, 90), (sx, sy), int(PROJECTILE_HIT_RADIUS))
                pygame.draw.circle(surface, (230, 245, 210), (sx, sy), int(PROJECTILE_HIT_RADIUS), 1)
            else:
                pygame.draw.circle(surface, (200, 180, 120), (sx, sy), 4)

    def _draw_transition_pulse(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.is_transitioning:
            return
        # ColorTools.rgb_to_hsv returns h in [0, 360] (color_tools.py:18-35),
        # not the [0, 1] a naive reading of the spec might assume — so the
        # per-second increment is expressed in degrees (0.4 * 360 = 144.0)
        # and wrapped mod 360, not mod 1.0.
        h, s, v = ColorTools.rgb_to_hsv(120, 220, 140)           # Unit V: HSV pulse
        h = (h + (2.5 - self.transition_timer) * 144.0) % 360.0
        color = ColorTools.hsv_to_rgb(h, s, v)
        cx = int(self.rect.centerx - camera_offset.x)
        cy = int(self.rect.centery - camera_offset.y)
        radius = 30 + int(8 * math.sin(self.transition_timer * 12.0))
        pygame.draw.circle(surface, color, (cx, cy), radius, 3)

    def _draw_weak_point_flash(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Feature C crit feedback: NOT Events.VFX_PARRY -- that event is
        already wired (stage_scene.py) but semantically means "parry",
        reusing it here would teach the player that a horn/flank hit is a
        parry (spec §3.1). Uses ColorTools directly, same as the rest of
        this boss's own VFX (_build_spore_glow / _draw_transition_pulse)
        instead of depending on a motor VFX event.
        """
        if self._weak_point_flash_timer <= 0 or self._weak_point_flash_point is None:
            return
        # rect_for() is recomputed every frame against the LIVE self.rect (not
        # cached at hit time) so the flash tracks the boss instead of hanging
        # in the world while it keeps drifting/flying during the ~0.12s flash.
        # AUD-606 — con la misma escala de fase y espejo de facing que usa
        # resolve_weak_point_damage, o el destello se pintaba donde el punto
        # ya no está (fase 2 crecida, sprite volteado).
        rect = self._weak_point_flash_point.rect_for(
            self.rect,
            escala=self._escala_viva(),
            facing=self.facing_direction,
        )
        ox, oy = camera_offset.x, camera_offset.y
        r = rect.move(int(-ox), int(-oy))
        # Unit V: HSV pulse, same technique as _draw_transition_pulse --
        # brightness ramps down with the timer instead of an abrupt on/off
        # blink, so a crit reads as a short flash, not a static decal.
        fade = max(0.0, min(1.0, self._weak_point_flash_timer / WEAK_POINT_FLASH_DURATION))
        color = ColorTools.hsv_to_rgb(self._WEAK_POINT_FLASH_HUE, 0.9, 0.55 + 0.45 * fade)
        tint = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        tint.fill((*color, int(190 * fade)))
        surface.blit(tint, r.topleft)
        pygame.draw.rect(surface, color, r, 2)

    def _draw_skull(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        frames = self._sprite_frames.get("skull")
        x = int(self.rect.x - camera_offset.x); y = int(self.rect.y - camera_offset.y)
        if frames:
            surface.blit(frames[0], (x, y))
        else:
            cx, cy = x + 24, y + 24
            pygame.draw.circle(surface, (235, 235, 220), (cx, cy), 10)
