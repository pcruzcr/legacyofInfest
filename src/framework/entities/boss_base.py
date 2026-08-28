from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.boss_kit import (
    AttackScheduler,
    AttackTiming,
    SummonTracker,
    WeakPoint,
    resolve_weak_point_damage,
)
from src.framework.entities.enemy_base import EnemyBase, EnemyState

logger = logging.getLogger(__name__)


def normalizar_skill_drop(declarado: object) -> list[str]:
    """Las habilidades de un jefe, venga como venga declarado (AUD-263).

    `skill_drop` era un solo `str`, y eso dejaba a `skill_parry` sin dueño
    posible: el venado ya suelta el dash y quitárselo habría borrado una
    mecánica. Ahora acepta también una lista.

    Es función de módulo y no sólo método porque los guardianes de la suite
    comprueban las **clases** de jefe sin instanciarlas —construir un jefe
    carga sprites— y necesitan la misma lectura, no una copia que se
    desincronice.
    """
    if isinstance(declarado, str):
        return [declarado] if declarado else []
    if isinstance(declarado, (list, tuple, set)):
        return [str(s) for s in declarado if s]
    return []

@dataclass
class BossPhase:
    """Definition of a single boss phase."""

    phase_index: int
    health_threshold: float
    attack_patterns: list[str] = field(default_factory=list)
    movement_type: str = "stationary"
    speed_multiplier: float = 1.0
    sprite_override: str | None = None
    filter_effect: str | None = None
    combos: dict[str, list[str]] = field(default_factory=dict)
    # ── F5.7 — mecánicas de fase del dossier de jefes ──────────
    #: Inmune al daño durante toda la fase. Nosk, Metal Sonic, Mother Brain.
    #:
    #: Sirve para una fase de puesta en escena o para una en la que hay que
    #: hacer otra cosa —romper los frascos de The Collector, esquivar la
    #: cascada de Mega Satan— antes de poder volver a golpear. Una fase
    #: invulnerable **sin nada que hacer** es una pausa forzada y se nota; el
    #: calificador de jefes no puede distinguirlo, pero un jugador sí.
    invulnerable: bool = False
    #: Multiplicador de tamaño. Baby Bowser, Grim Matchstick, Mega Satan: 11 de
    #: los 185 análisis del dossier usan el crecimiento como señal de fase.
    #:
    #: Los `WeakPoint` se recalculan solos porque `rect_for()` deriva del rect
    #: del jefe; no hay que tocarlos al escalar.
    escala: float = 1.0


_APPLY_FILTER_EVERY_N_FRAMES = 5


class BossBase(EnemyBase):
    """
    Base class for all boss entities. Extends EnemyBase with phase management,
    phase transition protocol, and boss HUD integration.

    Subclasses define phases; this class handles health threshold checks,
    transition animation, and BOSS_PHASE_CHANGED event emission.
    """

    #: Habilidad que este jefe deja al morir (AUD-238). Uno de los `skill_*`
    #: de `engine.core.inventory`; cadena vacía = no suelta ninguna.
    #:
    #: **Vacía por defecto a propósito.** Los cuatro jefes del repositorio y
    #: los que escriban los estudiantes se comportan igual que antes mientras
    #: nadie la rellene, que es lo que exige la invariante 2. Un jefe que
    #: quiera conceder algo declara, por ejemplo,
    #: `skill_drop = "skill_dash"` en su clase — una línea, sin tocar nada más.
    skill_drop: str = ""

    #: AUD-606 — ¿las cajas y puntos débiles siguen al cuerpo escalado?
    #:
    #: **False por defecto, y no es pereza: es que no hay forma fiable de
    #: deducirlo.** Un jefe cuyas `_build_hitbox`/`_build_hurtbox` devuelven
    #: CONSTANTES del sprite base (el patrón del jefe de referencia) necesita
    #: que el motor escale sus cajas con la fase; uno que ya deriva las cajas
    #: del rect vivo (`Rect(0, 0, self.rect.width, ...)`, `caja_ajustada`)
    #: recibiría una DOBLE escala. El motor no puede distinguir un caso de
    #: otro, así que decide quien declara las cajas:
    #:
    #:     class MiJefe(BossBase):
    #:         cajas_siguen_al_cuerpo = True
    #:
    #: Con True, hitbox/hurtbox se escalan ancladas abajo-centro y los
    #: `WeakPoint` siguen la escala Y el espejado del facing dentro del
    #: propio `rect_for` — no hace falta espejarlos a mano.
    cajas_siguen_al_cuerpo: bool = False

    #: AUD-279 — un jefe nunca se congela por estar fuera del encuadre.
    #:
    #: Sus fases, sus temporizadores y sus invocaciones corren aunque la cámara
    #: mire a otro lado, y su arena no cabe en pantalla: la de `boss_venado`
    #: mide 3.280 px. Congelar a un jefe porque el jugador se alejó es la clase
    #: de optimización que produce un combate que se para solo.
    siempre_activo: bool = True

    def habilidades_que_suelta(self) -> list[str]:
        """Las habilidades que este jefe deja al morir (AUD-263).

        `skill_drop` era un solo `str`, y eso dejaba a `skill_parry` sin dueño
        posible: el venado ya suelta el dash y no se le puede quitar sin cambiar
        la progresión. Darle una lista al motor es lo que permite que un jefe
        enseñe más de una cosa.

        Acepta las dos formas **a propósito**. Una entrega que escriba
        `skill_drop = "skill_dash"` sigue funcionando exactamente igual: son 26
        escenarios ya calificados y la invariante 2 no admite «actualiza tu
        código». Quien quiera varias, escribe una lista.
        """
        return normalizar_skill_drop(getattr(self, "skill_drop", ""))

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 20.0,
        damage_on_contact: float = 1.0,
    ) -> None:
        super().__init__(  # BUG-078 FIX: detection_range de arena, no de patrulla
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            contact_knockback=0.0,
            detection_range_x=640.0,
            detection_range_y=480.0,
        )

        self.phases: list[BossPhase] = []
        self.current_phase: int = 0
        self.phase_health_thresholds: list[float] = []
        self.is_transitioning: bool = False
        self.transition_timer: float = 0.0
        self._phase_max_health: float = max_health
        self._boss_name: str = "BOSS"
        self._filter_frame: int = 0
        self._boss_sprite_prefix: str = ""
        self._completion_fired: bool = False
        self._transition_overlay: pygame.Surface | None = None
        self._flip_cache: dict[tuple[str, int], pygame.Surface] = {}
        # B-048: cache para sobel (evita recalcular cada frame y evita parpadeo)
        self._filter_cache: dict[int, pygame.Surface] = {}

        # ── Kit de encuentro (AUD-053) ─────────────────────────
        # Antes de esto BossBase sólo sabía de fases. Telegrafiado, puntos
        # débiles e invocaciones — todo lo que docs/17_BOSS_SPEC.md describe —
        # no tenía representación en código. Se construye aquí para que
        # cualquier jefe lo herede en lugar de reimplementarlo.
        self.attacks: AttackScheduler = AttackScheduler()
        self.weak_points: list[WeakPoint] = []
        self.summons: SummonTracker = SummonTracker()
        #: Esbirros creados este fotograma; StageScene los recoge y los añade
        #: a la escena. El jefe no conoce la escena, así que no puede
        #: insertarlos él mismo — eso mantendría una dependencia al revés.
        self.pending_summons: list[EnemyBase] = []
        #: Último punto débil acertado, para VFX y para el overlay de debug.
        self.last_weak_point: WeakPoint | None = None
        #: Límites del arena, que la escena fija con el tamaño del mapa. `None`
        #: hasta entonces: un jefe construido en una prueba no tiene arena y no
        #: debe fingir una.
        self.arena_bounds: pygame.Rect | None = None
        #: Multiplicador de velocidad de la fase activa. Existe porque
        #: `_finish_phase_transition` leía `phase.speed_multiplier` y lo
        #: descartaba con un `pass`: un jefe que declaraba acelerar en la
        #: fase 2 no aceleraba.
        self.speed_multiplier: float = 1.0
        #: Tamaño de la caja antes de cualquier escalado de fase (AUD-257). Se
        #: fija en el primer cambio de fase: los jefes de los estudiantes
        #: ajustan su rect en `__init__` después de llamar a `super()`, así que
        #: leerlo aquí guardaría el tamaño equivocado.
        self._tam_base: tuple[int, int] | None = None

    def __setattr__(self, name: str, value: object) -> None:
        # AUD-XXX: is_visible=False debe interrumpir el ataque en curso
        # inmediatamente, no solo en el proximo tick.
        object.__setattr__(self, name, value)
        if name == "is_visible" and value is False:
            try:
                atk = object.__getattribute__(self, "attacks")
                atk.interrupt()
            except AttributeError:
                pass

    @property
    def completion_fired(self) -> bool:
        return self._completion_fired

    @completion_fired.setter
    def completion_fired(self, value: bool) -> None:
        self._completion_fired = value

    def _load_boss_sprites(  # BUG-077 FIX: sheets y base_dir opcionales; logging en DEBUG
        self, prefix: str, fw: int = 48, fh: int = 48,
        sheets: dict[str, tuple[int, int]] | None = None,
        base_dir: str | None = None,
    ) -> None:
        """Load boss sprites from assets/sprites/bosses/{prefix}_{name}.png.

        Args:
            prefix: File name prefix for sprite sheets.
            fw: Default frame width.
            fh: Default frame height.
            sheets: Optional mapping of anim_key → (frame_width, frame_height)
                    for bosses with varying frame sizes per animation.
            base_dir: Optional subdirectory override.
        """
        from pathlib import Path
        base = Path(base_dir) if base_dir else settings.ASSETS_DIR / "sprites/bosses"
        self._boss_sprite_prefix = prefix
        self._sprite_fw = fw
        self._sprite_fh = fh
        default_keys = ("drift", "hurt", "charge", "stomp", "vine", "death")
        anim_keys = list(sheets.keys()) if sheets else default_keys
        for anim_key in anim_keys:
            sw, sh = (sheets[anim_key] if sheets and anim_key in sheets else (fw, fh))
            path = base / f"{prefix}_{anim_key}.png"
            if not path.exists():
                logger.debug("boss_base: sprite not found (optional) %s", path)
                continue
            try:
                frames = AssetLoader.load_sprite_sheet(path, sw, sh)
                self._sprite_frames[anim_key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.debug("boss_base: failed to load sprite %s", path)

    def set_phases(self, phases: list[BossPhase]) -> None:
        """Set the phase list and extract health thresholds."""
        self.phases = phases
        self.phase_health_thresholds = [p.health_threshold for p in phases]

    def set_boss_name(self, name: str) -> None:
        self._boss_name = name

    @property
    def boss_name(self) -> str:
        return self._boss_name

    @property
    def phase_count(self) -> int:
        return len(self.phases) if self.phases else 1

    @property
    def phase_max_health(self) -> float:
        return self._phase_max_health

    def _get_animation_state(self) -> str:
        """Boss-specific animation mapping: uses 'death' instead of 'die'."""
        if self.state == EnemyState.DYING:
            return "death"
        if self.state == EnemyState.HURT:
            return "hurt"
        return self._get_animation_key()

    def _get_animation_key(self) -> str:
        """Return the sprite animation key for the current non-DYING/HURT state."""
        return "drift"

    def apply_hit(
        self,
        damage: float,
        source_position: tuple[float, float],
        canal: str | None = None,
    ) -> None:
        if not self.is_visible:
            return
        if not self.is_alive or self.is_transitioning:
            return
        if self._invincibility_timer > 0:
            return
        if self.fase_invulnerable:
            # F5.7 — una fase declarada invulnerable no recibe daño, y no es lo
            # mismo que estar en transición: aquí el jefe sigue atacando, sólo
            # que golpearlo no sirve hasta que se cumpla lo que la fase pida.
            return
        super().apply_hit(damage, source_position, canal=canal)

        if self.current_health > 0 and self.state != EnemyState.DYING:
            self._check_phase_transition()

    # ── F5.7 — estado de fase y desvío ─────────────────────────
    @property
    def fase_invulnerable(self) -> bool:
        """¿La fase actual declara inmunidad al daño?"""
        if not self.phases or self.current_phase >= len(self.phases):
            return False
        return bool(getattr(self.phases[self.current_phase], "invulnerable", False))

    @property
    def escala_de_fase(self) -> float:
        """Multiplicador de tamaño de la fase actual."""
        if not self.phases or self.current_phase >= len(self.phases):
            return 1.0
        return float(getattr(self.phases[self.current_phase], "escala", 1.0))

    def _aplicar_escala_de_fase(self) -> None:
        """Redimensiona la caja del jefe según `escala` de la fase (AUD-257).

        Hasta aquí `escala_de_fase` era una propiedad que devolvía un número
        que **nadie leía**: declararla en una fase no cambiaba nada, igual que
        pasaba con `speed_multiplier` antes de AUD-053.

        Se ancla por los pies y por el centro. Crecer desde la esquina
        superior izquierda —lo que sale gratis si sólo se toca `width`—
        hundiría medio jefe en el suelo y lo desplazaría a la derecha; anclar
        abajo es lo que hace cualquier transformación de personaje.

        `position` se actualiza junto al rect porque es la fuente de verdad
        del motor: `clamp_to_arena` hace `rect.x = int(position.x)` y desharía
        el cambio al fotograma siguiente.
        """
        if self._tam_base is None:
            self._tam_base = (self.rect.width, self.rect.height)
        escala = self.escala_de_fase
        ancho = max(1, int(self._tam_base[0] * escala))
        alto = max(1, int(self._tam_base[1] * escala))
        if (ancho, alto) == (self.rect.width, self.rect.height):
            return
        pies, centro = self.rect.bottom, self.rect.centerx
        self.rect.size = (ancho, alto)
        self.rect.bottom, self.rect.centerx = pies, centro
        self.position.update(float(self.rect.x), float(self.rect.y))

    def _escala_viva(self) -> float:
        """Factor de escala real del cuerpo (AUD-606).

        Derivado del rect vivo y no de `escala_de_fase` para que también
        cubra a quien redimensione el rect por fuera del protocolo de fases:
        la caja debe coincidir con el cuerpo que se ve, venga el tamaño de
        donde venga.
        """
        if self._tam_base is None or not self._tam_base[0]:
            return 1.0
        return self.rect.width / self._tam_base[0]

    def _escalar_local(self, caja: pygame.Rect) -> pygame.Rect:
        """Escala hitbox/hurtbox locales con la fase (AUD-606).

        Escalado PURO del offset y del tamaño, sin recentrar: el dibujo
        (`draw`) ya coloca el sprite escalado centrado sobre el rect vivo,
        así que el pixel local `p` del sprite base cae en `p * escala` del
        cuerpo — la caja tiene que caer exactamente igual. Recentrar por
        nuestra cuenta descolocaría la caja media silueta respecto de lo
        que se pinta. Sólo actúa en los jefes que declaran
        `cajas_siguen_al_cuerpo`; ver el comentario del atributo para por
        qué no puede ser el comportamiento por defecto.
        """
        if not self.cajas_siguen_al_cuerpo:
            return caja
        escala = self._escala_viva()
        if escala == 1.0:
            return caja
        return pygame.Rect(
            round(caja.x * escala),
            round(caja.y * escala),
            max(1, round(caja.width * escala)),
            max(1, round(caja.height * escala)),
        )

    @property
    def aturdido(self) -> bool:
        return getattr(self, "_aturdimiento", 0.0) > 0.0

    def recibir_parry(self) -> float:
        """El jugador desvió el ataque en curso. Devuelve el aturdimiento.

        Es el punto de entrada de la mecánica y vive en `BossBase` a propósito,
        para que **cualquier** jefe de un estudiante la tenga sin escribir nada:
        basta con marcar un `BossAttack(parriable=True)`. La alternativa —que
        cada uno se lo implemente— garantizaba que casi nadie lo hiciera.
        """
        aturde = self.attacks.desviar()
        if aturde > 0.0:
            self._aturdimiento = aturde
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="PARRIED", rect=self.rect)
        return aturde

    def _aturdimiento_por_parry(self) -> float:
        """Conecta el parry genérico con la mecánica de desvío del jefe.

        AUD-243 — el eslabón que faltaba. `recibir_parry()` se describe a sí
        misma como «el punto de entrada de la mecánica» y no tenía **ningún**
        llamante: ni en producción ni en pruebas. `BossAttack.parriable` y
        `aturde_al_parry` existían, se probaban por unidad, y no cambiaban
        nada en ningún jefe — el campo era decorativo.

        Si hay un ataque parable en curso manda su aturdimiento, que es mayor
        que el genérico porque acertar la ventana de un jefe es más difícil.
        Si no lo hay, se cae al de `EnemyBase`: parar a un jefe fuera de su
        ataque sigue valiendo, sólo que lo de siempre.
        """
        aturde = self.recibir_parry()
        return aturde if aturde > 0.0 else super()._aturdimiento_por_parry()

    def teletransportar(self, x: float, y: float) -> None:
        """Reaparece en otro punto de la arena. Death, Agahnim, The Time Keeper.

        `(x, y)` es la **esquina superior izquierda**, igual que `position` en
        todo el motor. La primera versión trataba el argumento como centro para
        el rect y como esquina para la posición, y `clamp_to_arena` —que hace
        `rect.x = int(position.x)`— deshacía la mitad: el jefe acababa doce
        píxeles a la derecha de donde se le había mandado.

        Es exactamente el error que este método existe para evitar, cometido al
        escribirlo. Lo cazó la primera prueba, que es para lo que están.
        """
        self.position.update(x, y)
        self.rect.topleft = (int(x), int(y))
        self.clamp_to_arena()

    def _check_phase_transition(self) -> None:
        """Check if health dropped below the next phase threshold."""
        if self.current_phase >= len(self.phase_health_thresholds) - 1:
            return
        next_threshold = self.phase_health_thresholds[self.current_phase + 1]
        if self.current_health <= next_threshold:
            self._start_phase_transition()

    def _start_phase_transition(self) -> None:
        """Begin phase transition: invincible, timer starts."""
        # AUD-064: el momento más importante del combate no hacía ruido.
        # AUD-489 — sin `pos`, `play_sfx_critico` cae a volumen fijo
        # (`audio_manager.py:310-316`); con él, usa el suelo de atenuación
        # que AUD-369 ya construyó para exactamente este caso — un cambio de
        # fase lejos de la cámara se sigue oyendo, y ahora además con la
        # distancia real en vez de ignorarla.
        self._event_bus.emit(
            Events.SFX_BOSS_PHASE_CHANGE, pos=(self.position.x, self.position.y),
        )
        self.is_transitioning = True
        self._invincibility_timer = float("inf")
        self.transition_timer = 2.5

    def _finish_phase_transition(self) -> None:
        """Complete phase transition: advance phase, emit event, trigger VFX."""
        self.current_phase += 1
        self.is_transitioning = False
        self._invincibility_timer = 0.0
        self._filter_frame = 0

        phase = self.phases[self.current_phase]
        # AUD-053: esto era `if phase.speed_multiplier != 1.0: pass` — se leía
        # el valor y se tiraba. Ahora se aplica, que es lo que hace que una
        # fase 2 "más agresiva" se note.
        self.speed_multiplier = float(phase.speed_multiplier)
        # AUD-257 — y lo mismo que le pasaba a `speed_multiplier` le pasaba a
        # `escala`: se leía en una propiedad que nadie consultaba. Aquí se
        # aplica de verdad.
        self._aplicar_escala_de_fase()
        # Un cambio de fase interrumpe el ataque en curso: seguir con el aviso
        # de la fase anterior mientras el jefe cambia de forma es ilegible.
        self.attacks.interrupt()

        if self.current_phase < len(self.phase_health_thresholds):
            self._phase_max_health = self.phase_health_thresholds[self.current_phase]
        self.current_health = min(self.current_health, self._phase_max_health)

        self._event_bus.emit(
            Events.BOSS_PHASE_CHANGED,
            boss_name=self._boss_name,
            phase=self.current_phase,
            phase_count=self.phase_count,
            new_max_health=self._phase_max_health,
        )
        self._event_bus.emit(
            Events.VFX_ULTIMATE,
            pos=(self.position.x, self.position.y - 20),
        )
        self._event_bus.emit(
            Events.VFX_PARRY,
            pos=(self.position.x, self.position.y - 20),
        )
        self._event_bus.emit(
            Events.MUSIC_STINGER,
            name=f"stinger_boss_phase_{self.current_phase}",
            volume=0.8,
        )

        # Check if another transition is needed (e.g. health dropped below multiple thresholds)
        self._check_phase_transition()

    def _pre_update(self, dt: float) -> bool:
        """Handle phase transitions. Return True to skip normal update."""
        # AUD-XXX: si el jefe está invisible, no avanza fase ni ataques
        if not self.is_visible:
            self.attacks.interrupt()
            return False
        if self.is_transitioning:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self._finish_phase_transition()
            return True

        self._update_encounter(dt)
        return False

    # ── Kit de encuentro (AUD-053) ─────────────────────────────

    def _update_encounter(self, dt: float) -> None:
        """Avanza ataques telegrafiados e invocaciones.

        Deliberadamente **no** escribe en `self.state`. Es tentador hacerlo —
        el tramo del ataque parece un estado— pero `EnemyBase._run_state_machine`
        trata TELEGRAPHING, FIRING y RECOVER como estados con temporizador
        propio y sale antes de ejecutar el comportamiento de la subclase. Si el
        planificador pusiera esos estados, habría dos relojes gobernando el
        mismo ataque y el jefe dejaría de moverse durante todo el ciclo: como
        casi siempre hay un ataque en curso, el Venado se quedaría quieto la
        práctica totalidad del combate.

        El tramo se consulta por `attack_timing`, que es lectura pura. La
        animación y el HUD leen de ahí; la máquina de estados sigue siendo la
        dueña del estado.
        """
        # AUD-XXX: invisible no telegrafia ni invoca
        if not self.is_visible:
            self.attacks.interrupt()
            return
        self.summons.update(dt)

        if self.state == EnemyState.DYING or not self.is_alive:
            return

        # F5.7 — aturdido por un desvío. Se descuenta aquí y no en `update` para
        # que un jefe que sobreescriba `update()` —lo hacen tres de las cuatro
        # entregas— siga descontándolo sin tener que acordarse.
        aturdimiento = getattr(self, "_aturdimiento", 0.0)
        if aturdimiento > 0.0:
            self._aturdimiento = max(0.0, aturdimiento - dt)
            self.attacks.interrupt()
            return

        # Aturdido: se cancela el ataque. Una parada acertada tiene que
        # interrumpir al jefe o parar no sirve para nada.
        if self.state == EnemyState.STUNNED:
            self.attacks.interrupt()
            return

        # Sin haber visto al jugador no se telegrafía nada: un jefe que ataca
        # al aire antes de que entres en la arena gasta sus enfriamientos y
        # llega al primer encuentro con todo en cooldown.
        if self._player_ref is None or self.state in (
            EnemyState.PATROL, EnemyState.IDLE,
        ):
            return

        distance = abs(self._player_ref.centerx - self.rect.centerx)

        fired = self.attacks.update(dt, distance, self.current_phase)
        if fired is not None:
            self.on_attack_fired(fired)

        wave = self.summons.ready_wave(self.current_phase)
        if wave is not None and self._player_ref is not None:
            spawned = self.summons.spawn(wave, self.position)
            if spawned:
                self.pending_summons.extend(spawned)
                self.on_summon(wave.species_id, len(spawned))

    def on_attack_fired(self, _attack_name: str) -> None:
        """Gancho: el ataque acaba de pasar de aviso a golpe.

        Las subclases lo sobreescriben para generar proyectiles, sacudir la
        cámara o lanzar VFX. La base no asume nada sobre qué hace cada ataque.
        """

    def on_summon(self, species_id: str, count: int) -> None:
        """Gancho: se acaba de invocar una oleada."""

    def take_summons(self) -> list[EnemyBase]:
        """Entrega los esbirros pendientes y vacía la cola.

        `StageScene` los recoge y los añade a la escena. El jefe no conoce la
        escena a propósito: que una entidad inserte cosas en el mundo invierte
        la dirección de dependencia y hace imposible probarla aislada.
        """
        pending = self.pending_summons
        self.pending_summons = []
        return pending

    def set_arena_bounds(self, bounds: pygame.Rect) -> None:
        """Define los límites dentro de los que el jefe puede moverse (AUD-061).

        La escena lo llama con el tamaño real del mapa. Antes cada jefe llevaba
        sus propias constantes —`BossVenado` declaraba `ARENA_W = 320` para un
        mapa de 640— y nadie las comparaba con nada: el jefe peleaba en la
        mitad del escenario y una embestida podía sacarlo fuera del mapa, donde
        el jugador no puede alcanzarlo y el combate deja de poder ganarse.
        """
        self.arena_bounds = pygame.Rect(bounds)

    def clamp_to_arena(self, margin: int = 16) -> None:
        """Devuelve al jefe dentro de su arena si se ha salido.

        Se aplica a la posición y al rect a la vez porque el movimiento del
        jefe escribe en `position` y el rect se deriva después; corregir sólo
        uno deja los dos en desacuerdo durante un fotograma, que es tiempo
        suficiente para que una comprobación de colisión use el valor viejo.
        """
        if self.arena_bounds is None:
            return
        left = self.arena_bounds.left + margin
        right = self.arena_bounds.right - margin - self.rect.width
        if right < left:  # arena más estrecha que el jefe: se centra
            left = right = self.arena_bounds.centerx - self.rect.width // 2
        self.position.x = max(left, min(right, self.position.x))
        self.rect.x = int(self.position.x)

    @property
    def attack_timing(self) -> AttackTiming:
        """Tramo del ataque en curso. Lo leen la animación y el HUD."""
        return self.attacks.timing

    @property
    def is_vulnerable(self) -> bool:
        """¿Está el jefe en su ventana de castigo?"""
        return self.attacks.is_vulnerable

    @property
    def telegraph_progress(self) -> float:
        """0-1 durante el aviso; el HUD lo usa para el indicador."""
        return self.attacks.telegraph_progress

    def weak_point_at(self, hit_rect: pygame.Rect) -> WeakPoint | None:
        """El punto débil expuesto que ese golpe alcanza, si alguno."""
        if not self.is_visible:
            return None
        for point in self.weak_points:
            # AUD-606 — escala de fase y espejado por dirección para los
            # jefes que declaran `cajas_siguen_al_cuerpo`; el resto conserva
            # la llamada histórica sin alterar.
            if point.exposed_in(self.current_phase) and hit_rect.colliderect(
                point.rect_for(
                    self.rect,
                    escala=self._escala_viva(),
                    facing=self.facing_direction,
                ) if self.cajas_siguen_al_cuerpo else point.rect_for(self.rect),
            ):
                return point
        return None

    def apply_hit_at(
        self,
        damage: float,
        source_position: tuple[float, float],
        hit_rect: pygame.Rect | None = None,
    ) -> float:
        """Aplica daño teniendo en cuenta puntos débiles. Devuelve el daño real.

        Acertar un punto débil multiplica el daño y lo anuncia por el bus, para
        que el VFX y el sonido confirmen al jugador que ha acertado *ahí*. Sin
        esa confirmación, un punto débil es indistinguible de un golpe normal y
        el jugador nunca aprende que existe.
        """
        final = damage
        point = None
        if hit_rect is not None and self.weak_points:
            final, point = resolve_weak_point_damage(
                self, hit_rect, damage, self.weak_points, self.current_phase,
            )
        self.last_weak_point = point

        if point is not None:
            self._event_bus.emit(
                Events.VFX_PARRY,
                pos=(self.position.x, self.position.y),
            )
        self.apply_hit(final, source_position)
        return final

    _PHASE_COLORS = [
        (200, 100, 0),
        (200, 0, 0),
        (150, 0, 200),
    ]

    def _get_ambient_tint(self) -> tuple[int, int, int] | None:
        if not self.phases or self.current_phase >= len(self.phases):
            return None
        if self.current_phase < len(self._PHASE_COLORS):
            return self._PHASE_COLORS[self.current_phase]
        return None

    def _apply_filter(self, frame: pygame.Surface) -> pygame.Surface:
        """Apply the current phase's filter effect to a sprite frame (fix B-048).

        Antes devolvía el sobel opaco negro que tapaba al jefe y solo 1 de cada
        5 frames → parpadeo negro ~12 Hz. Ahora el sobel devuelve contorno con
        SRCALPHA (ver FilterTools.sobel_edge) y se compone encima del sprite
        original, cacheando el resultado para no recalcular cada frame pero sin
        parpadear: cuando hay efecto, siempre se devuelve el frame filtrado.
        """
        if not self.phases or self.current_phase >= len(self.phases):
            return frame
        phase = self.phases[self.current_phase]
        effect = phase.filter_effect
        if effect is None:
            return frame
        # Throttle de cómputo pero sin parpadeo: cachear
        cache_key = id(frame) ^ hash(effect)
        cached = self._filter_cache.get(cache_key)
        # Solo recalcular cada N frames o si no hay cache
        self._filter_frame += 1
        if cached is not None and self._filter_frame % _APPLY_FILTER_EVERY_N_FRAMES != 0:
            return cached
        from src.framework.processing.filter_tools import FilterTools
        if effect == "sobel":
            edge = FilterTools.sobel_edge(frame)
            # Si sobel ya devuelve overlay transparente (sprite con alpha), componer
            if edge.get_flags() & pygame.SRCALPHA:
                composited = frame.copy().convert_alpha()
                # edge ya tiene fondo transparente y borde blanco → blit normal
                composited.blit(edge, (0, 0))
                self._filter_cache[cache_key] = composited
                return composited
            # Fallback opaco (foto de laboratorio): devolver tal cual
            self._filter_cache[cache_key] = edge
            return edge
        if effect == "sobel_x":
            import numpy as np
            k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
            result = FilterTools.apply_kernel(frame, k)
            self._filter_cache[cache_key] = result
            return result
        return frame

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        if not self.is_visible or not self.is_alive:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        # Try sprite rendering with filter effects
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            frame = frames[frame_idx]
            if self.facing_direction < 0:
                cached = self._flip_cache.get((anim_key, frame_idx))
                if cached is None:
                    cached = pygame.transform.flip(frame, True, False)
                    self._flip_cache[(anim_key, frame_idx)] = cached
                frame = cached
            if self.is_transitioning:
                # AUD-607 — tinte de transición POR SILUETA y sobre una copia.
                #
                # Antes se hacía `frame.blit(overlay, BLEND_RGBA_ADD)` sobre
                # `frame` **directamente**, y `frame` es una superficie
                # cacheada (`_sprite_frames` o `_flip_cache`): el tinte se
                # acumulaba fotograma a fotograma en la cache y sobrevivía al
                # final de la transición, además de cubrir el rectángulo
                # entero —un cuadrado translúcido— en vez del cuerpo. Ahora:
                # copia nueva, y el brillo se recorta contra el canal alfa
                # del sprite (BLEND_RGBA_MIN contra silueta blanqueada).
                frame = frame.copy()
                silueta = frame.copy()
                silueta.fill((255, 255, 255),
                             special_flags=pygame.BLEND_RGB_MAX)
                brillo = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                brillo.fill((200, 200, 0, 90))
                brillo.blit(silueta, (0, 0),
                            special_flags=pygame.BLEND_RGBA_MIN)
                frame.blit(brillo, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                frame = self._apply_filter(frame)
            # AUD-257 — el sprite sigue a la caja. Sin esto, una fase con
            # `escala` daba un jefe cuya silueta y cuyo alcance no coinciden:
            # el jugador golpea aire o recibe daño de la nada.
            escala = self.escala_de_fase
            if escala != 1.0:
                frame = pygame.transform.scale(
                    frame,
                    (max(1, int(frame.get_width() * escala)),
                     max(1, int(frame.get_height() * escala))),
                )
            ox = (self.rect.width - frame.get_width()) // 2
            oy = self.rect.height - frame.get_height()
            surface.blit(frame, (screen_x + ox, screen_y + oy))
            return

        # Fallback placeholder
        color = (120, 40, 140) if not self.is_transitioning else (200, 200, 0)
        pygame.draw.rect(
            surface,
            color,
            (screen_x, screen_y, self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, self.rect.width, self.rect.height),
            1,
        )
