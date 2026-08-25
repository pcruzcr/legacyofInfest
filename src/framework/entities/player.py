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
from typing import TYPE_CHECKING, Any, ClassVar

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.surface_pool import get_pool
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.player_state import PlayerStateData
from src.framework.entities.ranged_weapon import ArcoDelJugador
from src.framework.physics.perfil import CENITAL, PLATAFORMAS, VUELO, Material, PhysicsProfile
from src.framework.physics.resolucion import (
    EstadoDeMovimiento,
    acercarse_a,
    resolver_cuestas,
    resolver_eje_x,
    resolver_eje_y,
    resolver_paredes_de_pendientes,
    resolver_repisas,
)
from src.framework.vfx.contorno import (
    COLOR_JUGADOR,
    COMPENSACIONES,
    dibujar_con_contorno,
    silueta_de,
)

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.states import PlayerStateBase


SPRITE_W = 32
SPRITE_H = 32

#: AUD-190 — contorno de silueta del jugador.
#:
#: Medido sobre los 16 escenarios: el jugador tenía un contraste de **1,01 a
#: 1,18** contra el fondo que lo rodea en 15 de ellos (1,0 es indistinguible).
#: Sólo `boss_venado` llegaba a 1,98. En la práctica el personaje desaparecía
#: contra el decorado, que es el defecto de legibilidad más caro que puede
#: tener un plataformas: si no ves dónde estás, no puedes calcular un salto.
#:
#: La solución es la de cualquier juego 2D con fondos oscuros —Celeste, Dead
#: Cells, Hollow Knight—: un contorno de un píxel que separa la figura del
#: fondo. No se toca ni un sprite; se dibuja la misma imagen teñida en cuatro
#: desplazamientos, detrás. Las siluetas se cachean, así que cuesta cuatro
#: blits por fotograma de una superficie ya calculada.
#:
#: AUD-304 — la implementación se mudó a `framework.vfx.contorno` para que los
#: enemigos pudieran usarla también. Estos tres nombres se conservan porque son
#: los que cita `tests/test_legibilidad_del_jugador.py`, que es la prueba que
#: fija la medición de AUD-190 y no tiene por qué mudarse con el código.
_CONTORNO = COMPENSACIONES
_COLOR_CONTORNO = COLOR_JUGADOR
_silueta_de = silueta_de

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
    # AUD-525 — antes reutilizaba `player_jump.png`: cuatro copias del mismo
    # fotograma quieto, así que nadar se veía como quedarse clavado de pie
    # bajo el agua. `player_swim.png` alterna una patada abierta con la
    # silueta cerrada del salto: hay brazada real entre fotogramas.
    "SWIMMING": ("player_swim.png", 4),
    # AUD-558 — GAP-069: el golpe acuático que rompe `BloqueDestructible`
    # bajo el agua. Reusa la hoja del ataque corto en tierra
    # (`player_short_attack.png`) — mismo criterio que `GRAB`/`THROW`/
    # `DASH_ATTACK`/`AERIAL_ATTACK`: sin arte propio, una silueta
    # coherente vale más que una inventada.
    "SWIM_ATTACK": ("player_short_attack.png", 6),
    # F5.14 — lianas y tirolesas. Reutilizan la hoja de salto: el jugador va
    # colgado, y hasta que haya arte propio es mejor un sprite coherente que
    # uno inventado.
    "CLIMBING": ("player_jump.png", 2),
    "ZIPLINE": ("player_jump.png", 2),
    "ULTIMATE": ("player_long_attack.png", 10),
    "AERIAL_ATTACK": ("player_short_attack.png", 6),
    "AERIAL_SLAM": ("player_short_attack.png", 6),
    # AUD-619 — el pisotón reutiliza la hoja del ataque corto: sin arte
    # propio, una silueta coherente vale más que una inventada (AUD-558).
    "GROUND_POUND": ("player_short_attack.png", 6),
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
    "SWIM_ATTACK": 14.0,
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
    # AUD-619 — la caída del pisotón es corta; a 14 fps recorre la hoja
    # antes de tocar suelo, que es justo lo que se ve.
    "GROUND_POUND": 14.0,
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
    SWIM_ATTACK = "SWIM_ATTACK"
    CLIMBING = "CLIMBING"
    ZIPLINE = "ZIPLINE"
    ULTIMATE = "ULTIMATE"
    AERIAL_ATTACK = "AERIAL_ATTACK"
    AERIAL_SLAM = "AERIAL_SLAM"
    GROUND_POUND = "GROUND_POUND"
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

    #: AUD-502 — caja de colisión **de pie**, en px. `_update_rect_size` la
    #: encoge a 20×20 al agacharse, así que un punto de reaparición no se
    #: puede calcular con `rect.height`: tocar un checkpoint agachado
    #: dejaría el respawn más abajo de lo debido, que es este mismo defecto
    #: por otra puerta.
    ANCHO_DE_PIE: ClassVar[int] = 20
    ALTO_DE_PIE: ClassVar[int] = 32

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
        # AUD-333 — el perfil de física se crea antes que cualquier dato que
        # lo lea: el estado canónico arranca con el coyote del perfil, que
        # por defecto vale exactamente lo de `settings`.
        self.perfil = PhysicsProfile.plataformas()
        #: AUD-490 — GAP-039, la mitad que faltaba: la restitución del perfil
        #: es una constante para todo el nivel; esto es lo que una
        #: `ZonaDeFriccion` con `material` puede sobreescribir por región,
        #: fotograma a fotograma. Lo escribe `sistema_friccion` a través de
        #: `Transform.material_actual` (la misma vista que ya usa `facing`);
        #: aquí sólo se declara y se lee. `None` = usar `perfil.material`,
        #: que es el comportamiento de siempre en los mapas que no declaran
        #: ninguna zona de este tipo.
        self._material_de_zona: Material | None = None
        #: AUD-599 — GAP-072.1: la corriente del agua que rodea al jugador,
        #: escrita por la escena cada fotograma desde
        #: `ControlDeNado.corriente_medio`. La lee `SwimmingState` como la
        #: velocidad objetivo del arrastre neutral. Cero en tierra firme.
        self.corriente_medio = pygame.Vector2(0.0, 0.0)
        #: AUD-388 — los efectos temporales que lleva encima. Vacío casi
        #: siempre; lo llenan las charcas de veneno, los potenciadores y lo que
        #: venga. Es el mismo componente que llevan los enemigos, y por eso
        #: envenenar a uno es la misma llamada que envenenar al jugador — que
        #: era justo lo que no se podía hacer con los temporizadores sueltos de
        #: `PlayerStateData`.
        from src.framework.ecs.components import Efectos

        self.efectos = Efectos()
        self._state = PlayerStateData()
        self._state.health = settings.PLAYER_MAX_HEALTH
        self._state.coyote_counter = self.perfil.coyote_frames + 1
        self._state.prev_foot_y = spawn_position.y + 32.0

        # --- Physics state ---
        self.velocity: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        # AUD-336 — el estado de la integración horizontal del perfil: la
        # velocidad «real» cuando `aceleracion` > 0, espejo de la del estado
        # cuando no.
        self._vx_integrada: float = 0.0
        self.is_grounded: bool = False

        # --- Relic bonuses (AUD-022) ---
        # Zero until apply_relic_bonuses() is called, so a player with no
        # relics behaves exactly as before.
        self._bonus_max_health: float = 0.0
        self._bonus_speed: float = 0.0
        self._bonus_damage: float = 0.0
        #: AUD-293 — lo que aporta el árbol de habilidades, aparte de las
        #: reliquias. Separado y no sumado en el mismo campo para que la
        #: pantalla del árbol pueda decir cuánto viene de dónde.
        self._bonus_arbol_salud: float = 0.0
        self._bonus_arbol_dano: float = 0.0
        #: AUD-559 — fracción de daño recibido que resta "Coraza". Se lee
        #: en `apply_damage`, no en `damage_multiplier` (esa propiedad es
        #: daño de **salida**; esto es de **entrada** — dos direcciones
        #: distintas, dos campos distintos).
        self._bonus_arbol_defensa: float = 0.0
        #: Segundos extra que dura el ultimate. Los lee `UltimateState`.
        self._bonus_ultimate: float = 0.0
        #: AUD-294 — ¿este escenario regala las mecánicas de jefe?
        #:
        #: Lo pone la escena al entrar. Vive en el jugador y no en un global
        #: porque la exención es **por escenario**: pasar de un mapa entregado
        #: a uno nuevo dentro de la misma partida tiene que cambiar la
        #: respuesta, y un global obligaría a acordarse de restaurarlo.
        #:
        #: **Arranca en `True`, y esa es la decisión que protege la invariante
        #: 2.** Un `Player` construido fuera de un escenario —una prueba de
        #: física, el arnés de un estudiante, un laboratorio— se comporta
        #: exactamente como antes de AUD-294. El candado lo **enciende la
        #: escena** para los mapas que no están exentos, que son los nuevos.
        #: Al revés —arrancar bloqueado y que la escena libere— cualquier
        #: código que instancie un jugador suelto se encontraría sin doble
        #: salto sin haber pedido progresión.
        self._habilidades_libres: bool = True
        #: AUD-297 — las cuestas del escenario. Las pasa `update`.
        self._pendientes: list[Any] = []
        #: ¿Pisaba suelo antes de resolver este fotograma? Ver `_resolve_collision`.
        self._venia_del_suelo: bool = False
        #: AUD-636 — Squash & Stretch. Factores de escala del sprite, con
        #: identidad (1.0) como reposo. `_squash_y < 1` aplasta (aterrizaje),
        #: `> 1` estira (salto); `_squash_x` compensa para conservar el área.
        #: El decay vive en `_tick_timers`; el dibujado los aplica anclando
        #: abajo-centro — si el sprite encoge desde su centro flota sobre el
        #: suelo y deja de leerse como masa.
        self._squash_x: float = 1.0
        self._squash_y: float = 1.0

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

        # AUD-141 — la estamina, y por qué viene APAGADA de fábrica.
        #
        # Un medidor de estamina cambia cómo se juega: convierte el dash de
        # recurso libre en recurso administrado. Encenderlo para todos
        # cambiaría los quince escenarios ya entregados sin que sus autores lo
        # pidan, y algunos están medidos al dash. Se enciende por escenario,
        # con la propiedad `estamina` del mapa.
        self.estamina_max: float = 0.0
        self.estamina: float = 0.0
        #: Lo que cuesta un dash. Con 100 de máximo, cuatro dashes seguidos.
        self.coste_dash: float = 25.0
        #: Puntos por segundo que se recuperan.
        self.recuperacion_estamina: float = 35.0
        #: Segundos de espera antes de empezar a recuperar.
        #:
        #: Sin esta pausa la estamina se rellena mientras se encadenan dashes
        #: y el medidor no limita nada; con ella hay un ritmo que aprender,
        #: que es justo lo que la mecánica aporta.
        self.espera_estamina: float = 0.6
        self._espera_estamina_restante: float = 0.0

        # --- Air jump state (public) ---
        self.gravity_multiplier: float = 1.0
        #: AUD-129 — vista cenital: sin gravedad y con movimiento en dos ejes.
        #:
        #: Es un **modo del perfil de física** (AUD-333) y no un estado nuevo a
        #: propósito. Los 26 estados que ya existen —atacar, recibir daño,
        #: morir, parry— siguen valiendo tal cual desde arriba; lo único que
        #: cambia es **cómo se integra el movimiento**. Un
        #: `PlayerState.CENITAL` habría obligado a duplicar la mitad de la
        #: máquina de estados para no ganar nada. `vista_cenital` se conserva
        #: como propiedad: la leen y la escriben las escenas, y detrás es
        #: `self.perfil.modo`.

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
        """Vida máxima: base + reliquias + árbol, con tope de diez corazones.

        AUD-293 — el tope es del diseño y se aplica aquí, en el único sitio por
        el que pasan todos los sumandos. Recortarlo en el árbol dejaría que las
        reliquias se lo saltaran, y recortarlo en las reliquias, al revés.
        """
        from src.engine.core.skill_tree import CORAZONES_MAXIMOS

        total = (settings.PLAYER_MAX_HEALTH + self._bonus_max_health
                 + self._bonus_arbol_salud)
        return min(total, CORAZONES_MAXIMOS)

    @property
    def walk_speed(self) -> float:
        """Ground movement speed, including relic bonuses.

        AUD-022: movement states used to read ``settings.PLAYER_WALK_SPEED``
        directly, which is why ``Inventory.get_total_speed_bonus()`` had no
        callers — there was nowhere for the bonus to be applied. Routing speed
        through the player means every state picks up relic effects for free.

        AUD-333 — la base sale del perfil de física: un contexto con otra
        velocidad de suelo la declara en su perfil y todos los estados la
        heredan sin tocar una línea.
        """
        return self.perfil.velocidad_suelo * (1.0 + self._bonus_speed)

    @property
    def vista_cenital(self) -> bool:
        """AUD-333 — la vista cenital es un **modo del perfil**, no una bandera.

        La propiedad conserva el contrato de siempre —las escenas leen y
        escriben `player.vista_cenital`— y detrás el modo es `perfil.modo`:
        un contexto nuevo cambia el perfil y el integrador entero se entera.
        """
        return self.perfil.modo == CENITAL

    @vista_cenital.setter
    def vista_cenital(self, valor: bool) -> None:
        self.perfil.modo = CENITAL if valor else PLATAFORMAS

    @property
    def damage_multiplier(self) -> float:
        """Multiplicador de daño: reliquias y árbol (1,0 = sin bonificación).

        AUD-608 — la sinergia **Berserker** (fuerza y coraza al máximo)
        añade +0,2 con menos de la mitad de vida. Se lee en caliente del
        árbol para que cargar una partida vieja con menos rangos la pierda,
        igual que los bonus normales.
        """
        total = 1.0 + self._bonus_damage + self._bonus_arbol_dano
        from src.engine.core.skill_tree import ArbolDeHabilidades

        if ArbolDeHabilidades.get_instance().sinergia_activa("berserker"):
            tope = max(1.0, self.max_health)
            if self._health < tope / 2.0:
                total += 0.2
        return total

    def apply_relic_bonuses(self, inventory: Any) -> None:
        """Recompute stat bonuses from the player's collected relics.

        AUD-022: ``Inventory.get_total_hp_bonus`` / ``_speed_bonus`` /
        ``_damage_bonus`` were fully implemented and had zero callers — relic
        art shipped, the codex documented their effects, and picking one up did
        nothing at all. This is the missing connection. Called by ``StageScene``
        on stage entry and whenever an item is collected.
        """
        previous_max = self.max_health
        # AUD-293 — el árbol se recalcula aquí, con las reliquias, porque los
        # dos alimentan los mismos tres números y porque este método ya se
        # llama justo cuando hay que rehacerlos: al entrar al escenario y al
        # recoger algo. El nombre se queda como estaba: lo llaman las 26
        # entregas y renombrarlo por precisión rompería veintiséis ficheros.
        from src.engine.core.skill_tree import ArbolDeHabilidades

        arbol = ArbolDeHabilidades.get_instance()
        self._bonus_arbol_salud = float(arbol.bonus_corazones())
        self._bonus_arbol_dano = float(arbol.bonus_dano())
        self._bonus_ultimate = float(arbol.bonus_ultimate())
        self._bonus_arbol_defensa = float(arbol.bonus_defensa())
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

        AUD-603 — los estados de ataque que nacieron después del corto y
        del largo levantaban `active_hitbox` pero no tenían rama aquí, así
        que **conectaban y hacían 0.0**: sprite, sonido y combo sí existían,
        la vida del enemigo no se movía. Reportado en playtesting con el
        golpe aéreo; el mismo defecto estaba en el resto de ataques
        especiales, incluido el ultimate cuyo `_damage_mult = 3.0` era
        inerte al multiplicar una base cero. Valores:

        * AERIAL_ATTACK  0.5 — misma caja y sprite que el corto.
        * AERIAL_SLAM    1.0 — remate aéreo, caja mayor.
        * DASH_ATTACK    0.75 — entre ligero y pesado.
        * SWIM_ATTACK    0.5 — comparte sprite y fotogramas activos
          con el corto (`states/swim.py`).
        * THROW          1.0 — un lanzamiento duele.
        * ULTIMATE       1.0 × `_damage_mult` (3.0) = 3.0 — el mecanismo
          ya existía; sin base nunca se aplicaba.
        * CHARGE_RELEASE 1.0 × nivel de carga (1.0/1.5/2.0).
        """
        base = 0.0
        dmg_mult = getattr(self, "_damage_mult", 1.0) * self.damage_multiplier
        state = self._state_instance.state_enum
        if state == PlayerState.SHORT_ATTACK and self._active_hitbox is not None:
            base = 0.5
        elif state == PlayerState.LONG_ATTACK and self._active_hitbox is not None:
            base = 1.0
        # AUD-603 — las ramas que faltaban (ver docstring).
        elif state == PlayerState.AERIAL_ATTACK and self._active_hitbox is not None:
            base = 0.5
        elif state == PlayerState.AERIAL_SLAM and self._active_hitbox is not None:
            base = 1.0
        elif state == PlayerState.DASH_ATTACK and self._active_hitbox is not None:
            base = 0.75
        elif state == PlayerState.SWIM_ATTACK and self._active_hitbox is not None:
            base = 0.5
        elif state == PlayerState.THROW and self._active_hitbox is not None:
            base = 1.0
        elif state == PlayerState.ULTIMATE and self._active_hitbox is not None:
            base = 1.0
        elif state == PlayerState.CHARGE_RELEASE and self._active_hitbox is not None:
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
        # AUD-336 — reaparecer no puede dejar inercia: la integración del
        # perfil arranca de cero como la velocidad.
        self._vx_integrada = 0.0

    def heal(self, amount: float) -> None:
        from src.engine.core.difficulty import get_config
        antes = self._health
        self._health = min(self.max_health, self._health + amount * get_config().heal_mult)
        # AUD-255 — `SFX_PLAYER_HEAL` tenía fichero, tabla de sonidos y
        # subtítulo, y ni un solo emisor. Se emite sólo si la salud **subió**:
        # curarse a salud llena sonaría igual que curarse de verdad, y el
        # sonido dejaría de significar nada.
        if self._health > antes and self._event_bus is not None:
            self._event_bus.emit(Events.SFX_PLAYER_HEAL)

    def set_health(self, amount: float) -> None:
        self._health = max(0.0, min(self.max_health, amount))

    # ── AUD-141: estamina ─────────────────────────────────────────
    @property
    def estamina_activa(self) -> bool:
        """`False` mientras el escenario no la pida. Es el caso por defecto."""
        return self.estamina_max > 0.0

    @property
    def hay_estamina_para_correr(self) -> bool:
        """Lo consulta `_can_dash`, el único sitio que decide si hay dash."""
        if not self.estamina_activa:
            return True
        return self.estamina >= self.coste_dash

    def gastar_estamina(self, cantidad: float | None = None) -> bool:
        """Cobra el gasto. Devuelve `False` si no había bastante.

        Con la estamina apagada devuelve `True` sin tocar nada: el escenario
        que no la pide no puede notar que existe.
        """
        if not self.estamina_activa:
            return True
        coste = self.coste_dash if cantidad is None else max(0.0, cantidad)
        if self.estamina < coste:
            return False
        self.estamina -= coste
        self._espera_estamina_restante = self.espera_estamina
        return True

    def recuperar_estamina(self, dt: float) -> None:
        if not self.estamina_activa or dt <= 0.0:
            return
        if self._espera_estamina_restante > 0.0:
            self._espera_estamina_restante -= dt
            return
        self.estamina = min(
            self.estamina_max, self.estamina + self.recuperacion_estamina * dt)

    def activar_estamina(self, maximo: float) -> None:
        """La enciende el escenario al cargar. `0` la deja apagada."""
        self.estamina_max = max(0.0, float(maximo))
        self.estamina = self.estamina_max
        self._espera_estamina_restante = 0.0

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
        # AUD-559 — "Coraza" resta una fracción del daño de entrada,
        # después del multiplicador de dificultad y no en su lugar: un
        # jugador que invirtió puntos de habilidad sigue sintiendo el
        # nivel de dificultad que eligió, sólo que un poco más suave.
        # `max(0.05, ...)` porque cinco rangos ya llegan a -25 %; sin
        # tope, un futuro sexto rango podría acercarse peligrosamente a
        # "invencible", que no es lo que pide la rama.
        defensa = max(0.05, 1.0 - self._bonus_arbol_defensa)
        effective_damage = amount * cfg.incoming_damage_mult * defensa
        self._health = max(0.0, self._health - effective_damage)
        # AUD-608 — la sinergia **Titán** (vitalidad e ímpetu al máximo)
        # estira los i-frames: el jugador tanque vive en el meleé y unos
        # décimos de gracia es la única defensa que no toca el número de
        # daño, que coraza ya recorta.
        from src.engine.core.skill_tree import ArbolDeHabilidades

        extra_titan = (
            0.3
            if ArbolDeHabilidades.get_instance().sinergia_activa("titan")
            else 0.0
        )
        self._invincibility_timer = cfg.invincibility_duration + extra_titan
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
        pendientes: list[Any] | None = None,
    ) -> None:
        """
        Main update loop. Called every frame.
        If collision_rects is provided, performs AABB collision resolution.
        input_manager is injected by the stage — never accessed via App singleton.
        one_way_rects are platforms passable from below.

        AUD-297 — `pendientes` es el suelo inclinado, y va al final de la firma
        con valor por defecto por lo de siempre: las 26 entregas llaman a esto
        por posición. Sin pendientes, el paso entero se salta.
        """
        if collision_rects is None:
            collision_rects = []
        if one_way_rects is None:
            one_way_rects = []
        self._pendientes = pendientes or []

        # Tick timers (includes animation_timer)
        self._tick_timers(dt)
        # AUD-141 — la estamina se recupera aquí y no dentro de un estado:
        # se recupera en TODOS, incluso quieto, agachado o en el aire.
        self.recuperar_estamina(dt)

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
        if self.perfil.modo in (CENITAL, VUELO):
            # AUD-335 — el vuelo es la integración cenital declarada por su
            # perfil: sin gravedad, dos ejes libres, velocidad desde la
            # entrada. La diferencia entre modos es el dato (velocidad,
            # futura inercia), no el integrador: un contexto de vuelo
            # declara su perfil y hereda el comportamiento.
            self._aplicar_fisica_cenital(dt, input_manager)
        else:
            self._apply_physics(dt)

        # Collision resolution (axis-separated) — X then Y
        self._resolve_collision(dt, collision_rects)

        # AUD-297 — el suelo inclinado, **después** del eje Y y antes de las
        # plataformas de un sentido. Después de Y porque la pendiente corrige
        # la altura que la caja acaba de dejar; antes de las de un sentido
        # porque una repisa atravesable por encima de una cuesta tiene que
        # poder atraparlo, y eso exige que ya esté colocado en la cuesta.
        self._resolver_pendientes(dt)

        # One-way platforms (only resolve Y when falling)
        #
        # AUD-129 — desde arriba **no** se resuelven. Una repisa atravesable
        # vista en planta no es una repisa: es un rectángulo que frena al
        # jugador por un lado y no por el otro, sin nada en pantalla que lo
        # explique. El jugador concluye que el juego está roto, y tiene razón.
        if self.perfil.modo == PLATAFORMAS:
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
            #
            # AUD-335 — en vuelo idem, por la misma razón: las repisas son
            # semántica de plataformas y sin gravedad no hay «en el aire».
            self.is_grounded = True

        # AUD-373 — el salto con buffer. La ventana ya no se lleva aquí.
        #
        # Esto era `_pending_jump` + su temporizador, armados a mano desde
        # `AirborneState` y decrementados en esta misma función: el único
        # buffer del juego, para la única acción que lo tenía (GAP-040). Ahora
        # la ventana la cuenta `InputManager` para **todas** las acciones, y
        # aquí sólo queda la pregunta que le corresponde al jugador: ¿estoy en
        # el suelo y había un salto pendiente?
        #
        # No hace falta comprobar que el salto no salga dos veces: si el
        # estado ya saltó este fotograma, `_do_jump` dejó `is_grounded` en
        # False y esta condición no se cumple. Aun así se consume la
        # pulsación, porque quien ejecuta una acción es quien la gasta.
        #
        # AUD-573 — los estados acuáticos no saltan. Antes esto se
        # disparaba para cualquier estado con `is_grounded`, y en el 4-1b
        # posarse en el lecho marino (grounded dentro del agua, el lecho
        # está a 16px del borde de la `ZonaDeAgua`) dejaba saltar al
        # jugador con física de tierra en pleno abismo — reproducido en
        # simulación: `SWIMMING` + lecho + JUMP en buffer → `JumpingState`
        # con impulso de salto, una y otra vez («el personaje no nada»).
        # El salto es tierra firme; dentro del agua se nada, y el impulso
        # lo da `SwimmingState`, no `_do_jump`.
        if (
            input_manager is not None
            and self.is_grounded
            and self._state_instance.state_enum not in (
                PlayerState.SWIMMING, PlayerState.SWIM_ATTACK,
            )
        ):
            from src.engine.input.action_map import Action
            if input_manager.pulsada_en_buffer(Action.JUMP):
                input_manager.consumir_buffer(Action.JUMP)
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

            destino = (screen_x + offset_x, screen_y + offset_y)

            # AUD-636 — Squash & Stretch. Sólo se paga el `transform.scale`
            # cuando hay deformación real: el 99 % de los fotogramas el
            # jugador está en 1.0/1.0 y este bloque es dos comparaciones.
            if (self._squash_x != 1.0 or self._squash_y != 1.0):
                ancho = max(1, int(frame.get_width() * self._squash_x))
                alto = max(1, int(frame.get_height() * self._squash_y))
                frame = pygame.transform.scale(frame, (ancho, alto))
                # Anclado ABAJO-centro: si encoge desde su centro, los pies
                # flotan sobre el suelo y la masa deja de leerse.
                dx = (SPRITE_W - ancho) // 2
                dy = SPRITE_H - alto
                destino = (screen_x + offset_x + dx, screen_y + offset_y + dy)

            dibujar_con_contorno(surface, frame, destino)
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

    #: AUD-636 — cuánto tarda el squash en volver a identidad, en 1/s.
    _SQUASH_RETORNO: float = 10.0
    #: Aplastamiento máximo. A la velocidad de caída máxima (500 px/s) el
    #: sprite llega a 0,72 de alto — se lee como impacto sin romper la silueta.
    _SQUASH_MAX: float = 0.28

    def aplicar_squash_por_aterrizaje(self, velocidad_caida: float) -> None:
        """Aplasta el sprite al aterrizar, proporcional a la caída (AUD-636).

        La proporcionalidad es la mitad del efecto: caer dos baldosas y caer
        a un pozo no pueden deformar igual, o el grado deja de informar.
        `fuerza` viaja también en `VFX_LAND_DUST` para que las partículas
        hereden la misma lectura.
        """
        fuerza = max(0.0, min(1.0, abs(velocidad_caida) / settings.PLAYER_MAX_FALL_SPEED))
        # Umbral: una pisada de escalón no aplasta nada.
        if fuerza < 0.12:
            return
        aplaste = self._SQUASH_MAX * fuerza
        self._squash_y = 1.0 - aplaste
        # Conserva el área visual: lo que se pierde en alto se gana en ancho.
        self._squash_x = 1.0 + aplaste * 0.7
        self._event_bus.emit(
            Events.VFX_LAND_DUST,
            pos=(self.rect.centerx, self.rect.bottom),
            fuerza=fuerza,
        )

    def aplicar_stretch_por_salto(self) -> None:
        """Estira el sprite al despegar (AUD-636). Fijo: todo salto pesa lo
        mismo porque el impulso es constante (`perfil.salto_impulso`)."""
        self._squash_y = 1.14
        self._squash_x = 0.9
        self._event_bus.emit(
            Events.VFX_JUMP_DUST,
            pos=(self.rect.centerx, self.rect.bottom),
        )

    def _tick_timers(self, dt: float) -> None:
        """Tick all cooldown and duration timers."""
        # AUD-636 — retorno del squash a identidad. Exponencial y acotado:
        # multiplicar por un factor < 1 converge sin sobrepasar.
        if self._squash_x != 1.0 or self._squash_y != 1.0:
            decaimiento = min(1.0, dt * self._SQUASH_RETORNO)
            self._squash_x += (1.0 - self._squash_x) * decaimiento
            self._squash_y += (1.0 - self._squash_y) * decaimiento
            if abs(self._squash_x - 1.0) < 0.005 and abs(self._squash_y - 1.0) < 0.005:
                self._squash_x = self._squash_y = 1.0
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
        # AUD-573 — el nado gestiona su propio eje Y y no recibe la
        # gravedad del perfil. `SwimmingState` ya declara su peso residual
        # (`GRAVITY * 0.05`) pensado como ÚNICA fuerza vertical: con la
        # gravedad completa encima, el jugador sumergido se hundía a
        # ~113 px/s en vez de flotar (el freno del nado convergía contra
        # la gravedad, no contra cero), y posado en un lecho a 16px del
        # borde del agua —el caso del 4-1b— el empuje de -1.5 px/frame se
        # cancelaba contra la colisión del suelo antes de despegar: el
        # jugador no podía nadar hacia arriba de ninguna forma (reporte
        # «el personaje no nada»). `_apply_physics` es el integrador del
        # perfil; los estados acuáticos declaran su eje Y completo y el
        # integrador se lo deja.
        if not self.is_grounded and self._state_instance.state_enum not in (
            PlayerState.SWIMMING, PlayerState.SWIM_ATTACK,
        ):
            gm = self.gravity_multiplier
            # AUD-333 — gravedad, caída máxima y factores de muro salen del
            # perfil: un contexto declara su física, el integrador la lee.
            if wall_side != 0 and self.velocity.y > 0:
                self.velocity.y += (
                    self.perfil.gravedad * gm
                    * self.perfil.muro.factor_gravedad * dt
                )
                self.velocity.y = min(
                    self.velocity.y,
                    self.perfil.max_caida * gm * self.perfil.muro.factor_max_caida,
                )
                self._wall_slide_timer += dt
            else:
                self.velocity.y += self.perfil.gravedad * gm * dt
                self.velocity.y = min(
                    self.velocity.y,
                    self.perfil.max_caida * gm,
                )
                self._wall_slide_timer = 0.0

        # AUD-336 — la aceleración/fricción del perfil se aplica a la
        # velocidad horizontal que la máquina de estados acaba de fijar.
        self._aplicar_friccion_y_aceleracion(dt)

        # Coyote time
        if self.is_grounded:
            self._coyote_counter = 0
            self._wall_side = 0
        else:
            # AUD-143 — el contador avanza con el TIEMPO, no con los
            # fotogramas.
            #
            # Era `+= 1` por fotograma, así que la ventana de coyote duraba
            # seis fotogramas: 100 ms a 60 fps, 200 ms a 30 y 42 ms a 144. El
            # margen de perdón para saltar tarde —que es exactamente lo que
            # esta mecánica es— cambiaba con la máquina, y en un portátil que
            # baja a 30 fps el juego se volvía notablemente más blando.
            #
            # Se sigue contando en «fotogramas a 60 fps» para no tocar la
            # constante pública ni las comparaciones, pero la unidad ya es
            # real: `PLAYER_COYOTE_FRAMES = 6` son 100 ms en cualquier equipo.
            self._coyote_counter += dt * 60.0

    def _aplicar_friccion_y_aceleracion(self, dt: float) -> None:
        """AUD-336 — acerca la velocidad horizontal a la que fijó el estado.

        La máquina de estados sigue decidiendo la velocidad (`velocity.x`):
        andando, en el aire, en dash, al recibir daño. Con `aceleracion` en
        0 —el juego actual, los presets— esa cifra ES la velocidad, y aquí
        no hay nada que hacer. Con `aceleracion` > 0 la cifra pasa a ser el
        **objetivo**: la velocidad real parte de la del fotograma anterior
        (`_vx_integrada`) y se acerca al objetivo a ritmo acotado, de modo
        que un contexto de hielo o de inercia declara su perfil y el
        comportamiento lo hereda sin tocar los estados.

        Sin entrada el estado fija 0 y aquí se frena a ritmo de `friccion`
        (o de `aceleracion` si `friccion` no está). Las zonas del TMX
        (`sistema_friccion`, AUD-236) recortan la velocidad ya producida,
        así que multiplican la integración sin saber que existe.
        """
        if self.perfil.aceleracion <= 0.0 and self.perfil.friccion <= 0.0:
            self._vx_integrada = self.velocity.x
            return
        objetivo = self.velocity.x
        if objetivo != 0.0:
            if self.perfil.aceleracion > 0.0:
                self._vx_integrada = acercarse_a(
                    self._vx_integrada, objetivo,
                    self.perfil.aceleracion * dt)
            else:
                # Sin aceleración, el objetivo ES la velocidad: andar sigue
                # siendo instantáneo y `friccion` sólo manda al soltar.
                self._vx_integrada = objetivo
        else:
            tasa = self.perfil.friccion or self.perfil.aceleracion
            self._vx_integrada = acercarse_a(
                self._vx_integrada, 0.0, tasa * dt)
        self.velocity.x = self._vx_integrada

    # ──────────────────────────────────────────────
    # Collision resolution (AABB, axis-separated)
    # ──────────────────────────────────────────────

    def _estado_de_movimiento_para_resolver(self) -> EstadoDeMovimiento:
        """Construye el `EstadoDeMovimiento` de este fotograma.

        AUD-490 — separado de `_resolve_collision` para que la elección de
        material (zona vs. perfil) se pueda probar sin construir rects de
        colisión ni llamar al resolutor entero.
        """
        return EstadoDeMovimiento(
            posicion=self.position,
            velocidad=self.velocity,
            ancho=self.rect.width,
            alto=self.rect.height,
            en_el_suelo=self.is_grounded,
            prev_foot_y=self._prev_foot_y,
            # AUD-396 — el rebote sale del material (GAP-039). Con `ROCA`,
            # que es el de todos los mapas de hoy, vale 0 y el resolutor
            # hace exactamente lo de siempre.
            # AUD-490 — `_material_de_zona` gana si `sistema_friccion` lo
            # puso este fotograma (una `FrictionZone` con `material`); si
            # no, se usa el del perfil, que es el comportamiento de siempre.
            restitucion=(self._material_de_zona or self.perfil.material).restitucion,
        )

    def _resolve_collision(self, dt: float, collision_rects: list[pygame.Rect]) -> None:
        """
        AUD-334 — este método ya no resuelve: delega en el resolutor
        compartido (`framework/physics/resolucion.py`) y aplica sus hechos.

        Se conservan el nombre y la firma —lo llaman el jugador y las
        pruebas de los estudiantes— y el contrato de AUD-130: **integrar
        siempre, resolver sólo si hay contra qué**. La historia de por qué
        es de ejes separados, el umbral `v_overlap <= 2` y el `pre_mutate`
        del ledge grab viven ahora en `resolver_eje_x` y `resolver_eje_y`,
        que son el código que las cumple.
        """
        # AUD-636 — la velocidad de ANTES de resolver: el resolutor anula
        # `velocity.y` al aterrizar, y el aplastamiento necesita saber con
        # cuánta fuerza se llegó al suelo, no que ahora vale cero.
        vy_antes = self.velocity.y
        estado = self._estado_de_movimiento_para_resolver()
        eje_x = resolver_eje_x(estado, dt, collision_rects)
        if self.perfil.modo == PLATAFORMAS:
            # AUD-328/335 — sin gravedad no hay cuesta que resolver (pared
            # lateral incluida): en planta y en vuelo la rampa es terreno
            # pintado.
            resolver_paredes_de_pendientes(
                estado, self._pendientes,
                margen=self.perfil.cuestas.margen_pegado)
        eje_y = resolver_eje_y(estado, dt, collision_rects)

        self.position = estado.posicion
        self.velocity = estado.velocidad
        self.is_grounded = estado.en_el_suelo
        self._wall_side = eje_x.lado_de_pared
        self._can_wall_jump = eje_x.pared_en_el_aire
        self._can_ledge_grab = eje_x.repisa_libre
        # AUD-297 — se guarda para el paso de pendientes, que corre después
        # de este y necesita saber si el jugador **venía** pisando suelo.
        self._venia_del_suelo = estado.venia_del_suelo
        if eje_y.aterrizo_en == "suelo":
            self._event_bus.emit(Events.SFX_PLAYER_LAND)
            # AUD-636 — sólo si venía CAYENDO: aterrizar tras un salto cortado
            # (vy ≈ 0) no aplasta ni suelta polvo; la deformación es la señal
            # de impacto, y sin impacto no hay señal.
            if vy_antes > 0.0:
                self.aplicar_squash_por_aterrizaje(vy_antes)
            self._air_dash_count = 0
            self._air_jumps_used = 0

    def _resolver_pendientes(self, dt: float) -> None:
        """AUD-334 — delega en `resolver_cuestas`; los pies sobre la cuesta.

        La geometría vive en `framework/stage/pendientes.py`, que no toca al
        jugador: devuelve una `y` y aquí se aplica. Un módulo de geometría
        que mueve entidades ajenas es cómo se acaba con dos sistemas
        discutiendo la misma posición. AUD-297: las cuestas corren después
        del eje Y y antes de las repisas de un sentido.
        """
        if not self._pendientes:
            return
        if self.perfil.modo != PLATAFORMAS:
            # AUD-328 — idem que la pared lateral: sin gravedad la rampa es
            # terreno pintado y el glue vertical no debe activarse en la
            # vista cenital; AUD-335 — el vuelo idem, por la misma razón.
            return
        estado = EstadoDeMovimiento(
            posicion=self.position,
            velocidad=self.velocity,
            ancho=self.rect.width,
            alto=self.rect.height,
            en_el_suelo=self.is_grounded,
            venia_del_suelo=self._venia_del_suelo,
        )
        contacto = resolver_cuestas(
            estado, dt, self._pendientes, self.perfil.cuestas)

        self.position = estado.posicion
        self.velocity = estado.velocidad
        self.is_grounded = estado.en_el_suelo
        if contacto.aterrizo_en == "cuesta":
            self._event_bus.emit(Events.SFX_PLAYER_LAND)
        if contacto.aterrizo:
            self._air_dash_count = 0
            self._air_jumps_used = 0

    def _resolve_one_way_collision(self, dt: float, one_way_rects: list[pygame.Rect]) -> None:
        """AUD-334 — delega en `resolver_repisas`.

        Los guardas —sólo cayendo, con los pies a la altura del borde el
        fotograma anterior— viven en el resolutor. El sonido lo decide el
        jugador con el hecho `aterrizo_desde_el_aire`: AUD-255 — posarse en
        una repisa atravesable era **mudo**, y el evento existía con fichero
        y tabla desde el principio, sin emisor. Sólo al llegar desde el
        aire: si no, sonaría cada fotograma de pie encima.
        """
        if not one_way_rects:
            return
        if self.velocity.y < 0:
            return
        estado = EstadoDeMovimiento(
            posicion=self.position,
            velocidad=self.velocity,
            ancho=self.rect.width,
            alto=self.rect.height,
            en_el_suelo=self.is_grounded,
            prev_foot_y=self._prev_foot_y,
        )
        contacto = resolver_repisas(estado, one_way_rects)

        self.position = estado.posicion
        self.velocity = estado.velocidad
        self.is_grounded = estado.en_el_suelo
        if contacto.aterrizo:
            self._air_dash_count = 0
            self._air_jumps_used = 0
        if contacto.aterrizo_desde_el_aire and self._event_bus is not None:
            self._event_bus.emit(Events.SFX_ENVIRONMENT_ONE_WAY_PLATFORM)

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
