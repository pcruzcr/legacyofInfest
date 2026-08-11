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
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import TYPE_CHECKING

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
    Recogible,
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

VISTAS_VALIDAS: frozenset[str] = frozenset({"lateral", "cenital"})

#: AUD-143 — modos de cámara que el motor sabe encuadrar.
#:
#: `seguir` persigue con suavizado; `zona_muerta` no se mueve mientras el
#: jugador esté en el centro de la pantalla —lo que impide que saltar en el
#: sitio mueva el mundo entero—; `sala` salta de pantalla en pantalla, que es
#: el encuadre de Zelda, Metroid y los Castlevania clásicos.

MODOS_DE_CAMARA: frozenset[str] = frozenset({"seguir", "zona_muerta", "sala"})

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
    "Guard", "Stalker", "Vine", "Zipline", "Spring",
})

if TYPE_CHECKING:
    from src.framework.stage.checkpoint import Checkpoint
    from src.framework.stage.level_mechanics import ScrollForzado

@dataclass
class MessageTrigger:
    rect: pygame.Rect
    text: str
    triggered: bool = False
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
class StageData:
    map_layer: pyscroll.PyscrollGroup
    map_pixel_size: tuple[int, int] = (0, 0)
    collision_rects: list[pygame.Rect] = field(default_factory=list)
    one_way_rects: list[pygame.Rect] = field(default_factory=list)
    #: AUD-395 — las mismas cajas, indexadas por clase de sólido (GAP-038).
    #:
    #: Se publica **aparte** y no sustituyendo a las dos listas de arriba por
    #: el mismo motivo que `velocidades_parallax` unas líneas más abajo: esas
    #: dos las leen las veintiséis entregas, el arco del jefe, la cámara y el
    #: calificador de escenarios. Cambiarles el tipo para ganar capas habría
    #: sido pagar la característica con todo el contenido del curso.
    #:
    #: Las dos vistas dicen lo mismo; la que manda al construirlas es ésta, y
    #: `StageLoader._load_collision` las llena a la vez.
    capas: MapaDeCapas = field(default_factory=MapaDeCapas)
    #: AUD-400 — los objetivos que este mapa declara (GAP-047). Vacía en los
    #: diecisiete mapas anteriores, y un escenario sin objetivos no tiene nada
    #: pendiente: por eso añadirlos no cambia ninguno.
    objetivos: list[Objetivo] = field(default_factory=list)
    entity_list: list[BaseEntity] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    spawn_point: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    next_trigger: pygame.Rect | None = None
    background_layers: list[pygame.Surface] = field(default_factory=list)
    #: AUD-272 — velocidad de parallax de cada capa de `background_layers`, en
    #: el mismo orden. Se publica aparte en vez de cambiar el tipo de la lista
    #: porque `background_layers` lo leen las entregas.
    #:
    #: Vacía significa «usa la tabla por índice de siempre», que es lo que hace
    #: un `StageData` construido a mano.
    background_factors: list[float] = field(default_factory=list)
    message_triggers: list[MessageTrigger] = field(default_factory=list)
    hazard_zones: list[HazardZone] = field(default_factory=list)
    death_pits: list[DeathPit] = field(default_factory=list)
    #: AUD-136 — escenas narrativas declaradas en el TMX.
    escenas: list[EscenaGuionizada] = field(default_factory=list)
    #: AUD-140 — bloques que se empujan y bloques que se rompen.
    empujables: list[BloqueEmpujable] = field(default_factory=list)
    destructibles: list[BloqueDestructible] = field(default_factory=list)
    camera_locks: list[CameraLock] = field(default_factory=list)
    lights: list[LightSpec] = field(default_factory=list)
    #: F4.1 — objetos con los que el jugador interactúa.
    recogibles: list[Recogible] = field(default_factory=list)
    cerraduras: list[Cerradura] = field(default_factory=list)
    cofres: list[Cofre] = field(default_factory=list)
    disparadores: list[Disparador] = field(default_factory=list)
    #: AUD-287 — zonas de warp declaradas con `WarpZone`.
    #:
    #: Lista aparte y no un componente ECS por lo mismo que `scroll_forzados`:
    #: lo que mueven no es una entidad del mundo, es **el jugador**, y quien lo
    #: posee es la escena.
    warps: list[ZonaDeWarp] = field(default_factory=list)
    #: AUD-297 — el suelo inclinado del mapa.
    #:
    #: Lista aparte de `collision_rects` **a propósito**: si una pendiente
    #: entrara ahí, el eje X la trataría como pared y el jugador se pararía en
    #: seco al pie de la rampa.
    pendientes: list[Pendiente] = field(default_factory=list)
    #: AUD-294 — este mapa regala las mecánicas de jefe.
    #:
    #: Para un escenario nuevo que quiera jugarse suelto, sin la campaña
    #: detrás. Los mapas entregados **no** la necesitan: van por la lista de
    #: `settings`, para no tener que tocar sus ficheros.
    habilidades_libres: bool = False
    #: AUD-249 — scroll forzado declarado desde Tiled con `ScrollZone`.
    #:
    #: No es un componente ECS: `ScrollForzado` mueve la **cámara**, no una
    #: entidad, y los sistemas del ECS trabajan sobre entidades. Va aquí, junto
    #: al resto de lo que el mapa declara y la escena consume.
    scroll_forzados: list[ScrollForzado] = field(default_factory=list)
    #: F5.3–F5.6 — componentes ECS declarados desde el TMX.
    #:
    #: Se guardan como una lista de componentes sueltos y no como una lista por
    #: tipo. Con doce mecánicas nuevas, doce campos más aquí harían de
    #: `StageData` un catálogo que hay que ampliar cada vez, y la escena tendría
    #: que enterarse de cada uno. Así, la escena los vuelca al mundo ECS de una
    #: pasada y los sistemas encuentran lo suyo por el tipo del componente, que
    #: es justo lo que ECS resuelve bien.
    componentes: list[list[object]] = field(default_factory=list)
    zone: int = 0
    stage_id: str = ""
    stage_name: str = ""
    time_limit: int = 0
    bgm_track: str = ""
    gravity_multiplier: float = 1.0
    #: Punto de vista del escenario: `"lateral"` o `"cenital"` (AUD-129).
    #:
    #: Cenital es la vista desde arriba de Zelda, Hotline Miami o la sala de
    #: cámaras de César Ubáu: sin gravedad, movimiento libre en dos ejes y sin
    #: plataformas de un solo sentido —desde arriba, una repisa atravesable es
    #: un muro invisible—.
    #:
    #: Se declara por escenario y no por zona: el mismo mundo puede tener un
    #: sótano cenital y un exterior lateral, que es justo lo que hace que
    #: valga la pena tener las dos vistas.
    vista: str = "lateral"
    #: AUD-137 (F6) — el compás del escenario.
    #:
    #: `bpm = 0` significa «este escenario no es rítmico», que es el caso de
    #: casi todos, y entonces el reloj musical ni se construye. Un motor que
    #: obligara a declarar un tempo para hacer un nivel normal estaría
    #: cobrando a todo el mundo el precio de una función que usan pocos.
    bpm: float = 0.0
    #: Pulsos por compás. 4 es lo normal; 3 da un vals, 7 da un compás raro.
    compas: int = 4
    #: Segundos de latencia que compensar. Se calibra por máquina.
    desfase_audio: float = 0.0
    #: AUD-143 — modo de cámara: `seguir`, `zona_muerta` o `sala`.
    camara: str = "seguir"
    #: AUD-141 — máximo del medidor de estamina. **`0` = apagado**, que es el
    #: caso de los quince escenarios entregados: encenderla para todos
    #: cambiaría cómo se juegan sin que sus autores lo pidan.
    estamina: float = 0.0
    #: AUD-260 — segundos de reserva de tiempo bala. **`0` = apagado**, por la
    #: misma razón que la estamina: los dieciséis escenarios entregados están
    #: calificados y encenderles una mecánica nueva cambiaría el juego que sus
    #: autores diseñaron.
    tiempo_bala: float = 0.0
    #: AUD-277 — 2.5D: escala de las entidades según su altura en el mapa.
    #: `min` es la de lo más lejano (arriba) y `max` la de lo más cercano
    #: (abajo). **Iguales = apagado**, que es el valor por defecto y el de los
    #: dieciséis mapas entregados.
    profundidad_min: float = 1.0
    profundidad_max: float = 1.0
    #: AUD-339 — 2.5D fase 6. Curva de la escala por profundidad: 1.0 es la
    #: interpolación lineal de AUD-277; con más de 1.0 las filas del fondo se
    #: encogen más rápido, como en una perspectiva de verdad.
    profundidad_curva: float = 1.0
    #: AUD-339 — 2.5D fase 6. Orden por Y del pintor, **opcional**: con
    #: `False` (por defecto) se mantiene el orden por `rect.centery` de
    #: AUD-067; con `True` las entidades se ordenan por su **ancla de
    #: profundidad** —`depth_y` si la entidad lo declara, si no sus pies
    #: (`rect.bottom`)—, el mismo ancla que usa la escala: lo que se escala
    #: igual se ordena igual.
    orden_por_y: bool = False
    #: AUD-278 — sombras proyectadas desde los focos. **Apagadas por defecto**:
    #: cuestan una proyección por foco y por obstáculo, y el reporte 87 §11 las
    #: dejó anotadas como «viable, con coste».
    sombras_proyectadas: bool = False
    climate: str = ""
    #: Brillo ambiente del escenario, de 0 (oscuridad total) a 1 (sin
    #: oscurecer). `None` significa "no declarado": la escena caerá a su tabla
    #: por zona. Se distingue de 1.0 a propósito, porque 1.0 es una decisión
    #: explícita de diseño —"este nivel es a plena luz"— y `None` es la
    #: ausencia de decisión.
    ambient_light: float | None = None
    #: Bloom permanente del escenario, 0 a 1. `None` = no declarado.
    bloom: float | None = None
    #: Viñeta del escenario, 0 a 0,6. `None` = no declarado.
    vignette: float | None = None
    #: Partículas de ambiente: tipo y partículas por segundo. Cadena vacía =
    #: no declarado; la escena caerá a su tabla por zona.
    ambient_fx: str = ""
    ambient_fx_rate: float | None = None
    #: Hora inicial del escenario, 0 a 24. `None` = no declarada (mediodía).
    start_hour: float | None = None
    #: Segundos reales que dura un ciclo completo. 0 congela el reloj, que es
    #: el comportamiento de un escenario sin ciclo día/noche.
    day_length: float = 0.0
    #: Estación del escenario. Cadena vacía = no declarada; la escena usará la
    #: de por defecto. Las estaciones no avanzan solas: un escenario dura
    #: minutos y cambiar de invierno a primavera a mitad sería ruido.
    season: str = ""
    #: AUD-111 — radio en píxeles de la niebla de guerra. 0 = apagada.
    fog_of_war: float = 0.0
    #: AUD-111 — capa de ondas de agua sobre la escena.
    water_effect: bool = False
    #: AUD-240 — los cinco mandos del agua, desde el mapa.
    #:
    #: `docs/47` los documenta desde el principio y decía «all adjustable via
    #: `set_params()`». Nadie llamaba a `set_params`: `StageScene` construía un
    #: `WaterEffect()` con los valores por defecto, así que **toda el agua del
    #: juego era idéntica** y los cinco mandos eran inalcanzables desde el
    #: contenido. Los valores de aquí son exactamente los que `WaterEffect` usa
    #: por defecto, para que un mapa que no diga nada se vea igual que antes.
    water_speed: float = 1.5
    water_amplitude: int = 4
    water_frequency: float = 0.04
    water_alpha: int = 100
    water_tint: tuple[int, int, int] = (40, 80, 160)
    #: AUD-226 — fuerza de los rayos de luz volumétricos. 0 = apagados.
    #: Sólo hacen algo con el camino GL: son una pasada de sombreador y no
    #: tienen equivalente por CPU, así que un escenario que los pida se ve
    #: igual que siempre en una máquina sin ModernGL. El foco no se declara
    #: aquí —lo elige la escena, que es quien sabe qué luz hay en pantalla.
    god_rays: float = 0.0

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
