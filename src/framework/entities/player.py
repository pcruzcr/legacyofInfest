"""
Module: player
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit IV (Sprite Animation)
Description: Player entity with full state machine (9 states), physics
(gravity, coyote time, jump cut), damage system (invincibility, knockback),
attack hitboxes (short/long), and hurtbox (standard/crouching).

STATE PATTERN (Fase 2): Per-frame behavior is delegated to a
PlayerStateBase instance (see player_states.py). The Player class
owns shared infrastructure (physics, collision, animation, sprites)
while each state encapsulates its own update logic and transitions.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.surface_pool import get_pool
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.player_state import PlayerStateData
from src.framework.entities.ranged_weapon import ArcoDelJugador

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.states import PlayerStateBase


SPRITE_W = 32
SPRITE_H = 32

# State -> (filename, frame_count)
_PLAYER_SPRITE_MAP: dict[str, tuple[str, int]] = {
    "IDLE": ("player_idle.png", 4),
    "WALKING": ("player_walk.png", 8),
    "JUMPING": ("player_jump.png", 3),
    "FALLING": ("player_fall.png", 2),
    "CROUCHING": ("player_crouch.png", 2),
    "SHORT_ATTACK": ("player_short_attack.png", 6),
    "LONG_ATTACK": ("player_long_attack.png", 10),
    "HURT": ("player_hurt.png", 4),
    "DYING": ("player_die.png", 8),
    "DASHING": ("player_walk.png", 4),
    "PARRY": ("player_hurt.png", 4),
    "CHARGE_ATTACK": ("player_short_attack.png", 4),
    "DASH_ATTACK": ("player_short_attack.png", 4),
    "WALL_SLIDE": ("player_jump.png", 2),
    "GRAB": ("player_short_attack.png", 4),
    "THROW": ("player_short_attack.png", 4),
    "SLIDE": ("player_crouch.png", 4),
    "SWIMMING": ("player_jump.png", 4),
    # F5.14 — lianas y tirolesas. Reutilizan la hoja de salto: el jugador va
    # colgado, y hasta que haya arte propio es mejor un sprite coherente que
    # uno inventado.
    "CLIMBING": ("player_jump.png", 2),
    "ZIPLINE": ("player_jump.png", 2),
    "ULTIMATE": ("player_long_attack.png", 10),
    "AERIAL_ATTACK": ("player_short_attack.png", 6),
    "AERIAL_SLAM": ("player_short_attack.png", 6),
    "AIR_CHASE": ("player_jump.png", 3),
    "CHARGE_RELEASE": ("player_short_attack.png", 4),
    "LEDGE_GRAB": ("player_jump.png", 2),
}

# Per-state animation playback rate (frames per second)
_PLAYER_ANIM_FPS: dict[str, float] = {
    "IDLE": 8.0,
    "WALKING": 12.0,
    "JUMPING": 12.0,
    "FALLING": 8.0,
    "CROUCHING": 8.0,
    "SHORT_ATTACK": 18.0,
    "LONG_ATTACK": 16.0,
    "HURT": 12.0,
    "DYING": 10.0,
    "DASHING": 12.0,
    "PARRY": 16.0,
    "CHARGE_ATTACK": 14.0,
    "DASH_ATTACK": 16.0,
    "WALL_SLIDE": 8.0,
    "GRAB": 14.0,
    "THROW": 16.0,
    "SLIDE": 14.0,
    "SWIMMING": 10.0,
    "CLIMBING": 6.0,
    "ZIPLINE": 8.0,
    # AUD-109 — `LEDGE_GRAB` tenía hoja de sprites y **no** tenía velocidad, así
    # que caía al valor por defecto de 10 fps. No rompía nada, y por eso llevaba
    # ahí desde siempre: agarrarse a un borde con la misma cadencia que correr
    # se ve nervioso, y nadie lo relaciona con una tabla incompleta.
    #
    # Lo encontró la prueba que sustituyó a `assert len(PlayerState) == 24`.
    # Aquélla contaba estados; ésta comprueba que todos se puedan dibujar, y
    # encontró el hueco en la primera ejecución.
    "LEDGE_GRAB": 4.0,
    "ULTIMATE": 16.0,
    "AERIAL_ATTACK": 18.0,
    "AERIAL_SLAM": 16.0,
    "AIR_CHASE": 12.0,
    "CHARGE_RELEASE": 14.0,
}


class PlayerState(str, Enum):
    """All possible player states as defined in 04_PLAYER_SPEC.md §8.1."""
    IDLE = "IDLE"
    WALKING = "WALKING"
    JUMPING = "JUMPING"
    FALLING = "FALLING"
    CROUCHING = "CROUCHING"
    SHORT_ATTACK = "SHORT_ATTACK"
    LONG_ATTACK = "LONG_ATTACK"
    HURT = "HURT"
    DYING = "DYING"
    DASHING = "DASHING"
    PARRY = "PARRY"
    CHARGE_ATTACK = "CHARGE_ATTACK"
    DASH_ATTACK = "DASH_ATTACK"
    WALL_SLIDE = "WALL_SLIDE"
    LEDGE_GRAB = "LEDGE_GRAB"
    GRAB = "GRAB"
    THROW = "THROW"
    SLIDE = "SLIDE"
    SWIMMING = "SWIMMING"
    CLIMBING = "CLIMBING"
    ZIPLINE = "ZIPLINE"
    ULTIMATE = "ULTIMATE"
    AERIAL_ATTACK = "AERIAL_ATTACK"
    AERIAL_SLAM = "AERIAL_SLAM"
    AIR_CHASE = "AIR_CHASE"
    CHARGE_RELEASE = "CHARGE_RELEASE"


class Player(BaseEntity):
    """
    Player entity with physics, state machine, damage, combat, and sprite rendering.
    Inherits from BaseEntity.

    STATE PATTERN: self._state_instance holds the current PlayerStateBase
    subclass. Every frame, update() calls _state_instance.update() which
    handles state-specific logic and transitions. Shared infrastructure
    (physics, collision, animation frame advancement) remains in Player.
    """

    # Pylint no puede seguir el proxy de `__getattr__`/`__setattr__` de abajo:
    # ve `self._invincibility_timer` leído en la línea 362 y asignado en la 371
    # y concluye que se usa antes de existir. En realidad todos esos atributos
    # nacen con valor por defecto en `PlayerStateData`, y el proxy los enruta.
    # Se desactiva aquí, en la clase que tiene el proxy, y no globalmente: en
    # cualquier otra clase esa comprobación sí detecta errores reales.
    # pylint: disable=access-member-before-definition

    SHORT_ATTACK = PlayerState.SHORT_ATTACK
    LONG_ATTACK = PlayerState.LONG_ATTACK

    # ── State delegation (routes _prefixed gameplay attrs to _state dataclass) ──

    def __getattr__(self, name: str):
        """Fallback: look up underscore-prefixed attrs in _state dataclass."""
        if name.startswith("_") and "_state" in self.__dict__:
            stripped = name[1:]
            if hasattr(self._state, stripped):
                return getattr(self._state, stripped)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        """Route underscore-prefixed gameplay attrs to _state dataclass."""
        if name.startswith("_") and name != "_state" and "_state" in self.__dict__:
            stripped = name[1:]
            if hasattr(self._state, stripped):
                setattr(self._state, stripped, value)
                return
        super().__setattr__(name, value)

    def __init__(self, spawn_position: pygame.Vector2, event_bus=None) -> None:
        """Initialize the player at the given spawn position."""
        super().__init__(spawn_position, event_bus)

        # ── Canonical state dataclass ──────────────────────────
        self._state = PlayerStateData()
        self._state.health = settings.PLAYER_MAX_HEALTH
        self._state.coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
        self._state.prev_foot_y = spawn_position.y + 32.0

        # --- Physics state ---
        self.velocity: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self.is_grounded: bool = False

        # --- Relic bonuses (AUD-022) ---
        # Zero until apply_relic_bonuses() is called, so a player with no
        # relics behaves exactly as before.
        self._bonus_max_health: float = 0.0
        self._bonus_speed: float = 0.0
        self._bonus_damage: float = 0.0

        # --- State pattern ---
        self._state_instance: PlayerStateBase
        self._prev_state_instance: PlayerStateBase | None = None
        self._init_state()

        # --- Combo state (public) ---
        self.combo_count: int = 0
        self.combo_timer: float = 0.0
        self.last_attack_type: str = ""
        self.combo_active: bool = False

        # --- Special meter ---
        #
        # F4.2 — el ultimate era INALCANZABLE.
        #
        # `UltimateState` estaba escrito, tenía su animación, su hitbox de
        # 96x64 y su multiplicador de daño x3. `helpers.py` exigía
        # `special_meter >= special_meter_max` para entrar. Y **nada en todo el
        # proyecto subía el medidor**: se inicializaba a 0, se ponía a 0 al
        # gastarlo, y no había un solo `+=` en ninguna parte. Comprobado con
        # 300 golpes simulados: seguía en 0,0.
        #
        # El HUD lo dibujaba, así que el jugador veía una barra que nunca se
        # llenaba. Es la misma forma que la iluminación que no iluminaba y las
        # demos que dibujaban en una esquina: sistema completo y correcto que
        # no llegaba al jugador.
        self.special_meter: float = 0.0
        self.special_meter_max: float = 100.0
        #: Cuánto sube el medidor por golpe conectado. 100/12 ≈ 8,34: doce
        #: golpes por ultimate. Con menos se vuelve el ataque por defecto; con
        #: muchos más, un adorno que nadie llega a ver.
        self.special_gain_per_hit: float = 100.0 / 12.0
        #: F4.2 — arco. Se crea aquí y no en la escena para que el jugador lo
        #: lleve encima al cambiar de escenario, como la vida.
        self.arco = ArcoDelJugador()

        # --- Air jump state (public) ---
        self.gravity_multiplier: float = 1.0
        #: AUD-129 — vista cenital: sin gravedad y con movimiento en dos ejes.
        #:
        #: Es una bandera del jugador y no un estado nuevo a propósito. Los 26
        #: estados que ya existen —atacar, recibir daño, morir, parry— siguen
        #: valiendo tal cual desde arriba; lo único que cambia es **cómo se
        #: integra el movimiento**. Un `PlayerState.CENITAL` habría obligado a
        #: duplicar la mitad de la máquina de estados para no ganar nada.
        self.vista_cenital: bool = False

        # --- Direction ---
        self.facing_direction: int = 1  # -1 left, 1 right

        # --- Rect setup ---
        self.rect = pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            20,
            32,
        )

        # --- Sprite frames ---
        self._sprite_frames: dict[str, list[pygame.Surface]] = {}
        self._load_sprites()

        # --- Animation state ---
        self._animation_timer: float = 0.0
        self._animation_frame: int = 0

    def _init_state(self) -> None:
        """Create the initial idle state instance."""
        from src.framework.entities.states import IdleState
        self._state_instance = IdleState()
        self._state_instance.enter(self)

    def _load_sprites(self) -> None:
        """Load all player sprite sheets into frame lists."""
        sprite_dir = settings.ASSETS_DIR / "sprites" / "player"
        for state_name, (filename, _) in _PLAYER_SPRITE_MAP.items():
            path = sprite_dir / filename
            frames = AssetLoader.load_sprite_sheet(path, SPRITE_W, SPRITE_H)
            self._sprite_frames[state_name] = frames

    # ── Properties ──────────────────────────────────────────────

    @property
    def current_health(self) -> float:
        """Read-only health value."""
        return self._health

    @property
    def max_health(self) -> float:
        """Maximum health, including bonuses granted by collected relics."""
        return settings.PLAYER_MAX_HEALTH + self._bonus_max_health

    @property
    def walk_speed(self) -> float:
        """Ground movement speed, including relic bonuses.

        AUD-022: movement states used to read ``settings.PLAYER_WALK_SPEED``
        directly, which is why ``Inventory.get_total_speed_bonus()`` had no
        callers — there was nowhere for the bonus to be applied. Routing speed
        through the player means every state picks up relic effects for free.
        """
        return settings.PLAYER_WALK_SPEED * (1.0 + self._bonus_speed)

    @property
    def damage_multiplier(self) -> float:
        """Outgoing damage multiplier from relics (1.0 = no bonus)."""
        return 1.0 + self._bonus_damage

    def apply_relic_bonuses(self, inventory: Any) -> None:
        """Recompute stat bonuses from the player's collected relics.

        AUD-022: ``Inventory.get_total_hp_bonus`` / ``_speed_bonus`` /
        ``_damage_bonus`` were fully implemented and had zero callers — relic
        art shipped, the codex documented their effects, and picking one up did
        nothing at all. This is the missing connection. Called by ``StageScene``
        on stage entry and whenever an item is collected.
        """
        previous_max = self.max_health
        self._bonus_max_health = float(inventory.get_total_hp_bonus())
        # AUD-070: el inventario guarda el bono de velocidad en **porcentaje**
        # —`swift_feather` declara `speed_bonus=10.0` y se describe como «Move
        # 10% faster»— y aquí se estaba usando como fracción: `90 * (1 + 10)`
        # dejaba al jugador a 990 px/s, y con dos reliquias a 1890. A 60 fps
        # son 31 px por fotograma: el personaje cruzaba el mapa en un segundo,
        # atravesaba las paredes de un salto y era imposible de controlar.
        #
        # Es el mismo defecto de siempre visto desde el otro lado: al conectar
        # `get_total_speed_bonus()` —que no tenía ningún consumidor— nadie
        # comprobó en qué unidad estaba lo que devolvía. Conectar dos piezas
        # exige mirar las dos.
        self._bonus_speed = float(inventory.get_total_speed_bonus()) / 100.0
        self._bonus_damage = float(inventory.get_total_damage_bonus())
        # Grant newly added maximum health as actual health, so a relic that
        # raises the cap is felt immediately rather than only after healing.
        gained = self.max_health - previous_max
        if gained > 0:
            self._health = min(self.max_health, self._health + gained)

    @property
    def hurtbox(self) -> pygame.Rect:
        """
        Damage-receiving hitbox. Smaller than the collision rect so that
        enemy sprites can overlap visually without dealing contact damage.
          Standing:  20×28, offsetY=4  (top = rect.y + 4, bottom = rect.y + 32)
          Crouching: 20×18, offsetY=14 (top = rect.y + 14, bottom = rect.y + 32)
        """
        if self._state_instance.state_enum == PlayerState.CROUCHING:
            off_y = 14
            h = 18
        else:
            off_y = 4
            h = 28
        return pygame.Rect(self.rect.x, self.rect.y + off_y, self.rect.width, h)

    @property
    def state(self) -> PlayerState:
        """Read-only current state enum value."""
        return PlayerState(self._state_instance.state_enum.value)

    @property
    def active_hitbox(self) -> pygame.Rect | None:
        """
        Returns the current active hitbox if in an attack frame
        that deals damage, otherwise None.
        """
        if self._hitbox_consumed:
            return None
        return self._active_hitbox

    @property
    def current_attack_damage(self) -> float:
        """
        Damage value for the current attack state, scaled by combo.
        0.50 during SHORT_ATTACK active frames,
        1.00 during LONG_ATTACK active frames,
        0.0 otherwise.
        Combo multiplier from settings.COMBO_DAMAGE_MULT[combo_count - 1].
        """
        base = 0.0
        dmg_mult = getattr(self, "_damage_mult", 1.0) * self.damage_multiplier
        if (self._state_instance.state_enum == PlayerState.SHORT_ATTACK
                and self._active_hitbox is not None):
            base = 0.5
        elif (self._state_instance.state_enum == PlayerState.LONG_ATTACK
                and self._active_hitbox is not None):
            base = 1.0
        from src.engine.core.difficulty import get_config
        cfg = get_config()
        if base > 0.0 and self.combo_active and self.combo_count > 0:
            import src.engine.core.settings as settings
            idx = min(self.combo_count - 1, len(settings.COMBO_DAMAGE_MULT) - 1)
            return base * settings.COMBO_DAMAGE_MULT[idx] * cfg.outgoing_damage_mult * dmg_mult
        return base * cfg.outgoing_damage_mult * dmg_mult

    # ── Public methods ──────────────────────────────────────────

    def set_spawn(self, position: pygame.Vector2) -> None:
        """The ONLY sanctioned way to reposition the player."""
        self.position = pygame.Vector2(position)
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
        self.velocity = pygame.Vector2(0.0, 0.0)

    def heal(self, amount: float) -> None:
        from src.engine.core.difficulty import get_config
        self._health = min(self.max_health, self._health + amount * get_config().heal_mult)

    def set_health(self, amount: float) -> None:
        self._health = max(0.0, min(self.max_health, amount))

    def consume_hitbox(self) -> None:
        """El sistema de colisión avisa de que un golpe ha conectado.

        Evita el golpe múltiple en el mismo fotograma y, desde F4.2, es
        también el **único** sitio donde sube el medidor de especial y se
        recupera munición.

        Aquí y no en el estado de ataque porque aquí es donde se sabe que el
        golpe *acertó*: llenar el medidor al lanzarlo premiaría dar palos al
        aire, que es exactamente el hábito que no interesa recompensar.
        """
        self._hitbox_consumed = True
        self._active_hitbox = None
        self.gain_special(self.special_gain_per_hit)
        self.arco.recargar()

    def gain_special(self, amount: float) -> None:
        """Sube el medidor de especial, con tope."""
        self.special_meter = min(
            self.special_meter_max, self.special_meter + max(0.0, amount),
        )

    #: Margen para comparar el medidor con su tope.
    #:
    #: Doce sumas de 100/12 dan **99,99999999999999**, no 100. Sin este margen
    #: el jugador llenaba la barra en pantalla y el ultimate seguía sin
    #: activarse: exactamente el defecto que F4.2 arregla, reintroducido por
    #: una comparación de flotantes. Lo cazó la primera ejecución.
    _EPSILON_MEDIDOR = 1e-6

    @property
    def ultimate_listo(self) -> bool:
        """¿Está el medidor lleno? Lo consultan el HUD y las pruebas."""
        return self.special_meter >= self.special_meter_max - self._EPSILON_MEDIDOR

    def apply_damage(
        self,
        amount: float,
        source_position: tuple[float, float],
        knockback_force: float = 150.0,
    ) -> None:
        """
        Apply damage to the player. No-op if invincibility is active.
        Emits PLAYER_DAMAGED and potentially PLAYER_DIED.
        """
        if self._invincibility_timer > 0:
            return
        if self._state_instance.state_enum == PlayerState.DYING:
            return

        from src.engine.core.difficulty import get_config
        cfg = get_config()
        effective_damage = amount * cfg.incoming_damage_mult
        self._health = max(0.0, self._health - effective_damage)
        self._invincibility_timer = cfg.invincibility_duration
        self._flash_timer = 0.0

        # Knockback away from source
        dx = self.position.x - source_position[0]
        kb = knockback_force * cfg.knockback_mult
        self.velocity.x = kb * (1 if dx >= 0 else -1)
        self.velocity.y = -200.0 * cfg.knockback_mult
        self._knockback_timer = 0.3

        self._event_bus.emit(
            Events.PLAYER_DAMAGED,
            amount=amount,
            source=source_position,
        )

        if self._health <= 0.0:
            from src.framework.entities.states import DyingState
            self._change_state_instance(DyingState(), force=True)
            self._event_bus.emit(Events.PLAYER_DIED)
            self._event_bus.emit(Events.SFX_PLAYER_DIE)
        else:
            from src.framework.entities.states import HurtState
            self._change_state_instance(HurtState(), force=True)
            self._event_bus.emit(Events.SFX_PLAYER_HURT)

    def _change_state_instance(self, new_state: PlayerStateBase, force: bool = False) -> bool:
        """
        Transition to a new state instance.
        Calls exit() on the current state, then enter() on the new state.
        BUG-001 FIX: force=True skips the same-state early return so states
        that need re-entry (e.g. HURT, DYING) get fresh exit/enter calls.
        Returns True if state was changed, False if it was skipped (same state).
        """
        if self._state_instance.state_enum == new_state.state_enum and not force:
            return False
        self._prev_state_instance = self._state_instance
        self._state_instance.exit(self)
        self._state_instance = new_state
        self._state_instance.enter(self)
        return True

    # ──────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────

    def update(
        self,
        dt: float,
        collision_rects: list[pygame.Rect] | None = None,
        input_manager: InputManager | None = None,
        one_way_rects: list[pygame.Rect] | None = None,
    ) -> None:
        """
        Main update loop. Called every frame.
        If collision_rects is provided, performs AABB collision resolution.
        input_manager is injected by the stage — never accessed via App singleton.
        one_way_rects are platforms passable from below.
        """
        if collision_rects is None:
            collision_rects = []
        if one_way_rects is None:
            one_way_rects = []

        # Tick timers (includes animation_timer)
        self._tick_timers(dt)

        # State machine — delegate to current state
        self._state_instance.update(self, dt, input_manager)

        # Update rect dimensions for current state BEFORE collision
        # so _resolve_collision and _resolve_one_way_collision use
        # correct width/height for the current stance.
        self._update_rect_size()

        # Feet position BEFORE integration — one-way platforms only catch
        # the player if they were at/above the platform top last frame.
        self._prev_foot_y = self.position.y + self.rect.height

        # Advance animation frame (attack states handle their own animation)
        if self._state_instance.state_enum not in (
            PlayerState.SHORT_ATTACK,
            PlayerState.LONG_ATTACK,
            PlayerState.DASH_ATTACK,
        ):
            self._advance_animation(dt)

        # Physics (gravity + movement)
        if self.vista_cenital:
            self._aplicar_fisica_cenital(dt, input_manager)
        else:
            self._apply_physics(dt)

        # Collision resolution (axis-separated) — X then Y
        self._resolve_collision(dt, collision_rects)

        # One-way platforms (only resolve Y when falling)
        #
        # AUD-129 — desde arriba **no** se resuelven. Una repisa atravesable
        # vista en planta no es una repisa: es un rectángulo que frena al
        # jugador por un lado y no por el otro, sin nada en pantalla que lo
        # explique. El jugador concluye que el juego está roto, y tiene razón.
        if not self.vista_cenital:
            self._resolve_one_way_collision(dt, one_way_rects)
        else:
            # AUD-129 — el suelo se restituye **después** de la colisión.
            #
            # `_resolve_collision` pone `is_grounded = False` al integrar Y y
            # sólo lo devuelve a True si encuentra algo debajo. Desde arriba no
            # hay «debajo», así que sin esto el jugador quedaría en el aire
            # permanentemente: animación de caída, sonido de aterrizaje en
            # bucle y saltos recargándose sin parar.
            #
            # Como efecto lateral deseable, esto **desactiva el salto**: la
            # tecla arriba y la de saltar comparten enlace (`W` y `↑`), así que
            # en cenital el jugador va a pulsar saltar sin querer todo el rato.
            # Con el suelo siempre presente, el estado aéreo se abandona al
            # fotograma siguiente y la velocidad vertical la fija el
            # movimiento, no el impulso.
            self.is_grounded = True

        # Decay pending jump timer so the buffer only lasts ~5 frames
        if self._pending_jump:
            self._pending_jump_timer -= dt
            if self._pending_jump_timer <= 0:
                self._pending_jump = False

        # Buffered jump: fires only if the buffer hasn't expired
        if self._pending_jump and self.is_grounded:
            self._pending_jump = False
            self._pending_jump_timer = 0.0
            from src.framework.entities.states import _do_jump
            _do_jump(self)

        # Sync rect position to final resolved position
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """
        Draw the player sprite to the surface.
        camera_offset is subtracted from world position.
        """
        if not self.is_visible:
            return

        # Invincibility flash: skip drawing every other period
        if self._invincibility_timer > 0 and not self._flash_visible:
            return

        frames = self._sprite_frames.get(self._state_instance.state_enum.value)
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            frame = frames[frame_idx]

            if self.facing_direction < 0:
                flipped_frames = get_pool().get_flipped_frames(frames)
                frame = flipped_frames[frame_idx]

            # Center the 32-wide sprite on the 20-wide collision rect
            offset_x = (self.rect.width - SPRITE_W) // 2
            offset_y = 0 if self._state_instance.state_enum == PlayerState.CROUCHING else self.rect.height - SPRITE_H

            surface.blit(frame, (screen_x + offset_x, screen_y + offset_y))
            return

        # Fallback: colored rectangle when sprites are unavailable
        w = 20
        h = 20 if self._state_instance.state_enum == PlayerState.CROUCHING else 32
        color = (0, 120, 255)
        if self._state_instance.state_enum == PlayerState.HURT:
            color = (255, 100, 100)
        elif self._state_instance.state_enum == PlayerState.DYING:
            color = (100, 100, 100)
        pygame.draw.rect(surface, color, (screen_x, screen_y, w, h))
        pygame.draw.rect(surface, (255, 255, 255), (screen_x, screen_y, w, h), 1)

    # ──────────────────────────────────────────────
    # Timer ticking
    # ──────────────────────────────────────────────

    def _tick_timers(self, dt: float) -> None:
        """Tick all cooldown and duration timers."""
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt
            period = 0.1
            self._flash_timer += dt
            if self._flash_timer >= period:
                self._flash_timer -= period
                self._flash_visible = not self._flash_visible
        else:
            self._flash_visible = True
            self._flash_timer = 0.0
        if self._knockback_timer > 0:
            self._knockback_timer -= dt
        if self._cooldown_timer > 0:
            self._cooldown_timer -= dt
        if self._dash_cooldown > 0:
            self._dash_cooldown -= dt
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_active = False
                self.combo_count = 0
        self._animation_timer += dt

    def _advance_animation(self, dt: float) -> None:
        """Advance the sprite animation frame based on per-state FPS."""
        fps = _PLAYER_ANIM_FPS.get(self._state_instance.state_enum.value, 10.0)
        frame_duration = 1.0 / fps
        total_frames = _PLAYER_SPRITE_MAP.get(
            self._state_instance.state_enum.value, (None, 1),
        )[1]
        if self._animation_timer >= frame_duration:
            self._animation_timer -= frame_duration
            self._animation_frame = (self._animation_frame + 1) % total_frames

    # ──────────────────────────────────────────────
    # State machine (delegated to player_states.py)
    # ──────────────────────────────────────────────

    # All state-specific logic moved to PlayerStateBase subclasses
    # in player_states.py. The Player class handles shared infrastructure.

    def _do_jump(self) -> None:
        """Execute a jump (forwarder to module-level helper)."""
        from src.framework.entities.states import _do_jump as _do_jump_fn
        _do_jump_fn(self)

    def _can_jump(self) -> bool:
        """Check if the player can jump (forwarder to module-level helper)."""
        from src.framework.entities.states import _can_jump as _can_jump_fn
        return _can_jump_fn(self)

    # ──────────────────────────────────────────────
    # Physics
    # ──────────────────────────────────────────────

    def _aplicar_fisica_cenital(
        self, dt: float, input_manager: InputManager | None,
    ) -> None:
        """Física de la vista desde arriba: sin gravedad, dos ejes libres.

        AUD-129 — qué cambia y qué no
        ------------------------------
        Cambia **sólo la integración del movimiento**. El estado que gobierna
        al jugador sigue decidiendo la velocidad horizontal —así los ataques,
        el daño y el parry se comportan igual—, y aquí se añade la vertical,
        que en lateral la pone la gravedad.

        Tres decisiones que se notan al jugar:

        * **`is_grounded` siempre verdadero.** Desde arriba no hay «en el
          aire»: sin esto el jugador entraría en `FALLING` en el primer
          fotograma, sonaría el aterrizaje en bucle y el salto se recargaría
          sin parar. El suelo es el plano de juego.
        * **La diagonal se normaliza.** Sin normalizar, moverse en diagonal
          da 1,41 veces la velocidad, y todo jugador acaba andando en zigzag
          porque es objetivamente más rápido. Es el defecto clásico de la
          vista cenital y sale gratis evitarlo.
        * **La velocidad vertical no acumula.** Se fija desde la entrada, no
          se integra: en cenital no hay inercia de caída que respetar, y
          acumular haría que soltar la tecla dejara al jugador derrapando.
        """
        self.is_grounded = True
        self._wall_side = 0
        self._wall_slide_timer = 0.0

        vy = 0.0
        if input_manager is not None:
            from src.engine.input.action_map import Action
            if input_manager.is_action_held(Action.MOVE_UP):
                vy -= 1.0
            if input_manager.is_action_held(Action.MOVE_DOWN):
                vy += 1.0

        velocidad = self.walk_speed
        if vy != 0.0 and self.velocity.x != 0.0:
            # Diagonal: se reparte para que el módulo siga siendo `walk_speed`.
            factor = 0.70710678                      # 1 / raíz de 2
            self.velocity.x *= factor
            vy *= factor
        self.velocity.y = vy * velocidad

    def _apply_physics(self, dt: float) -> None:
        """Apply gravity. Movement integration happens per-axis in _resolve_collision."""
        wall_side = self._wall_side
        self._wall_side = 0
        if not self.is_grounded:
            gm = self.gravity_multiplier
            # Wall slide: reduced gravity when touching wall
            if wall_side != 0 and self.velocity.y > 0:
                self.velocity.y += settings.GRAVITY * gm * 0.3 * dt
                self.velocity.y = min(
                    self.velocity.y,
                    settings.PLAYER_MAX_FALL_SPEED * gm * 0.5,
                )
                self._wall_slide_timer += dt
            else:
                self.velocity.y += settings.GRAVITY * gm * dt
                self.velocity.y = min(
                    self.velocity.y,
                    settings.PLAYER_MAX_FALL_SPEED * gm,
                )
                self._wall_slide_timer = 0.0

        # Coyote time
        if self.is_grounded:
            self._coyote_counter = 0
            self._wall_side = 0
        else:
            self._coyote_counter += 1

    # ──────────────────────────────────────────────
    # Collision resolution (AABB, axis-separated)
    # ──────────────────────────────────────────────

    def _resolve_collision(self, dt: float, collision_rects: list[pygame.Rect]) -> None:
        """
        True axis-separated AABB resolution:
        1. Integrate X, resolve X against overlapping rects.
        2. Integrate Y, resolve Y against overlapping rects, using the
           direction of motion (came-from-above lands, came-from-below bonks).
        No heuristics needed: each axis only sees penetration caused by
        its own movement.

        AUD-130 — este método también **integra**, y ahí estaba el defecto
        ---------------------------------------------------------------------
        La primera línea era::

            if not collision_rects:
                return

        …y como la integración de la posición vive dentro de este método, un
        escenario **sin ninguna caja de colisión dejaba al jugador congelado**:
        la velocidad crecía fotograma a fotograma y la posición no se movía
        nunca. Salir por «no hay nada contra lo que chocar» también saltaba el
        «avanzar».

        En los quince mapas del curso no se notaba porque todos tienen suelo.
        Se notaría en el primer mapa de un estudiante con la capa `Collision`
        vacía —que es un error frecuentísimo, y ya avisado por el validador—:
        el síntoma sería «no me muevo», que no apunta ni de lejos a la causa.
        Lo encontró la vista cenital, donde probar sin geometría es lo natural.

        El nombre del método miente un poco y eso es lo que lo hizo posible:
        se llama «resolver colisión» y hace dos cosas. Se deja el nombre —lo
        llaman el jugador y las pruebas de los estudiantes— y se arregla el
        contrato: **integrar siempre, resolver sólo si hay contra qué**.
        """
        w, h = self.rect.width, self.rect.height

        # --- X axis ---
        self._wall_side = 0
        self._can_wall_jump = False
        self._can_ledge_grab = False
        self.position.x += self.velocity.x * dt
        if collision_rects:
            for tile in collision_rects:
                px = pygame.Rect(int(self.position.x), int(self.position.y), w, h)
                if px.colliderect(tile):
                    # BUG-003 FIX: Save pre-mutation top for ledge grab check
                    pre_mutate_top = px.top
                    pre_px = pygame.Rect(int(self.position.x - self.velocity.x * dt), int(self.position.y), w, h)
                    v_overlap = min(pre_px.bottom, tile.bottom) - max(pre_px.top, tile.top)
                    if v_overlap <= 2:
                        continue
                    if self.velocity.x > 0:
                        px.right = tile.left
                        self._wall_side = 1
                    elif self.velocity.x < 0:
                        px.left = tile.right
                        self._wall_side = -1
                    else:
                        if (px.right - tile.left) < (tile.right - px.left):
                            px.right = tile.left
                            self._wall_side = 1
                        else:
                            px.left = tile.right
                            self._wall_side = -1
                    if self._wall_side != 0 and not self.is_grounded:
                        self._can_wall_jump = True
                        ledge_check = pygame.Rect(
                            tile.left if self._wall_side == 1 else tile.right - 2,
                            tile.top - 16,
                            max(tile.width, 2),
                            16,
                        )
                        ledge_found = False
                        for t2 in collision_rects:
                            if ledge_check.colliderect(t2):
                                ledge_found = True
                                break
                        self._can_ledge_grab = (
                            not ledge_found
                            and pre_mutate_top <= tile.top + 8
                            and pre_mutate_top >= tile.top - 16
                        )
                    self.velocity.x = 0.0
                    self.position.x = float(px.x)

        # --- Y axis ---
        prev_bottom = self.position.y + h
        prev_top = self.position.y
        self.position.y += self.velocity.y * dt
        was_grounded = self.is_grounded
        self.is_grounded = False
        if collision_rects:
            py = pygame.Rect(int(self.position.x), int(self.position.y), w, h)
            check = py.inflate(0, 2)
            check.y = py.y - 1
            for tile in collision_rects:
                if check.colliderect(tile):
                    if self.velocity.y >= 0 and prev_bottom <= tile.top + 1:
                        # Came from above: land
                        if not was_grounded and self.velocity.y > 0:
                            self._event_bus.emit(Events.SFX_PLAYER_LAND)
                        py.bottom = tile.top
                        self.velocity.y = 0.0
                        self.is_grounded = True
                        self._air_dash_count = 0
                        self._air_jumps_used = 0
                    elif self.velocity.y < 0 and prev_top >= tile.bottom - 1:
                        # Came from below: bonk
                        py.top = tile.bottom
                        self.velocity.y = 0.0
                    self.position.y = float(py.y)
                    check.y = py.y - 1
                    check.height = py.height + 2

    def _resolve_one_way_collision(self, dt: float, one_way_rects: list[pygame.Rect]) -> None:
        """Resolve Y-axis collision for one-way platforms (passable from below).
        Only resolves when falling (velocity.y >= 0) AND the player's feet
        were at or above the platform top on the previous frame. Walking into
        a platform from lower ground passes through (true one-way semantics:
        07_STAGE0_DESIGN §Zone E — "Jump up through it; fall back down")."""
        if not one_way_rects:
            return
        if self.velocity.y < 0:
            return

        player_rect = pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            self.rect.width,
            self.rect.height,
        )
        # Inflate by 2px so edge-aligned platforms (player bottom == plat top)
        # are detected via colliderect's strict comparison.
        collision_check_rect = player_rect.inflate(0, 2)
        for plat in one_way_rects:
            if (collision_check_rect.colliderect(plat)
                    and self._prev_foot_y <= plat.top + 1):
                player_rect.bottom = plat.top
                self.velocity.y = 0.0
                self.is_grounded = True
                self._air_dash_count = 0
                self._air_jumps_used = 0
                self.position.y = float(player_rect.y)
                if self.position.y + self.rect.height > plat.top + 4:
                    self.position.y = float(plat.top - self.rect.height)
                break

    # ──────────────────────────────────────────────
    # Rect / Hurtbox sizing
    # ──────────────────────────────────────────────

    def _update_rect_size(self) -> None:
        """Update rect size based on current state (crouching vs standing).
        Shifts position.y so the rect bottom (feet) stays at the same height."""
        old_bottom = self.position.y + self.rect.height
        target_h = 20 if self._state_instance.state_enum == PlayerState.CROUCHING else 32
        if self.rect.height == target_h:
            self.rect.x = int(self.position.x)
            self.rect.y = int(self.position.y)
            return
        self.rect.width = 20
        self.rect.height = target_h
        self.position.y += old_bottom - (self.position.y + self.rect.height)
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
