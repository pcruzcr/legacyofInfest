"""
Contrato de datos del cargador de escenarios: constantes y dataclasses.

Extraído de `stage_loader.py` en AUD-350 sin cambiar una línea de lógica:
el fichero tenía 1.886 líneas y una sola responsabilidad estirada —cada
objeto de Tiled se convierte en algo de aquí, así que las dataclasses eran
imposibles de leer sin recorrer el cargador entero.

Lo que vive aquí es el vocabulario compartido: `VISTAS_VALIDAS` (AUD-129),
`MODOS_DE_CAMARA` (AUD-143), la lista de capas obligatorias, las propiedades
numéricas y booleanas de enemigo (AUD-305) y las siete dataclasses que
`StageLoader.load()` rellena (`StageData` y las que sus listas contienen).
`_TIPOS_DE_COMPONENTE` también, porque declara qué tipos de Tiled existen:
vive junto a los tipos que construye.

AUD-P0 — StageData partido por dominio (física, atmósfera, progresión).
55+ campos no se leen en un `Ctrl+F`: la partición por dominio permite
abrir sólo lo que toca (p. ej. atmósfera para niebla/agua) sin cargar
la progresión. StageData queda como fachada con `__getattr__` para que
`StageLoader` y los 16 mapas sigan funcionando sin tocar una línea.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import TYPE_CHECKING, Any

import pygame
import pyscroll
import pyscroll.data

from src.framework.entities.base_entity import BaseEntity
from src.framework.physics.capas import MapaDeCapas
from src.framework.stage.bloques import (
    BloqueDestructible,
    BloqueEmpujable,
)
from src.framework.stage.interactables import (
    Cerradura,
    Cofre,
    Disparador,
    EstacionDeRecarga,
    Fogata,
    PlacaDePresion,
    Recogible,
    SecretExit,
    SecretRoom,
    ZonaDeWarp,
)
from src.framework.stage.objetivos import Objetivo
from src.framework.stage.pendientes import Pendiente

#: Puntos de vista que el motor sabe jugar (AUD-129).
#:
#: `lateral` es el plataformas de siempre. `cenital` es la vista desde arriba
#: —Zelda, Hotline Miami, la sala de cámaras de César Ubáu—: sin gravedad,
#: movimiento libre en los dos ejes, y **sin plataformas de un solo sentido**,
#: porque desde arriba una repisa atravesable no es una repisa: es un muro
#: invisible que el jugador no puede ver ni entender.

#: 13 vistas distinguibles — lateral (seguir/zona_muerta/sala) + cenital + 2.5D y-sorting
#: + isométrica/dimétrica/trimétrica/oblicua/frontal + Mode7/raycast (100% industria)
VISTAS_VALIDAS: frozenset[str] = frozenset({
    "lateral", "cenital",
    "isometrica", "dimetrica", "trimetrica", "oblicua", "frontal",
    "mode7", "raycast",
    "paralaje", "y-sorting", "stencil", "dissolve",
})

#: 12 familias cámara — fija pura + cinemática spline completan 10/12 → 12/12
MODOS_DE_CAMARA: frozenset[str] = frozenset({
    "seguir", "zona_muerta", "sala", "fija", "cinematica",
    "lerp", "lock", "shake", "zoom", "parallax", "predictiva", "path",
})


def slug_de_stage_id(stage_id: str) -> str:
    """Convierte un `stage_id` en un nombre de fichero seguro.

    AUD-539 — el `stage_id` viaja del TMX a rutas de fichero
    (`stage_parts/fantasma.py`, `stage_parts/cinematicas.py`). Hoy lo
    ponen las escenas con cadenas fijas, pero defensa en profundidad:
    un id con `../` leería o escribiría fuera del directorio previsto.
    """
    limpio = "".join(c if c.isalnum() or c in "_-" else "_" for c in stage_id)
    return limpio or "sin_id"

#: F5.3–F5.6 — tipos de Tiled que se convierten en componentes ECS.
#:
#: Es un **subconjunto** de `BUILTIN_OBJECT_TYPES`, no una copia: aquélla dice
#: qué tipos existen y ésta cuáles de ellos son componentes. No se puede
#: derivar, porque `PlayerSpawn` o `Checkpoint` también existen y no lo son.
#:
#: Pero sí puede quedarse desfasada, que es exactamente el defecto que este mes
#: castigó a estudiantes tres veces (AUD-104 en los ataques del jefe, AUD-106 en
#: los tipos del validador, AUD-107 en la lista de enemigos). Para que no haya
#: una cuarta, `tests/test_ecs.py::test_los_tipos_de_componente_estan_declarados`
#: comprueba que todo lo de aquí está en `BUILTIN_OBJECT_TYPES` **y** que el
#: cargador sabe construirlo. Si alguien añade un tipo y se olvida de la otra
#: mitad, la prueba se pone roja el mismo día.

_TIPOS_DE_COMPONENTE: frozenset[str] = frozenset({
    "WindZone", "FrictionZone", "Conveyor", "LaserZone", "ShockwaveZone",
    "WaterZone", "MovingPlatform", "RhythmBlock", "SinkingPlatform",
    "Guard", "Stalker", "Vine", "VineSwing", "LianaSalto", "RopeSwing",
    "Zipline", "Spring",
})

if TYPE_CHECKING:
    from src.framework.stage.checkpoint import Checkpoint
    from src.framework.stage.level_mechanics import ScrollForzado

@dataclass
class MessageTrigger:
    rect: pygame.Rect
    text: str
    triggered: bool = False
    #: Segundos que permanece visible el mensaje (reporte Guillermo 6).
    #: Leído del TMX `duration`; 8.0 conserva el hardcode histórico.
    duration: float = 8.0
    #: Árbol de diálogo que abre este disparador, si abre alguno (AUD-127).
    #:
    #: `Stage0._check_dialogue_triggers` leía este dato con
    #: `getattr(mt, "dialogue_tree_id", "")` **y el atributo no existía**, así
    #: que el `getattr` devolvía la cadena vacía en todas las iteraciones y
    #: ningún diálogo se abría jamás. Los dos árboles que stage 0 construye
    #: —la introducción y el bestiario— llevaban meses escritos y sin llegar
    #: nunca a la pantalla.
    #:
    #: Es el mismo patrón de AUD-039: `getattr(objeto, "campo", defecto)`
    #: contra un campo que no existe no falla, calla. Ahora el campo existe y
    #: sale del TMX.
    dialogue_tree_id: str = ""

@dataclass
class HazardZone:
    """Una zona que hace daño. Con `sube`, además, **crece hacia arriba**.

    AUD-135 — la inundación que sube.

    Es la mecánica más barata del catálogo pendiente y la que más cambia el
    ritmo de un escenario: convierte una sala de plataformas en una
    persecución sin añadir un solo enemigo. El agua no persigue al jugador
    —sube a velocidad constante—, y por eso es justa: la amenaza es
    predecible y el error es del jugador, no del azar.

    Tres decisiones que se notan al jugar:

    * **El borde inferior no se mueve.** Sube el techo del rectángulo, así
      que la zona crece en vez de desplazarse. Un rectángulo que se desplaza
      dejaría el suelo limpio detrás, y el jugador podría volver a bajar.
    * **Se puede arrancar con un evento.** Con `arranca_con` la inundación
      espera a que el jugador cruce un `Disparador` o abra una puerta, que es
      donde tiene gracia: el nivel se recorre tranquilo y a la vuelta ya no.
    * **`reiniciar()` la devuelve a su sitio.** Sin esto, morir dejaría el
      agua arriba y el reintento sería imposible — el fallo clásico de las
      mecánicas con estado que nadie prueba en la segunda vida.
    """

    rect: pygame.Rect
    damage: float = 0.25
    cooldown: float = 0.5
    timer: float = 0.5

    #: Píxeles por segundo que sube el borde superior. 0 = zona fija.
    sube: float = 0.0
    #: Coordenada `y` del mapa donde el agua se detiene. `None` = sin tope.
    sube_hasta: float | None = None
    #: Nombre del evento que la pone en marcha. Vacío = arranca ya.
    arranca_con: str = ""

    #: Si el motor pinta el aviso. AUD-228 — antes **no se pintaba ninguna zona
    #: fija**, sólo las que suben, y el contrato implícito era que el diseñador
    #: dibujara pinchos en las baldosas. Ese contrato no estaba escrito y no se
    #: cumplía: los dos únicos mapas del proyecto con `HazardZone` fija
    #: —`stage0`, que es el que copian los estudiantes, y `stage3_3_el_patio`—
    #: hacían daño desde un rectángulo invisible.
    #:
    #: Se pone a `false` en el TMX cuando el mapa **sí** trae su propio arte de
    #: peligro y el aviso del motor sobraría encima.
    #:
    #: AUD-241 — se llama `avisar` y no `visible` porque **`visible` es un nombre
    #: reservado en Tiled**: pytmx rechaza el mapa entero con «Reserved names and
    #: duplicate names are not allowed», así que la propiedad que AUD-228
    #: documentó no apagaba el aviso — impedía cargar el nivel. Es la misma
    #: piedra con la que ya tropezó `BloqueRitmico`, que por eso usa
    #: `visible_seg` en vez de `visible`.
    avisar: bool = True

    #: AUD-387 — el canal de daño de la zona. Cierra una promesa que
    #: `06_TMX_SPEC.md` llevaba rota desde AUD-310: la propiedad estaba
    #: documentada como «no está implementada», y no podía estarlo porque el
    #: motor no tenía canales — prometer un tipo cuando sólo sabes restar un
    #: número es prometer nada.
    #:
    #: Por defecto el físico, así que las zonas de los dieciséis mapas
    #: entregados hacen exactamente el mismo daño que antes. Con `veneno`, una
    #: charca deja de ser una zona de daño con otro nombre y la resistencia de
    #: cada enemigo empieza a significar algo.
    damage_type: str = "fisico"

    #: Estado interno. `_alto_inicial` guarda la altura original porque el
    #: `rect` es mutable y lo vamos a modificar en sitio.
    activa: bool = True
    _alto_inicial: int = 0
    _borde: float = 0.0

    def __post_init__(self) -> None:
        self._alto_inicial = self.rect.height
        self._borde = float(self.rect.top)
        if self.arranca_con:
            self.activa = False

    @property
    def sube_de_verdad(self) -> bool:
        return self.sube > 0.0

    def arrancar(self) -> None:
        self.activa = True

    def avanzar(self, dt: float) -> None:
        """Sube el borde superior. No hace nada si la zona es fija."""
        if not self.activa or self.sube <= 0.0 or dt <= 0.0:
            return
        tope = self.sube_hasta
        nuevo = self._borde - self.sube * dt
        if tope is not None and nuevo < tope:
            nuevo = float(tope)
        if nuevo == self._borde:
            return
        # El borde se lleva en float y el rect en int: acumular el redondeo
        # frame a frame haría que a 30 px/s y 60 fps el agua no subiera nunca.
        self._borde = nuevo
        fondo = self.rect.bottom
        self.rect.top = round(nuevo)
        self.rect.height = fondo - self.rect.top

    def reiniciar(self) -> None:
        """Devuelve el agua a su altura inicial. Se llama al reaparecer."""
        fondo = self.rect.bottom
        self.rect.height = self._alto_inicial
        self.rect.bottom = fondo
        self._borde = float(self.rect.top)
        self.activa = not self.arranca_con

@dataclass
class EscenaGuionizada:
    """Una cutscene declarada en el TMX. AUD-136 (D3).

    Hasta ahora una escena narrativa sólo se podía montar desde Python:
    importar tres clases, construir acciones y arrancarlas a mano. En un curso
    donde el estudiante trabaja en Tiled, eso significa que las escenas son
    cosa del profesor. Con esto son cosa de quien diseña el nivel.
    """

    #: Zona que la dispara al entrar el jugador. Vacía (un punto en Tiled) =
    #: se dispara al empezar el escenario.
    rect: pygame.Rect
    guion: str = ""
    bloquea: bool = True
    saltable: bool = True
    una_vez: bool = True
    #: Nombre de un evento del bus que la arranca, en vez de la posición.
    arranca_con: str = ""
    disparada: bool = False

    @property
    def al_empezar(self) -> bool:
        return self.rect.width <= 0 or self.rect.height <= 0

@dataclass
class DeathPit:
    rect: pygame.Rect

@dataclass
class CameraLock:
    rect: pygame.Rect
    lock_x: bool = False
    lock_y: bool = False

@dataclass
class LightSpec:
    """Un foco declarado en el TMX, en coordenadas del mapa.

    F1.1 — por qué esto es un dato y no un objeto de VFX
    ----------------------------------------------------
    El cargador no debe construir `LightSource`: eso ataría el módulo de
    escenarios al de efectos y obligaría a importar pygame-surface machinery
    para leer un mapa. Aquí sólo se describe *qué* pidió el diseñador; la
    escena decide cómo materializarlo.

    Antes de esto, las luces estaban **escritas a mano en el motor**, en una
    cadena `if zone == 0: ... elif zone == 1: ...` con coordenadas fijas. Un
    estudiante que construyera un escenario en Tiled no podía colocar ni una
    sola luz: heredaba las dos del zone 0, en (80, 80) y (240, 80), estuviera
    ahí su nivel o no.
    """

    position: tuple[float, float]
    radius: float = 80.0
    color: tuple[int, int, int] = (255, 220, 180)
    intensity: float = 0.8
    flicker: bool = False
    flicker_speed: float = 4.0
    flicker_amount: float = 0.15


@dataclass
class ZonaLuzAmbienteSpec:
    """Un rectángulo que impone brillo ambiental mientras el jugador esté
    dentro (GAP-072 punto 4, AUD-598).

    El blueprint del 4-1b pide un `ambient_light` que baja por tramos
    (0.50 → 0.25); la propiedad del mapa es una sola para todo el nivel.
    Ésta es la pieza que falta: igual que `LightSpec`, es sólo la
    descripción de lo que dibujó el diseñador en Tiled — la escena decide
    cómo aplicarla.

    `fundido` es el ancho en px de la banda de transición alrededor del
    rectángulo: dentro a fondo se aplica `valor`, y a medida que el jugador
    se acerca al borde desde fuera el valor interpola hacia el base del
    mapa para que la oscuridad no aparezca de golpe en una línea.
    """

    rect: pygame.Rect
    #: Brillo objetivo dentro de la zona, 0 a 1 (1.0 = sin cambio).
    valor: float = 1.0
    #: Ancho de la banda de fundido en el borde, en px.
    fundido: int = 64


@dataclass
class ZonaMusicaSpec:
    """Un rectángulo que manda sobre la música mientras el jugador esté
    dentro (GAP-072 punto 2, AUD-600).

    El mapa declara un único `bgm_track`; el blueprint del 4-1b pide
    cambiar de pista por tramo — y su herramienta es el SILENCIO: una zona
    con `track=""` deja el nivel sin música para que se oiga lo que pasa.

    `track` es el nombre de pista sin extensión (lo resuelve
    `resolver_pista_de_musica`: .ogg > .wav > .mp3). Al salir de toda
    zona, vuelve la base del mapa.
    """

    rect: pygame.Rect
    #: Nombre de pista, o cadena vacía = silencio deliberado.
    track: str = ""
    #: Fundido de entrada de la pista, en ms.
    fundido_ms: int = 800


@dataclass
class ZonaZoomSpec:
    """Un rectángulo que conduce el zoom de cámara mientras el jugador esté
    dentro (GAP-072 punto 3, AUD-601).

    Los momentos del blueprint (revelación del pez, cavidad final) piden un
    zoom corto: dentro del rectángulo la cámara tiende a `factor` en
    `segundos`; fuera, vuelve a 1.0 con la misma duración. El fotograma del
    mundo se compone a tamaño alterno y se reescala — la UI nunca escala.
    """

    rect: pygame.Rect
    #: Factor de zoom: >1 acerca (recorta y amplifica), <1 aleja.
    factor: float = 1.0
    #: Duración del tween hacia el factor, en segundos.
    segundos: float = 1.5

# ── P0: StageData partido por dominio ──────────────────────────

@dataclass
class StagePhysics:
    """Dominio físico: colisión, gravedad y profundidad 2.5D."""

    collision_rects: list[pygame.Rect] = field(default_factory=list)
    one_way_rects: list[pygame.Rect] = field(default_factory=list)
    #: AUD-395 — las mismas cajas, indexadas por clase de sólido (GAP-038).
    capas: MapaDeCapas = field(default_factory=MapaDeCapas)
    #: AUD-297 — el suelo inclinado del mapa.
    pendientes: list[Pendiente] = field(default_factory=list)
    gravity_multiplier: float = 1.0
    #: AUD-277 — 2.5D: escala de las entidades según su altura en el mapa.
    profundidad_min: float = 1.0
    profundidad_max: float = 1.0
    #: AUD-339 — 2.5D fase 6. Curva de la escala por profundidad
    profundidad_curva: float = 1.0
    #: AUD-339 — 2.5D fase 6. Orden por Y del pintor, opcional
    orden_por_y: bool = False
    #: AUD-278 — sombras proyectadas desde los focos.
    sombras_proyectadas: bool = False


@dataclass
class StageAtmosphere:
    """Dominio atmosférico: luz, clima, agua, partículas y fondo."""

    #: AUD-426 — cielo procedural
    cielo: bool = False
    background_layers: list[pygame.Surface] = field(default_factory=list)
    background_factors: list[float] = field(default_factory=list)
    lights: list[LightSpec] = field(default_factory=list)
    #: Zonas de brillo ambiental (GAP-072.4, AUD-598)
    zonas_luz_ambiente: list[ZonaLuzAmbienteSpec] = field(default_factory=list)
    #: Zonas de música por sección (GAP-072.2, AUD-600)
    zonas_musica: list[ZonaMusicaSpec] = field(default_factory=list)
    #: Zonas de zoom de cámara (GAP-072.3, AUD-601)
    zonas_zoom: list[ZonaZoomSpec] = field(default_factory=list)
    climate: str = ""
    #: Brillo ambiente del escenario, de 0 a 1. None = no declarado
    ambient_light: float | None = None
    #: Bloom permanente del escenario, 0 a 1. None = no declarado.
    bloom: float | None = None
    #: Viñeta del escenario, 0 a 0,6. None = no declarado.
    vignette: float | None = None
    #: Partículas de ambiente: tipo y partículas por segundo.
    ambient_fx: str = ""
    ambient_fx_rate: float | None = None
    #: Hora inicial del escenario, 0 a 24. None = no declarada (mediodía).
    start_hour: float | None = None
    #: Segundos reales que dura un ciclo completo. 0 congela el reloj
    day_length: float = 0.0
    #: Estación del escenario.
    season: str = ""
    #: AUD-111 — radio en píxeles de la niebla de guerra. 0 = apagada.
    fog_of_war: float = 0.0
    #: AUD-111 — capa de ondas de agua sobre la escena.
    water_effect: bool = False
    #: AUD-240 — los cinco mandos del agua, desde el mapa.
    water_speed: float = 1.5
    water_amplitude: int = 4
    water_frequency: float = 0.04
    water_alpha: int = 100
    water_tint: tuple[int, int, int] = (40, 80, 160)
    #: AUD-226 — fuerza de los rayos de luz volumétricos. 0 = apagados.
    god_rays: float = 0.0


@dataclass
class StageProgression:
    """Dominio de progresión: objetivos, entidades y metadatos del nivel."""

    #: AUD-400 — los objetivos que este mapa declara (GAP-047).
    objetivos: list[Objetivo] = field(default_factory=list)
    entity_list: list[BaseEntity] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)  # type: ignore[name-defined]
    spawn_point: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    next_trigger: pygame.Rect | None = None
    message_triggers: list[MessageTrigger] = field(default_factory=list)
    hazard_zones: list[HazardZone] = field(default_factory=list)
    death_pits: list[DeathPit] = field(default_factory=list)
    #: AUD-136 — escenas narrativas declaradas en el TMX.
    escenas: list[EscenaGuionizada] = field(default_factory=list)
    #: AUD-140 — bloques que se empujan y bloques que se rompen.
    empujables: list[BloqueEmpujable] = field(default_factory=list)
    destructibles: list[BloqueDestructible] = field(default_factory=list)
    camera_locks: list[CameraLock] = field(default_factory=list)
    #: AUD-605 — arenas de jefe declaradas con `ArenaZone`.
    zonas_arena: list[pygame.Rect] = field(default_factory=list)
    #: F4.1 — objetos con los que el jugador interactúa.
    recogibles: list[Recogible] = field(default_factory=list)
    cerraduras: list[Cerradura] = field(default_factory=list)
    cofres: list[Cofre] = field(default_factory=list)
    disparadores: list[Disparador] = field(default_factory=list)
    #: AUD-287 — zonas de warp declaradas con `WarpZone`.
    warps: list[ZonaDeWarp] = field(default_factory=list)
    #: AUD-625 — salidas secretas (`SecretExit`) que revelan nodos en el mapa.
    secret_exits: list[SecretExit] = field(default_factory=list)
    #: AUD-625 — salas secretas (`SecretRoom`) con tell visual.
    secret_rooms: list[SecretRoom] = field(default_factory=list)
    #: B4 — fogatas reutilizables (bonfire) — Dark Souls/Hollow Knight
    fogatas: list[Fogata] = field(default_factory=list)  # type: ignore[name-defined]
    #: B4.3 — estaciones de recarga (recharge) — restaura estamina/mana
    estaciones_recarga: list[EstacionDeRecarga] = field(default_factory=list)  # type: ignore[name-defined]
    #: Placas de presión (PressurePlate)
    placas: list[PlacaDePresion] = field(default_factory=list)  # type: ignore[name-defined]
    #: AUD-249 — scroll forzado declarado desde Tiled con `ScrollZone`.
    scroll_forzados: list[ScrollForzado] = field(default_factory=list)  # type: ignore[name-defined]
    #: Indoor/outdoor — zonas donde el clima y día/noche se atenúan (techo)
    indoor_zones: list[pygame.Rect] = field(default_factory=list)
    #: F5.3–F5.6 — componentes ECS declarados desde el TMX.
    componentes: list[list[object]] = field(default_factory=list)
    zone: int = 0
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""
    #: Punto de vista del escenario: `"lateral"` o `"cenital"` (AUD-129).
    vista: str = "lateral"
    #: AUD-137 (F6) — el compás del escenario.
    bpm: float = 0.0
    #: Pulsos por compás. 4 es lo normal; 3 da un vals, 7 da un compás raro.
    compas: int = 4
    #: Segundos de latencia que compensar. Se calibra por máquina.
    desfase_audio: float = 0.0
    #: AUD-143 — modo de cámara: `seguir`, `zona_muerta` o `sala`.
    camara: str = "seguir"
    #: AUD-141 — máximo del medidor de estamina. `0` = apagado
    estamina: float = 0.0
    #: AUD-260 — segundos de reserva de tiempo bala. `0` = apagado
    tiempo_bala: float = 0.0
    #: AUD-294 — este mapa regala las mecánicas de jefe.
    habilidades_libres: bool = False


class StageData:
    """Fachada que expone los tres dominios como un único objeto.

    Mantiene compatibilidad: `stage.collision_rects` sigue funcionando porque
    `__getattr__` delega a `physics`, `atmosphere` o `progression`. El cargador
    puede seguir haciendo `StageData(map_layer=..., collision_rects=..., ...)`
    con kwargs planos y se reparten solos. Los accesos nuevos pueden usar
    `stage.physics` / `stage.atmosphere` / `stage.progression` directamente.
    """

    def __init__(
        self,
        map_layer: pyscroll.PyscrollGroup,
        map_pixel_size: tuple[int, int] = (0, 0),
        physics: StagePhysics | None = None,
        atmosphere: StageAtmosphere | None = None,
        progression: StageProgression | None = None,
        **kwargs: Any,
    ) -> None:
        object.__setattr__(self, "map_layer", map_layer)
        object.__setattr__(self, "map_pixel_size", map_pixel_size)
        object.__setattr__(self, "physics", physics if physics is not None else StagePhysics())
        object.__setattr__(self, "atmosphere", atmosphere if atmosphere is not None else StageAtmosphere())
        object.__setattr__(self, "progression", progression if progression is not None else StageProgression())
        # Reparte kwargs planos a su dominio para compat con StageLoader
        for k, v in kwargs.items():
            if hasattr(self.physics, k):
                setattr(self.physics, k, v)
            elif hasattr(self.atmosphere, k):
                setattr(self.atmosphere, k, v)
            elif hasattr(self.progression, k):
                setattr(self.progression, k, v)
            else:
                # Campo desconocido: lo guarda en la fachada para no perderlo
                object.__setattr__(self, k, v)

    def __getattr__(self, name: str) -> Any:
        # Sólo se llama si el atributo no se encontró por vía normal
        for sub in (object.__getattribute__(self, "physics"),
                    object.__getattribute__(self, "atmosphere"),
                    object.__getattribute__(self, "progression")):
            if hasattr(sub, name):
                return getattr(sub, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"map_layer", "map_pixel_size", "physics", "atmosphere", "progression"}:
            object.__setattr__(self, name, value)
            return
        # Si ya existe en algún sub-objeto, delega la escritura
        for sub_name in ("physics", "atmosphere", "progression"):
            try:
                sub = object.__getattribute__(self, sub_name)
            except AttributeError:
                continue
            if hasattr(sub, name):
                setattr(sub, name, value)
                return
        # Si no, crea en la fachada
        object.__setattr__(self, name, value)

    # ── B3 — Item Completion ───────────────────────────────────────
    def item_keys(self) -> list[str]:
        """Lista estable de ITEM keys declarados en este mapa (para persistencia).

        Usa StageData.stage_id como MAP_ID. Cada key es MAP_ID:TMX_ID:ITEM_ID.
        Sólo incluye Pickup/Key, Chest con contenido y SecretRoom con recompensa
        cuyo tmx_object_id != 0 (excluye dinámicos y vacíos).
        """
        from src.framework.stage.interactables import (
            cofre_key,
            es_item_coleccionable_cofre,
            es_item_coleccionable_recogible,
            es_item_coleccionable_secret_room,
            recogible_key,
            secret_room_key,
        )

        m = str(getattr(self, "stage_id", "") or "")
        keys: list[str] = []
        for r in getattr(self, "recogibles", []) or []:
            if es_item_coleccionable_recogible(r):
                keys.append(recogible_key(m, r))
        for c in getattr(self, "cofres", []) or []:
            if es_item_coleccionable_cofre(c):
                keys.append(cofre_key(m, c))
        for s in getattr(self, "secret_rooms", []) or []:
            if es_item_coleccionable_secret_room(s):
                keys.append(secret_room_key(m, s))
        return keys

    def item_total(self) -> int:
        """TOTAL determinístico del mapa (cacheable)."""
        return len(self.item_keys())

    def item_collected_count(self, collected_set: set[str] | None) -> int:
        """Cuántos ITEMS de este mapa están en el set persistido."""
        if not collected_set:
            return 0
        # Intersección con las keys de este mapa (aisla por map_id)
        keys = set(self.item_keys())
        return len(keys & set(collected_set))

    def item_percentage(self, collected_set: set[str] | None) -> float | None:
        """Porcentaje 0.0-1.0 o None si TOTAL==0. Clamp."""
        total = self.item_total()
        if total == 0:
            return None
        collected = self.item_collected_count(collected_set)
        # clamp COLLECTED> TOTAL
        if collected > total:
            collected = total
        return max(0.0, min(1.0, collected / total))

    def __dir__(self) -> list[str]:
        base = set(super().__dir__())
        for sub in (self.physics, self.atmosphere, self.progression):
            base.update(dir(sub))
        return sorted(base)

REQUIRED_LAYERS: tuple[str, ...] = (
    "BG_Far", "BG_Mid", "BG_Near", "Terrain",
    "Terrain_Detail", "Objects", "Collision", "FG_Overlay",
)

_NUMERIC_PROPS: tuple[str, ...] = (
    "max_health", "damage_on_contact", "patrol_length",
    "fire_rate", "projectile_speed", "projectile_damage",
    "sine_amplitude", "sine_frequency", "flight_speed",
    "patrol_speed", "alert_speed", "contact_knockback",
    "detection_range_x", "detection_range_y", "charge_speed",
)

#: Propiedades de enemigo que son booleanas (AUD-305).
#:
#: Hacen falta declaradas porque un estudiante que escriba `admite_bash` en
#: Tiled **sin marcar el tipo `bool`** entrega la cadena `"false"`, y una cadena
#: no vacía es cierta en Python. Sin esta lista, escribir «false» encendía la
#: propiedad — el peor fallo posible, porque parece que la opción no funciona
#: cuando lo que pasa es que no se puede apagar.

_BOOL_PROPS: tuple[str, ...] = ("admite_bash",)
