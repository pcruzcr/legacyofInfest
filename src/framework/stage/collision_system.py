"""
Module: collision_system
System: framework.stage
Academic Unit: Unit IV — Collision detection

Combat-space arbitration: resolves the player's attack hitbox against enemy
hurtboxes, applies damage, knockback and hit-stop.

SCOPE (AUD-004). This module deliberately does *not* own locomotion physics.
Movement, gravity and world collision for the player and for enemies are
resolved by their own swept-AABB integrators (``Player.update`` and
``EnemyBase.update``), which are authoritative. An earlier revision of this
file claimed to run a pymunk/Chipmunk2D rigid-body simulation and constructed
a ``pymunk.Space``, dynamic bodies, collision categories and a one-way
platform helper — but nothing in the game ever called the methods that
populated that space. The space was empty on every frame, so:

  * ``apply_knockback`` looked up an always-empty body map and silently did
    nothing on every hit;
  * ``step`` integrated a world containing zero bodies, every frame;
  * ``update_enemies`` ran an O(n) no-op sync loop, every frame;
  * the ``_CAT_*`` constants were assigned to ``shape.collision_type`` (a
    handler-dispatch key) rather than to ``shape.filter`` (the actual bitmask
    filter), and no collision handler was ever registered, so they filtered
    nothing.

Rather than leave a misleading façade in place, the dead simulation has been
removed and the honest behaviour — a broadphase-free AABB pass over the
entity list plus the entity's own knockback impulse — is what the code now
says it is. Reintroducing a real rigid-body pipeline is tracked as a separate
piece of work; see docs/AUDIT_2026-07.md, refactor item R-03.
"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core.clock import FUENTE_HITSTOP
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData


# Impulse applied to an enemy struck by the player, in px/s.
KNOCKBACK_IMPULSE_X: float = 200.0
KNOCKBACK_IMPULSE_Y: float = -100.0
# Freeze duration on a connected hit, in *real* seconds.
HITSTOP_DURATION: float = 0.05


class CollisionSystem:
    """Resolves player attacks against enemies for a single stage.

    Responsibilities
    ----------------
    * Test the player's active attack hitbox against every living enemy's
      hurtbox and apply damage exactly once per swing.
    * Apply knockback to the struck enemy.
    * Drive hit-stop (a brief global freeze that sells the impact).

    Explicitly *not* responsible for locomotion, gravity, world collision or
    one-way platforms — those belong to the entities' own integrators.
    """

    def __init__(self, context: Any = None) -> None:
        self._context = context
        self._hitstop_timer: float = 0.0
        # Enemies already damaged by the *current* swing. Cleared when the
        # player's hitbox is retired, so each swing lands at most once per
        # enemy (AUD-003).
        self._hit_this_swing: set[int] = set()

    # ── lifecycle ──────────────────────────────────────────────

    def reset(self) -> None:
        """Clear all per-stage state. Called on stage load and on respawn."""
        self._hitstop_timer = 0.0
        self._hit_this_swing.clear()

    # ── hit-stop ───────────────────────────────────────────────

    def trigger_hitstop(self, duration: float = HITSTOP_DURATION) -> None:
        """Freeze the simulation for ``duration`` real seconds."""
        # Never shorten an in-flight freeze: a second hit landing mid-stop
        # should extend the impact, not cut it short.
        self._hitstop_timer = max(self._hitstop_timer, duration)

    @property
    def is_hitstopped(self) -> bool:
        return self._hitstop_timer > 0.0

    def update_hitstop(self, unscaled_dt: float, clock: Any = None) -> None:
        """Advance the hit-stop countdown and register its time factor.

        ``unscaled_dt`` MUST be the clock's real, unscaled delta. Passing the
        scaled delta here reintroduces AUD-001: ``time_scale`` drops to 0.0,
        which drives the scaled delta to 0.0, which stops this countdown from
        ever draining — the game freezes permanently on the first landed hit.

        AUD-118 — por qué ya no se escribe ``clock.time_scale = 1.0``
        ------------------------------------------------------------
        La línea anterior era::

            clock.time_scale = 0.0 if self._hitstop_timer > 0.0 else 1.0

        Ese ``else 1.0`` afirma que **nadie más** ha tocado el reloj, y era
        falso: `TiempoBala` lo pone a 0,35 mientras el jugador mantiene la
        cámara lenta. Golpear a un enemigo durante la cámara lenta daba
        ``0.35 → 0.0 → 1.0`` y al fotograma siguiente ``0.35`` otra vez: un
        fotograma a velocidad completa en mitad de la cámara lenta, justo en
        el impacto.

        Ahora el hit-stop registra su factor con su nombre y lo retira al
        acabar; el reloj compone lo que quede. El ``getattr`` conserva los
        dobles de reloj de las entregas de estudiantes, que sólo tienen el
        atributo ``time_scale`` y ninguno de los dos métodos.
        """
        if self._hitstop_timer > 0.0:
            self._hitstop_timer -= unscaled_dt
            if self._hitstop_timer <= 0.0:
                self._hitstop_timer = 0.0
        if clock is None:
            return
        registrar = getattr(clock, "escalar", None)
        retirar = getattr(clock, "restaurar", None)
        if registrar is None or retirar is None:
            clock.time_scale = 0.0 if self._hitstop_timer > 0.0 else 1.0
            return
        if self._hitstop_timer > 0.0:
            registrar(FUENTE_HITSTOP, 0.0)
        else:
            retirar(FUENTE_HITSTOP)

    def step(self, dt: float) -> None:
        """Obsoleto: no hace nada y lo dice en voz alta (AUD-063).

        Se conservaba como no-op silencioso «por compatibilidad». Su hermano
        `update_enemies` hizo exactamente eso durante toda la auditoría y el
        resultado fue que ningún enemigo del juego se movía ni podía dañar al
        jugador: el nombre prometía trabajo, el cuerpo no hacía ninguno, y nadie
        que leyera la llamada tenía forma de saberlo.

        Un método que no hace nada debe **decirlo**, no fingir. Quien lo llame
        recibe un aviso y puede borrar la línea; quien lea el código no puede
        confundirlo con lógica viva.
        """
        warnings.warn(
            "CollisionSystem.step() no hace nada: la resolución de combate "
            "ocurre en process_attack(). Elimina la llamada.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ── knockback ──────────────────────────────────────────────

    def apply_knockback(self, entity: BaseEntity, impulse_x: float, impulse_y: float) -> None:
        """Push ``entity`` away from the attacker.

        Delegates to the entity's own knockback velocity, which is what its
        integrator actually reads.
        """
        kb = getattr(entity, "_knockback_velocity", None)
        if kb is not None:
            kb.x += impulse_x
            kb.y += impulse_y
            return
        velocity = getattr(entity, "velocity", None)
        if velocity is not None:
            velocity.x += impulse_x
            velocity.y += impulse_y

    # ── enemy sync ─────────────────────────────────────────────

    def update_enemies(self, dt: float, player: Player, stage: StageData) -> None:
        """Obsoleto y peligroso de creer. **Ya no actualiza nada** (AUD-063).

        Historia, porque explica por qué este método grita en lugar de callar:
        aquí vivía el bucle que llamaba a `_check_player_contact` y a
        `update(dt)` de cada enemigo. Durante la auditoría lo convertí en un
        no-op con un docstring que afirmaba que no había nada que sincronizar.
        Era falso: **era el único sitio que actualizaba a los enemigos**.
        Resultado, durante toda la remediación: enemigos y jefe inmóviles,
        invulnerables e incapaces de hacer daño (AUD-060, AUD-062).

        La responsabilidad vive ahora en `StageScene._update_gameplay`, que es
        donde corresponde: decidir a quién se actualiza cada fotograma es de la
        escena. Este método permanece sólo para que el código antiguo que lo
        invoque reciba un aviso en lugar de un silencio tranquilizador.
        """
        warnings.warn(
            "CollisionSystem.update_enemies() ya no actualiza a los enemigos; "
            "de eso se encarga StageScene._update_gameplay. Elimina la llamada: "
            "mantenerla sugiere que los enemigos se actualizan aquí y no es así.",
            DeprecationWarning,
            stacklevel=2,
        )

    # ── attack resolution ──────────────────────────────────────

    def process_attack(
        self, dt: float, player: Player, stage: StageData,
        camera: Camera | None = None, clock: Any = None,
    ) -> None:
        """Resolve the player's active hitbox against every living enemy."""
        hitbox = player.active_hitbox
        if hitbox is None:
            # Swing is over (or was consumed) — arm the next one.
            self._hit_this_swing.clear()
            return

        connected = False
        for entity in stage.entity_list:
            if not isinstance(entity, EnemyBase) or not entity.is_alive:
                continue
            if id(entity) in self._hit_this_swing:
                continue
            if not hitbox.colliderect(entity.hurtbox):
                continue

            entity.apply_hit(
                self._calculate_damage(player, entity),
                (player.position.x, player.position.y),
            )
            self.apply_knockback(
                entity,
                player.facing_direction * KNOCKBACK_IMPULSE_X,
                KNOCKBACK_IMPULSE_Y,
            )
            self._hit_this_swing.add(id(entity))
            connected = True

        if connected:
            self.trigger_hitstop(HITSTOP_DURATION)
            # Retire the hitbox so a multi-frame swing cannot re-damage the
            # same enemy on the following frames (AUD-003).
            player.consume_hitbox()

    def _calculate_damage(self, player: Player, enemy: EnemyBase) -> float:
        """Damage this swing deals to ``enemy``.

        Reads the player's public ``current_attack_damage`` property, which
        already folds in attack weight (light 0.5 / heavy 1.0), the combo
        multiplier and the difficulty modifier. The previous implementation
        read a private attribute ``_current_attack_damage`` that has never
        existed on ``Player``, so ``getattr`` always returned its 1.0 fallback
        and every attack in the game dealt a flat 1.0 — light and heavy
        attacks were indistinguishable and the combo system was inert
        (AUD-002).
        """
        damage = getattr(player, "current_attack_damage", None)
        if damage is None:
            from src.engine.core.difficulty import get_config
            return 1.0 * get_config().outgoing_damage_mult
        return float(damage)

    def remove_entity(self, entity: BaseEntity) -> None:
        """Forget any per-swing hit record for ``entity``."""
        self._hit_this_swing.discard(id(entity))

    def draw_debug(
        self, surface: pygame.Surface,
        player: Player | None = None,
        stage: StageData | None = None,
        camera: Camera | None = None,
    ) -> None:
        """Outline the player's active hitbox (green) and enemy hurtboxes (red)."""
        ox, oy = 0.0, 0.0
        if camera is not None:
            ox, oy = camera.offset.x, camera.offset.y

        def _shift(r: pygame.Rect) -> pygame.Rect:
            return pygame.Rect(int(r.x - ox), int(r.y - oy), r.width, r.height)

        if stage is not None:
            for entity in stage.entity_list:
                if isinstance(entity, EnemyBase) and entity.is_alive:
                    pygame.draw.rect(surface, (255, 64, 64), _shift(entity.hurtbox), 1)
        if player is not None and player.active_hitbox is not None:
            pygame.draw.rect(surface, (64, 255, 64), _shift(player.active_hitbox), 1)
