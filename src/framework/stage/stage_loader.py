"""
Module: stage_loader
System: framework.stage
Academic Unit: Unit II (Collision Detection), Unit IV (Game Architecture)
Description: Parses TMX map files using pytmx and pyscroll to assemble
a complete stage environment: tile layers, entity spawn points, collision
zones, checkpoints, and the next-trigger portal.
"""
from __future__ import annotations

import logging
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame
import pyscroll
import pyscroll.data
from pytmx.util_pygame import load_pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework import FrameworkUsageError
from src.framework.entities.base_entity import BaseEntity
from src.framework.stage.bloques import BloqueDestructible, BloqueEmpujable
from src.framework.stage.interactables import (
    Cerradura,
    Cofre,
    Disparador,
    Recogible,
    ZonaDeWarp,
)
from src.framework.stage.pendientes import Pendiente
from src.framework.stage.tmx_diagnostics import (
    TmxObjectProblem,
    TmxReport,
    known_object_types,
    suggest_types,
)

logger = logging.getLogger(__name__)

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


class StageLoader:
    _entity_registry: dict[str, type[BaseEntity]] = {}
    #: Todo lo que se registró alguna vez (AUD-144).
    #:
    #: Varias pruebas hacen `StageLoader._entity_registry.clear()` para
    #: empezar de cero. Eso vacía también los tipos que registran los
    #: escenarios a nivel de módulo —`LaSodaWalkerRaton`, `BossGavilan`…— y,
    #: como el módulo ya está importado, sus efectos de importación no se
    #: repiten. Este registro histórico no se vacía nunca: el cargador lo
    #: usa para devolver al registro lo que falte antes de procesar el mapa.
    _registro_historico: dict[str, type[BaseEntity]] = {}
    #: Escenarios cuyo paquete ya se intentó importar (AUD-106).
    _escenarios_ya_importados: set[str] = set()
    # (resolved path, mtime_ns, size) -> parsed pytmx map. See _parse_tmx.
    _tmx_cache: dict[tuple[str, int, int], Any] = {}

    @classmethod
    def _registrar_tipos_del_escenario(cls, tmx_path: Path) -> bool:
        """Importa el paquete del escenario para que registre sus entidades.

        Devuelve `True` si importó algo nuevo. Convención:
        ``assets/maps/<nombre>/<nombre>.tmx`` ↔ ``src/stages/<nombre>/``.

        Se importa el paquete entero porque el framework no dice desde qué
        fichero hay que registrar: sobre las entregas reales, unos lo hacen en
        el módulo principal, otros en un módulo de entidades aparte, y otros
        dentro de la escena. Sólo se hace **una vez por escenario** y sólo
        cuando ya ha habido un tipo desconocido, así que no cuesta nada en el
        camino normal.

        AUD-144: antes de importar se restauran del registro histórico los
        tipos que alguien vació. Un módulo re-importado no repetiría sus
        efectos, así que esta copia es lo único que puede devolverlos.
        """
        import importlib
        import pkgutil

        faltan = {
            k: v for k, v in cls._registro_historico.items()
            if k not in cls._entity_registry
        }
        if faltan:
            cls._entity_registry.update(faltan)
            return True

        nombre = tmx_path.parent.name
        if nombre in cls._escenarios_ya_importados:
            return False
        cls._escenarios_ya_importados.add(nombre)

        antes = len(cls._entity_registry)
        raiz = f"src.stages.{nombre}"
        try:
            paquete = importlib.import_module(raiz)
        except ImportError:
            return False
        except Exception:
            logger.warning("stage_loader: '%s' no se pudo importar", raiz, exc_info=True)
            return False

        for info in pkgutil.walk_packages(getattr(paquete, "__path__", []), f"{raiz}."):
            if any(p in info.name for p in (".tools", ".tests", ".herramientas")):
                continue
            try:
                importlib.import_module(info.name)
            except Exception:
                logger.debug("stage_loader: '%s' no se pudo importar", info.name, exc_info=True)

        return len(cls._entity_registry) > antes

    @classmethod
    def register_entity(cls, type_name: str, entity_class: type[BaseEntity]) -> None:
        cls._entity_registry[type_name] = entity_class
        cls._registro_historico[type_name] = entity_class

    @classmethod
    def _parse_tmx(cls, tmx_path: Path) -> Any:
        """Parse a TMX file, reusing a previous parse when the file is unchanged.

        AUD-027: ``StageScene.respawn()`` calls ``on_enter()``, which called
        ``load()``, which re-parsed the entire TMX and re-decoded every tileset
        image on **every player death** — a guaranteed hitch at the worst
        possible moment for game feel.

        ``tmx_data`` is read-only map geometry; entities are constructed fresh
        from it on each load, so the parse result is safe to share. The cache is
        keyed on the file's modification time and size, so editing a map in
        Tiled and re-running still picks up the change — important, since this
        engine is used by students iterating on level design.
        """
        resolved = tmx_path.resolve()
        try:
            stat = resolved.stat()
            key = (str(resolved), stat.st_mtime_ns, stat.st_size)
        except OSError:
            key = (str(resolved), 0, 0)

        cached = cls._tmx_cache.get(key)
        if cached is not None:
            return cached

        cls._rechazar_mapa_hostil(resolved)
        tmx_data = load_pygame(str(resolved))
        # Only ever keep one parse in flight; stages are large and holding
        # several maps' tilesets resident is not worth the memory.
        cls._tmx_cache.clear()
        cls._tmx_cache[key] = tmx_data
        return tmx_data

    #: `source="..."` aparece en `<tileset>`, `<image>` y `<objecttemplate>`.
    #: Es la lista de rutas que pytmx abrirá por su cuenta.
    _FUENTE_TMX = re.compile(rb'source="([^"]*)"')

    @classmethod
    def _rechazar_mapa_hostil(cls, tmx_path: Path) -> None:
        """AUD-317 — dos cosas que pytmx hace sin preguntar y que un TMX
        hostil puede explotar:

        * **Expansión de entidades XML** (*billion laughs*): el parser de
          pytmx expande `<!ENTITY>` sin límite; un mapa de 400 bytes puede
          pedir gigabytes de RAM. Tiled jamás exporta entidades propias, así
          que cualquier `<!ENTITY>` es un ataque y se corta antes de parsear.
        * **Travesía de rutas**: las `source="..."` se resuelven contra el
          directorio del mapa y pytmx abre el resultado sin preguntar. Para
          los mapas dentro del árbol del juego, ninguna source puede resolver
          fuera de él (los mapas reales usan `../../../assets/...`, que
          vuelve a entrar en el árbol). Los mapas fuera del árbol —pruebas,
          herramientas— no se juzgan: no hay raíz que usar como contención.

        Falla duro y pronto: un mapa envenenado no debe llegar a abrir ficheros.
        """
        try:
            crudo = tmx_path.read_bytes()
        except OSError:
            # El fichero no se puede leer: pytmx ya dirá su error. No cambia
            # el comportamiento, sólo no mete una lectura extra en el camino.
            return

        if b"<!ENTITY" in crudo.upper():
            raise ValueError(
                f"mapa hostil: {tmx_path.name} declara entidades XML "
                "(<!ENTITY>); el parser las expande sin límite. Se rechaza "
                "antes de parsear para que no haya expansión que acotar."
            )

        if cls._bajo(tmx_path, settings.PROJECT_ROOT):
            cls._rechazar_travesia_en(tmx_path, crudo)

    @classmethod
    def _rechazar_travesia_en(cls, tmx_path: Path, crudo: bytes) -> None:
        """Recorre las `source="..."` del TMX y de sus TSX comprobando que
        ninguna resuelva fuera de `PROJECT_ROOT`."""
        pendientes: list[tuple[Path, bytes]] = [(tmx_path, crudo)]
        vistos: set[Path] = set()
        while pendientes:
            archivo, texto = pendientes.pop()
            vistos.add(archivo)
            for m in cls._FUENTE_TMX.finditer(texto):
                referencia = m.group(1).decode("utf-8", "replace")
                if not referencia:
                    continue
                destino = (archivo.parent / referencia).resolve()
                if not cls._bajo(destino, settings.PROJECT_ROOT):
                    raise ValueError(
                        f"mapa hostil: {tmx_path.name} referencia {referencia!r}, "
                        f"que resuelve fuera del árbol del juego ({destino}). "
                        "Los mapas y sus tilesets viven dentro del proyecto."
                    )
                if destino.suffix.lower() == ".tsx" and destino not in vistos:
                    try:
                        pendientes.append((destino, destino.read_bytes()))
                    except OSError:
                        pass  # pytmx dirá que falta; aquí no hay travesía que juzgar

    @staticmethod
    def _bajo(ruta: Path, raiz: Path) -> bool:
        try:
            ruta.relative_to(raiz)
            return True
        except ValueError:
            return False

    @classmethod
    def clear_tmx_cache(cls) -> None:
        """Drop the parsed-TMX cache (test teardown, or on low memory)."""
        cls._tmx_cache.clear()

    @classmethod
    def _ensure_entities_registered(cls) -> None:
        """Registra el bestiario si nadie lo ha hecho todavía (AUD-056).

        Hasta ahora el único sitio que llamaba a `ensure_registered()` era
        `App.__init__`, así que `StageLoader.load()` sólo reconocía las
        entidades si alguien había construido la aplicación antes. Cargar un
        mapa desde un script, una prueba o una herramienta producía un escenario
        al que **le faltaban enemigos, sin decirlo**: `tests/test_stage0_smoke.py`
        cargaba stage0 con 5 de sus enemigos descartados en silencio
        —Charger, Archer, Brute, Caster y Assassin— y a continuación afirmaba
        que el escenario tenía enemigos. Pasaba, porque Walker y Flying sí
        sobrevivían.

        Una dependencia de orden que no se puede ver desde el sitio donde se
        incumple es una trampa, y en un framework que usan estudiantes es una
        trampa que van a pisar. La importación es local porque `entity_factory`
        importa este módulo; la llamada es idempotente y cuesta un `if`.
        """
        from src.framework.entities.entity_factory import ensure_registered

        ensure_registered()

    @classmethod
    def load(cls, tmx_path: Path) -> StageData:
        tmx_path = Path(tmx_path)
        if not tmx_path.exists():
            raise FrameworkUsageError(f"TMX file not found: {tmx_path}")

        cls._ensure_entities_registered()

        tmx_data = cls._parse_tmx(tmx_path)
        cls._validate_layers(tmx_data)
        stage = cls._build_stage_data(tmx_data)

        cls._load_backgrounds(stage, tmx_data.properties.get("background_zone", ""))
        waypoints_by_owner = cls._build_waypoints(tmx_data)
        report = TmxReport(tmx_path=str(tmx_path))
        spawn_found = cls._process_objects(tmx_data, stage, waypoints_by_owner, report)

        # AUD-055: los objetos no interpretables se informan **antes** que la
        # falta de PlayerSpawn, porque lo más habitual es que sean la causa: un
        # «PlayerSpwan» mal escrito produce las dos cosas a la vez, y decir
        # «falta el PlayerSpawn» cuando está ahí, mal escrito, manda a buscar
        # en la dirección contraria.
        if not report.ok:
            # AUD-106: antes de rendirse, dar al escenario la oportunidad de
            # registrar sus propios tipos.
            #
            # El curso pide que quien inventa un enemigo o un jefe lo registre
            # desde su paquete. Al jugar funciona, porque la escena importa su
            # módulo antes de cargar el mapa. Pero cargar el TMX **suelto** —el
            # validador, el previsualizador, el calificador, esta suite— fallaba
            # con «type='BossPaburu' no existe», y entonces la herramienta del
            # profesor contradecía al juego.
            #
            # Importar el paquete aquí hace que las cuatro rutas coincidan, que
            # es lo único que hace fiable a un validador.
            if cls._registrar_tipos_del_escenario(tmx_path):
                # Se rehace la pasada desde cero: la primera dejó a medias las
                # listas del escenario, y duplicar entidades sería peor que el
                # fallo que se está intentando arreglar.
                report = TmxReport(tmx_path=str(tmx_path))
                stage.entity_list.clear()
                stage.checkpoints.clear()
                stage.message_triggers.clear()
                stage.hazard_zones.clear()
                stage.death_pits.clear()
                stage.scroll_forzados.clear()
                stage.escenas.clear()
                stage.empujables.clear()
                stage.destructibles.clear()
                stage.camera_locks.clear()
                stage.lights.clear()
                stage.recogibles.clear()
                stage.cerraduras.clear()
                stage.cofres.clear()
                stage.disparadores.clear()
                stage.componentes.clear()
                stage.next_trigger = None
                waypoints_by_owner.clear()
                spawn_found = cls._process_objects(
                    tmx_data, stage, waypoints_by_owner, report,
                )

        if not report.ok:
            raise FrameworkUsageError(
                report.format(known_object_types(list(cls._entity_registry))),
            )

        if not spawn_found:
            raise FrameworkUsageError(
                f"No hay ningún objeto de tipo «PlayerSpawn» en {tmx_path}.\n"
                f"Añade un objeto de tipo punto en la capa «Objects» con "
                f"type=PlayerSpawn: es donde aparece el jugador al empezar y "
                f"al reaparecer.",
            )

        cls._load_collision(tmx_data, stage)
        return stage

    # ── Internal helpers ──────────────────────────────────────────

    @classmethod
    def _validate_layers(cls, tmx_data: Any) -> None:
        tmx_layer_names = {layer.name for layer in tmx_data.visible_layers}
        tmx_layer_names.update({layer.name for layer in tmx_data.layers})
        for name in REQUIRED_LAYERS:
            if name not in tmx_layer_names:
                raise FrameworkUsageError(f"Missing required layer: {name}")

    @classmethod
    def _build_stage_data(cls, tmx_data: Any) -> StageData:
        props = tmx_data.properties
        stage_id = props.get("stage_id", "")
        stage_name = props.get("stage_name", "")
        time_limit = cls._safe_int(props.get("time_limit", 0), "time_limit")
        bgm_track = props.get("bgm_track", "")
        gravity_multiplier = cls._safe_float(props.get("gravity_multiplier", 1.0), "gravity_multiplier")
        # AUD-137 — el compás. Sin `bpm` no hay reloj musical y el escenario se
        # comporta como siempre.
        bpm = max(0.0, cls._safe_float(props.get("bpm", 0.0), "bpm"))
        compas = max(1, cls._safe_int(props.get("compas", 4), "compas"))
        desfase_audio = cls._safe_float(
            props.get("desfase_audio", 0.0), "desfase_audio")
        estamina = max(0.0, cls._safe_float(props.get("estamina", 0.0), "estamina"))
        tiempo_bala = max(
            0.0, cls._safe_float(props.get("tiempo_bala", 0.0), "tiempo_bala"))
        profundidad_min = max(0.05, cls._safe_float(
            props.get("profundidad_min", 1.0), "profundidad_min"))
        profundidad_max = max(0.05, cls._safe_float(
            props.get("profundidad_max", 1.0), "profundidad_max"))
        # AUD-339 — la curva comparte el suelo de 0.05 con los extremos: una
        # curva negativa invertiría el degradado y una de 0.0 lo congelaría.
        profundidad_curva = max(0.05, cls._safe_float(
            props.get("profundidad_curva", 1.0), "profundidad_curva"))
        orden_por_y = cls._bool_de(
            props.get("orden_por_y"), por_defecto=False)
        sombras_proyectadas = cls._bool_de(
            props.get("sombras_proyectadas"), por_defecto=False)
        habilidades_libres = cls._bool_de(
            props.get("habilidades_libres"), por_defecto=False)
        camara = str(props.get("camara") or props.get("camera") or "seguir").strip().lower()
        if camara not in MODOS_DE_CAMARA:
            logger.warning(
                "StageLoader: camara %r desconocida — se usa 'seguir'. "
                "Valores válidos: %s", camara, ", ".join(sorted(MODOS_DE_CAMARA)),
            )
            camara = "seguir"
        climate = props.get("climate", "")
        # AUD-129 — una vista desconocida cae a lateral con aviso, no rompe.
        # `view` en inglés se acepta igual: el proyecto es bilingüe en las
        # propiedades desde F3.1 y obligar a recordar cuál lleva cada una es
        # la clase de fricción que produce mapas que no cargan.
        vista = str(props.get("vista") or props.get("view") or "lateral").strip().lower()
        if vista not in VISTAS_VALIDAS:
            logger.warning(
                "StageLoader: vista %r desconocida — se usa 'lateral'. "
                "Valores válidos: %s", vista, ", ".join(sorted(VISTAS_VALIDAS)),
            )
            vista = "lateral"
        zone = cls._safe_int(props.get("zone", 0), "zone")
        ambient_light = cls._parse_ambient_light(props)
        bloom = cls._parse_unit_prop(props, "bloom", 0.0, 1.0)
        vignette = cls._parse_unit_prop(props, "vignette", 0.0, 0.6)
        ambient_fx = cls._parse_ambient_fx(props)
        ambient_fx_rate = cls._parse_unit_prop(props, "ambient_fx_rate", 0.0, 120.0)
        start_hour, day_length = cls._parse_day_night(props)
        season = cls._parse_season(props)
        # AUD-111 — VFX opcionales. Apagados salvo que el mapa los pida.
        fog_of_war = cls._safe_float(props.get("fog_of_war", 0.0), "fog_of_war")
        water_effect = cls._bool_de(props.get("water_effect"), por_defecto=False)
        # AUD-240 — los mandos del agua. Los rangos no son decorativos: una
        # amplitud de 40 px convierte la lámina en ruido y un alfa de 255 tapa
        # el escenario. Se acotan aquí y no en el efecto para que un mapa mal
        # escrito se vea raro pero jugable, que es la regla del resto del
        # cargador.
        # `_parse_unit_prop` devuelve `None` cuando el mapa no dice nada, y su
        # tercer argumento es el MÍNIMO del rango, no el valor por defecto: los
        # defectos se aplican aquí, y son los de `WaterEffect`, para que un mapa
        # que no declare nada se vea exactamente igual que antes de AUD-240.
        water_speed = cls._parse_unit_prop(props, "water_speed", 0.0, 8.0)
        water_amplitude = cls._parse_unit_prop(props, "water_amplitude", 0.0, 16.0)
        water_frequency = cls._parse_unit_prop(props, "water_frequency", 0.0, 1.0)
        water_alpha = cls._parse_unit_prop(props, "water_alpha", 0.0, 255.0)
        water_tint = (cls._parse_light_color(props["water_tint"])
                      if props.get("water_tint") is not None else (40, 80, 160))
        god_rays = cls._safe_float(props.get("god_rays", 0.0), "god_rays")

        map_data = pyscroll.data.TiledMapData(tmx_data)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            renderer = pyscroll.BufferedRenderer(
                map_data,
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
                clamp_camera=True,
                alpha=True,
            )
        group = pyscroll.PyscrollGroup(map_layer=renderer, default_layer=4)

        map_w = tmx_data.width * tmx_data.tilewidth
        map_h = tmx_data.height * tmx_data.tileheight

        return StageData(
            map_layer=group,
            map_pixel_size=(map_w, map_h),
            stage_id=stage_id,
            stage_name=stage_name,
            time_limit=time_limit,
            bgm_track=bgm_track,
            gravity_multiplier=gravity_multiplier,
            vista=vista,
            bpm=bpm,
            compas=compas,
            desfase_audio=desfase_audio,
            estamina=estamina,
            tiempo_bala=tiempo_bala,
            profundidad_min=profundidad_min,
            profundidad_max=profundidad_max,
            profundidad_curva=profundidad_curva,
            orden_por_y=orden_por_y,
            sombras_proyectadas=sombras_proyectadas,
            habilidades_libres=habilidades_libres,
            camara=camara,
            climate=climate,
            zone=zone,
            ambient_light=ambient_light,
            bloom=bloom,
            vignette=vignette,
            ambient_fx=ambient_fx,
            ambient_fx_rate=ambient_fx_rate,
            start_hour=start_hour,
            day_length=day_length,
            season=season,
            fog_of_war=fog_of_war,
            water_effect=water_effect,
            water_speed=1.5 if water_speed is None else water_speed,
            water_amplitude=4 if water_amplitude is None else int(water_amplitude),
            water_frequency=0.04 if water_frequency is None else water_frequency,
            water_alpha=100 if water_alpha is None else int(water_alpha),
            water_tint=water_tint,
            god_rays=god_rays,
        )

    @classmethod
    def _parse_season(cls, props: dict[str, Any]) -> str:
        """Lee `season` del mapa y avisa si el nombre no existe.

        Igual que con `ambient_fx`: una errata no puede dejar el escenario a
        medias en silencio. Se avisa con la lista de nombres válidos y se
        devuelve cadena vacía para que la escena use su valor por defecto.
        """
        from src.framework.stage.seasons import ESTACIONES, es_valida

        valor = str(props.get("season", "") or "").strip().lower()
        if not valor:
            return ""
        if not es_valida(valor):
            logger.warning(
                "season: '%s' no es una estación conocida. Válidas: %s",
                valor, ", ".join(sorted(ESTACIONES)),
            )
            return ""
        return valor

    @classmethod
    def _parse_day_night(cls, props: dict[str, Any]) -> tuple[float | None, float]:
        """Lee `start_hour` y `day_length` del mapa.

        `start_hour` acepta un nombre (`dawn`, `dusk`, `night`...), un número
        (`18.5`) o `HH:MM`. Los tres se admiten porque el nombre es lo que un
        diseñador tiene en la cabeza, el número es lo que quiere quien está
        ajustando, y `HH:MM` es lo que se escribe sin pensar.

        `day_length` va en **segundos reales**: 300 significa que el ciclo
        completo dura cinco minutos de partida. Cero congela el reloj.
        """
        from src.framework.stage.day_night import RelojDeMundo

        hora = None
        if "start_hour" in props:
            hora = RelojDeMundo.hora_desde_texto(props.get("start_hour"))
        duracion = cls._parse_unit_prop(props, "day_length", 0.0, 36000.0) or 0.0
        return hora, duracion

    @classmethod
    def _parse_ambient_fx(cls, props: dict[str, Any]) -> str:
        """Lee `ambient_fx` del mapa y avisa si el tipo no existe.

        Una errata aquí no puede fallar en silencio: escribir `leafs` en vez de
        `leaves` dejaría el nivel sin partículas y sin ninguna pista de por qué.
        Se avisa por el registro y se devuelve cadena vacía, para que la escena
        caiga a su valor por zona en vez de quedarse a medias.
        """
        from src.framework.vfx.ambient_particles import AmbientParticleSystem

        valor = str(props.get("ambient_fx", "") or "").strip().lower()
        if not valor or valor == "none":
            return ""
        if valor not in AmbientParticleSystem.TIPOS:
            logger.warning(
                "ambient_fx: '%s' no es un tipo conocido. Válidos: %s, none",
                valor, ", ".join(AmbientParticleSystem.TIPOS),
            )
            return ""
        return valor

    @classmethod
    def _parse_unit_prop(
        cls, props: dict[str, Any], nombre: str, minimo: float, maximo: float,
    ) -> float | None:
        """Lee una propiedad numérica acotada del mapa, o `None` si no está.

        Se recorta al rango en vez de rechazar: un estudiante que escriba
        `bloom = 5` quiere "mucho brillo", y abortar la carga del nivel por eso
        no le enseña nada. Un valor no numérico sí es un error, porque ahí no
        hay intención que adivinar.
        """
        if nombre not in props:
            return None
        valor = cls._safe_float(props.get(nombre, minimo), nombre)
        return max(minimo, min(maximo, valor))

    @classmethod
    def _parse_ambient_light(cls, props: dict[str, Any]) -> float | None:
        """Lee `ambient_light` del mapa, o `None` si no está declarado.

        Se recorta a [0, 1] en vez de rechazar los valores fuera de rango: un
        estudiante que escriba `2` quiere "muy iluminado", y castigarle con un
        error de carga por eso no le enseña nada. Un valor no numérico sí es
        un error, porque ahí no hay intención que adivinar.
        """
        if "ambient_light" not in props:
            return None
        valor = cls._safe_float(props.get("ambient_light", 1.0), "ambient_light")
        return max(0.0, min(1.0, valor))

    #: AUD-272 — las capas de fondo, de lo más lejano a lo más cercano.
    #:
    #: Eran tres y el dibujado ya admitía cuatro velocidades: la profundidad
    #: estaba limitada por el lado que menos costaba cambiar. `sky` y `deep`
    #: son nuevas.
    CAPAS_DE_FONDO: tuple[str, ...] = ("sky", "deep", "far", "mid", "near")

    #: Las que un mapa puede no tener sin que eso sea una errata. Las tres de
    #: siempre siguen avisando si faltan, porque ahí sí lo es.
    CAPAS_OPCIONALES: frozenset[str] = frozenset({"sky", "deep"})

    #: Cuánto se mueve cada capa respecto a la cámara, **por nombre**.
    #:
    #: Por nombre y no por posición: antes el factor salía del índice de carga,
    #: así que un mapa que añadiera una capa delante hacía que `far` pasara de
    #: 0,15 a 0,35 y el mismo fondo se moviera distinto en dos escenarios sin
    #: que nadie lo pidiera.
    #:
    #: Ninguna llega a 1,0: un fondo a la velocidad de la cámara se pega al
    #: terreno y deja de leerse como fondo.
    VELOCIDAD_DE_FONDO: dict[str, float] = {
        "sky": 0.06,     # casi quieto; un cielo que sigue a la cámara no es cielo
        "deep": 0.10,
        "far": 0.15,     # los tres de siempre conservan su velocidad exacta
        "mid": 0.35,
        "near": 0.60,
    }

    @classmethod
    def _load_backgrounds(cls, stage: StageData, background_zone: str) -> None:
        if not background_zone:
            return
        bg_dir = settings.ASSETS_DIR / "backgrounds" / background_zone
        base = bg_dir if bg_dir.is_dir() else settings.ASSETS_DIR / "backgrounds"
        for bg_name in cls.CAPAS_DE_FONDO:
            bg_path = base / f"bg_{background_zone}_{bg_name}.png"
            if bg_name in cls.CAPAS_OPCIONALES and not bg_path.is_file():
                continue
            if cls._try_append_bg(stage, bg_path):
                stage.background_factors.append(cls.VELOCIDAD_DE_FONDO[bg_name])

    @classmethod
    def _try_append_bg(cls, stage: StageData, bg_path: Path) -> bool:
        """Carga una capa de fondo. Devuelve si se pudo (AUD-272).

        Devuelve algo, y no nada, porque quien llama necesita saberlo para
        apuntar la velocidad de la capa **sólo si la capa existe**: si no, los
        dos listados se desincronizarían en cuanto faltara un fichero.
        """
        try:
            bg_surf = AssetLoader.load_image(
                bg_path, size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            )
            stage.background_layers.append(bg_surf)
            return True
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("StageLoader: missing bg %s", bg_path)
            return False

    @classmethod
    def _build_waypoints(cls, tmx_data: Any) -> dict[str, list[tuple[float, float]]]:
        waypoints_by_owner: dict[str, list[tuple[float, float]]] = {}
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            if obj_type == "Waypoint":
                props = dict(obj.properties) if obj.properties else {}
                owner_id = props.get("owner_id", "")
                if owner_id:
                    waypoints_by_owner.setdefault(owner_id, []).append((float(obj.x), float(obj.y)))
        return waypoints_by_owner

    @classmethod
    def _process_objects(
        cls,
        tmx_data: Any,
        stage: StageData,
        waypoints_by_owner: dict[str, list[tuple[float, float]]],
        report: TmxReport,
    ) -> bool:
        player_spawn_found = False
        for obj in tmx_data.get_layer_by_name("Objects"):
            obj_type = getattr(obj, "type", None) or ""
            obj_name = getattr(obj, "name", "") or ""
            props = dict(obj.properties) if obj.properties else {}

            if obj_type == "PlayerSpawn":
                if player_spawn_found:
                    raise FrameworkUsageError("More than one PlayerSpawn object found")
                cls._handle_player_spawn(stage, obj)
                player_spawn_found = True

            elif obj_type == "MessageTrigger":
                cls._handle_message_trigger(stage, obj, props)

            elif obj_type == "MessageTrigger_Once":
                cls._handle_message_trigger(stage, obj, props)

            elif obj_type in cls._entity_registry:
                cls._handle_entity_spawn(stage, obj, obj_name, props, waypoints_by_owner)

            elif obj_type == "Checkpoint":
                cls._handle_checkpoint(stage, obj, props)

            elif obj_type == "NextTrigger":
                if obj.width > 0 and obj.height > 0:
                    stage.next_trigger = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            elif obj_type == "HazardZone":
                cls._handle_hazard_zone(stage, obj, props)

            elif obj_type == "PushBlock":
                cls._handle_bloque(stage, obj, props, empujable=True)

            elif obj_type == "BreakableBlock":
                cls._handle_bloque(stage, obj, props, empujable=False)

            elif obj_type == "Cutscene":
                cls._handle_cutscene(stage, obj, props)

            elif obj_type == "DeathPit":
                if obj.width > 0 and obj.height > 0:
                    stage.death_pits.append(DeathPit(rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height)))

            elif obj_type == "CameraLock":
                cls._handle_camera_lock(stage, obj, props)

            elif obj_type == "Light":
                cls._handle_light(stage, obj, props)

            # F4.1 — objetos con los que el jugador interactúa. Pedidos por los
            # estudiantes tras jugar la fase 1: llaves, puertas, jaulas, cofres
            # y disparadores de evento.
            elif obj_type in ("Pickup", "Key"):
                cls._handle_recogible(stage, obj, props)

            elif obj_type in ("Door", "Cage", "LockedDoor"):
                cls._handle_cerradura(stage, obj, props, obj_type)

            elif obj_type == "Chest":
                cls._handle_cofre(stage, obj, props)

            elif obj_type == "EventTrigger":
                cls._handle_disparador(stage, obj, props)

            elif obj_type == "BossSpawn":
                problema = cls._handle_boss_spawn(stage, obj)
                if problema is not None:
                    report.add(problema)

            elif obj_type == "ScrollZone":
                cls._handle_scroll_forzado(stage, obj, props)

            elif obj_type == "WarpZone":
                cls._handle_warp(stage, obj, props)

            elif obj_type == "Slope":
                cls._handle_pendiente(stage, obj, props)

            # F5.3–F5.6 — mecánicas del Top 200 declaradas desde Tiled.
            elif obj_type in _TIPOS_DE_COMPONENTE:
                cls._handle_componente(stage, obj, props, obj_type)

            elif obj_type != "Waypoint":
                # AUD-055. Esta rama no existía: cualquier `type` que no
                # coincidiera se descartaba en silencio, así que una errata en
                # Tiled producía un enemigo que simplemente no aparecía. Los
                # problemas se acumulan en lugar de abortar en el primero,
                # porque encontrar seis erratas de una vez es una corrección y
                # encontrarlas de una en una son seis ejecuciones del juego.
                report.add(cls._diagnose_object(obj, obj_type, obj_name))

        return player_spawn_found

    @classmethod
    def _diagnose_object(cls, obj: Any, obj_type: str, obj_name: str) -> TmxObjectProblem:
        """Describe un objeto que el cargador no supo interpretar."""
        known = known_object_types(list(cls._entity_registry))
        return TmxObjectProblem(
            object_id=int(getattr(obj, "id", 0) or 0),
            object_name=obj_name,
            object_type=obj_type,
            x=float(getattr(obj, "x", 0.0) or 0.0),
            y=float(getattr(obj, "y", 0.0) or 0.0),
            suggestions=suggest_types(obj_type, known),
            reason="objeto sin type" if not obj_type else "tipo desconocido",
        )

    @classmethod
    def _handle_player_spawn(cls, stage: StageData, obj: Any) -> None:
        stage.spawn_point = pygame.Vector2(obj.x, obj.y - 32)

    @classmethod
    def _handle_message_trigger(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        rect = pygame.Rect(obj.x, obj.y, obj.width or 32, obj.height or 32)
        text = props.get("text", "")
        # AUD-127 — `dialogue` abre un árbol de diálogo en vez de un mensaje.
        #
        # Un `MessageTrigger` con `dialogue` y sin `text` es una conversación;
        # con `text` y sin `dialogue`, un aviso de una línea. Con los dos, el
        # aviso se muestra y la conversación se abre después: no se pierde
        # ninguno de los dos, que es lo que ocurriría si uno tuviera prioridad
        # sobre el otro en silencio.
        arbol = str(props.get("dialogue", "") or props.get("dialogue_tree", ""))
        stage.message_triggers.append(
            MessageTrigger(rect=rect, text=text, dialogue_tree_id=arbol),
        )

    @classmethod
    def _handle_entity_spawn(
        cls,
        stage: StageData,
        obj: Any,
        obj_name: str,
        props: dict[str, Any],
        waypoints_by_owner: dict[str, list[tuple[float, float]]],
    ) -> None:
        obj_type = getattr(obj, "type", None) or ""
        entity_class = cls._entity_registry[obj_type]
        cleaned = cls._parse_entity_props(props)
        if obj_name and obj_name in waypoints_by_owner:
            cleaned["waypoints"] = waypoints_by_owner[obj_name]
        entity = entity_class(pygame.Vector2(obj.x, obj.y), **cleaned)
        stage.entity_list.append(entity)

    @classmethod
    def _handle_boss_spawn(cls, stage: StageData, obj: Any) -> TmxObjectProblem | None:
        """`BossSpawn` — dónde entra el jefe que el mapa nombra (AUD-259).

        `17_BOSS_SPEC.md` §8.2 lo exige en todo mapa de jefe desde que se
        escribió, y el cargador **no lo conocía**: un estudiante que siguiera
        su propia especificación recibía un aviso de tipo desconocido y su
        jefe no aparecía.

        No construye «un jefe» —el motor no sabe cuál— sino el que declara la
        propiedad `boss`, resuelto por el mismo registro de entidades que usan
        `BossVenado` y compañía. Escribir `BossSpawn` con `boss="BossVenado"`
        produce exactamente la misma entidad que escribir `BossVenado`.

        Sin `boss`, o con un nombre no registrado, **avisa** por el camino de
        diagnóstico de AUD-055. Callarse sería repetir el defecto que esto
        arregla: el estudiante escribe algo razonable y no ocurre nada.
        """
        props = dict(obj.properties) if obj.properties else {}
        nombre = str(props.pop("boss", "") or "")
        if not nombre or nombre not in cls._entity_registry:
            problema = cls._diagnose_object(
                obj, "BossSpawn", getattr(obj, "name", "") or "")
            problema.reason = (
                "BossSpawn sin propiedad `boss`" if not nombre
                else f"BossSpawn declara boss='{nombre}', que no está registrado"
            )
            return problema

        entity_class = cls._entity_registry[nombre]
        entity = entity_class(
            pygame.Vector2(obj.x, obj.y), **cls._parse_entity_props(props))
        stage.entity_list.append(entity)
        return None

    @classmethod
    def _handle_boss_spawn_para_pruebas(
        cls, obj: Any, destino: list[Any],
    ) -> TmxObjectProblem | None:
        """Adaptador para probar `_handle_boss_spawn` sin un `StageData`.

        Existe porque el defecto que cierra AUD-259 vive en la resolución del
        tipo, no en el escenario: montar un TMX entero para comprobarlo haría
        la prueba lenta y menos clara sobre qué falló.
        """
        class _Destino:
            entity_list = destino

        return cls._handle_boss_spawn(_Destino(), obj)  # type: ignore[arg-type]

    @classmethod
    def _parse_entity_props(cls, props: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for k, v in props.items():
            if k in ("zone",):
                cleaned[k] = cls._safe_int(v, "zone")
            elif k in _NUMERIC_PROPS:
                cleaned[k] = cls._safe_float(v, k)
            elif k in _BOOL_PROPS:
                cleaned[k] = cls._bool_de(v, por_defecto=False)
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    def _handle_checkpoint(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if "checkpoint_id" not in props:
            raise FrameworkUsageError("Checkpoint missing required property: checkpoint_id")
        rect = pygame.Rect(obj.x, obj.y, obj.width or 24, obj.height or 32)
        from src.framework.stage.checkpoint import Checkpoint
        cp = Checkpoint(pygame.Vector2(obj.x, obj.y), rect, int(props["checkpoint_id"]))
        stage.checkpoints.append(cp)

    #: Colores con nombre para la propiedad `color` de un objeto `Light`.
    #: Existen porque escribir `#ffdcb4` en Tiled es un obstáculo real para
    #: alguien que está aprendiendo, y porque una paleta corta produce
    #: escenarios más coherentes que la libertad total.
    LIGHT_COLORS: dict[str, tuple[int, int, int]] = {
        "warm": (255, 220, 180),      # antorcha, lámpara
        "cold": (180, 210, 255),      # luna, hielo
        "fire": (255, 120, 50),       # fuego, lava
        "toxic": (150, 255, 130),     # esporas, veneno
        "blood": (255, 60, 60),       # alarma, sangre
        "white": (255, 255, 255),
    }

    @classmethod
    def _handle_light(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """Convierte un objeto `Light` de Tiled en un `LightSpec`.

        Propiedades reconocidas, todas opcionales:

        ==============  ======  ===========================================
        propiedad       tipo    significado
        ==============  ======  ===========================================
        `radius`        float   alcance en píxeles (por defecto 80)
        `color`         string  nombre de `LIGHT_COLORS` o `#rrggbb`
        `intensity`     float   0 a 1 (por defecto 0.8)
        `flicker`       bool    parpadeo tipo antorcha
        `flicker_speed` float   oscilaciones por segundo
        `flicker_amount` float  amplitud del parpadeo, 0 a 1
        ==============  ======  ===========================================

        El punto de luz se toma del **centro** del rectángulo dibujado en
        Tiled, no de su esquina. Es lo que espera cualquiera que dibuje un
        recuadro alrededor de una antorcha; usar la esquina desplazaría la luz
        y el estudiante no sabría por qué.
        """
        ancho = float(getattr(obj, "width", 0) or 0)
        alto = float(getattr(obj, "height", 0) or 0)
        centro = (float(obj.x) + ancho / 2.0, float(obj.y) + alto / 2.0)

        radio = cls._safe_float(props.get("radius", 80.0), "light radius")
        if radio <= 0:
            radio = 80.0

        stage.lights.append(LightSpec(
            position=centro,
            radius=radio,
            color=cls._parse_light_color(props.get("color")),
            intensity=max(0.0, min(1.0, cls._safe_float(
                props.get("intensity", 0.8), "light intensity"))),
            flicker=bool(props.get("flicker", False)),
            flicker_speed=cls._safe_float(
                props.get("flicker_speed", 4.0), "light flicker_speed"),
            flicker_amount=max(0.0, min(1.0, cls._safe_float(
                props.get("flicker_amount", 0.15), "light flicker_amount"))),
        ))

    @classmethod
    def _parse_light_color(cls, valor: Any) -> tuple[int, int, int]:
        """Acepta un nombre de la paleta, `#rrggbb`, o el formato de Tiled.

        Tiled guarda los colores como `#aarrggbb` —con alfa delante—, que es
        justo lo que nadie espera. Se aceptan las tres formas y se cae al
        color cálido ante cualquier cosa ininteligible, porque una luz del
        color equivocado se ve y se corrige, mientras que un error de carga
        deja al estudiante sin nivel.
        """
        if valor is None:
            return cls.LIGHT_COLORS["warm"]
        texto = str(valor).strip().lower()
        if texto in cls.LIGHT_COLORS:
            return cls.LIGHT_COLORS[texto]
        if texto.startswith("#"):
            digitos = texto[1:]
            if len(digitos) == 8:      # #aarrggbb de Tiled: se descarta el alfa
                digitos = digitos[2:]
            if len(digitos) == 6:
                try:
                    return (
                        int(digitos[0:2], 16),
                        int(digitos[2:4], 16),
                        int(digitos[4:6], 16),
                    )
                except ValueError:
                    pass
        logger.warning(
            "Light: color '%s' no reconocido; se usa 'warm'. Válidos: %s o #rrggbb",
            valor, ", ".join(sorted(cls.LIGHT_COLORS)),
        )
        return cls.LIGHT_COLORS["warm"]

    @classmethod
    def _handle_recogible(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`Pickup` / `Key` — algo que el jugador coge del suelo.

        `Key` es un alias de `Pickup`: nombrar el tipo por lo que es hace el
        mapa legible en Tiled, y a efectos del motor son lo mismo.
        """
        item_id = str(props.get("item_id") or props.get("key_id") or obj.name or "")
        if not item_id:
            logger.warning(
                "Pickup en (%s, %s) sin 'item_id': se ignora. Ponle un item_id "
                "o dale nombre al objeto en Tiled.", obj.x, obj.y,
            )
            return
        stage.recogibles.append(Recogible(
            rect=cls._rect_de(obj),
            item_id=item_id,
            automatico=cls._bool_de(props.get("automatico"), por_defecto=True),
            mensaje=str(props.get("mensaje", "")),
        ))

    @classmethod
    def _handle_cerradura(
        cls, stage: StageData, obj: Any, props: dict[str, Any], obj_type: str,
    ) -> None:
        """`Door` / `Cage` / `LockedDoor` — bloquea el paso hasta tener la llave."""
        if obj.width == 0 or obj.height == 0:
            logger.warning(
                "%s en (%s, %s) no tiene tamaño: una puerta sin área no bloquea "
                "nada. Dibújala como rectángulo en Tiled.", obj_type, obj.x, obj.y,
            )
            return
        stage.cerraduras.append(Cerradura(
            rect=cls._rect_de(obj),
            key_id=str(props.get("key_id", "")),
            clase="jaula" if obj_type == "Cage" else "puerta",
            consume_llave=cls._bool_de(props.get("consume_llave"), por_defecto=False),
            mensaje_bloqueado=str(props.get("mensaje", "")),
            evento_al_abrir=str(props.get("evento", "")),
            # AUD-132 — interruptor y puerta cronometrada, desde Tiled.
            abre_con_evento=str(props.get("abre_con", "")),
            cierra_en=cls._safe_float(props.get("cierra_en", 0.0), "cierra_en"),
        ))

    @classmethod
    def _handle_cofre(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`Chest` — se abre con el botón y entrega su contenido una vez."""
        stage.cofres.append(Cofre(
            rect=cls._rect_de(obj),
            contenido=str(props.get("contenido") or props.get("item_id") or ""),
            key_id=str(props.get("key_id", "")),
            mensaje=str(props.get("mensaje", "")),
            evento_al_abrir=str(props.get("evento", "")),
        ))

    @classmethod
    def _handle_disparador(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`EventTrigger` — emite un evento del bus; el escenario decide qué hace."""
        evento = str(props.get("evento") or obj.name or "")
        if not evento:
            logger.warning(
                "EventTrigger en (%s, %s) sin 'evento': no emitiría nada, así "
                "que se ignora.", obj.x, obj.y,
            )
            return
        stage.disparadores.append(Disparador(
            rect=cls._rect_de(obj),
            evento=evento,
            automatico=cls._bool_de(props.get("automatico"), por_defecto=True),
            una_vez=cls._bool_de(props.get("una_vez"), por_defecto=True),
            key_id=str(props.get("key_id", "")),
        ))

    @classmethod
    def _handle_pendiente(cls, stage: StageData, obj: Any,
                          props: dict[str, Any]) -> None:
        """`Slope` — suelo inclinado (AUD-297).

        El rectángulo del objeto es el **triángulo entero**, no la línea de la
        superficie: se dibuja en Tiled como se dibujaría la roca. La hipotenusa
        va de esquina a esquina, y `sube` dice cuál de las dos está arriba.

        `sube` admite `derecha` (por defecto) o `izquierda`. Una palabra y no un
        booleano porque «sube=false» no dice hacia dónde, y en Tiled se lee la
        propiedad sin el código delante.
        """
        sube = str(props.get("sube", "derecha")).strip().lower()
        if sube not in ("derecha", "izquierda"):
            logger.warning(
                "Slope en (%s, %s): `sube` es %r y sólo vale 'derecha' o "
                "'izquierda'. Se toma 'derecha'.", obj.x, obj.y, sube)
            sube = "derecha"
        stage.pendientes.append(Pendiente(
            rect=cls._rect_de(obj),
            sube_a_la_derecha=sube == "derecha",
        ))

    @classmethod
    def _handle_warp(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """`WarpZone` — teletransporta dentro del mismo mapa (AUD-287).

        Propiedades:

        * `destino_x`, `destino_y` — **obligatorias**, en píxeles de mundo. Es
          adonde va el centro inferior del jugador, o sea sus pies: dar el punto
          en el suelo es lo natural mirando el mapa en Tiled, y evita el error de
          dejarlo medio hundido.
        * `automatico` — al tocar (por defecto) o pulsando usar.
        * `una_vez`, `key_id`, `enfriamiento`, `mensaje`.

        Sin destino no se carga y se avisa. Un warp sin destino no es un warp a
        medio configurar: es un rectángulo que teletransporta al origen del
        mapa, que es peor que no existir porque parece un fallo del motor.
        """
        if "destino_x" not in props or "destino_y" not in props:
            logger.warning(
                "WarpZone en (%s, %s) sin 'destino_x'/'destino_y': se ignora. "
                "Con destino implícito mandaría al jugador a la esquina del "
                "mapa y parecería un fallo del motor.", obj.x, obj.y,
            )
            return
        stage.warps.append(ZonaDeWarp(
            rect=cls._rect_de(obj),
            destino=pygame.Vector2(float(props["destino_x"]),
                                   float(props["destino_y"])),
            automatico=cls._bool_de(props.get("automatico"), por_defecto=True),
            una_vez=cls._bool_de(props.get("una_vez"), por_defecto=False),
            key_id=str(props.get("key_id", "")),
            enfriamiento=float(props.get("enfriamiento", 0.5)),
            mensaje=str(props.get("mensaje", "")),
        ))

    @classmethod
    def _handle_scroll_forzado(
        cls, stage: StageData, obj: Any, props: dict[str, Any],
    ) -> None:
        """`ScrollZone` — la cámara arranca sola al pisar el rectángulo (AUD-249).

        El rectángulo del objeto es el **disparador**, no la zona de muerte: se
        pisa una vez y a partir de ahí manda la cámara. Quien mata es el borde
        izquierdo de la pantalla, con `margen_de_gracia` píxeles de cortesía
        para que la muerte no ocurra mientras el sprite aún se ve.

        Propiedades, todas opcionales:

        * `velocidad_x` / `velocidad_y` — px/s. Por defecto 40 hacia la derecha.
        * `margen_de_gracia` — px que se puede rebasar el borde. Por defecto 24.
        * `parar_en_x` — la cámara se detiene ahí. Sin ella, hasta el final.
        """
        from src.framework.stage.level_mechanics import ScrollForzado

        def f(clave: str, defecto: float) -> float:
            return cls._safe_float(props.get(clave, defecto), f"ScrollZone.{clave}")

        parar = props.get("parar_en_x")
        stage.scroll_forzados.append(ScrollForzado(
            velocidad=pygame.Vector2(f("velocidad_x", 40.0), f("velocidad_y", 0.0)),
            margen_de_gracia=f("margen_de_gracia", 24.0),
            parar_en_x=(
                cls._safe_float(parar, "ScrollZone.parar_en_x")
                if parar is not None else None
            ),
            disparador=cls._rect_de(obj),
        ))

    @staticmethod
    def _rect_de(obj: Any) -> pygame.Rect:
        """El rectángulo de un objeto de Tiled, con un mínimo utilizable.

        Un objeto de tipo punto tiene ancho y alto 0 y sería imposible de
        tocar. Se le da el tamaño de una baldosa, que es lo que el diseñador
        ve en Tiled cuando coloca el punto.
        """
        ancho = int(obj.width) or settings.TILE_SIZE
        alto = int(obj.height) or settings.TILE_SIZE
        return pygame.Rect(int(obj.x), int(obj.y), ancho, alto)

    @staticmethod
    def _bool_de(valor: Any, *, por_defecto: bool) -> bool:
        """Tiled entrega los booleanos como bool, como 'true' o como '1'."""
        if valor is None or valor == "":
            return por_defecto
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in ("true", "1", "si", "sí", "yes")

    # ── F5.3–F5.6: componentes ECS desde el TMX ────────────────
    @classmethod
    def _handle_componente(
        cls, stage: StageData, obj: Any, props: dict[str, Any], obj_type: str,
    ) -> None:
        """Convierte un objeto de Tiled en un componente ECS.

        Una sola función para las once mecánicas nuevas, y no once métodos:
        todas hacen lo mismo —leer un rectángulo, leer unas propiedades,
        construir un `dataclass`— y once copias de eso serían once sitios donde
        olvidar el mismo `_safe_float`.

        Los nombres de las propiedades son los que un estudiante escribiría en
        Tiled sin consultar nada: `fuerza_x`, `velocidad`, `alcance`. Se
        eligieron antes que los del código.
        """
        from src.framework.ecs.components import (
            Acosador,
            Alerta,
            BloqueRitmico,
            ConoDeVision,
            Liana,
            PlataformaHundible,
            PlataformaMovil,
            Resorte,
            Solido,
            Tirolesa,
            Transform,
            ZonaDeAgua,
            ZonaDeFriccion,
            ZonaDeViento,
            ZonaLetalTemporizada,
        )

        rect = cls._rect_de(obj)

        def f(clave: str, defecto: float) -> float:
            return cls._safe_float(props.get(clave, defecto), f"{obj_type}.{clave}")

        def transform() -> Transform:
            """Las mecánicas que se mueven necesitan `Transform`; las zonas no.

            Una zona es un rectángulo quieto y le basta con llevarlo dentro. Una
            plataforma se mueve, así que su posición tiene que estar donde los
            sistemas de movimiento y arrastre saben buscarla.
            """
            return Transform(
                posicion=pygame.Vector2(rect.topleft), rect=rect.copy(),
            )

        # Cada entrada es **la lista de componentes de UNA entidad**. Uniforme
        # para las once mecánicas: la escena hace `mundo.crear(*grupo)` y no
        # tiene que saber cuál es cuál.
        grupo: list[object]

        if obj_type == "Spring":
            # AUD-131 — resorte. El rectángulo es la zona de contacto, así que
            # un resorte dibujado ancho rebota en todo su ancho: es lo que el
            # diseñador ve en Tiled y por tanto lo que espera.
            grupo = [Resorte(
                rect=rect,
                impulso=f("impulso", -520.0),
                rearme=f("rearme", 0.15),
            )]

        elif obj_type == "WindZone":
            grupo = [ZonaDeViento(
                rect=rect,
                fuerza=pygame.Vector2(f("fuerza_x", 0.0), f("fuerza_y", 0.0)),
                periodo=f("periodo", 0.0),
            )]

        elif obj_type in ("FrictionZone", "Conveyor"):
            # `Conveyor` es un alias con otro valor por defecto: una cinta sin
            # arrastre no es una cinta, y obligar al estudiante a recordarlo
            # sería una errata esperando a ocurrir.
            arrastre_defecto = 60.0 if obj_type == "Conveyor" else 0.0
            grupo = [ZonaDeFriccion(
                rect=rect,
                multiplicador=f("multiplicador", 1.0),
                arrastre=f("arrastre", arrastre_defecto),
            )]

        elif obj_type in ("LaserZone", "ShockwaveZone"):
            grupo = [ZonaLetalTemporizada(
                rect=rect,
                dano=f("dano", 99.0),
                encendido=f("encendido", 1.0),
                apagado=f("apagado", 1.0),
                desfase=f("desfase", 0.0),
            )]

        elif obj_type == "WaterZone":
            grupo = [ZonaDeAgua(
                rect=rect,
                corriente=pygame.Vector2(f("corriente_x", 0.0), f("corriente_y", 0.0)),
            )]

        elif obj_type == "MovingPlatform":
            # El destino se declara como desplazamiento y no en coordenadas
            # absolutas: mover la plataforma en Tiled no debería obligar a
            # recalcular su destino a mano, y con absolutas hay que hacerlo
            # siempre.
            grupo = [
                transform(),
                PlataformaMovil(
                    origen=pygame.Vector2(rect.topleft),
                    destino=pygame.Vector2(
                        rect.x + f("destino_dx", 0.0), rect.y + f("destino_dy", 0.0),
                    ),
                    velocidad=f("velocidad", 40.0),
                    espera=f("espera", 0.5),
                ),
                Solido(atravesable_desde_abajo=cls._bool_de(
                    props.get("atravesable"), por_defecto=False)),
            ]

        elif obj_type == "RhythmBlock":
            grupo = [
                transform(),
                BloqueRitmico(
                    # `visible` y `oculto` a secas serían tentadores, pero
                    # **`visible` es un nombre reservado en Tiled**: pytmx
                    # rechaza el mapa entero con «Reserved names and duplicate
                    # names are not allowed». Lo descubrió el escenario de
                    # referencia al cargarlo por primera vez.
                    visible_seg=f("visible_seg", 1.0),
                    oculto_seg=f("oculto_seg", 1.0),
                    desfase=f("desfase", 0.0),
                    # AUD-137: con patrón manda la música y los segundos
                    # dejan de contar. `"x.x."` = sí, no, sí, no.
                    patron=str(props.get("patron", "") or ""),
                ),
            ]

        elif obj_type == "SinkingPlatform":
            grupo = [
                transform(),
                PlataformaHundible(
                    retraso=f("retraso", 0.4),
                    velocidad_caida=f("velocidad_caida", 90.0),
                    reaparece_en=f("reaparece_en", 3.0),
                    y_original=float(rect.y),
                ),
                Solido(atravesable_desde_abajo=True),
            ]

        elif obj_type == "Guard":
            grupo = [
                transform(),
                ConoDeVision(
                    mira=pygame.Vector2(f("mira_x", 1.0), f("mira_y", 0.0)),
                    alcance=f("alcance", 160.0),
                    semiangulo=f("semiangulo", 30.0),
                    barrido=f("barrido", 0.0),
                    velocidad_barrido=f("velocidad_barrido", 45.0),
                ),
                Alerta(),
            ]

        elif obj_type == "Stalker":
            grupo = [
                transform(),
                Acosador(
                    velocidad=f("velocidad", 55.0),
                    distancia_retirada=f("distancia_retirada", 480.0),
                    reaparicion=f("reaparicion", 6.0),
                ),
            ]

        elif obj_type == "Vine":
            grupo = [Liana(
                rect=rect,
                ancho_de_agarre=int(f("ancho_de_agarre", 10.0)),
                velocidad=f("velocidad", 70.0),
            )]

        elif obj_type == "Zipline":
            # El destino va en desplazamiento, igual que en `MovingPlatform`:
            # mover el cable en Tiled no debería obligar a recalcular su
            # extremo a mano.
            grupo = [Tirolesa(
                origen=pygame.Vector2(rect.topleft),
                destino=pygame.Vector2(
                    rect.x + f("destino_dx", 96.0),
                    rect.y + f("destino_dy", 64.0),
                ),
                velocidad=f("velocidad", 190.0),
                radio_de_enganche=f("radio_de_enganche", 14.0),
                solo_de_bajada=cls._bool_de(
                    props.get("solo_de_bajada"), por_defecto=True),
            )]

        else:  # pragma: no cover - `_TIPOS_DE_COMPONENTE` y esto van juntos
            return

        stage.componentes.append(grupo)

    @classmethod
    def _handle_hazard_zone(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        damage = cls._safe_float(props.get("damage", 0.25), "hazard damage")
        # AUD-135 — la inundación. `sube` en píxeles por segundo; `sube_hasta`
        # es una `y` del mapa, así que el diseñador pone el tope donde ve el
        # techo en Tiled y no tiene que calcular alturas.
        sube = cls._safe_float(props.get("sube", 0.0), "hazard sube")
        tope_bruto = props.get("sube_hasta")
        sube_hasta = (
            cls._safe_float(tope_bruto, "hazard sube_hasta")
            if tope_bruto not in (None, "") else None
        )
        stage.hazard_zones.append(HazardZone(
            rect=rect,
            damage=damage,
            sube=max(0.0, sube),
            sube_hasta=sube_hasta,
            arranca_con=str(props.get("arranca_con", "") or ""),
            # Tiled escribe los booleanos como `"true"`/`"false"`, y la cadena
            # `"false"` es verdadera en Python: leerla sin convertir haría que
            # `avisar=false` no apagara nada.
            avisar=str(props.get("avisar", "true")).lower() != "false",
        ))

    @classmethod
    def _handle_bloque(cls, stage: StageData, obj: Any, props: dict[str, Any],
                       *, empujable: bool) -> None:
        """AUD-140 — `PushBlock` y `BreakableBlock`.

        Sin tamaño se ignora con aviso: un bloque de 0×0 sería un sólido
        invisible de área nula, que no estorba a nadie y no se ve. El
        estudiante creería haberlo puesto.
        """
        if obj.width <= 0 or obj.height <= 0:
            logger.warning(
                "bloque sin tamaño en (%s, %s): se ignora", obj.x, obj.y)
            return
        rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
        if empujable:
            stage.empujables.append(BloqueEmpujable(
                rect=rect,
                velocidad=max(1.0, cls._safe_float(
                    props.get("velocidad", 45.0), "velocidad del bloque")),
                con_gravedad=cls._bool_de(props.get("con_gravedad"),
                                          por_defecto=True),
            ))
        else:
            stage.destructibles.append(BloqueDestructible(
                rect=rect,
                golpes=max(1, cls._safe_int(props.get("golpes", 1), "golpes")),
                evento_al_romper=str(props.get("evento_al_romper", "") or ""),
            ))

    @classmethod
    def _handle_cutscene(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        """AUD-136 — `Cutscene` en Tiled.

        Con rectángulo, se dispara al entrar el jugador; como punto, al empezar
        el escenario. Sin `guion` se ignora con un aviso: una escena vacía no
        haría nada y quitaría el mando durante un instante, que es peor que no
        estar.
        """
        guion = str(props.get("guion", "") or props.get("script", "") or "")
        if not guion.strip():
            logger.warning(
                "Cutscene sin propiedad 'guion' en (%s, %s): se ignora",
                getattr(obj, "x", "?"), getattr(obj, "y", "?"),
            )
            return
        stage.escenas.append(EscenaGuionizada(
            rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height),
            guion=guion,
            bloquea=cls._bool_de(props.get("bloquea"), por_defecto=True),
            saltable=cls._bool_de(props.get("saltable"), por_defecto=True),
            una_vez=cls._bool_de(props.get("una_vez"), por_defecto=True),
            arranca_con=str(props.get("arranca_con", "") or ""),
        ))

    @classmethod
    def _handle_camera_lock(cls, stage: StageData, obj: Any, props: dict[str, Any]) -> None:
        if obj.width == 0 or obj.height == 0:
            return
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        lock_x = props.get("lock_x", False) in (True, "true", "True", 1, "1")
        lock_y = props.get("lock_y", False) in (True, "true", "True", 1, "1")
        stage.camera_locks.append(CameraLock(rect=rect, lock_x=lock_x, lock_y=lock_y))

    @classmethod
    def _load_collision(cls, tmx_data: Any, stage: StageData) -> None:
        try:
            collision_layer = tmx_data.get_layer_by_name("Collision")
            for obj in collision_layer:
                rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                if rect.width > 0 and rect.height > 0:
                    obj_type = getattr(obj, "type", None) or ""
                    if obj_type == "Platform":
                        stage.one_way_rects.append(rect)
                    else:
                        stage.collision_rects.append(rect)
        except ValueError:
            logger.warning("StageLoader: Collision layer not found")

    # ── Safe converters ───────────────────────────────────────────

    @classmethod
    def _safe_int(cls, value: Any, name: str) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning("StageLoader: invalid %s value '%s', using 0", name, value)
            return 0

    @classmethod
    def _safe_float(cls, value: Any, name: str) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("StageLoader: invalid %s value '%s', using 0.0", name, value)
            return 0.0
