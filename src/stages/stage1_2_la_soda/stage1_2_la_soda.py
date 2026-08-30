"""
Módulo: stage1_2_la_soda
Sistema: stage (asignación del estudiante)
Unidad académica: ver el front-matter de README.md para units_demonstrated.

Copiado y adaptado desde student_templates/stage_template/ siguiendo sus
propias instrucciones. No modifica StageScene ni ningún código del
engine/framework.

Probar con:
   python main.py --stage stage1_2_la_soda
"""
from __future__ import annotations

import random
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.ui.theme import Theme
from src.engine.ui.theme import font as _fuente_del_tema
from src.engine.utils.math_utils import ease_out_cubic, ease_out_quad
from src.engine.utils.surface_pool import get_pool
from src.framework.ecs import ZonaDeFriccion
from src.framework.entities.enemy_base import EnemyBase
from src.framework.processing.color_tools import ColorTools
from src.framework.processing.filter_tools import FilterTools
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.cutscene_system import CutsceneScript, FadeAction
from src.framework.stage.interactable_system import EVENTO_BLOQUEADA, EVENTO_RECOGIDO
from src.framework.stage.stage_loader import StageLoader
from src.framework.vfx.particle_system import ParticleEmitter
from src.stages.stage1_2_la_soda.entities import (
    FlyingCucaracha,
    FlyingZancudo,
    ShooterCocinero,
    WalkerCulebra,
    WalkerRaton,
)

if TYPE_CHECKING:
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera

# Registra las entidades propias para que el .tmx pueda referenciarlas por
# nombre de tipo. Corre una sola vez al importar el módulo, mucho antes de
# que cualquier StageScene cargue el mapa. Claves con prefijo "LaSoda" para
# evitar choque con bestiary_registry.py del profe, que auto-registra las
# especies genéricas "WalkerRaton" / "FlyingCucaracha" y, si no, las
# pisaría en silencio.
StageLoader.register_entity("LaSodaWalkerRaton", WalkerRaton)
StageLoader.register_entity("LaSodaFlyingCucaracha", FlyingCucaracha)
StageLoader.register_entity("LaSodaCulebra", WalkerCulebra)
StageLoader.register_entity("LaSodaZancudo", FlyingZancudo)
StageLoader.register_entity("LaSodaShooterCocinero", ShooterCocinero)


def _color_de_salud(pct: float) -> tuple[int, int, int]:
    """Verde (120°) a rojo (0°) proporcional a `pct` — Unidad V
    (ColorTools): conversión HSV->RGB compartida entre la barra de un
    enemigo común (`Stage1_2_LaSoda._draw_enemy_health_bars`) y la barra
    de jefe del cocinero (`_BarraDeJefe`, AUD-650), para que las dos
    barras de vida del nivel usen exactamente el mismo degradado en vez
    de dos fórmulas iguales copiadas dos veces."""
    pct = max(0.0, min(1.0, pct))
    return ColorTools.hsv_to_rgb(120.0 * pct, 1.0, 1.0)


class _RoomTransition:
    """Transición dura entre el camino exterior y el interior de La Soda al
    cruzar la puerta — estilo "puerta de Mario": fundido a negro,
    teletransporte real del jugador al otro lado (mientras la pantalla está
    sólida negra, invisible), fundido de vuelta. La cámara (clamped en
    apply_camera_box) usa el cuarto activo (`room`) para no mostrar nunca las
    dos áreas a la vez — reemplazando un anterior sistema de fundido
    puramente cosmético que no afectaba el gameplay.

    AUD-629 — ROOM_LIMIT_X vs. TRIGGER_X, y por qué hacía falta separarlos.
    Hasta este cambio una sola constante (`DOOR_X = 2560`) hacía de límite
    del cuarto Y de disparador del fundido a la vez. Con `screen_w=800` el
    clamp del exterior en `apply_camera_box` es `hi = DOOR_X - screen_w =
    1760`, así que el borde derecho de la pantalla cae EXACTAMENTE en
    `DOOR_X` cuando la cámara llega a su tope — el jugador se salía de
    cuadro por la derecha y recién ahí, fuera de vista, arrancaba el
    fundido. Encima el vano pintado en el .tmx (columnas 155-158 antes de
    este commit) quedaba 16-80px a la izquierda de `DOOR_X`, así que el
    jugador ya había cruzado el hueco visual de la puerta un tile antes de
    que pasara cualquier cosa. El resultado se leía como atravesar una
    pared en el borde de pantalla, no como cruzar una puerta (diagnóstico
    completo en `Claude - Uso General/DIAGNOSTICO_AUD627.md` §3).

    La separación:
      * `ROOM_LIMIT_X` — el límite REAL del cuarto (x=2560, columna 160 del
        .tmx, donde arranca el interior). Es geometría del mapa, no cambia:
        lo siguen usando `apply_camera_box` (para no revelar nunca el
        interior desde el exterior ni al revés), `clamp_one_way` (qué tan
        cerca de la puerta se puede estar ya adentro) y el destino del
        teletransporte (`+ ENTRY_OFFSET`, bien adentro del cuarto nuevo).
      * `TRIGGER_X` — el disparador del fundido, movido al CENTRO del vano
        que ahora pinta el .tmx (columnas 149-152, ver AUD-629 en el commit
        de assets). `maybe_trigger` compara contra éste, no contra
        `ROOM_LIMIT_X`. Al quedar estrictamente a la izquierda del límite
        del cuarto, el fundido arranca con el jugador todavía DENTRO de
        cuadro, parado en el vano — que es además el momento en que
        `_MarcoDeLaPuerta` (ver más abajo) ya lo está ocultando detrás del
        marco, así que lo último que se ve antes del negro es al jugador
        desapareciendo en la sombra de la puerta, no un corte a mitad de
        zancada.

    No usa un WaitAction entre los dos fundidos para evitar gaps de
    visibilidad: el teletransporte corre en el callback de fin del fade-out
    (pantalla 100% negra, alpha=255) y el fade-in arranca en ese mismo frame,
    sin ningún hueco entre medio. El fade-in se actualiza solo en frames
    donde ya estaba activo al inicio, para garantizar alpha=255 en el primer
    frame visible.

    La puerta es de una sola dirección: clamp_one_way bloquea el regreso al
    camino una vez adentro. Si el jugador muere sin alcanzar un checkpoint,
    respawning lo pone en el spawn exterior inicial, pero room queda
    "interior" — el siguiente update() lo clampea just-inside la puerta,
    un compromiso entre "perder todo progreso" y "permitir back/forth".
    """

    ROOM_LIMIT_X: float = 2560.0  # límite del cuarto — geometría del mapa, no se mueve
    TRIGGER_X: float = 2416.0  # disparador — centro del vano (columnas 149-152, ver AUD-629)
    ENTRY_OFFSET: float = 32.0  # dentro del interior, más allá del marco de la puerta
    ONE_WAY_MARGIN: float = 8.0  # qué tan cerca de la puerta se puede estar ya adentro

    def __init__(self, map_width: float) -> None:
        self._map_w = map_width
        self._room: str = "exterior"
        self._triggered: bool = False
        self._pending_player: Player | None = None  # Limpiado después de set_spawn en _on_fade_out_done
        self._fade_out = CutsceneScript([FadeAction(0.2, fade_in=False)])
        self._fade_in = CutsceneScript([FadeAction(0.25, fade_in=True)])

    @property
    def room(self) -> str:
        return self._room

    def maybe_trigger(self, player: Player) -> None:
        if not self._triggered and player.position.x >= self.TRIGGER_X:
            self._triggered = True
            self._pending_player = player
            self._fade_out.start(callback=self._on_fade_out_done)

    def _on_fade_out_done(self) -> None:
        if self._pending_player is not None:
            self._pending_player.set_spawn(pygame.Vector2(
                self.ROOM_LIMIT_X + self.ENTRY_OFFSET, self._pending_player.position.y,
            ))
            self._pending_player = None
        self._room = "interior"
        self._fade_in.start()

    def disarm_to_interior(self) -> None:
        """Partida cargada ya dentro del interior (checkpoint pasado la
        puerta) — el fundido/teletransporte no tienen sentido, se marca el
        cuarto directamente sin reproducir la secuencia."""
        self._triggered = True
        self._room = "interior"

    def clamp_one_way(self, player: Player) -> None:
        """Puerta sin vuelta atrás: una vez adentro, no se puede volver a
        cruzar hacia el camino — evita que la cámara (fija en el cuadro
        del interior) quede desincronizada de un jugador que caminó de
        vuelta. Mismo patrón que el leash de `boss_base.py` (clamp de
        `position.x` + sync manual de `rect.x`, sin tocar `velocity`).

        COMPORTAMIENTO AL MORIR: Si el jugador muere sin alcanzar un
        checkpoint (el primero en el interior está en x=2940, bien adentro),
        StageScene.respawn() lo pone de vuelta en el spawn del mapa
        (x≈32, exterior). Pero _room sigue siendo "interior" porque se
        preservó a través del respawn (el None-guard en on_stage_start solo
        inicializa una vez). El siguiente update() ejecuta este clamp, lo
        que reubica al jugador a ROOM_LIMIT_X+ONE_WAY_MARGIN (x≈2568), justo
        pasado la puerta. Esto es intencional: un compromiso entre "perder
        todo progreso" (malo para gameplay) y "permitir volver atrás"
        (rompe el design de una sola dirección).
        """
        if self._room != "interior":
            return
        floor = self.ROOM_LIMIT_X + self.ONE_WAY_MARGIN
        if player.position.x < floor:
            player.position.x = floor
            player.rect.x = int(player.position.x)

    def apply_camera_box(self, camera: Camera) -> None:
        """Sobreescribe camera.offset.x con un clamp extra según el cuarto
        activo. Se llama DESPUÉS de que Camera.update() ya corrió para
        este frame (Stage1_2_LaSoda.update llama a super().update(dt)
        primero) — así que este clamp es el que efectivamente queda
        dibujado. camera.offset es un atributo público mutable (mismo
        patrón que ya usa CameraMoveAction del propio framework), no se
        toca camera.py.

        Cuarto exterior: el offset nunca puede pasar de ROOM_LIMIT_X -
        screen_w, así la cámara jamás revela nada del interior mientras se
        camina por el camino. Cuarto interior: el interior (2560-3456px,
        896px de ancho) es más ancho que la pantalla (800px) — a diferencia
        de una versión anterior de este mapa, donde el interior medía 768px
        y no llegaba a llenar la pantalla, colando ~32px del borde del
        camino por el borde izquierdo del cuadro (una concesión aceptada en
        su momento, documentada aquí mismo). Al ensanchar la sala esa
        concesión queda eliminada: `lo` y `hi` caen ambos en o después de
        ROOM_LIMIT_X (lo = ROOM_LIMIT_X exactamente, ya que map_w - screen_w
        > ROOM_LIMIT_X con estas dimensiones), así que el clamp nunca puede
        revelar nada a la izquierda de la puerta y la cámara tiene margen
        real de scroll (96px) enteramente dentro de la sala.
        """
        screen_w = settings.INTERNAL_WIDTH
        if self._room == "exterior":
            lo, hi = 0.0, self.ROOM_LIMIT_X - screen_w
        else:
            hi = self._map_w - screen_w
            lo = max(0.0, min(self.ROOM_LIMIT_X, hi))
        camera.offset.x = max(lo, min(camera.offset.x, hi))

    def update(self, dt: float) -> None:
        # Evitar doble avance del fade-in: si está activo ANTES de actualizar
        # el fade-out, actualízalo; si se acaba de activar *durante* este
        # update (por el callback), deja que se dibuje en el siguiente frame.
        fade_in_was_active = self._fade_in.active
        self._fade_out.update(dt)
        if fade_in_was_active:
            self._fade_in.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self._fade_out.active:
            self._fade_out.draw(surface)
        elif self._fade_in.active:
            self._fade_in.draw(surface)


class _LecturaDeLuz:
    """Unidad VII (Evaluación Práctica II) — el histograma del fotograma
    REAL decide la "adaptación a la penumbra" al cruzar de la calle a la
    sala de La Soda.

    Por qué acá y no en cualquier otro lugar: `_room_transition.room` ya
    modela el cruce "exterior" -> "interior" (ver `_RoomTransition` arriba),
    y `AmbientLightZone_Sala`/`AmbientLightZone_Cocina` del .tmx ya oscurecen
    esa mitad del mapa (`TestJerarquiaDeLuzDelNivel` en `test_la_soda.py`
    mide esa jerarquía real: exterior > cocina > sala). Lo que NO existía es
    que el propio JUEGO se enterara de cuánto más oscuro está — esta clase
    cierra ese hueco con `FilterTools.compute_histogram()`
    (`framework/processing/filter_tools.py`), en vez de asumir a ciegas que
    "cruzar la puerta = está oscuro".

    AUD-646 — regresión de AUD-645, encontrada revisando las propias
    capturas del README (`unit7_histograma_despues.png`,
    `unit7_sobel_contorno_despues.png`): la medición y el factor de
    `adjust_brightness` estaban bien (54/255 medido en la sala, 86.9/255
    corregido), pero la ACCIÓN de juego era un `overlay` BLANCO
    `(255,255,255,alpha)` con `alpha` hasta 132/255 (~52%) blitteado en
    `dibujar_ui` sobre TODO el fotograma — ladrillos, HUD y letreros
    incluidos — mientras el jugador seguía adentro. El resultado no era
    "adaptación a la penumbra", era la pantalla entera lavada/pálida,
    destruyendo la ambientación 0.58/0.78 que el dueño calibró jugando en
    AUD-633. Dos correcciones, ambas necesarias:
      1. El overlay ahora es CÁLIDO `(255, 230, 190)` (luz tibia, no niebla
         blanca) y su alpha tiene un tope duro de `ALPHA_MAXIMO = 36`
         (~14%, ver `analizar_si_hace_falta`) — sutil por diseño, nunca un
         velo.
      2. Se aplica al final de `Stage1_2_LaSoda.dibujar_mundo()` (mundo YA
         pintado por completo: entidades, contorno de alerta, puerta,
         marco), NUNCA en `dibujar_ui` — así el HUD y los letreros de esa
         clase quedan siempre fuera del teñido. Ver el comentario en
         `dibujar_mundo` para el porqué exacto de ese punto.
      3. `UMBRAL_LUMINANCIA` sube de 90 a 70 (con `LUMINANCIA_OBJETIVO`
         bajado de 115 a 90 en consecuencia) porque a 90 el umbral era tan
         generoso que casi cualquier interior lo cruzaba; medido contra el
         mapa real (`TestUmbralLuminanciaSalaYCocina`): la sala da
         ~55-62/255 (sigue disparando, correcto) y la cocina ~74-78/255
         (con `valor=0.78` en el .tmx, ya está bien iluminada para
         trabajar — NUNCA debe dispararse ahí, y con el umbral en 70 no lo
         hace, con margen).

    Disparo, una sola vez por vida de la escena (no cada fotograma): apenas
    `room` pasa a "interior", `analizar_si_hace_falta` reduce el fotograma
    YA DIBUJADO a una muestra chica (`ANCHO_MUESTRA`x`ALTO_MUESTRA`, ~1/64
    de los 800x600 reales) y llama a `FilterTools.compute_histogram()` sobre
    esa muestra — la luminancia media (`_luminancia_media`, promedio
    ponderado del histograma `luminance`) es la cifra que decide todo lo que
    sigue. Si cae por debajo de `UMBRAL_LUMINANCIA`:
      1. `FilterTools.adjust_brightness()` corre UNA vez sobre la misma
         muestra chica para calcular qué factor hace falta para acercarse a
         `LUMINANCIA_OBJETIVO` (medido de nuevo con `compute_histogram`, no
         supuesto) — esas dos cifras (antes/después) son las que reporta el
         README; el `factor` sigue siendo la medida "honesta" de cuánto
         hace falta corregir, aunque el overlay que en verdad se ve en
         juego quede acotado por `ALPHA_MAXIMO` (ver punto AUD-646 arriba).
      2. Ese factor se hornea en un `overlay` cálido translúcido de
         800x600, calculado una sola vez y reutilizado cada fotograma
         (`dibujar_overlay` sólo hace un `Surface.blit`) — el juego NUNCA
         vuelve a llamar `compute_histogram`/`adjust_brightness` sobre el
         fotograma completo, así que el costo por fotograma después del
         cruce es el de un blit chico, no el de una conversión a numpy de
         800x600 px.
      3. `Events.SHOW_MESSAGE` avisa al jugador — la misma cola que ya usa
         `_PuertaDelCocinero`/`_RecompensaDePickup` (ver esas clases).

    Se reconstruye en cada `on_stage_start()` (mismo criterio que
    `_objetivo_cocinero`): si el jugador muere antes de cruzar la puerta y
    reaparece afuera, tiene que poder volver a medir al cruzar de nuevo.
    """

    #: Luminancia media (0-255, canal `luminance` de `compute_histogram`)
    #: por debajo de la cual el cuarto se lee "oscuro". AUD-646 lo sube de
    #: 90 a 70 — medido contra el mapa real (`TestUmbralLuminanciaSalaY
    #: Cocina` en test_la_soda.py): la sala da ~55-62/255 (bajo el nuevo
    #: umbral, sigue disparando) y la cocina ~74-78/255 (`valor=0.78` en
    #: el .tmx: con 90 de umbral la cocina también quedaba adentro, con
    #: margen chico; con 70 queda afuera con margen de sobra).
    UMBRAL_LUMINANCIA: float = 70.0
    #: Luminancia media que `adjust_brightness` intenta alcanzar. AUD-646
    #: la baja de 115 a 90 en la misma proporción que UMBRAL_LUMINANCIA
    #: (mismo ratio objetivo/umbral ~1.28 que antes) — el `factor`
    #: resultante se sigue reportando entero (ver README), aunque el
    #: overlay real quede acotado aparte por ALPHA_MAXIMO.
    LUMINANCIA_OBJETIVO: float = 90.0
    #: `adjust_brightness` valida `factor` en [0.0, 4.0] (filter_tools.py:74);
    #: 1.6 es el tope propio de esta clase para no lavar la escena entera.
    FACTOR_MAXIMO: float = 1.6
    #: AUD-646 — tope duro de opacidad del overlay de juego, 36/255 ≈ 14%.
    #: Independiente de FACTOR_MAXIMO: ese factor sigue siendo la medida
    #: "honesta" de cuánto haría falta corregir la luminancia (se reporta
    #: en el README), pero la ACCIÓN visible en juego —lo que antes de
    #: AUD-646 lavaba la pantalla entera con alpha hasta 132/255 (~52%)—
    #: nunca puede superar este tope, sea cual sea el factor calculado.
    ALPHA_MAXIMO: int = 36
    #: Muestra reducida para abaratar compute_histogram/adjust_brightness:
    #: 100x75 son ~7500 px contra los 480000 del fotograma completo.
    ANCHO_MUESTRA: int = 100
    ALTO_MUESTRA: int = 75
    #: AUD-646 — acortado (antes "Está muy oscuro aquí adentro..."): el
    #: overlay ahora es sutil, el aviso no necesita ser tan insistente.
    MENSAJE: str = "Está oscuro aquí..."
    DURACION_MENSAJE: float = 2.5

    def __init__(self) -> None:
        self._medido: bool = False
        self.luminancia_antes: float | None = None
        self.luminancia_despues: float | None = None
        self.factor_aplicado: float = 1.0
        self.pixeles_muestra: int = 0
        self._overlay: pygame.Surface | None = None
        self.ms_medidos: float = 0.0

    @staticmethod
    def _luminancia_media(histograma: dict[str, object]) -> float:
        """Promedio ponderado del histograma de luminancia (256 bins) —
        mismo cálculo tanto para la muestra real del juego como para
        cualquier superficie sintética de prueba."""
        bins = histograma["luminance"]
        total = int(histograma["total_pixels"])  # type: ignore[arg-type]
        if total <= 0:
            return 0.0
        return float(np.dot(bins, np.arange(256))) / total

    def analizar_si_hace_falta(
        self, mundo: pygame.Surface, cuarto: str, event_bus: EventBus,
    ) -> None:
        if self._medido or cuarto != "interior":
            return
        self._medido = True
        inicio = time.perf_counter()
        muestra = pygame.transform.smoothscale(
            mundo, (self.ANCHO_MUESTRA, self.ALTO_MUESTRA),
        )
        histograma = FilterTools.compute_histogram(muestra)
        self.pixeles_muestra = int(histograma["total_pixels"])  # type: ignore[arg-type]
        luminancia = self._luminancia_media(histograma)
        self.luminancia_antes = luminancia
        if luminancia < self.UMBRAL_LUMINANCIA:
            factor = min(
                self.FACTOR_MAXIMO,
                self.LUMINANCIA_OBJETIVO / max(luminancia, 1.0),
            )
            corregida = FilterTools.adjust_brightness(muestra, factor)
            self.luminancia_despues = self._luminancia_media(
                FilterTools.compute_histogram(corregida),
            )
            self.factor_aplicado = factor
            # AUD-646 — escalado para que el tope ALPHA_MAXIMO se alcance
            # justo en FACTOR_MAXIMO (0.6 de sobra sobre 1.0 * 60 = 36): el
            # overlay sube en proporción a cuánto factor hizo falta, nunca
            # más allá del tope, en vez del alpha hasta 132/255 (~52%) de
            # AUD-645 que lavaba la pantalla entera.
            alpha = max(0, min(self.ALPHA_MAXIMO, int((factor - 1.0) * 60)))
            overlay = pygame.Surface(
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA,
            )
            # AUD-646 — cálido (255,230,190), no blanco: una corrección de
            # brillo honesta se ve como más luz tibia entrando, no como un
            # velo blanco lavando ladrillos y HUD por igual (la regresión
            # de AUD-645, ver el docstring de la clase).
            overlay.fill((255, 230, 190, alpha))
            # AUD-645 — `convert_alpha()` una sola vez, acá, no en cada
            # blit: una Surface SRCALPHA sin convertir usa la ruta de blit
            # por software de SDL (mucho más lenta a 800x600 por
            # fotograma); convertida, `dibujar_overlay` es un blit de
            # superficie nativa. Medido con `sc.update+dibujar_mundo+
            # dibujar_ui` (ver README, Unidad VII): sin este
            # `convert_alpha()` el promedio de 100 fotogramas subía ~1.1 ms
            # sobre la base sin la Unidad VII; con él, la suba queda muy
            # por debajo de ese margen.
            self._overlay = overlay.convert_alpha()
            event_bus.emit(
                Events.SHOW_MESSAGE, text=self.MENSAJE, duration=self.DURACION_MENSAJE,
            )
        else:
            self.luminancia_despues = luminancia
            self.factor_aplicado = 1.0
            self._overlay = None
        self.ms_medidos = (time.perf_counter() - inicio) * 1000.0

    def dibujar_overlay(self, surface: pygame.Surface) -> None:
        """Costo por fotograma de esta clase después del cruce: este único
        `blit` — nada de numpy ni de `FilterTools` corre más de una vez."""
        if self._overlay is not None:
            surface.blit(self._overlay, (0, 0))


class _ContornoDeAlerta:
    """Unidad VII — `FilterTools.sobel_edge()` decide cuándo un enemigo
    muestra un "contorno de alerta" al caer a ≤25% de vida.

    Le corre Sobel al SPRITE PROPIO de la entidad (su frame actual, ver
    `_recorte_de_la_entidad`) una sola vez por enemigo — cacheado por
    `id(entity)`, nunca recalculado mientras la vida siga por debajo del
    umbral. `pixeles_borde` (cuántos píxeles de la magnitud de gradiente
    superan el umbral efectivo, ver `_umbral_adaptativo`) es la cifra que
    decide si de verdad hay una silueta reconocible que resaltar: un
    recorte vacío o fuera de cámara no la tiene, y no se dibuja nada — el
    procesamiento filtra falsos positivos, no sólo decora.

    AUD-646 — regresión de AUD-645: `unit7_sobel_contorno_detalle_
    despues.png` mostraba un bloque rosa SÓLIDO del tamaño del rect del
    enemigo tapando al ratón, no un contorno. Diagnosticado con evidencia
    (`Claude - Uso General/previews/AUD646_sobel_debug_*.png`,
    `AUD646_v2_*.png`), tres causas, la primera con diferencia la que de
    verdad producía el bloque:

    1. **La causa dominante — `BLEND_RGBA_ADD` no pesa por alpha.**
       `_medir` (AUD-645) pintaba TODOS los píxeles del recorte con el
       mismo color `(255,40,30)` y sólo variaba su ALPHA (magnitud donde
       superaba el umbral, 0 en el resto) — asumiendo que blitear con
       `special_flags=pygame.BLEND_RGBA_ADD` iba a usar ese alpha como
       peso de mezcla, igual que un blit normal. No es así: `BLEND_RGBA_
       ADD` SUMA los canales R,G,B (y A) del origen al destino tal cual,
       sin escalar por alpha — comprobado a mano (`pygame.Surface.blit`
       con `special_flags=BLEND_RGBA_ADD`): un píxel con alpha=0 sumó
       exactamente el mismo `(255,40,30)` que uno con alpha=255. Con el
       color de TODOS los píxeles del recorte fijado en rojo/rosa (sólo
       el alpha cambiaba, y el alpha no pesaba nada), el resultado era
       necesariamente un bloque sólido del tamaño íntegro del recorte,
       sin importar cuántos píxeles hubiera "contado" como borde. Arreglo:
       blit normal (sin `special_flags`), que sí honra el alpha
       per-píxel de una `Surface(..., pygame.SRCALPHA)`.
    2. **El recorte salía de la pantalla, no del sprite.** `_medir`
       recortaba `surface.subsurface(entity.rect)` — el fotograma YA
       dibujado. El rect de colisión del ratón (24×28) es bastante más
       grande que su sprite real (16×12): `EnemyBase.draw()` lo centra
       horizontal y lo apoya abajo, dejando piso/pared visibles arriba y
       a los costados DENTRO del propio recorte. Sobel encontraba ahí
       bordes de piso/pared ajenos al bicho.
    3. **El propio sprite, aislado, ya es denso.** Incluso recortando
       sólo el frame del ratón (16×12) y componiéndolo sobre negro (no
       sobre el fondo), `UMBRAL_MAGNITUD=40` solo deja **53.6%** del
       recorte "opaco" (103/192 px, medido) — el detalle interno del
       propio pixel art (orejas, cola, sombreado) a esa resolución ya
       tiene bordes internos densos. Sin nada más, seguiría siendo un
       relleno, no un contorno.

    Arreglo para (2) y (3): `_recorte_de_la_entidad` usa el `frame` actual
    de `entity._sprite_frames` (mismo `anim_key`/índice/orientación que
    `EnemyBase.draw()` ya eligió para pintarlo), compuesto sobre un fondo
    negro — `sobel_edge()` sólo lee RGB e ignora alpha (filter_tools.py:
    154), así que componer sobre negro es la única forma de que el área
    transparente del sprite no aporte gradiente falso. Y
    `_umbral_adaptativo` sólo sube el umbral (al percentil de la propia
    magnitud que hace falta) cuando el umbral base deja más de
    `AREA_DISPARA_ADAPTATIVO` (50%) del recorte opaco, hasta bajar a
    `AREA_MAXIMA_CONTORNO` (30%) o menos — un contorno de verdad, no un
    relleno, reportando las cifras reales (ver README).

    Si la entidad no tiene sprite propio cargado (placeholder sin arte),
    `_recorte_de_la_entidad` cae al recorte viejo de pantalla: el contorno
    sale del borde de su rectángulo, no de una silueta — aceptable a falta
    de arte real (no le pasa a ningún enemigo de este mapa: todos cargan
    sprites propios en `_load_extra_sprites`, ver `entities.py`).
    """

    UMBRAL_VIDA: float = 0.25
    #: Por debajo de esta magnitud de gradiente (0-255) se descarta como
    #: ruido de compresión/antialiasing, no un borde real del sprite.
    UMBRAL_MAGNITUD: int = 40
    #: AUD-646 — si UMBRAL_MAGNITUD por sí solo deja más de esta fracción
    #: del recorte "opaca" (un pixel-art chico ya es denso, ver el
    #: docstring de la clase), `_umbral_adaptativo` sube el umbral.
    AREA_DISPARA_ADAPTATIVO: float = 0.50
    #: Área máxima que debe ocupar el contorno tras subir el umbral -- un
    #: contorno de verdad alrededor del bicho, no un relleno.
    AREA_MAXIMA_CONTORNO: float = 0.30
    #: Mínimo de píxeles de borde para considerar que hay una silueta real
    #: que alertar (evita marcar un recorte vacío/transparente).
    MIN_PIXELES_BORDE: int = 12
    COLOR: tuple[int, int, int] = (255, 40, 30)

    def __init__(self) -> None:
        # id(entity) -> (contorno coloreado con alpha = magnitud, píxeles de
        # borde, esquina superior-izquierda de pantalla donde se recortó)
        # o (None, 0, None) cuando ya se midió y no había silueta real que
        # marcar -- evita reintentar la medición cada fotograma en ese caso.
        self._cache: dict[int, tuple[pygame.Surface | None, int, tuple[int, int] | None]] = {}
        self.ms_medidos: float = 0.0
        #: AUD-646 — porcentaje de área que terminó ocupando el último
        #: contorno medido (0.0-1.0), para reportar/depurar
        #: `_umbral_adaptativo` sin tener que recalcularlo aparte.
        self.ultimo_porcentaje_area: float = 0.0

    def actualizar_y_dibujar(
        self, surface: pygame.Surface, stage_data: object, offset: pygame.Vector2,
    ) -> None:
        if stage_data is None:
            return
        vivos: set[int] = set()
        for entity in stage_data.entity_list:  # type: ignore[attr-defined]
            if not (isinstance(entity, EnemyBase) and entity.is_alive):
                continue
            pct = entity.current_health / max(entity.max_health, 0.001)
            if pct > self.UMBRAL_VIDA:
                continue
            eid = id(entity)
            vivos.add(eid)
            if eid not in self._cache:
                self._medir(surface, entity, offset, eid)
            contorno, _, topleft = self._cache.get(eid, (None, 0, None))
            if contorno is None or topleft is None:
                continue
            # AUD-646 — blit NORMAL, sin special_flags: BLEND_RGBA_ADD (lo
            # que usaba AUD-645) suma los canales R,G,B del origen al
            # destino tal cual, SIN pesarlos por alpha -- comprobado a
            # mano, un píxel con alpha=0 sumaba exactamente el mismo color
            # que uno con alpha=255. Con el color de `contorno` fijo en
            # rojo/rosa y sólo el alpha variando por píxel (ver `_medir`),
            # ese blend pintaba el recorte ENTERO al mismo tono sin
            # importar la magnitud real -- el bloque sólido que reportó el
            # dueño. Un blit normal sí honra el alpha per-píxel de una
            # `Surface(..., pygame.SRCALPHA)`: transparente donde no hay
            # borde, opaco donde sí.
            surface.blit(contorno, topleft)
        # Entidades que ya no califican (murieron o se curaron por encima
        # del umbral) no necesitan seguir ocupando la caché.
        for eid_viejo in list(self._cache.keys()):
            if eid_viejo not in vivos:
                self._cache.pop(eid_viejo, None)

    @staticmethod
    def _componer_sobre_negro(frame: pygame.Surface) -> pygame.Surface:
        """AUD-646 — `FilterTools.sobel_edge()` sólo lee RGB (`array3d`,
        filter_tools.py:154) e ignora el canal alpha por completo, así que
        correrlo directo sobre un `frame` con transparencia real mide
        gradiente contra lo que sea que haya ahí guardado en el PNG (a
        menudo basura o negro, según cómo se exportó) — un resultado que
        no tiene nada que ver con lo que el jugador ve. Componer sobre un
        fondo NEGRO opaco primero (`Surface.blit` con alpha SÍ blende de
        verdad) es lo que convierte "transparente" en "un color de fondo
        conocido y uniforme", para que el único gradiente real que quede
        sea el de la silueta del sprite contra ese fondo."""
        negro = pygame.Surface(frame.get_size())
        negro.fill((0, 0, 0))
        negro.blit(frame, (0, 0))
        return negro

    @staticmethod
    def _recorte_de_la_entidad(
        surface: pygame.Surface, entity: EnemyBase, rect_mundo: pygame.Rect,
        offset: pygame.Vector2, r: pygame.Rect,
    ) -> tuple[pygame.Surface, tuple[int, int]]:
        """El recorte que de verdad hay que auditar con Sobel: el sprite
        PROPIO de la entidad (su frame actual, misma orientación que ya
        eligió `EnemyBase.draw()` para pintarlo), compuesto sobre un fondo
        negro — no el fotograma de pantalla. Ver el punto 2 del docstring
        de la clase para el porqué exacto (el rect de colisión trae piso/
        pared de regalo que `surface.subsurface()` capturaba también).
        `sobel_edge()` sólo lee RGB e ignora el canal alpha
        (filter_tools.py:154) — componer sobre negro es la única forma de
        que el área transparente del sprite no aporte gradiente falso
        contra lo que sea que haya detrás en el mundo ese fotograma.

        Devuelve `(recorte, topleft)` — `topleft` es dónde blitear el
        contorno resultante para que caiga exactamente sobre el sprite tal
        como lo pintó `EnemyBase.draw()` (mismo cálculo de `ox`/`oy` que
        ese método: centrado horizontal, apoyado abajo).
        """
        anim_key = entity._get_animation_state()
        frames = entity._sprite_frames.get(anim_key)
        if frames:
            idx = min(entity._animation_frame, len(frames) - 1)
            frame = (
                get_pool().get_flipped_frames(frames)[idx]
                if entity.facing_direction < 0 else frames[idx]
            )
            negro = _ContornoDeAlerta._componer_sobre_negro(frame)
            ox = (rect_mundo.width - entity._sprite_fw) // 2
            oy = rect_mundo.height - entity._sprite_fh
            topleft = (
                int(rect_mundo.x - offset.x) + ox,
                int(rect_mundo.y - offset.y) + oy,
            )
            return negro, topleft
        # Placeholder sin arte propio (no le pasa a ningún enemigo de este
        # mapa hoy) -- recorte viejo de pantalla: el contorno sale del
        # borde de su rectángulo, no de una silueta real, pero es lo mejor
        # disponible sin arte (ver el docstring de la clase).
        return surface.subsurface(r).copy(), r.topleft

    @classmethod
    def _umbral_adaptativo(cls, magnitud: np.ndarray) -> tuple[float, int, float]:
        """AUD-646 — devuelve `(umbral_efectivo, pixeles_borde,
        porcentaje_area)`.

        `UMBRAL_MAGNITUD` (40) aplicado al sprite propio de un pixel-art
        chico (16×12 en `WalkerRaton_01`) por sí solo deja más de la mitad
        del recorte "opaco" (medido: 103/192 = 53.6%) — el propio detalle
        del dibujo (orejas, cola, sombreado) ya es denso a esa resolución.
        Eso seguiría siendo un relleno, no un contorno, aunque ya no
        viniera del fondo (ver el punto 3 del docstring de la clase). Sólo
        cuando el umbral base deja más de `AREA_DISPARA_ADAPTATIVO` (50%)
        del recorte opaco, se prueban percentiles crecientes de la propia
        magnitud (70, 75, ..., 95) hasta encontrar el primero que recorta
        el área a `AREA_MAXIMA_CONTORNO` (30%) o menos — el percentil MÁS
        BAJO que cumple, para perder el mínimo detalle posible. Si ninguno
        alcanza (magnitud casi uniforme), se queda con el más agresivo
        probado (95) en vez de fallar.
        """
        area = magnitud.size
        umbral = float(cls.UMBRAL_MAGNITUD)
        pixeles = int(np.count_nonzero(magnitud > umbral))
        if area == 0:
            return umbral, pixeles, 0.0
        porcentaje = pixeles / area
        if porcentaje <= cls.AREA_DISPARA_ADAPTATIVO:
            return umbral, pixeles, porcentaje
        for percentil in range(70, 100, 5):
            candidato = max(umbral, float(np.percentile(magnitud, percentil)))
            pixeles_candidato = int(np.count_nonzero(magnitud > candidato))
            porcentaje_candidato = pixeles_candidato / area
            if porcentaje_candidato <= cls.AREA_MAXIMA_CONTORNO:
                return candidato, pixeles_candidato, porcentaje_candidato
        return candidato, pixeles_candidato, porcentaje_candidato

    def _medir(
        self, surface: pygame.Surface, entity: EnemyBase,
        offset: pygame.Vector2, eid: int,
    ) -> None:
        rect_mundo = entity.rect
        r = pygame.Rect(
            int(rect_mundo.x - offset.x), int(rect_mundo.y - offset.y),
            rect_mundo.width, rect_mundo.height,
        ).clip(surface.get_rect())
        if r.width <= 0 or r.height <= 0:
            self._cache[eid] = (None, 0, None)
            return
        inicio = time.perf_counter()
        recorte, topleft = self._recorte_de_la_entidad(surface, entity, rect_mundo, offset, r)
        bordes = FilterTools.sobel_edge(recorte)
        magnitud = pygame.surfarray.array3d(bordes)[:, :, 0]
        umbral, pixeles_borde, self.ultimo_porcentaje_area = self._umbral_adaptativo(magnitud)
        self.ms_medidos = (time.perf_counter() - inicio) * 1000.0
        if pixeles_borde < self.MIN_PIXELES_BORDE:
            self._cache[eid] = (None, pixeles_borde, None)
            return
        ancho, alto = magnitud.shape
        rgb = np.zeros((ancho, alto, 3), dtype=np.uint8)
        rgb[:, :, 0] = self.COLOR[0]
        rgb[:, :, 1] = self.COLOR[1]
        rgb[:, :, 2] = self.COLOR[2]
        contorno = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.surfarray.blit_array(contorno, rgb)
        alpha_view = pygame.surfarray.pixels_alpha(contorno)
        # AUD-645 — el alpha usa el MISMO umbral (efectivo, ver
        # `_umbral_adaptativo`) que ya filtró `pixeles_borde` (arriba):
        # sin este `np.where`, un gradiente débil igual pintaba algo de
        # alpha -- contar una cosa y pintar otra distinta era parte de la
        # causa original. Ahora sólo los píxeles que de verdad se
        # contaron como "borde" se colorean, y AUD-646 hace que ese alpha
        # por fin se respete al blitear (ver `actualizar_y_dibujar`).
        alpha_view[:, :] = np.where(
            magnitud > umbral, np.clip(magnitud, 0, 255), 0,
        ).astype(np.uint8)
        del alpha_view  # libera el lock de superficie que arma pixels_alpha
        self._cache[eid] = (contorno, pixeles_borde, topleft)


class _MarcoDeLaPuerta:
    """AUD-629 — hace que el jugador se PIERDA detrás del vano al cruzarlo,
    en vez de quedar dibujado encima de él.

    El problema de fondo (diagnóstico AUD-627 §3): `FG_Overlay` no puede
    ocluir al jugador porque `DrawingSystem.draw()` pinta TODAS las capas de
    tiles del .tmx de una sola pasada — incluida `FG_Overlay`, pese al
    nombre — antes de llegar a las entidades. Ningún tile del mapa, por
    "delante" que se declare en Tiled, puede tapar un sprite. El único
    gancho real para dibujar por encima es el que esta misma stage ya usa
    para la barra de vida del enemigo y las luciérnagas: sobreescribir
    `dibujar_mundo()` (AUD-643 — antes `draw()`, ver el docstring de
    `Stage1_2_LaSoda.dibujar_mundo` para el porqué del cambio), llamar a
    `super().dibujar_mundo(surface)` primero (mapa + entidades) y pintar
    después.

    Esta clase repinta, en ese momento posterior, el mismo hueco oscuro que
    ya pinta `BG_Near` sobre el vano (columnas 149-152 — ver `_RoomTransition`
    y la fachada de AUD-629). Mientras nadie cruza es visualmente redundante
    con ese tile de fondo; la única razón de que exista es que ESTA copia se
    dibuja por encima de las entidades y la de `BG_Near` no. El resultado:
    el jugador entra al vano y desaparece detrás del marco en vez de quedar
    pintado sobre la puerta.

    Separada de `_RoomTransition` a propósito, con el mismo criterio de una
    responsabilidad por clase que ya siguen `_FireflyField`/`_RoomTransition`
    en este archivo: `_RoomTransition` sólo sabe de fundidos y teletransporte,
    no de cómo se ve el vano. El día que haga falta una hoja de puerta
    animada (abrirse/cerrarse) en vez de esta versión estática, el cambio
    entra acá sin tocar la lógica de la transición.
    """

    # Vano en coordenadas de mundo: columnas 149-152 (x=2384-2448, 64px de
    # ancho) por filas 33-36 (y=528-592, 64px de alto — el hueco oscuro del
    # tile 500 más la base de piedra del tile 486 debajo). Mismo rango que
    # pinta `BG_Near` en el .tmx (ver AUD-629); si la fachada se vuelve a
    # mover, este rect tiene que moverse con ella.
    RECT: pygame.Rect = pygame.Rect(2384, 528, 64, 64)

    # Más oscuro que el promedio del tile 500 (~37,24,17): tiene que leerse
    # como un vacío real, no como una repintada del mismo tile de fondo.
    COLOR_UMBRAL: tuple[int, int, int] = (10, 8, 14)
    # Mismo tono que la columna ocre (gid 490) que ya enmarca la puerta en
    # el .tmx — muestreado de tileset_soda_real.png, local id 5.
    COLOR_MARCO: tuple[int, int, int] = (159, 123, 74)
    GROSOR_MARCO: int = 4  # px de las jambas y el dintel

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        r = self.RECT.move(-int(offset.x), -int(offset.y))
        if not surface.get_rect().colliderect(r):
            return  # fuera de cámara -- no hay nada que tapar este frame
        pygame.draw.rect(surface, self.COLOR_UMBRAL, r)
        # Dintel: barra superior, donde el techo de la fachada se apoya.
        pygame.draw.rect(
            surface, self.COLOR_MARCO,
            (r.left, r.top, r.width, self.GROSOR_MARCO),
        )
        # Jambas: tiras verticales en los dos bordes internos del vano —
        # dan la lectura de "marco" en vez de un simple rectángulo oscuro.
        pygame.draw.rect(
            surface, self.COLOR_MARCO,
            (r.left, r.top, self.GROSOR_MARCO, r.height),
        )
        pygame.draw.rect(
            surface, self.COLOR_MARCO,
            (r.right - self.GROSOR_MARCO, r.top, self.GROSOR_MARCO, r.height),
        )


class _FireflyField:
    """Luciérnagas del camino exterior — enjambre de partículas amarillas
    que flotan despacio y titilan. El titileo sale gratis de que cada
    partícula vive poco (2.5-4.5s) y aparece/desaparece en un instante al
    nacer/morir (ParticleEmitter.draw dibuja con pygame.draw.rect, que no
    hace blending de alfa real sobre la superficie principal): con varias
    encendidas a la vez naciendo y muriendo en momentos distintos, el
    efecto colectivo se ve como parpadeo real, sin necesidad de un shader
    de brillo aparte.

    Acotado al rango x del camino exterior — el interior nunca ve
    luciérnagas simplemente porque nunca se genera una ahí, no hace falta
    ninguna lógica de detección de zona.
    """

    COLOR: tuple[int, int, int] = (255, 230, 120)
    RATE: float = 3.0  # partículas nuevas por segundo
    X_RANGE: tuple[float, float] = (0.0, _RoomTransition.ROOM_LIMIT_X)
    Y_RANGE: tuple[float, float] = (420.0, 585.0)

    def __init__(self) -> None:
        self._emitter = ParticleEmitter()
        self._timer: float = 0.0

    def update(self, dt: float) -> None:
        self._timer += dt
        interval = 1.0 / self.RATE
        while self._timer >= interval:
            self._timer -= interval
            self._spawn()
        self._emitter.update(dt)

    def _spawn(self) -> None:
        x = random.uniform(*self.X_RANGE)
        y = random.uniform(*self.Y_RANGE)
        angle = random.uniform(0, 360)
        self._emitter.emit_directed(
            x, y, angle=angle, speed=random.uniform(4.0, 10.0),
            count=1, lifetime=random.uniform(2.5, 4.5),
            size=(1, 2), color=self.COLOR, spread=180.0,
            gravity=0.0, friction=0.3,
        )

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        self._emitter.draw(surface, offset)


class _RecompensaDePickup:
    """Cierra el circuito de `EventBus` que `InteractableSystem` deja abierto
    para los 5 `Recogible` del mapa (F4.1) — la "interacción propia vía
    `EventBus`" de la Unidad VI (Evaluación Práctica II).

    El hueco, verificado leyendo el motor (AUD-632): `InteractableSystem.
    _recoger()` marca `recogido=True` y emite `EVENTO_RECOGIDO` (=
    `"INTERACT_ITEM_PICKED"`, `interactable_system.py:46,127-138`) con
    `item_id`/`cantidad`/`pos`, pero el único suscriptor del framework
    —`_on_item_picked` en `stage_parts/senales.py:52-88`— sólo sabe hablar
    con `Inventory`: como ninguno de los `item_id` de este mapa
    (`vaso_soda`, `cupon_descuento`, `servilletas_cocina`, `taza_cafe`,
    `combo_estudiantil`) está en su catálogo (`inventory.py:_ITEM_DEFS`),
    `collect()` devuelve `False` y el objeto termina en el llavero —una
    bolsa de llaves que nadie mira— sin que suba ningún número ni aparezca
    ningún texto. Es comportamiento del motor y no un bug de este nivel: los
    `fragmento_N` del `stage0` del profe se comportan igual.

    Qué hace al recoger uno de los 5 `Pickup` del mapa (decisión del dueño):
    (a) sube el marcador de PUNTOS del HUD —nunca el contador de monedas 🟡
        ni `Inventory`: no se toca la economía del motor, sólo se le da a
        cada recogible la recompensa visible que hoy no tiene—, con la
        única API pública de `ScoreSystem` que permite sumar sin tocar
        `score_system.py` (que sólo suma con `ENEMY_DIED`): leer `.score` y
        volver a fijarlo con `set_score()` (`score_system.py:194-201`, ya
        pública para AUD-292 — restaurar el puntaje de una partida
        cargada); `actualizaciones.py:165` ya lee `ScoreSystem.score` cada
        fotograma para el HUD, así que no hace falta empujar nada aparte;
    (b) muestra el `mensaje` de la propiedad del pickup por la MISMA vía que
        ya usa `MessageTrigger` (`hazard_system.py:109-111`):
        `Events.SHOW_MESSAGE`, que ya escucha `MessageBox`
        (`engine/ui/message_box.py:72,82-88`);
    (c) sonido: el motor no declara ningún `Events.SFX_ITEM_PICKUP` /
        `SFX_PICKUP` / `SFX_COLLECT` (comprobado contra
        `engine/core/events.py` entero) — no se inventa uno.

    Por qué se filtra por `stage_data.recogibles` y no por cualquier
    `EVENTO_RECOGIDO`: el mismo evento lo emite también una moneda que
    suelta un enemigo al morir (`stage_parts/economia.py:_soltar_botin`,
    `item_id="coin"`, sin `mensaje`). Esas monedas se anexan sólo a
    `InteractableSystem.recogibles` —la copia viva que arranca de
    `stage_data.recogibles` y después crece (`InteractableSystem.__init__`
    hace `list(...)`, una copia, no la misma lista)— nunca al snapshot que
    `StageLoader` arma del `.tmx` (`stage_scene.py:542-549`). Buscar el
    `item_id` recibido en ese snapshot es, por construcción, "es uno de los
    5 objetos que puso el mapa"; sin este filtro cada moneda del juego
    normal también pagaría puntos de pickup.

    Por qué un `set` de `item_id` ya premiados: `StageScene.on_enter()` —y
    por lo tanto `respawn()`, mismo mecanismo que documenta AUD-613 para el
    cartel de bienvenida— vuelve a llamar `StageLoader.load()` y reconstruye
    `_stage_data` entero, incluidos los 5 `Recogible` con `recogido=False`
    de nuevo. Sin este registro, una partida con muertes/respawns podría
    cobrar el mismo pickup más de una vez. Vive en esta instancia y no en
    `_stage_data` por la misma razón que `_carteles_disparados` (ver
    `Stage1_2_LaSoda.__init__`): esta instancia sobrevive al respawn,
    `_stage_data` no.
    """

    #: Puntos por pickup (AUD-636). El GDD (`docs/64_GAME_DESIGN_DOCUMENT.md`
    #: §9, tabla del HUD) declara la fila «Puntuación — Puntos por derrotas y
    #: recolección», pero el motor sólo implementa la mitad: `ScoreSystem`
    #: (`score_system.py`) escucha únicamente `ENEMY_DIED`, y `_SCORE_BY_TYPE`
    #: (líneas 53-62) sólo tiene entradas de enemigo — no hay ningún gancho de
    #: recolección; de ahí este `_RecompensaDePickup`. AUD-632 había igualado
    #: el valor más bajo de esa tabla (el `walker`, 100), pero eso cobra un
    #: souvenir de cafetería igual que derrotar al enemigo más débil del
    #: nivel. 50 en vez de 100: por debajo de cualquier entrada de
    #: `_SCORE_BY_TYPE` (100-1000) para que un pickup siempre valga menos que
    #: vencer a un enemigo, y coincide con el propio mínimo que ya usa el
    #: motor para un tipo que no reconoce (`_points_for`, `score_system.py:
    #: 100-102`, el `.get(..., 50)` de respaldo) — no es un número inventado,
    #: es el piso que el motor ya eligió para "una recompensa que cuenta, pero
    #: la más chica posible".
    PUNTOS_POR_PICKUP: int = 50
    #: Duración del cartel, en segundos (AUD-643 — bajó de 2.5 a 1.5).
    #:
    #: Medido con el recorrido de la ruta alta (`Claude - Uso General/
    #: playtest/medicion_cola_mensajes.py`): entre x=560 y x=2600 el
    #: jugador recoge hasta 3 objetos seguidos y cada uno encola DOS
    #: `SHOW_MESSAGE` — el de este cartel y, aparte, el de un
    #: `MessageTrigger_Once` cercano —, y `MessageBox` los muestra de a
    #: uno (`message_box.py:82-88,134-138`). Con 2.5s + máquina de escribir
    #: la cola tardaba ~8-9s en vaciarse; el cartel de la fachada llegaba a
    #: pantalla con el jugador ya adentro de la sala.
    #:
    #: Se ELIGIÓ acortar en vez de suprimir el cartel del pickup (opción
    #: (a) del encargo): el único otro texto que un pickup dispara es el
    #: del motor —`_on_item_picked` en `stage_parts/senales.py:52-88`—, y
    #: ese handler no muestra NINGÚN texto para un `item_id` fuera del
    #: catálogo de `Inventory` (partículas + `sfx_select` +
    #: `hud.pulso_de_recogida()`, ninguno con palabras; ver el docstring de
    #: esta clase, más arriba). Suprimir el cartel dejaría a los 5
    #: `Pickup`/`Key` del mapa sin ningún texto que diga QUÉ se recogió —
    #: los puntos ya suben en el HUD de cualquier forma, con o sin cartel,
    #: así que acortar no le cuesta nada a la recompensa numérica y sí
    #: conserva la única fuente de sabor narrativo de cada objeto.
    DURACION_MENSAJE: float = 1.5

    def __init__(self, stage: Stage1_2_LaSoda) -> None:
        self._stage = stage
        self._premiados: set[str] = set()

    def suscribir(self, bus: EventBus) -> None:
        """Se llama UNA sola vez, desde `Stage1_2_LaSoda.__init__`.

        El `EventBus` de la escena (`self.context.event_bus`) es el mismo
        objeto durante toda la vida de la escena — lo que `on_enter()`/
        `respawn()` reconstruyen es `_stage_data` y `_interactables`, no el
        bus (`stage_scene.py:410-549`) — así que no hace falta volver a
        suscribirse en cada respawn. Y aunque se llamara de más,
        `EventBus.subscribe()` es idempotente por contrato para el mismo
        método enlazado (`event_bus.py:110-133`): no duplicaría la
        recompensa.

        El manejador es un método enlazado de ESTA instancia, que
        `Stage1_2_LaSoda` mantiene viva en `self._recompensa_pickup`
        durante toda la partida — el bus sólo guarda referencias débiles
        (`event_bus.py:11-17,55-63`), así que sin ese dueño fuerte el
        recolector de basura se llevaría el manejador y el juego avisaría
        "dropping collected subscriber" sin volver a sonar ni un punto.
        """
        bus.subscribe(EVENTO_RECOGIDO, self._on_item_picked)

    def _on_item_picked(self, **data: object) -> None:
        item_id = str(data.get("item_id", ""))
        if not item_id or item_id in self._premiados:
            return
        stage_data = self._stage._stage_data
        if stage_data is None:
            return
        recogible = next(
            (r for r in stage_data.recogibles if r.item_id == item_id), None,
        )
        if recogible is None:
            # No es uno de los 5 Pickup del mapa (p. ej. "coin" de un
            # enemigo, que sólo vive en InteractableSystem.recogibles).
            return

        self._premiados.add(item_id)
        score = self._stage._score
        score.set_score(score.score + self.PUNTOS_POR_PICKUP)
        if recogible.mensaje:
            self._stage.context.event_bus.emit(
                Events.SHOW_MESSAGE, text=recogible.mensaje,
                duration=self.DURACION_MENSAJE,
            )


class _LlavesPersistentes:
    """La llave se pierde al morir (AUD-643) — mismo patrón que
    `_carteles_disparados` (ver `Stage1_2_LaSoda.__init__`), aplicado al
    llavero en vez de a los `MessageTrigger`.

    El bug, reproducido con el camino real de la stage (`respawn()`, no un
    atajo de prueba): `StageScene.on_enter()` —y por lo tanto `respawn()`—
    reconstruye `_stage_data` e `_interactables` enteros
    (`stage_scene.py:410-549`, mismo mecanismo que ya documentan
    `_RecompensaDePickup` y `_carteles_disparados` para sus propios huecos).
    Eso da un `Llavero` NUEVO —vacío— y una lista NUEVA de `Recogible` con
    `recogido=False`, incluida la llave que el jugador ya había levantado.
    El resultado, tal como lo jugó el dueño: recoger `llave_deposito`,
    morir en la cocina, reaparecer, y el cofre vuelve a pedir una llave que
    el jugador siente que ya tiene — porque la tuvo, un instante antes de
    morir.

    Por qué esta clase y no ensanchar `_RecompensaDePickup`: esa clase
    premia PUNTOS por los 5 `Pickup`/`Key` del mapa y no le importa cuál
    de ellos era; ésta sólo le importa a las llaves (`item_id` que
    empieza con `"llave_"`, el mismo prefijo que ya filtra `Stage1_2_LaSoda.
    _dibujar_iconos_interactivos` para el glifo propio) y **reinyecta**
    estado en cada arranque, una responsabilidad distinta. Igual que
    `_RecompensaDePickup`/`_PuertaDelCocinero`/`_AvisoDeBloqueo`, se
    suscribe una sola vez al mismo `EVENTO_RECOGIDO` — `EventBus.subscribe`
    es idempotente por método enlazado y el bus de la escena no se
    reconstruye en cada respawn, así que no hace falta repetirlo.

    Qué guarda y dónde se reinyecta: un `set[str]` de `item_id` de llave ya
    recogidos, en esta instancia (que `Stage1_2_LaSoda` mantiene viva a
    través de los respawns, igual que `_carteles_disparados`). `reaplicar()`
    se llama desde `on_stage_start()`, DESPUÉS de que `_interactables`/
    `_stage_data` existan (mismo orden que ya usa el reaplique de
    `_carteles_disparados` un poco más abajo en ese método): por cada
    `item_id` ya recogido, (a) se lo vuelve a meter al `Llavero` NUEVO —
    `Llavero.coger` es un `set.add`, idempotente— para que el cofre/puerta
    que lo pida lo reconozca de inmediato, sin que el jugador tenga que
    volver a caminar hasta donde estaba tirado; (b) se marca `recogido=True`
    en el `Recogible` equivalente de `stage_data.recogibles` — la MISMA
    lista (mismos objetos, no una copia) que `InteractableSystem.__init__`
    usa para poblar `.recogibles` (`list(recogibles or [])` copia el
    contenedor, no los `Recogible`) — así que este único cambio alcanza a
    las dos vistas: `InteractableSystem._recoger()` ya no vuelve a
    entregarla (`if objeto.recogido: continue`) y `_dibujar_iconos_
    interactivos` ya no vuelve a dibujar su glifo. Sin este segundo paso el
    jugador vería la llave tirada de nuevo en x=936 —contradiciendo que ya
    la lleva encima— y podría "recogerla" otra vez sin que cambiara nada.
    """

    def __init__(self, stage: Stage1_2_LaSoda) -> None:
        self._stage = stage
        self._recogidas: set[str] = set()

    def suscribir(self, bus: EventBus) -> None:
        """Una sola vez, desde `Stage1_2_LaSoda.__init__` — mismo argumento
        de idempotencia que `_RecompensaDePickup.suscribir`."""
        bus.subscribe(EVENTO_RECOGIDO, self._on_item_picked)

    def _on_item_picked(self, **data: object) -> None:
        item_id = str(data.get("item_id", ""))
        if item_id.startswith("llave_"):
            self._recogidas.add(item_id)

    def reaplicar(self) -> None:
        """Reinyecta las llaves ya recogidas — ver el docstring de la clase.

        Llamar sólo cuando `_interactables`/`_stage_data` ya existen (el
        primer arranque y cada respawn los reconstruyen ANTES de que
        `on_stage_start()` llegue a esta llamada — ver ese método)."""
        if not self._recogidas:
            return
        stage = self._stage
        interactables = getattr(stage, "_interactables", None)
        if interactables is not None:
            for item_id in self._recogidas:
                interactables.llavero.coger(item_id)
        stage_data = stage._stage_data
        if stage_data is not None:
            for recogible in stage_data.recogibles:
                if recogible.item_id in self._recogidas:
                    recogible.recogido = True


class _ObjetivoCocinero:
    """Letrero de objetivo en pantalla, con animación con easing (AUD-641).

    Evaluación Práctica II (Unidad VI) — "animación con easing disparada
    por EventBus, el estudiante define cuándo": esta clase es el disparo
    visual (el cuándo lo decide `_PuertaDelCocinero.marcar_cumplido`, más
    abajo, al recibir `Events.ENEMY_DIED`); ésta sólo sabe animarse, no
    escuchar el bus.

    Máquina de 5 fases, avanzadas por `update(dt, ...)`:
      "oculto"        -> nada se dibuja.
      "apareciendo"   -> se desliza desde arriba con `ease_out_cubic`
                         durante `DURACION_DESLIZAMIENTO` (~0.5s).
      "visible"       -> en su lugar, sin animación, mientras el cocinero
                         siga vivo.
      "cumplido"      -> texto cambiado a "CUMPLIDO", opaco, durante
                         `DURACION_QUEDARSE` (~4s).
      "desvaneciendo" -> alpha baja con `ease_out_cubic` durante
                         `DURACION_DESVANECIMIENTO`, y vuelve a "oculto".

    `Stage1_2_LaSoda` reconstruye esta clase entera en cada
    `on_stage_start()` (primer arranque y cada respawn) — mismo criterio
    que `_cocinero_vencido` (ver esa bandera en `Stage1_2_LaSoda.__init__`):
    si el cocinero reaparece vivo tras un respawn, el objetivo tiene que
    volver a "oculto" y estar listo para deslizarse de nuevo, no seguir
    mostrando "CUMPLIDO" de la vida anterior.

    Unidad VII (AUD-645) — el fondo del panel es un desenfoque real:
    `_fondo_para` recorta los píxeles del fotograma que hay DETRÁS del
    letrero (el mundo ya dibujado, no un color inventado) y les corre
    `FilterTools.apply_kernel()` con el kernel `box_blur` precargado
    (`framework/processing/filter_tools.py`, matriz en el README). El
    recorte se cachea por tamaño de panel (`_fondo_tam`) — el panel sólo
    cambia de tamaño dos veces en toda su vida (texto pendiente -> texto
    "CUMPLIDO", que mide distinto), así que la convolución corre como
    máximo dos veces por partida, nunca por fotograma.
    """

    #: Umbral de entrada a la cocina — coincide con el límite que ya usa
    #: `AmbientLightZone_Cocina`/`FrictionZone_Cocina_Trapeado` en el .tmx
    #: (x=2880), no un número inventado para esta clase.
    X_ENTRADA_COCINA: float = 2880.0
    DURACION_DESLIZAMIENTO: float = 0.5
    DURACION_QUEDARSE: float = 4.0
    DURACION_DESVANECIMIENTO: float = 0.6
    #: Cuánto más arriba de su sitio final arranca el deslizamiento, en px.
    DESPLAZAMIENTO_INICIAL: float = 40.0

    TEXTO_PENDIENTE: str = "OBJETIVO: derrota al cocinero para abrir la puerta trasera"
    TEXTO_CUMPLIDO: str = "OBJETIVO CUMPLIDO: la puerta trasera está abierta"

    #: y de pantalla del letrero ya en su sitio. El HUD ocupa la franja
    #: y≈2-60 (retrato + barras a la izquierda, puntos/monedas/reloj al
    #: centro, `hud.py`); y=84 deja aire de sobra debajo de ese bloque.
    Y_DESTINO: int = 84

    def __init__(self) -> None:
        self._fase: str = "oculto"
        self._timer: float = 0.0
        # AUD-645 — Unidad VII: fondo borroso cacheado, ver _fondo_para.
        self._fondo_borroso: pygame.Surface | None = None
        self._fondo_tam: tuple[int, int] | None = None
        self.ms_medidos_blur: float = 0.0

    # -- disparo (llamado por _PuertaDelCocinero) --------------------
    def marcar_cumplido(self) -> None:
        """El cocinero cayó: cambia de inmediato a "cumplido", sin
        importar en qué fase estuviera (incluso "oculto", por si el
        cocinero muere justo cuando el jugador entra a la cocina en el
        mismo fotograma)."""
        self._fase = "cumplido"
        self._timer = 0.0

    # -- ciclo ---------------------------------------------------------
    def update(self, dt: float, jugador_x: float | None, cocinero_vencido: bool) -> None:
        if self._fase == "oculto":
            if (
                not cocinero_vencido
                and jugador_x is not None
                and jugador_x >= self.X_ENTRADA_COCINA
            ):
                self._fase = "apareciendo"
                self._timer = 0.0
            return
        if self._fase == "apareciendo":
            self._timer += dt
            if self._timer >= self.DURACION_DESLIZAMIENTO:
                self._fase = "visible"
            return
        if self._fase == "visible":
            return
        if self._fase == "cumplido":
            self._timer += dt
            if self._timer >= self.DURACION_QUEDARSE:
                self._fase = "desvaneciendo"
                self._timer = 0.0
            return
        if self._fase == "desvaneciendo":
            self._timer += dt
            if self._timer >= self.DURACION_DESVANECIMIENTO:
                self._fase = "oculto"
            return

    # -- consulta (pruebas leen esto en vez de píxeles) ----------------
    @property
    def fase(self) -> str:
        return self._fase

    @property
    def texto_actual(self) -> str | None:
        if self._fase == "oculto":
            return None
        if self._fase in ("cumplido", "desvaneciendo"):
            return self.TEXTO_CUMPLIDO
        return self.TEXTO_PENDIENTE

    @property
    def alpha(self) -> int:
        if self._fase == "desvaneciendo":
            t = min(1.0, self._timer / self.DURACION_DESVANECIMIENTO)
            return int(255 * (1.0 - ease_out_cubic(t)))
        if self._fase == "oculto":
            return 0
        return 255

    def _offset_y(self) -> float:
        if self._fase == "apareciendo":
            t = min(1.0, self._timer / self.DURACION_DESLIZAMIENTO)
            return (1.0 - ease_out_cubic(t)) * -self.DESPLAZAMIENTO_INICIAL
        return 0.0

    # -- dibujado --------------------------------------------------
    def _fondo_para(
        self, surface_mundo: pygame.Surface, x: int, ancho: int, alto: int,
    ) -> pygame.Surface | None:
        """Unidad VII (AUD-645) — desenfoque `box_blur` real del fondo del
        letrero, cacheado por tamaño de panel (ver el docstring de la
        clase). Usa `Y_DESTINO` fijo, no la `y` animada de `_offset_y()`,
        para que el recorte no dependa de en qué fotograma exacto de la
        animación de entrada se calculó — sólo importa una vez que el
        panel ya está asentado, que es donde se ve la enorme mayoría del
        tiempo (fases "visible"/"cumplido")."""
        tam = (ancho, alto)
        if self._fondo_borroso is not None and self._fondo_tam == tam:
            return self._fondo_borroso
        rect_mundo = pygame.Rect(x, self.Y_DESTINO, ancho, alto).clip(
            surface_mundo.get_rect(),
        )
        if rect_mundo.width <= 0 or rect_mundo.height <= 0:
            return None
        inicio = time.perf_counter()
        recorte = surface_mundo.subsurface(rect_mundo).copy()
        borroso = FilterTools.apply_kernel(
            recorte, FilterTools.get_standard_kernel("box_blur"),
        )
        if borroso.get_size() != tam:
            # El recorte quedó más chico que el panel (borde de pantalla) —
            # se completa sobre un lienzo del tamaño pedido para que el
            # blit de más abajo no falle por tamaños distintos.
            lienzo = pygame.Surface(tam)
            lienzo.fill((15, 12, 10))
            lienzo.blit(borroso, (0, 0))
            borroso = lienzo
        self._fondo_borroso = borroso
        self._fondo_tam = tam
        self.ms_medidos_blur = (time.perf_counter() - inicio) * 1000.0
        return borroso

    def draw(self, surface: pygame.Surface) -> None:
        texto = self.texto_actual
        if texto is None:
            return
        fuente = _fuente_del_tema(Theme.FONT_SMALL)
        render = fuente.render(texto, True, (255, 255, 255))
        pad_x, pad_y = 12, 6
        ancho = render.get_width() + pad_x * 2
        alto = render.get_height() + pad_y * 2
        x = (settings.INTERNAL_WIDTH - ancho) // 2
        panel = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        fondo = self._fondo_para(surface, x, ancho, alto)
        if fondo is not None:
            panel.blit(fondo, (0, 0))
            velo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            velo.fill((15, 12, 10, 150))
            panel.blit(velo, (0, 0))
        else:
            panel.fill((15, 12, 10, 190))
        panel.blit(render, (pad_x, pad_y))
        panel.set_alpha(self.alpha)
        y = self.Y_DESTINO + int(self._offset_y())
        surface.blit(panel, (x, y))


class _BarraDeJefe:
    """Barra de vida del jefe (`ShooterCocinero`) en pantalla, con daño
    diferido y entrada/salida animadas con easing (AUD-650).

    Unidad VI (Evaluación Práctica II) — la misma "animación con easing
    disparada por EventBus, el estudiante define cuándo" que ya
    documenta `_ObjetivoCocinero` un poco más arriba, aplicada ahora a
    una barra de jefe: aparece la primera vez que el jugador pisa la
    cocina con el cocinero vivo (`ease_out_cubic`, igual que el
    deslizamiento del letrero), sigue la vida real del cocinero mientras
    dura el combate, y se vacía/desvanece (`ease_out_cubic`) al morir —
    `_PuertaDelCocinero._on_enemy_died` la dispara (`marcar_muerte()`),
    el mismo lugar y el mismo evento que ya dispara
    `_objetivo_cocinero.marcar_cumplido()`.

    No asume `max_health == 3`: `_fraccion_actual` siempre se calcula
    como `current_health / max_health` LEÍDOS de la instancia del
    `ShooterCocinero` en cada `update()` (nunca una constante), porque
    ese valor cambia según cómo se balancee la entidad en `entities.py`
    (fuera del alcance de este archivo).

    Por qué en y≈150 y no en y≈320 (a media pantalla, flotando sobre la
    pared de la sala — el error del intento anterior) ni tampoco con un
    desplazamiento condicional en tiempo de ejecución (lo que pedía el
    encargo si "el MessageBox choca", ver más abajo por qué no hace
    falta)
    -------------------------------------------------------------------
    El intento anterior bajó la barra a `Y_BARRA=320` razonando sobre
    `MessageBox.caja_rect()` (`message_box.py:157-173`), que devuelve
    `Rect(0, escalar(64), 800, max(escalar(56), INTERNAL_HEIGHT*0.085))`
    = `Rect(0, 160, 800, 140)` — una banda que llega hasta y=300. Ese
    razonamiento tiene un error de fondo: `caja_rect()` es la banda de
    DISEÑO que el layout RESERVA como máximo (impuesta por la maqueta,
    320px de ancho, `theme.py:124-128`), no lo que `MessageBox.draw()`
    de verdad blitea. Leyendo `draw()` (`message_box.py:194-216`): pinta
    `self.rect_del_panel()`, no `caja_rect()`. Y `rect_del_panel()`
    (`message_box.py:175-192`) es un panel angosto, centrado, del alto
    exacto del TEXTO envuelto (`banda.height` sólo aparece como tope
    máximo de ancho, nunca de alto) — con la `y` SIEMPRE igual a
    `banda.y = escalar(64) = 160` sin importar cuántas líneas tenga el
    mensaje; sólo la ALTURA crece hacia abajo con el contenido.

    Medido dos veces, no una:
      1. Código (`message_box.py:175-192`): `rect_del_panel()` devuelve
         `pygame.Rect((banda.width-ancho)//2, banda.y, ancho, alto)` —
         la `y` es literalmente `caja_rect().y`, invariante.
      2. Empírico (script ad-hoc, mismo patrón que ya usa
         `_LecturaDeLuz`/AUD-646 para medir contra el juego real): con
         la escena construida por `_construir_escena_la_soda()`,
         `pygame.time.get_ticks()` congelado (si no, el pulso de brillo
         de `drawing_system.py:305` mete ruido de reloj real ajeno al
         mensaje) y un diff de píxeles entre un fotograma sin mensaje y
         uno con el cartel real de la cocina (MSG_04_Cocina) mostrado
         por el camino real (`Events.SHOW_MESSAGE`, igual que
         `hazard_system.py:110`): el panel se pinta en
         `Rect(179, 160, 441, 33)` — y=160-193, ni cerca del y≈300 que
         asumía `Y_BARRA=320`, y bastante más abajo del y≈96-108 que
         pedía el encargo original.
      3. El letrero de `_ObjetivoCocinero` (`Y_DESTINO=84`) mide, con la
         fuente `Theme.FONT_SMALL` real, `font(17).get_height()=13` px
         de alto de línea + 12 de padding vertical: su panel ocupa
         y≈84-109.

    La pieza clave para la posición final: el TOP de `rect_del_panel()`
    es `banda.y=160`, una CONSTANTE — no depende de cuántas líneas tenga
    el mensaje ni de si está visible (`caja_rect()` siempre devuelve
    `y=160` aunque `MessageBox` esté oculto; sólo cambia si se pinta
    algo o no). Un mensaje más largo empuja el BORDE INFERIOR del panel
    hacia abajo, nunca el superior. Eso significa que basta con mantener
    `rect_total().bottom <= 160` para que la barra de jefe NUNCA se
    solape con el `MessageBox` real, sea cual sea el mensaje, visible o
    no — sin necesidad de ningún desplazamiento condicional en tiempo de
    ejecución (el encargo preveía uno, "24px hacia abajo mientras
    `_msg_box` esté visible", para el caso en que la posición calculada
    todavía pisara el panel real; con los valores elegidos abajo no pisa
    NUNCA, así que ese desplazamiento sobra — y, de hecho, "hacia abajo"
    habría ido en la dirección EQUIVOCADA: el panel real está más abajo
    que donde cae la barra, no arriba, así que empujarla hacia abajo la
    metería más adentro del panel, no la sacaría).

    La guirnalda de luces de la cocina (el otro límite que pedía el
    encargo, "por encima de la guirnalda") tampoco es donde se estimó a
    ojo (y≈155): son los objetos `Light_266/268/269/270` del `.tmx`
    (`assets/maps/stage1_2_la_soda/stage1_2_la_soda.tmx`, 16×16px, world
    y=128-176 según la luz) — con la cámara en `offset=(2560, 8)` para
    este spawn (`_construir_escena_la_soda()` + `set_spawn(2950, 560)`),
    la más alta (`y=128`) cae en pantalla en y=120-136 (`128-8` a
    `144-8`), verificado con un umbral de color sobre el fotograma real
    (no a ojo): fila por fila, y=120-135 tiene ≥590/720px del tono
    apagado del techo sin luz directa (con las bombillas como puntos
    brillantes salpicados encima) y y=136 ya vuelve a cero — corte neto.
    Es arte de MUNDO (capa `dibujar_mundo`, se mueve con la cámara), no
    UI, así que no participa de ningún `colliderect` de esta prueba; se
    la evita solo por prolijidad visual.

    El presupuesto vertical que queda, con los tres límites reales:
    letrero (84-109), guirnalda (120-136), `MessageBox` (160+) dejan dos
    huecos: 109-120 (11px, no alcanza para nada) y 136-160 (24px). Con
    `ANCHO=280`, `ALTO=10` (pedidos por el encargo) y `TEXTO="COCINERO
    DE MAL HUMOR"` (108×13px con `Theme.FONT_SMALL`), rótulo+gap+barra
    mide `GAP_TEXTO + 13 + 10` — con el `GAP_TEXTO=4` que traía la clase
    antes de este arreglo (27px) NO entra en el hueco de 24px sin tocar
    la guirnalda o el `MessageBox`. Se bajó a `GAP_TEXTO=1` (24px exactos
    — el mínimo que deja aire visible entre el texto y la barra sin
    desperdiciar el único píxel de margen que hay) y `Y_BARRA=150`, que
    da `rect_total() = Rect(260, 136, 280, 24)`:
      - top=136, tocando el borde inferior de la guirnalda (135) sin
        pisarlo — 27px por debajo del letrero (109);
      - bottom=160, tocando el borde superior REAL del `MessageBox`
        (`rect_del_panel().top`, constante) sin pisarlo — en NINGÚN
        estado, verificado en `TestBarraDeJefeYSacudida.test_la_barra_
        no_pisa_hud_letrero_ni_messagebox` contra `rect_del_panel()` (el
        rect real), no contra `caja_rect()` (el rect de diseño);
    `Y_BARRA<=152` queda como el tope que blinda contra un futuro cambio
    que la vuelva a mandar a media pantalla (ver el assert homónimo en
    la prueba de colisión).

    Daño diferido (la "barra fantasma" blanca): igual que la vida de un
    jefe en un juego de pelea, el relleno de color sigue la vida REAL al
    instante y detrás queda un segmento blanco que marca cuánta vida
    HABÍA antes del último golpe — se queda quieto `DEMORA_DIFERIDA`
    (0.25s, el número que pide el encargo) y recién ahí empieza a
    retraerse hacia la vida real con `ease_out_quad` durante
    `DURACION_RETRACCION`. Un golpe nuevo mientras el segmento ya se
    está retrayendo no lo reinicia al 100%: lo congela en el punto
    exacto donde iba (`_fraccion_diferida` en ese instante, ver
    `update`) y arranca una retracción nueva desde ahí — dos golpes
    seguidos no hacen que el fantasma "salte" hacia atrás de más de lo
    que debería.
    """

    ANCHO: int = 280
    ALTO: int = 10
    #: Tope de la barra en sí — ver el porqué de esta cifra (medida
    #: contra los rects reales, no a ojo) en el docstring de la clase.
    #: `rect_total().bottom` (Y_BARRA+ALTO=160) toca, sin pisar, el panel
    #: REAL de `MessageBox` (`rect_del_panel().top=160`, constante — ver
    #: el docstring) y `rect_total().top` (136) toca, sin pisar, el
    #: borde inferior de la guirnalda de luces de la cocina (135) —
    #: franja superior de verdad, nunca a media pantalla.
    Y_BARRA: int = 150
    #: Aire entre el rótulo y la barra — 1px, no 4: con la guirnalda de
    #: luces de la cocina y el `MessageBox` reales (ver el docstring de
    #: la clase) el hueco disponible es de sólo 24px, y `GAP_TEXTO+13
    #: (alto del rótulo)+ALTO` tiene que entrar justo ahí.
    GAP_TEXTO: int = 1

    DURACION_ENTRADA: float = 0.6
    DEMORA_DIFERIDA: float = 0.25
    #: El encargo sólo pide "se retrae con ease_out_quad", sin cifra —
    #: 0.35s deja que el tramo perdido de un golpe típico se lea con
    #: claridad antes de desvanecerse, sin quedar pegado tanto tiempo
    #: como para confundirse con la vida real que ya bajó.
    DURACION_RETRACCION: float = 0.35
    DURACION_MUERTE: float = 0.5

    TEXTO: str = "COCINERO DE MAL HUMOR"

    COLOR_MARCO: tuple[int, int, int] = (20, 16, 14)
    COLOR_FONDO: tuple[int, int, int] = (40, 10, 10)
    COLOR_DIFERIDO: tuple[int, int, int] = (235, 235, 230)
    COLOR_TEXTO: tuple[int, int, int] = (255, 255, 255)

    def __init__(self) -> None:
        # oculto -> apareciendo -> visible -> muriendo -> terminado
        self._fase: str = "oculto"
        self._timer: float = 0.0
        #: La animación de entrada (0 -> vida actual con ease_out_cubic)
        #: sólo corre la primera vez que la barra aparece en toda la
        #: vida de la escena — ver el docstring de la clase.
        self._ya_aparecio: bool = False
        self._fraccion_actual: float = 1.0
        self._fraccion_visible: float = 0.0
        self._fraccion_diferida: float = 1.0
        self._demora_restante: float = 0.0
        self._retraccion_timer: float = self.DURACION_RETRACCION
        self._retraccion_inicio: float = 1.0
        self._retraccion_destino: float = 1.0
        # Instantánea tomada al empezar a morir — de ahí decae a 0.
        self._fraccion_al_morir_visible: float = 1.0
        self._fraccion_al_morir_diferida: float = 1.0
        # AUD-650 — caché de dibujado: `rect_total()`/el rótulo (`TEXTO`
        # es una constante de clase, nunca cambia) y la propia Surface
        # del panel se recalculan UNA vez y se reutilizan cada
        # fotograma, no en cada `draw()`. Medido (`Claude - Uso General/
        # playtest/medir_costo_aud650.py`): sin este caché, crear una
        # `Surface(..., pygame.SRCALPHA)` nueva y volver a `font.render()`
        # el mismo texto en cada fotograma costaba ~0.6ms extra por
        # fotograma mientras la barra está en pantalla — por encima del
        # presupuesto de +0.5ms/fotograma; con el caché (y
        # `convert_alpha()`, mismo motivo que documenta `_LecturaDeLuz`
        # para su overlay: la ruta de blit nativa contra la de software
        # de una `SRCALPHA` sin convertir) el costo real medido baja muy
        # por debajo de ese presupuesto.
        self._rect_cache: pygame.Rect | None = None
        self._panel: pygame.Surface | None = None
        self._texto_render: pygame.Surface | None = None

    # -- consulta (pruebas y draw() leen esto, nunca píxeles) ----------

    @property
    def fase(self) -> str:
        return self._fase

    @property
    def visible(self) -> bool:
        return self._fase not in ("oculto", "terminado")

    @property
    def fraccion_visible(self) -> float:
        if self._fase == "muriendo":
            t = ease_out_cubic(min(1.0, self._timer / self.DURACION_MUERTE))
            return self._fraccion_al_morir_visible * (1.0 - t)
        if self._fase == "terminado":
            return 0.0
        return self._fraccion_visible

    @property
    def fraccion_diferida(self) -> float:
        if self._fase == "muriendo":
            t = ease_out_cubic(min(1.0, self._timer / self.DURACION_MUERTE))
            return self._fraccion_al_morir_diferida * (1.0 - t)
        if self._fase == "terminado":
            return 0.0
        return self._fraccion_diferida

    @property
    def alpha(self) -> int:
        if self._fase == "muriendo":
            t = min(1.0, self._timer / self.DURACION_MUERTE)
            return int(255 * (1.0 - ease_out_cubic(t)))
        if self._fase in ("oculto", "terminado"):
            return 0
        return 255

    # -- disparo (llamado por _PuertaDelCocinero) -----------------------

    def marcar_muerte(self) -> None:
        """El cocinero cayó: la barra empieza a vaciarse/desvanecerse
        desde donde esté en ese instante (relleno real + fantasma
        diferido), sin importar en qué fase estuviera."""
        if self._fase in ("muriendo", "terminado"):
            return
        self._fraccion_al_morir_visible = self.fraccion_visible
        self._fraccion_al_morir_diferida = self.fraccion_diferida
        self._fase = "muriendo"
        self._timer = 0.0

    # -- ciclo -----------------------------------------------------------

    def update(
        self, dt: float, jugador_x: float | None, cocinero: object | None,
        golpe_detectado: bool,
    ) -> None:
        """`cocinero` es el `ShooterCocinero` de la escena (o `None`) —
        duck-typed a propósito (`is_alive`/`current_health`/`max_health`)
        para que las pruebas puedan pasar un doble sin construir uno
        real. `golpe_detectado` lo decide `Stage1_2_LaSoda` comparando
        `current_health` entre fotogramas (ver
        `_detectar_golpe_al_cocinero`): no hay ningún evento del motor
        con el `entity_id` de quién recibió un golpe."""
        if self._fase == "terminado":
            return

        if self._fase == "muriendo":
            self._timer += dt
            if self._timer >= self.DURACION_MUERTE:
                self._fase = "terminado"
            return

        cocinero_vivo = cocinero is not None and getattr(cocinero, "is_alive", False)
        if cocinero_vivo:
            vida = float(cocinero.current_health)  # type: ignore[union-attr]
            maxima = max(float(cocinero.max_health), 0.001)  # type: ignore[union-attr]
            self._fraccion_actual = max(0.0, min(1.0, vida / maxima))

        visible_ahora = (
            jugador_x is not None
            and jugador_x >= _ObjetivoCocinero.X_ENTRADA_COCINA
            and cocinero_vivo
        )
        if not visible_ahora:
            if self._fase != "oculto":
                self._fase = "oculto"
            return

        if self._fase == "oculto":
            if not self._ya_aparecio:
                self._fase = "apareciendo"
                self._timer = 0.0
                self._ya_aparecio = True
            else:
                self._fase = "visible"
                self._fraccion_visible = self._fraccion_actual
            # Sin fantasma pendiente al (re)aparecer — cualquier daño
            # que llegue de acá en más se detecta con el próximo
            # `golpe_detectado` como de costumbre.
            self._fraccion_diferida = self._fraccion_actual
            self._retraccion_inicio = self._fraccion_actual
            self._retraccion_destino = self._fraccion_actual
            self._demora_restante = 0.0
            self._retraccion_timer = self.DURACION_RETRACCION

        if self._fase == "apareciendo":
            self._timer += dt
            t = min(1.0, self._timer / self.DURACION_ENTRADA)
            self._fraccion_visible = self._fraccion_actual * ease_out_cubic(t)
            if t >= 1.0:
                self._fase = "visible"
        elif self._fase == "visible":
            self._fraccion_visible = self._fraccion_actual

        if golpe_detectado:
            self._retraccion_inicio = self._fraccion_diferida
            self._retraccion_destino = self._fraccion_actual
            self._demora_restante = self.DEMORA_DIFERIDA
            self._retraccion_timer = 0.0
        else:
            # AUD-650 — `dt` se reparte entre lo que quede de la demora
            # y lo que sobre para la retracción DENTRO del mismo
            # `update()`, en vez de un `elif` que sólo gasta `dt` contra
            # una de las dos fases por llamada: con un `dt` que cruza el
            # límite exacto entre demora y retracción (a 60fps real esto
            # no pasa casi nunca porque los pasos son de ~1/60s, pero
            # cualquier fotograma más largo — o el fast-forward de una
            # prueba — sí lo cruza), el `elif` viejo se comía el resto
            # del `dt` sin avanzar nada de retracción ese fotograma: la
            # barra fantasma quedaba pegada un fotograma de más antes de
            # empezar a moverse.
            resto = dt
            if self._demora_restante > 0.0:
                consumido = min(self._demora_restante, resto)
                self._demora_restante -= consumido
                resto -= consumido
            if resto > 0.0 and self._retraccion_timer < self.DURACION_RETRACCION:
                self._retraccion_timer = min(
                    self.DURACION_RETRACCION, self._retraccion_timer + resto,
                )
            if self._retraccion_timer >= self.DURACION_RETRACCION:
                self._fraccion_diferida = self._retraccion_destino
            else:
                t = self._retraccion_timer / self.DURACION_RETRACCION
                self._fraccion_diferida = (
                    self._retraccion_inicio
                    + (self._retraccion_destino - self._retraccion_inicio)
                    * ease_out_quad(t)
                )

    # -- dibujado ----------------------------------------------------

    def rect_total(self) -> pygame.Rect:
        """El rectángulo que ocupa el panel entero (rótulo + barra) en
        espacio de PANTALLA — público para que `draw()` y las pruebas de
        colisión con el HUD/letrero/MessageBox usen el mismo cálculo.
        Cacheado: `TEXTO`/`Theme.FONT_SMALL`/`Y_BARRA` son constantes de
        clase, el rect nunca cambia entre llamadas."""
        if self._rect_cache is None:
            fuente = _fuente_del_tema(Theme.FONT_SMALL)
            ancho_texto, alto_texto = fuente.size(self.TEXTO)
            ancho = max(self.ANCHO, ancho_texto)
            y_top = self.Y_BARRA - self.GAP_TEXTO - alto_texto
            alto = (self.Y_BARRA + self.ALTO) - y_top
            x = (settings.INTERNAL_WIDTH - ancho) // 2
            self._rect_cache = pygame.Rect(x, y_top, ancho, alto)
        return self._rect_cache

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        rect = self.rect_total()
        if self._panel is None:
            # `convert_alpha()` una sola vez, acá — no en cada `draw()` —
            # mismo motivo que ya documenta `_LecturaDeLuz.analizar_si_
            # hace_falta`: una `Surface(..., pygame.SRCALPHA)` sin
            # convertir usa la ruta de blit por software de SDL.
            self._panel = pygame.Surface(rect.size, pygame.SRCALPHA).convert_alpha()
            self._texto_render = _fuente_del_tema(Theme.FONT_SMALL).render(
                self.TEXTO, True, self.COLOR_TEXTO,
            ).convert_alpha()
        panel = self._panel
        panel.fill((0, 0, 0, 0))

        texto_x = (rect.width - self._texto_render.get_width()) // 2
        panel.blit(self._texto_render, (texto_x, 0))

        barra_x = (rect.width - self.ANCHO) // 2
        barra_y = rect.height - self.ALTO
        marco = pygame.Rect(barra_x - 2, barra_y - 2, self.ANCHO + 4, self.ALTO + 4)
        pygame.draw.rect(panel, self.COLOR_MARCO, marco)
        pygame.draw.rect(panel, self.COLOR_FONDO, (barra_x, barra_y, self.ANCHO, self.ALTO))

        # El fantasma diferido se pinta PRIMERO (todo su ancho, blanco) y
        # el relleno de color ENCIMA, más angosto — así el tramo entre
        # los dos anchos es justo el "daño reciente" que queda en blanco.
        ancho_diferido = int(self.ANCHO * self.fraccion_diferida)
        if ancho_diferido > 0:
            pygame.draw.rect(
                panel, self.COLOR_DIFERIDO, (barra_x, barra_y, ancho_diferido, self.ALTO),
            )
        ancho_relleno = int(self.ANCHO * self.fraccion_visible)
        if ancho_relleno > 0:
            color = _color_de_salud(self._fraccion_actual)
            pygame.draw.rect(
                panel, color, (barra_x, barra_y, ancho_relleno, self.ALTO),
            )
        panel.set_alpha(self.alpha)
        surface.blit(panel, rect.topleft)


class _SacudidaDeCamara:
    """Sacudida de cámara para los tres momentos de impacto del cocinero
    (AUD-650): cada golpe que conecta, la apertura de la puerta trasera y
    la muerte del jefe.

    Por qué esto NO reimplementa un sistema de sacudida propio
    -------------------------------------------------------------
    `Camera.apply_shake` (`src/framework/stage/camera.py:217-262`) YA
    trae, con `direccion`, exactamente la sacudida que pide el encargo:
    una oscilación COHERENTE a lo largo de un eje que decae en su
    duración (`_aplicar_sacudida`, AUD-282 — "lo que se lee como
    empujón es un movimiento coherente de ida y vuelta", no ruido).
    Verificado leyendo/probando el motor (`camera.py:438-472`): SIN
    dirección la sacudida es ruido isótropo de amplitud CONSTANTE con
    un corte abrupto al final (`sx = rng.uniform(-1,1) * amplitud`, sin
    ninguna curva de decaimiento) — así que esta clase SIEMPRE pasa una
    dirección (ver `_direccion_pseudoaleatoria`) para activar la rama
    que sí decae. Encima ya filtra la preferencia de accesibilidad
    "movimiento reducido" al 25% (`_factor_de_movimiento()`, AUD-126)
    — un sistema de sacudida hecho a mano en código de escenario la
    ignoraría por completo, y eso no es negociable. Escribir un segundo
    sistema de sacudida en este archivo duplicaría, peor, lo que el
    motor ya resolvió para esto — así que esta clase es sólo la FACHADA
    que decide CUÁNDO, CUÁNTO y en qué eje sacudir para los tres
    disparadores de este nivel; el CÓMO decae queda en
    `Camera.apply_shake`.

    Dirección pseudoaleatoria determinista (`_direccion_pseudoaleatoria`)
    -------------------------------------------------------------
    El encargo pide que no dependa de `random` global sin semilla. En
    vez de usar el `random.Random` propio de la cámara (`AUD-398`, ya
    semillado, pero pensado para el ruido isótropo de golpe a golpe, no
    para elegir un eje) esta clase lleva su PROPIO contador entero
    (`_contador`, uno por instancia — vive tanto como la escena, no se
    reinicia entre disparos) y lo pasa por el ángulo áureo
    (`_ANGULO_AUREO≈137.5°`, la misma técnica de secuencia de baja
    discrepancia que reparte semillas de girasol sin que dos vueltas
    caigan nunca en el mismo ángulo): cada disparo consecutivo cae en
    un eje distinto y bien repartido, 100% determinista a partir de
    cuántas veces se disparó, sin tocar ningún generador de azar.

    `StageScene.on_enter()` reconstruye `self._camera` como una
    `Camera()` nueva en cada respawn (`stage_scene.py:450`) — este
    envoltorio no guarda una referencia propia a la cámara vieja: cada
    disparo resuelve `stage._camera` en el momento (`getattr` defensivo,
    mismo patrón que `_PuertaDelCocinero._on_enemy_died` usa para
    `_interactables`), así que un golpe que llega justo antes de un
    respawn no termina sacudiendo una cámara que el juego ya reemplazó,
    y no hace falta resetear nada propio tras un `respawn()`.

    La sacudida sólo mueve `camera.offset`, que `dibujar_mundo()` resta
    para pasar de coordenadas de mundo a pantalla — el HUD/letrero/barra
    de jefe (`dibujar_ui()`) y el minimapa se dibujan en espacio de
    PANTALLA fijo, sin tocar `camera.offset` en ningún punto de este
    archivo, así que ninguno de los dos se mueve con la sacudida.
    """

    #: Cada golpe que conecta — el más chico y frecuente de los tres.
    AMPLITUD_GOLPE: float = 2.0
    DURACION_GOLPE: float = 0.12
    #: Apertura de la puerta trasera — a mitad de camino entre golpe y muerte.
    AMPLITUD_PUERTA: float = 3.0
    DURACION_PUERTA: float = 0.25
    #: Muerte del cocinero — el golpe más fuerte, cierra el combate.
    AMPLITUD_MUERTE: float = 6.0
    DURACION_MUERTE: float = 0.35

    #: Ángulo áureo (137.5077...°) — ver el docstring de la clase.
    _ANGULO_AUREO: float = 137.50776405003785

    def __init__(self, stage: Stage1_2_LaSoda) -> None:
        self._stage = stage
        self._contador: int = 0

    def golpe(self) -> None:
        self._disparar(self.AMPLITUD_GOLPE, self.DURACION_GOLPE)

    def apertura_de_puerta(self) -> None:
        self._disparar(self.AMPLITUD_PUERTA, self.DURACION_PUERTA)

    def muerte_del_cocinero(self) -> None:
        self._disparar(self.AMPLITUD_MUERTE, self.DURACION_MUERTE)

    def _direccion_pseudoaleatoria(self) -> pygame.Vector2:
        """Un eje distinto y determinista en cada disparo — ver el
        docstring de la clase."""
        self._contador += 1
        angulo = (self._contador * self._ANGULO_AUREO) % 360.0
        return pygame.Vector2(1.0, 0.0).rotate(angulo)

    def _disparar(self, amplitud: float, duracion: float) -> None:
        camara = getattr(self._stage, "_camera", None)
        if camara is not None:
            camara.apply_shake(amplitud, duracion, self._direccion_pseudoaleatoria())


class _PuertaTraseraVisual:
    """Dibuja `Door_Trasera` (AUD-641) como una puerta de madera y anima su
    apertura (se levanta hacia el marco) con easing al recibir el aviso de
    `_PuertaDelCocinero`.

    El motor (`DrawingSystem._draw_interactables`, drawing_system.py:365-380)
    ya dibuja la `Cerradura` como un rectángulo plano marrón (cerrada) o un
    marco hueco (abierta) — el mismo placeholder genérico que cualquier
    puerta o jaula del motor. Igual que `_dibujar_llave`/`_dibujar_cofre` más
    abajo en esta clase (AUD-639), esto repinta ENCIMA de ese placeholder con
    un glifo propio: listones de madera con un marco ocre, en vez de un
    rectángulo liso.

    La solidez real la sigue decidiendo el motor —`cerradura.abierta`, leída
    por `InteractableSystem.rects_solidos()`— y cambia de golpe en el
    fotograma en que `_PuertaDelCocinero` llama a `abrir_por_evento`: **esta
    clase es puramente cosmética**, nunca decide si el jugador pasa o no.
    Por eso la hoja se levanta con `ease_out_cubic` durante
    `DURACION_APERTURA` (~0.8s) aunque el jugador ya pueda atravesar el vano
    desde el primer fotograma de la animación — el mismo desfase que ya
    acepta `_MarcoDeLaPuerta` de esta misma stage (lo cosmético llega un
    poco después de lo mecánico, nunca antes).
    """

    DURACION_APERTURA: float = 0.8

    COLOR_MARCO: tuple[int, int, int] = (100, 66, 32)
    #: Contraste subido a propósito (antes 150,105,60 / 125,85,46 — casi
    #: indistinguibles a 16px de ancho): con el tono claro y el oscuro más
    #: separados, los listones se leen como tablas de verdad y no como un
    #: rectángulo liso, incluso en la captura de 1x sin recortar.
    COLOR_TABLA_A: tuple[int, int, int] = (172, 128, 74)
    COLOR_TABLA_B: tuple[int, int, int] = (100, 68, 34)
    COLOR_TIRADOR: tuple[int, int, int] = (235, 200, 70)

    def __init__(self, rect_cerrada: pygame.Rect) -> None:
        self._rect = pygame.Rect(rect_cerrada)
        self._abriendo: bool = False
        self._terminada: bool = False
        self._timer: float = 0.0

    def iniciar_apertura(self) -> None:
        if self._terminada:
            return
        self._abriendo = True
        self._timer = 0.0

    def update(self, dt: float) -> None:
        if not self._abriendo:
            return
        self._timer += dt
        if self._timer >= self.DURACION_APERTURA:
            self._timer = self.DURACION_APERTURA
            self._abriendo = False
            self._terminada = True

    @property
    def terminada(self) -> bool:
        return self._terminada

    def _alto_hoja(self) -> int:
        """Alto visible de la hoja de la puerta — se reduce (se "levanta"
        hacia el dintel) mientras se abre, y llega a 0 cuando termina."""
        if self._terminada:
            return 0
        if not self._abriendo:
            return self._rect.height
        t = ease_out_cubic(min(1.0, self._timer / self.DURACION_APERTURA))
        return int(self._rect.height * (1.0 - t))

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        marco = self._rect.move(-int(offset.x), -int(offset.y))
        if not surface.get_rect().colliderect(marco):
            return
        # El marco (dos jambas + dintel) queda visible siempre, abierta o
        # cerrada — es lo que hace que "sólo el marco" (puerta abierta) se
        # siga leyendo como un vano de verdad y no como un hueco vacío.
        pygame.draw.rect(surface, self.COLOR_MARCO, marco, 2)

        alto_hoja = self._alto_hoja()
        if alto_hoja <= 0:
            return  # terminó de abrirse: sólo el marco de arriba.

        # La hoja se "levanta" HACIA el dintel: el borde de arriba queda
        # siempre pegado a `marco.top` (ahí es donde se guarda, como una
        # cortina metálica o una puerta de garaje) y el borde de abajo es
        # el que sube a medida que `alto_hoja` baja. Con el rect anclado
        # al revés (abajo fijo, huyendo hacia el piso) la animación se leía
        # como si la puerta se HUNDIERA en el suelo — el efecto opuesto al
        # pedido ("se levanta").
        hoja = pygame.Rect(marco.left, marco.top, marco.width, alto_hoja)
        pygame.draw.rect(surface, self.COLOR_TABLA_A, hoja)
        # Listones verticales alternados — la textura que distingue una
        # puerta de madera de un simple rectángulo marrón.
        paso = 4
        for i, x in enumerate(range(hoja.left + 1, hoja.right - 1, paso)):
            color = self.COLOR_TABLA_B if i % 2 == 0 else self.COLOR_TABLA_A
            pygame.draw.line(surface, color, (x, hoja.top + 1), (x, hoja.bottom - 1), 2)
        # Dos travesaños horizontales (arriba y abajo de la hoja visible) —
        # el detalle que termina de leerse como una puerta de tablas
        # reforzadas, no sólo listones sueltos.
        for frac in (0.18, 0.82):
            y = hoja.top + int(hoja.height * frac)
            if hoja.top + 1 < y < hoja.bottom - 1:
                pygame.draw.line(
                    surface, self.COLOR_MARCO, (hoja.left + 1, y), (hoja.right - 2, y), 2,
                )
        pygame.draw.rect(surface, self.COLOR_MARCO, hoja, 1)
        # Tirador a una altura fija relativa al marco cerrado (55% del
        # alto total, la posición natural de un picaporte) — sólo se
        # dibuja mientras la hoja todavía lo cubre.
        y_tirador = marco.top + int(marco.height * 0.55)
        if hoja.top + 2 <= y_tirador <= hoja.bottom - 2:
            pygame.draw.circle(surface, self.COLOR_TIRADOR, (hoja.centerx, y_tirador), 2)


class _PuertaDelCocinero:
    """Cierra el circuito de `EventBus` entre "el cocinero murió" y "la
    puerta trasera se destraba" (AUD-641).

    Por qué hace falta código propio
    ---------------------------------
    `InteractableSystem.abrir_por_evento(evento)` (interactable_system.py:
    153-180) sabe abrir cualquier `Cerradura` cuyo `abre_con_evento`
    coincida — pero, como documenta su propio código, **sólo lo llama un
    `Disparador`** (`_disparar`, línea 261, cuando un `EventTrigger` del
    .tmx se activa). El motor no tiene ningún concepto de "abrir una puerta
    al matar a un enemigo concreto": `EnemyBase._die()` emite
    `Events.ENEMY_DIED` con un `entity_id` genérico
    (`enemy_base.py:591-595`) y nadie más en el motor escucha ese evento
    para abrir cerraduras. Sin esta clase, `Door_Trasera` (`abre_con_evento
    ="cocinero_muerto"` en el .tmx) se quedaría cerrada para siempre: no
    hay ningún `EventTrigger` en el mapa que emita `"cocinero_muerto"`, a
    propósito — ese evento sólo tiene sentido si lo dispara la muerte del
    cocinero, y eso es exactamente la "interacción propia vía `EventBus`"
    que pide la Evaluación Práctica II (Unidad VI): el estudiante decide
    cuándo.

    Qué escucha y qué dispara
    --------------------------
    Suscribe `_on_enemy_died` a `Events.ENEMY_DIED` (mismo evento, mismo
    bus que `_RecompensaDePickup` con `EVENTO_RECOGIDO` — ver esa clase más
    arriba para el mismo patrón de suscripción única). Filtra por
    `entity_id.startswith("ShooterCocinero")`: `EnemyBase._die()` arma el
    `entity_id` como `f"{type(self).__name__}_{id(self)}"`
    (`enemy_base.py:592`), así que cualquier instancia de `ShooterCocinero`
    —del mapa o de una futura entrega que reutilice esta clase— matchea sin
    depender de un id concreto. Al matchear, en este orden:

      1. marca `stage._cocinero_vencido = True` (idempotente: una segunda
         llamada —no debería ocurrir, pero por si el motor emite el evento
         dos veces— se descarta antes de repetir nada de lo de abajo);
      2. llama a `InteractableSystem.abrir_por_evento("cocinero_muerto")`
         con `getattr` defensivo, por si la escena todavía no tiene
         `_interactables` montado (antes de `on_stage_start`);
      3. emite `Events.SHOW_MESSAGE` con el aviso de destrabado, por el
         mismo camino que ya usa `_RecompensaDePickup` para sus carteles;
      4. arranca las dos animaciones con easing (`_ObjetivoCocinero.
         marcar_cumplido()` y `_PuertaTraseraVisual.iniciar_apertura()`),
         dibujadas en `Stage1_2_LaSoda.dibujar_ui()` y `.dibujar_mundo()`
         respectivamente (AUD-643 — antes las dos vivían en `draw()`).
    """

    MENSAJE_DESTRABADO: str = "El cocinero cayó. La puerta trasera se destraba."
    DURACION_MENSAJE: float = 2.5

    def __init__(self, stage: Stage1_2_LaSoda) -> None:
        self._stage = stage

    def suscribir(self, bus: EventBus) -> None:
        """Una sola vez, desde `Stage1_2_LaSoda.__init__` — mismo argumento
        que `_RecompensaDePickup.suscribir`: el bus de la escena no se
        reconstruye en cada respawn, y `EventBus.subscribe` es idempotente
        por método enlazado, así que no hay riesgo de doble suscripción."""
        bus.subscribe(Events.ENEMY_DIED, self._on_enemy_died)

    def _on_enemy_died(self, **data: object) -> None:
        entity_id = str(data.get("entity_id", ""))
        if not entity_id.startswith("ShooterCocinero"):
            return
        stage = self._stage
        if stage._cocinero_vencido:
            return  # ya se procesó (ver punto 1 del docstring de la clase)

        stage._cocinero_vencido = True
        interactables = getattr(stage, "_interactables", None)
        if interactables is not None:
            interactables.abrir_por_evento("cocinero_muerto")
        stage.context.event_bus.emit(
            Events.SHOW_MESSAGE, text=self.MENSAJE_DESTRABADO,
            duration=self.DURACION_MENSAJE,
        )
        stage._objetivo_cocinero.marcar_cumplido()
        # AUD-650 — la barra de jefe se vacía/desvanece, y la cámara
        # sacude dos veces en este mismo evento: una por la muerte en sí
        # (la más fuerte) y otra —más chica— justo donde arranca la
        # animación de `_PuertaTraseraVisual` un par de líneas más abajo
        # (ver el docstring de `_SacudidaDeCamara`: no reimplementa un
        # sistema propio, sólo decide cuándo/cuánto llamar a
        # `Camera.apply_shake`, que se queda con la MÁS FUERTE de las
        # dos si coinciden en el mismo fotograma).
        stage._barra_jefe.marcar_muerte()
        stage._sacudida_camara.muerte_del_cocinero()
        if stage._puerta_visual is not None:
            stage._puerta_visual.iniciar_apertura()
            stage._sacudida_camara.apertura_de_puerta()


class _AvisoDeBloqueo:
    """Cierra OTRO hueco de `EventBus` que `InteractableSystem` deja
    abierto (AUD-641), necesario para que el "cartel de bloqueo" que pide
    la Tarea 1 (tocar `Door_Trasera` sin haber vencido al cocinero) se vea
    de verdad en pantalla.

    El hueco, verificado leyendo el motor entero (`drawing_system.py`,
    `stage_scene.py`, `hud.py`, `message_box.py`): `_abrir_cerraduras`/
    `_abrir_cofres` (`interactable_system.py:199-237`) fijan
    `InteractableSystem.mensaje` con el texto de "está cerrado, te falta
    tal llave" vía `_avisar` (línea 297) y emiten `EVENTO_BLOQUEADA` — pero
    **ningún sistema del framework dibuja `InteractableSystem.mensaje`**.
    Es un dato que el motor calcula y nadie muestra — el mismo tipo de
    hueco que `_RecompensaDePickup` ya documenta para `EVENTO_RECOGIDO` más
    arriba, sólo que del lado de "bloqueado" en vez de "recogido". Sin este
    puente, tocar la puerta trasera sin haber vencido al cocinero (o el
    cofre del depósito sin la llave, AUD-639) no le decía nada al jugador:
    el personaje simplemente no se movía, sin ninguna pista del porqué.

    El puente: al recibir `EVENTO_BLOQUEADA`, lee `InteractableSystem.
    mensaje` —que `_avisar` ya dejó con el texto correcto ANTES de emitir
    el evento, en el mismo fotograma— y lo reemite como
    `Events.SHOW_MESSAGE`, la misma vía que ya usa `_RecompensaDePickup`
    para sus carteles y que `MessageBox` ya sabe mostrar
    (`message_box.py:72,82-88`). Deliberadamente general —no filtra por
    `key_id` ni por qué cerradura o cofre lo disparó—: así también le
    devuelve su cartel al cofre del depósito, que tenía exactamente el
    mismo hueco desde AUD-639.

    AUD-643 — dos arreglos más sobre ese puente, del punto 3 del encargo
    ("los carteles llegan tarde"):

    (1) Rate-limit del MISMO aviso. `EVENTO_BLOQUEADA` se dispara una vez
    por fotograma mientras el jugador sostenga/pulse GRAB junto a una
    cerradura sin la llave (`InteractableSystem.update`, `usar=True` cada
    vez que se pulsa) — el dueño lo vivió como "el cofre le dijo 'Necesitas
    llave_deposito' diez veces" tras insistir con GRAB. Sin límite, cada
    pulsación reencola OTRO `SHOW_MESSAGE` idéntico detrás del anterior en
    `MessageBox._queue` (`message_box.py:82-88`), y la cola se llena de
    copias del mismo texto en vez de vaciarse. `update()` (llamado desde
    `Stage1_2_LaSoda.update()`, con el `dt` del fotograma — no
    `time.time()`, mismo criterio que `_objetivo_cocinero`/
    `_room_transition`) cuenta atrás una ventana de `VENTANA_REPETICION`
    tras cada aviso; mientras esté activa, un aviso con el MISMO texto no
    se reencola. Uno con texto DISTINTO (p. ej. pasar de la puerta a un
    cofre distinto) sí sale de inmediato: el límite es "no te repitas a vos
    mismo", no "cállate un rato".

    (2) Nombres legibles. `_abrir_cofres` (`interactable_system.py:224`)
    compone su aviso por defecto con el `key_id` crudo del `.tmx`:
    `f"El cofre está cerrado. Necesitas «{cofre.key_id}»."` — y
    `key_id="llave_deposito"` (identificador de programador, con guion
    bajo) es exactamente lo que el dueño vio en pantalla, tal cual. La
    puerta trasera no tiene este problema (`Door_Trasera.mensaje` en el
    `.tmx` ya cubre su propio `mensaje_bloqueado`), pero `Cerradura` no
    tiene un campo de texto separado para el cofre — así que el reemplazo
    de `NOMBRES_LEGIBLES` pasa por acá: sustituye el `key_id` crudo, entre
    guillemets, por su nombre en español antes de reemitir.
    """

    #: Dentro del rango 2-3s que ya usa `_RecompensaDePickup` para sus
    #: propios carteles.
    DURACION_MENSAJE: float = 2.0
    #: Ventana de silencio para el MISMO aviso repetido, en segundos.
    VENTANA_REPETICION: float = 2.0
    #: `key_id` crudo (tal como aparece en el `.tmx`) -> nombre legible en
    #: español. Sólo cubre lo que este mapa usa; un `key_id` que no esté acá
    #: se muestra tal cual (mejor un aviso con jerga que ninguno).
    NOMBRES_LEGIBLES: dict[str, str] = {"llave_deposito": "la llave del depósito"}

    def __init__(self, stage: Stage1_2_LaSoda) -> None:
        self._stage = stage
        self._ultimo_texto: str | None = None
        self._cooldown: float = 0.0

    def suscribir(self, bus: EventBus) -> None:
        """Una sola vez, desde `Stage1_2_LaSoda.__init__` — mismo
        argumento de idempotencia que `_RecompensaDePickup.suscribir` y
        `_PuertaDelCocinero.suscribir`."""
        bus.subscribe(EVENTO_BLOQUEADA, self._on_bloqueada)

    def update(self, dt: float) -> None:
        """Cuenta atrás la ventana de repetición — ver el punto (1) del
        docstring de la clase. Llamado desde `Stage1_2_LaSoda.update()`."""
        if self._cooldown > 0.0:
            self._cooldown = max(0.0, self._cooldown - dt)

    def _texto_legible(self, texto: str) -> str:
        for crudo, legible in self.NOMBRES_LEGIBLES.items():
            texto = texto.replace(f"«{crudo}»", f"«{legible}»")
        return texto

    def _on_bloqueada(self, **_data: object) -> None:
        interactables = getattr(self._stage, "_interactables", None)
        texto = getattr(interactables, "mensaje", "") if interactables else ""
        if not texto:
            return
        texto = self._texto_legible(texto)
        if texto == self._ultimo_texto and self._cooldown > 0.0:
            # Mismo aviso, todavía dentro de la ventana de silencio del
            # punto (1) del docstring de la clase — no se reencola.
            return
        self._ultimo_texto = texto
        self._cooldown = self.VENTANA_REPETICION
        self._stage.context.event_bus.emit(
            Events.SHOW_MESSAGE, text=texto, duration=self.DURACION_MENSAJE,
        )


class Stage1_2_LaSoda(StageScene):
    """Stage 1-2 — La Soda. Cafetería universitaria, en pleno caos.
    Demo básica de movimiento/traversal — todavía no es la asignación
    completa (ver docs/16_WORLD_DESIGN.md §3.3 para el brief de diseño
    completo)."""

    STAGE_ID: str = "stage1_2_la_soda"
    STAGE_NAME: str = "1-2  LA SODA"
    ZONE: int = 1
    # AUD-643 — el reloj real del HUD no lee esta constante (no aparece en
    # ningún otro archivo del motor: `StageScene.on_stage_start` arranca el
    # cronómetro con `_stage_data.time_limit`, que `StageLoader` lee de la
    # propiedad `time_limit` del propio `.tmx` — ver
    # `assets/maps/stage1_2_la_soda/stage1_2_la_soda.tmx`). Se mantiene en
    # sincronía con esa propiedad de todos modos, como metadato de
    # documentación: 240 -> 360, subido tras el playtest del dueño (una
    # pasada normal con una muerte agotó el reloj a 00:54 sin vencer al
    # cocinero).
    TIME_LIMIT: int = 360
    BGM_TRACK: str = "bgm_zone1"

    # AUD-620 — frenado del piso recién trapeado de la cocina, en px/s².
    # Ver `_aplicar_agarre_del_piso_trapeado`: es la fricción que el jugador
    # SÍ lee dentro de su update (a diferencia de `inercia`), y 60 px/s²
    # frenan de walk_speed (~90 px/s) a 0 en ~1.5 s, deslizando ~67 px —
    # un resbalón claro sin quitar el control.
    FRICCION_PISO_TRAPEADO: float = 60.0

    # AUD-639 — íconos propios para Key/Chest.
    #
    # `DrawingSystem._draw_interactables` (drawing_system.py:330-395) no
    # conoce el concepto "esto es una llave": todo `Recogible` sin entrada en
    # el catálogo de `Inventory` se pinta con el mismo `_COLOR_RECOGIBLE`
    # (240,210,90) — un cuadrado dorado liso, igual al de un vaso de soda o
    # una moneda —, así que la llave del depósito era indistinguible de
    # cualquier otro `Pickup` del mapa. El cofre es un rectángulo marrón con
    # una línea de tapa que sólo cambia a gris al abrirse. Corregir el
    # aspecto es contenido de este nivel, no del motor — `src/stages/` es
    # donde vive este código y el framework no se toca (CLAUDE.md §3,
    # invariante 1) — así que los glifos van acá, en
    # `_dibujar_iconos_interactivos`/`_dibujar_llave`/`_dibujar_cofre` más
    # abajo, encima del placeholder del framework, con el mismo mecanismo
    # que ya usa `_draw_enemy_health_bars`: convertir un rect de mundo a
    # pantalla restando `self._camera.offset`, después de
    # `super().dibujar_mundo()` (AUD-643 — antes `super().draw()`).
    #
    # Unidad V (ColorTools) — el dorado de la llave sale de
    # `ColorTools.hsv_to_rgb` en vez de una tripleta RGB a mano, mismo
    # mecanismo de conversión de espacio de color que ya usa
    # `_draw_enemy_health_bars` para el degradado verde→rojo de la barra de
    # vida. Se computa una sola vez, a nivel de clase: es un color fijo, no
    # hace falta recalcularlo cada fotograma.
    _COLOR_LLAVE_DORADO: tuple[int, int, int] = ColorTools.hsv_to_rgb(46.0, 0.85, 0.95)
    _COLOR_LLAVE_CONTORNO: tuple[int, int, int] = (40, 30, 10)

    # Paleta del cofre — cálida, en la misma familia dorado/marrón que el
    # resto de La Soda, a propósito distinta de `_COLOR_COFRE`/
    # `_COLOR_ABIERTO` del framework (drawing_system.py:333-334), que sólo
    # distinguen abierto/cerrado con un gris apagado.
    _COLOR_COFRE_CUERPO: tuple[int, int, int] = (140, 95, 50)
    _COLOR_COFRE_LISTON: tuple[int, int, int] = (185, 145, 85)
    _COLOR_COFRE_TAPA: tuple[int, int, int] = (170, 120, 65)
    _COLOR_COFRE_INTERIOR: tuple[int, int, int] = (230, 200, 150)
    _COLOR_COFRE_CERROJO: tuple[int, int, int] = (235, 200, 70)
    _COLOR_COFRE_CONTORNO: tuple[int, int, int] = (55, 35, 15)

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/stage1_2_la_soda/stage1_2_la_soda.tmx"))
        self._fireflies = _FireflyField()
        self._room_transition: _RoomTransition | None = None
        # AUD-629 — no depende de _stage_data ni de la puerta estar cruzada;
        # vive fuera del if de abajo porque no necesita reconstruirse en
        # cada respawn (a diferencia de _room_transition, cuyo estado
        # "interior"/"exterior" sí tiene que sobrevivir entre respawns).
        self._marco_puerta = _MarcoDeLaPuerta()
        self._exterior_enemies_muted: bool = False
        # AUD-620 — la FrictionZone del piso trapeado, cacheada porque
        # `_stage_data.componentes` se reconstruye en cada on_enter()/respawn.
        self._zona_trapeado: ZonaDeFriccion | None = None
        # AUD-613 — mismo patrón que _room_transition: un valor guardado en
        # la propia instancia del stage, que no se reinicia en on_stage_start
        # y por lo tanto sobrevive a un respawn (a diferencia de
        # _stage_data, que on_enter() reconstruye entero cada vez).
        #
        # AUD-640 — pasa de `bool` a `set[int]` de índices. Con un único
        # MessageTrigger_Once en el mapa (MSG_01, hasta AUD-639) un solo
        # booleano "¿ya se disparó ALGUNO?" bastaba. Con los tres carteles
        # de guía nuevos ese booleano queda mal: `any(mt.triggered ...)` se
        # volvía True apenas CUALQUIERA de los cuatro se disparaba, y
        # on_stage_start() marcaba los CUATRO como "ya mostrados" en el
        # `_stage_data` reconstruido — un jugador que viera el cartel de
        # bienvenida y muriera antes de llegar a la fachada o a la cocina
        # perdía esos carteles para siempre, sin haberlos visto nunca. El
        # índice de cada disparador dentro de `message_triggers` es estable
        # entre respawns (StageLoader reconstruye la lista en el mismo orden
        # del .tmx cada vez), así que sirve de identidad sin tocar
        # `MessageTrigger` (dataclass del framework, fuera de alcance).
        self._carteles_disparados: set[int] = set()
        # AUD-632 — la "interacción propia vía EventBus" de la Unidad VI:
        # cierra el hueco de los 5 Pickup del mapa (ver el docstring de
        # _RecompensaDePickup). Se suscribe una sola vez, aquí: el bus de
        # la escena (self.context.event_bus, ya disponible tras
        # super().__init__() arriba) no se reconstruye en cada respawn —
        # a diferencia de _stage_data/_interactables — así que no hace
        # falta repetir la suscripción en on_stage_start como sí necesita
        # _room_transition con su propio estado (interior/exterior).
        self._recompensa_pickup = _RecompensaDePickup(self)
        self._recompensa_pickup.suscribir(self.context.event_bus)
        # AUD-641 — la puerta trasera de la cocina, disparada al matar al
        # cocinero. `_cocinero_vencido` vive en la propia instancia del
        # stage (mismo lugar que `_room_transition`/`_carteles_disparados`)
        # porque `_PuertaDelCocinero._on_enemy_died` la escribe desde un
        # manejador de evento y `Stage1_2_LaSoda.update`/`draw` la leen cada
        # fotograma; no puede vivir en `_stage_data` porque `on_enter()` la
        # reconstruye entera en cada respawn.
        #
        # A diferencia de `_carteles_disparados` (que SÍ sobrevive a un
        # respawn), ésta se reinicia a `False` en cada `on_stage_start()`
        # (ver más abajo) — el motivo está documentado ahí: `respawn()`
        # reconstruye `entity_list` desde cero, así que el cocinero
        # reaparece vivo y hay que volver a vencerlo.
        self._cocinero_vencido: bool = False
        self._objetivo_cocinero = _ObjetivoCocinero()
        # AUD-650 — barra de vida del jefe y sacudida de cámara.
        #
        # `_barra_jefe` se reconstruye en cada `on_stage_start()` (mismo
        # criterio que `_objetivo_cocinero`, ver ese método): el cocinero
        # reaparece con vida llena tras un respawn y hay que poder verla
        # llenarse otra vez, no seguir en "terminado" de la vida anterior.
        #
        # `_sacudida_camara` es sólo una fachada sobre `Camera.
        # apply_shake` (ver esa clase) — no tiene estado propio que
        # sobreviva o no a un respawn, así que se construye una sola vez
        # acá, igual que `_puerta_cocinero`/`_recompensa_pickup`.
        #
        # `_cocinero_vida_anterior` es la línea de base de
        # `_detectar_golpe_al_cocinero` (ver ese método): `None` fuerza a
        # que el primer muestreo de cada vida del cocinero nunca cuente
        # como "golpe" por sí solo.
        self._barra_jefe = _BarraDeJefe()
        self._sacudida_camara = _SacudidaDeCamara(self)
        self._cocinero_vida_anterior: float | None = None
        # Cerradura y puerta visual: se resuelven de verdad en
        # `on_stage_start()`, una vez que `_stage_data`/`_interactables`
        # existen. `None` acá sólo evita `AttributeError` si algo llama a
        # `draw()`/`update()` antes del primer `on_stage_start()`.
        self._cerradura_puerta_trasera = None
        self._puerta_visual: _PuertaTraseraVisual | None = None
        self._puerta_cocinero = _PuertaDelCocinero(self)
        self._puerta_cocinero.suscribir(self.context.event_bus)
        # AUD-641 — el "cartel de bloqueo" (tocar la puerta trasera sin
        # haber vencido al cocinero) necesita este puente aparte: ver el
        # docstring de `_AvisoDeBloqueo` para el hueco exacto que cierra.
        self._aviso_bloqueo = _AvisoDeBloqueo(self)
        self._aviso_bloqueo.suscribir(self.context.event_bus)
        # AUD-643 — la llave sobrevive a un respawn (ver el docstring de
        # _LlavesPersistentes para el bug exacto: sin esto, morir después
        # de levantar la llave del depósito la borra del llavero y vuelve
        # a tirarla en el suelo). Igual que `_recompensa_pickup`/
        # `_puerta_cocinero`/`_aviso_bloqueo`: se suscribe una sola vez
        # aquí porque el bus de la escena no se reconstruye en cada
        # respawn; `reaplicar()` sí se llama en cada `on_stage_start()`
        # (ver ese método), una vez que `_interactables`/`_stage_data`
        # existen.
        self._llaves_persistentes = _LlavesPersistentes(self)
        self._llaves_persistentes.suscribir(self.context.event_bus)
        # AUD-645 — Unidad VII: histograma dirige la "adaptación a la
        # penumbra" al cruzar a la sala, y Sobel decide el contorno de
        # alerta de un enemigo a punto de morir. Ninguna de las dos escucha
        # el EventBus (no hace falta: se consultan directamente desde
        # dibujar_mundo/dibujar_ui, igual que _draw_enemy_health_bars), así
        # que no llevan `.suscribir()`.
        self._lectura_de_luz = _LecturaDeLuz()
        self._contorno_alerta = _ContornoDeAlerta()

    def on_enter(self) -> None:
        super().on_enter()
        self._ajustar_minimapa_al_nivel()
        self._silenciar_avisos_genericos_del_motor()

    def _ajustar_minimapa_al_nivel(self) -> None:
        """AUD-647 — recuadro del minimapa a la proporción real del nivel.

        `StageScene.on_enter()` (stage_scene.py:~627-629) coloca el
        minimapa en `HUD.minimap_rect()` —el recuadro cuadrado de 44x44 de
        maqueta (110x110 px en pantalla) que AUD-560 pidió a propósito
        para el HUD general, revirtiendo el círculo de AUD-547— y después
        llama `set_map_size(*map_pixel_size)`. `Minimap.set_map_size`
        (minimap.py:84-88) escala con `min(sx, sy)`: en un mapa cuadrado
        eso llena el recuadro entero, pero La Soda mide 3456x608 px —una
        proporción 5.7:1—, así que el lado limitante es el ancho (`sx`) y
        el nivel entero queda comprimido en una tira de ~19 px pegada al
        borde superior del cuadrado, con el resto (91 px de alto) vacío:
        justo lo que reportó el dueño ("se ve como una parte de arriba y
        tanto vacío", ver la captura de AUD-647).

        Este método corre DESPUÉS de que el `on_enter()` heredado ya dejó
        colocado ese recuadro cuadrado por defecto —se llama desde el
        `on_enter()` de esta clase, justo tras `super().on_enter()`, y por
        lo tanto también en cada `respawn()` (que vuelve a invocar
        `on_enter()`, ver `StageScene.respawn()`: `self.on_enter()`)— y lo
        reemplaza por uno con la proporción real del mapa: 200 px de ancho
        en la pantalla interna de 800x600, alto proporcional (`200 *
        map_h / map_w`, ≈35 px para 3456x608). Se ubica a la derecha del
        cronómetro, en la misma franja del HUD —mismo `top` que
        `HUD.timer_rect()`, mismo margen al borde derecho que ya usaba el
        recuadro cuadrado (`HUD.minimap_rect().right`)— porque a la
        derecha del reloj hay de sobra (465 a 785 px en pantalla, ~320 px
        libres) para un recuadro de 200 sin invadir el hueco original.

        Fallback (no se activa con el layout actual, medido: no hay
        solape; queda documentado por si el HUD cambia de forma que deje
        de haber sitio): si el recuadro calculado solapa cualquier otra
        región del HUD (`HUD.regiones()` — retrato, vida, marcador,
        cronómetro), se usa el mismo `right`/`top` que el recuadro
        cuadrado original con el alto proporcional, sobresaliendo hacia
        la izquierda del recuadro original en vez de hacia la derecha del
        reloj.

        No toca `src/engine/ui/minimap.py` ni `hud.py` —son del framework,
        fuera del candado de este nivel— sólo llama a la API pública que
        ya usa `StageScene.on_enter()`: `colocar()` + `set_map_size()`.
        `getattr` defensivo porque las pruebas headless pueden construir
        la escena sin HUD/minimapa montados todavía.
        """
        minimapa = getattr(self, "_minimap", None)
        hud = getattr(self, "_hud", None)
        stage_data = getattr(self, "_stage_data", None)
        if minimapa is None or hud is None or stage_data is None:
            return
        map_w, map_h = stage_data.map_pixel_size
        if map_w <= 0 or map_h <= 0:
            return

        ancho = 200
        alto = max(1, round(ancho * map_h / map_w))
        recuadro_defecto = hud.minimap_rect()
        timer_rect = hud.timer_rect()
        rect = pygame.Rect(recuadro_defecto.right - ancho, timer_rect.top, ancho, alto)

        otras_regiones = [r for nombre, r in hud.regiones().items() if nombre != "minimapa"]
        if any(rect.colliderect(r) for r in otras_regiones):
            rect = pygame.Rect(
                recuadro_defecto.right - ancho, recuadro_defecto.top, ancho, alto)

        minimapa.colocar(rect)
        minimapa.set_map_size(map_w, map_h)

    def _silenciar_avisos_genericos_del_motor(self) -> None:
        """AUD-656 — blindaje defensivo ante un `InteractableSystem._avisar`
        que también publique al `MessageBox`, en vez de asumir para siempre
        el comportamiento actual del motor.

        En esta base (`origin/dev`) `InteractableSystem._avisar`
        (`interactable_system.py:297-299`) sólo fija `mensaje`/
        `mensaje_timer` — nunca emite al `EventBus` — y esta stage ya cierra
        ese hueco por su cuenta, con criterio propio: `_AvisoDeBloqueo`
        traduce el `key_id` crudo del `.tmx` (`llave_deposito` -> "la llave
        del depósito") y rate-limita el mismo texto repetido
        (`VENTANA_REPETICION`, ver esa clase), y `_PuertaDelCocinero`
        muestra su propio cartel de destrabado ("El cocinero cayó..."). Ver
        el punto 7(b) de "Hallazgos del motor reportados al profesor" en
        README.md — este método es la contraparte de aquel hallazgo.

        En `feature/master-plan` (reporte propio, "Fix reporte Guillermo
        7b") `_avisar` pasa a hacer ADEMÁS `self._bus.emit(Events.
        SHOW_MESSAGE, text=texto, duration=duracion)` — publicando directo
        al `MessageBox`, con el texto crudo (key_id sin traducir) y sin
        ningún rate-limit propio (`_abrir_cofres` llama a `_avisar` una vez
        por fotograma mientras se sostenga GRAB junto a un cofre cerrado).
        Sobre esa rama el resultado son carteles duplicados: el aviso crudo
        del motor detrás del de `_AvisoDeBloqueo` ya traducido, o "Se ha
        abierto algo. (1)" apareciendo ANTES que "El cocinero cayó..." al
        vencerlo (`abrir_por_evento` llama a `_avisar` antes de que
        `_PuertaDelCocinero._on_enemy_died` emita su propio cartel).

        El arreglo reemplaza `_avisar` en la INSTANCIA de `_interactables`
        —nunca en la clase: `InteractableSystem` es del motor, fuera del
        candado de esta stage— por una función con la misma firma que sólo
        fija `mensaje`/`mensaje_timer`, igual que el `_avisar` de `dev` hoy.
        En `dev` esto es un no-op inofensivo (mismo comportamiento de
        siempre, ninguna prueba existente cambia); en un motor que publique
        al bus, silencia justo esa publicación sin tocar `_AvisoDeBloqueo`
        ni `_PuertaDelCocinero`, que siguen siendo la única vía por la que
        esta stage decide qué avisos mostrar (traducidos y rate-limitados).

        Se llama desde `on_enter()`, después de `super().on_enter()` —quien
        reconstruye `self._interactables` como una instancia NUEVA en cada
        `on_enter()`/`respawn()` (`StageScene.on_enter`, `stage_scene.py:
        542-549`)— así que el reemplazo se reaplica en cada respawn, no
        sólo una vez al cargar el nivel. `getattr` defensivo: si algún día
        `InteractableSystem` deja de tener `_avisar`, no rompe el arranque.
        """
        interactables = getattr(self, "_interactables", None)
        if interactables is None or not hasattr(interactables, "_avisar"):
            return

        def _avisar_sin_bus(texto: str, duracion: float = 2.0) -> None:
            """Misma firma que `InteractableSystem._avisar` — sólo fija el
            mensaje para que la escena lo lea (`_AvisoDeBloqueo`), nunca
            publica al `EventBus` directamente."""
            interactables.mensaje = texto
            interactables.mensaje_timer = duracion

        interactables._avisar = _avisar_sin_bus

    def update(self, dt: float) -> None:
        # AUD-620 — se fija la fricción del piso trapeado ANTES de que corra
        # la física del jugador (super().update → player.update): es la única
        # palanca que `_aplicar_friccion_y_aceleracion` lee en ese momento.
        self._aplicar_agarre_del_piso_trapeado()
        super().update(dt)
        if self._room_transition is not None:
            self._room_transition.apply_camera_box(self._camera)
        if self._paused:
            return
        self._fireflies.update(dt)
        if self._player is not None and self._room_transition is not None:
            self._room_transition.maybe_trigger(self._player)
            self._room_transition.clamp_one_way(self._player)
        if self._room_transition is not None:
            self._room_transition.update(dt)
            self._maybe_mute_exterior_enemies()
        self._maybe_persist_carteles_disparados()
        # AUD-641 — letrero de objetivo y animación de apertura de la
        # puerta trasera. Guardado con el `dt` de este `update()` (no
        # `time.time()`), para que la animación sea determinista en
        # pruebas — igual criterio que `_fireflies`/`_room_transition`
        # arriba.
        jugador_x = self._player.position.x if self._player is not None else None
        self._objetivo_cocinero.update(dt, jugador_x, self._cocinero_vencido)
        if self._puerta_visual is not None:
            self._puerta_visual.update(dt)
        # AUD-643 — cuenta atrás la ventana de repetición del cartel de
        # bloqueo (ver el punto (1) del docstring de _AvisoDeBloqueo).
        self._aviso_bloqueo.update(dt)
        # AUD-650 — barra de vida del jefe y sacudida de cámara por golpe.
        # `_detectar_golpe_al_cocinero` muestrea `current_health` este
        # fotograma (no hay evento del motor con el entity_id de quién
        # recibió un golpe, ver el docstring de ese método) y dispara la
        # sacudida más chica de las tres; `_barra_jefe` recibe el mismo
        # booleano para animar su segmento de daño diferido.
        cocinero = self._buscar_cocinero()
        golpe_detectado = self._detectar_golpe_al_cocinero(cocinero)
        if golpe_detectado:
            self._sacudida_camara.golpe()
        self._barra_jefe.update(dt, jugador_x, cocinero, golpe_detectado)

    def _maybe_persist_carteles_disparados(self) -> None:
        """Recuerda, en la propia instancia del stage, qué carteles
        (`MessageTrigger_Once`) ya salieron — mismo patrón que
        `_room_transition` para recordar en qué sala está el jugador entre
        respawns (ver on_stage_start más abajo).

        AUD-613 — `StageScene.respawn()` llama a `on_enter()`, que
        reconstruye `_stage_data` entero (StageLoader vuelve a leer el
        .tmx). Los `MessageTrigger` que consulta `hazard_system.py:96-98`
        son, por lo tanto, objetos NUEVOS en cada respawn, todos con
        `triggered=False` de nuevo — sin este registro los carteles se
        repetirían cada vez que el jugador muere y reaparece sin checkpoint.

        AUD-640 — antes de los tres carteles de guía sólo hacía falta un
        `bool` (había un único MessageTrigger_Once, MSG_01). Ahora se
        registra el ÍNDICE de cada disparador con `triggered=True`, no si
        "alguno" se disparó — el índice es estable entre respawns porque
        StageLoader reconstruye `message_triggers` en el mismo orden del
        .tmx cada vez. Ver el comentario de `_carteles_disparados` en
        `__init__` para el bug concreto que esto reemplaza.

        Se comprueba aquí, en `update()`, y no sólo en `on_stage_start()`
        (que es donde se reaplica) porque hace falta ver el
        `triggered=True` que `hazard_system.py` puso en algún fotograma
        anterior; `on_stage_start()` corre demasiado pronto para eso —
        antes de que el jugador haya podido pisar nada.
        """
        if self._stage_data is None:
            return
        for indice, mt in enumerate(self._stage_data.message_triggers):
            if mt.triggered:
                self._carteles_disparados.add(indice)

    def _aplicar_agarre_del_piso_trapeado(self) -> None:
        """Da vida al "piso recién trapeado" de la cocina (AUD-620).

        El `FrictionZone` con `inercia` no produce ningún resbalón en el
        jugador en suelo: `sistema_friccion` corre ANTES que `player.update`
        y `IdleState`/`WalkingState` sobreescriben `velocity.x` cada
        fotograma (grounded.py), revirtiendo el mezclado de `inercia` antes
        de la integración. Medido con la escena real: con y sin zona, al
        soltar la tecla el jugador frena de 90 px/s a 0 en un fotograma
        (resbalón 0.0 px en los dos casos).

        La única palanca que el jugador lee DENTRO de su update es
        `perfil.friccion` (la consume `_aplicar_friccion_y_aceleracion`
        justo antes de integrar el eje X) — el mismo mecanismo que el motor
        ya usa para el suelo mojado (`_aplicar_agarre` en simulacion.py).
        Mientras el jugador toca la zona se fija una fricción positiva:
        soltar la tecla decelera de walk_speed a 0 a ritmo acotado (el
        resbalón), y andar sigue siendo instantáneo (con `aceleracion` en 0,
        el objetivo ES la velocidad). Fuera de la zona se restaura 0 — el
        frenado instantáneo de siempre, un paso fuera y el resbalón termina.
        """
        if self._player is None or self._zona_trapeado is None:
            return
        if self._zona_trapeado.rect.colliderect(self._player.rect):
            self._player.perfil.friccion = self.FRICCION_PISO_TRAPEADO
        else:
            self._player.perfil.friccion = 0.0

    def _maybe_mute_exterior_enemies(self) -> None:
        """WalkerCulebra/FlyingZancudo solo existen en el camino exterior —
        apenas el cuarto activo pasa a "interior" (cruzando en vivo o
        cargando una partida ya adentro vía disarm_to_interior), se apagan
        todas sus instancias de una sola vez. No hace falta chequear
        posición: los dos tipos son exclusivos del camino."""
        if self._exterior_enemies_muted or self._room_transition.room != "interior":
            return
        if self._stage_data is not None:
            for entity in self._stage_data.entity_list:
                if isinstance(entity, (WalkerCulebra, FlyingZancudo)):
                    entity.deactivate()
        self._exterior_enemies_muted = True

    def _buscar_cocinero(self) -> ShooterCocinero | None:
        """El `ShooterCocinero` de la escena, si existe (AUD-650).

        Se puede buscar directo por `isinstance` porque `ShooterCocinero`
        ya está importado al tope de este archivo — a diferencia de
        `_PuertaDelCocinero._on_enemy_died`, que sólo tiene el
        `entity_id` de texto que trae `Events.ENEMY_DIED` (la instancia
        ya no está disponible ahí) y por eso filtra con
        `entity_id.startswith("ShooterCocinero")`. No cachea la
        instancia: `_stage_data.entity_list` se reconstruye entera en
        cada respawn (igual que el resto de esta clase), así que
        cachear un `ShooterCocinero` viejo lo dejaría apuntando a una
        instancia muerta de una vida anterior.
        """
        if self._stage_data is None:
            return None
        for entity in self._stage_data.entity_list:
            if isinstance(entity, ShooterCocinero):
                return entity
        return None

    def _detectar_golpe_al_cocinero(self, cocinero: ShooterCocinero | None) -> bool:
        """`True` si el cocinero recibió un golpe que de verdad conectó
        este fotograma (AUD-650), detectado por `current_health` que
        bajó respecto al último muestreo.

        Mismo mecanismo que ya usa `_GolpeYMuerteVisibles.apply_hit` en
        `entities.py` para el destello de las cinco plagas: comparar
        vida antes/después, porque `EnemyBase.apply_hit` es un no-op
        silencioso durante la invencibilidad post-golpe o si la entidad
        ya está en DYING (`enemy_base.py:507-510`) — comparar la salud
        es la forma de distinguir "conectó" de "no-op" sin duplicar esa
        condición acá. No hay ningún evento del motor con el
        `entity_id` de QUIÉN recibió el golpe (`Events.SFX_ENEMY_HIT` se
        emite sin datos, `enemy_base.py:520-523`), así que el muestreo
        por fotograma es la única señal disponible sin tocar
        `enemy_base.py` (fuera de alcance).
        """
        if cocinero is None or not cocinero.is_alive:
            self._cocinero_vida_anterior = None
            return False
        vida = cocinero.current_health
        golpe = (
            self._cocinero_vida_anterior is not None
            and vida < self._cocinero_vida_anterior
        )
        self._cocinero_vida_anterior = vida
        return golpe

    def on_stage_start(self) -> None:
        # Inicializar _room_transition antes de cualquier otro código que
        # intente accederlo (incluyendo super().on_stage_start() si fuese
        # llamado desde dentro de on_enter()). Solo se inicializa una vez;
        # en respawns posteriores permanece con su estado previo. Esta
        # preservación es intencional: permite que el room state (interior/exterior)
        # persista a través de una muerte + respawn. Combinado con clamp_one_way,
        # un jugador que muere sin alcanzar un checkpoint respawning en el spawn
        # inicial es inmediatamente reclampeado just-inside la puerta.
        if self._room_transition is None:
            self._room_transition = _RoomTransition(self._stage_data.map_pixel_size[0])
        # AUD-620 — la FrictionZone del piso trapeado se relee acá porque
        # `on_enter()` (incluido el respawn) reconstruye `_stage_data` entero.
        self._zona_trapeado = None
        if self._stage_data is not None:
            for grupo in self._stage_data.componentes:
                for componente in grupo:
                    if isinstance(componente, ZonaDeFriccion):
                        self._zona_trapeado = componente
                        break
        # entity_list se reconstruye en cada on_enter() (incluido respawn), así
        # que las instancias nuevas de WalkerCulebra/FlyingZancudo vuelven a
        # necesitar el apagado — sin este reset, _exterior_enemies_muted seguiría en True
        # de la vida anterior y las nuevas instancias nunca se apagarían.
        self._exterior_enemies_muted = False

        # AUD-641 — la puerta trasera de la cocina y su objetivo en pantalla.
        #
        # `on_stage_start()` corre en el primer arranque Y en cada
        # `respawn()` (`StageScene.on_enter()` lo llama al final). En un
        # respawn, `data = StageLoader.load(...)` (on_enter, arriba en la
        # jerarquía) reconstruye `_stage_data.entity_list` leyendo el .tmx
        # de nuevo — el `ShooterCocinero` que el jugador ya había matado
        # vuelve a existir, vivo, como instancia NUEVA — y también
        # reconstruye `_interactables`/`_stage_data.cerraduras`, así que
        # `Door_Trasera` vuelve a nacer `abierta=False`. Verificado leyendo
        # `on_enter()` (stage_scene.py:410-549): ninguna de las dos cosas
        # sobrevive al respawn, a diferencia de `_carteles_disparados` (que
        # si se preserva a propósito, ver __init__). Con el cocinero vivo
        # de nuevo Y la puerta cerrada de nuevo, el jugador NO queda
        # encerrado — sólo tiene que volver a vencerlo — así que lo
        # correcto es resetear los tres a su estado inicial en cada
        # arranque/respawn, no preservarlos.
        self._cocinero_vencido = False
        self._objetivo_cocinero = _ObjetivoCocinero()
        # AUD-650 — misma razón que _objetivo_cocinero, justo arriba: el
        # respawn repone al cocinero vivo con vida llena, así que la
        # barra tiene que volver a "oculto"/lista para su animación de
        # entrada, y la línea de base de detección de golpes se pierde
        # junto con la instancia vieja del ShooterCocinero.
        self._barra_jefe = _BarraDeJefe()
        self._cocinero_vida_anterior = None
        # AUD-645 — mismo criterio que _objetivo_cocinero justo arriba: si
        # el jugador muere antes de cruzar a la sala y reaparece afuera,
        # tiene que poder disparar la lectura de luz otra vez al volver a
        # cruzar, y los contornos de alerta cacheados por id() de una
        # entidad ya destruida en el respawn no sirven de nada.
        self._lectura_de_luz = _LecturaDeLuz()
        self._contorno_alerta = _ContornoDeAlerta()
        self._cerradura_puerta_trasera = None
        if self._stage_data is not None:
            for cerradura in self._stage_data.cerraduras:
                if cerradura.abre_con_evento == "cocinero_muerto":
                    self._cerradura_puerta_trasera = cerradura
                    break
        self._puerta_visual = (
            _PuertaTraseraVisual(self._cerradura_puerta_trasera.rect)
            if self._cerradura_puerta_trasera is not None else None
        )

        super().on_stage_start()
        if self._player is not None and self._player.position.x >= _RoomTransition.ROOM_LIMIT_X:
            self._room_transition.disarm_to_interior()
        # AUD-613 — reaplica sobre los MessageTrigger recién creados por
        # StageLoader (on_enter() los reconstruye en cada respawn, ver
        # _maybe_persist_carteles_disparados): sin esto, cada objeto nuevo
        # nace con triggered=False y hazard_system.py vuelve a mostrar el
        # cartel correspondiente cada vez que el jugador muere y reaparece.
        #
        # AUD-640 — por índice, no "todos si alguno se disparó" (ver el
        # comentario de `_carteles_disparados` en __init__): sólo se marca
        # `triggered=True` en los disparadores cuyo índice ya se vio antes,
        # el resto queda intacto para que el jugador los siga viendo.
        if self._stage_data is not None:
            for indice, mt in enumerate(self._stage_data.message_triggers):
                if indice in self._carteles_disparados:
                    mt.triggered = True
        # AUD-643 — reaplica las llaves ya recogidas sobre el `Llavero`/
        # `_stage_data.recogibles` recién reconstruidos por `on_enter()`
        # (ver el docstring de `_LlavesPersistentes` para el bug exacto que
        # esto cierra: sin esto, morir con la llave del depósito encima la
        # borra y el cofre vuelve a pedirla). Después de
        # `super().on_stage_start()` a propósito: ahí es donde el motor
        # termina de montar `_interactables` para este arranque/respawn.
        self._llaves_persistentes.reaplicar()
        # El mapa de La Soda es mucho más ancho que el viewport (3456px ancho
        # vs. 800px de pantalla), así que el fog-of-war del minimapa que se
        # revela a medida que avanzás (StageScene._update_minimap, que solo
        # hace explore_rect() de una caja de 160x120 alrededor del jugador
        # cada frame) nunca alcanza a mostrar la región completa pasivamente.
        # Marcar todo el mapa como explorado de una vez, al inicio, hace que
        # se vea como un mapa estático completamente mapeado desde el primer
        # frame. Los enemigos ya se dibujan como puntos rojos ahí
        # automáticamente (StageScene lee cada EnemyBase vivo en entity_list)
        # — no hace falta cablear nada extra.
        if self._stage_data is not None:
            self._minimap.explore_rect(
                pygame.Rect(0, 0, *self._stage_data.map_pixel_size),
            )

    def on_player_landed(self) -> None:
        super().on_player_landed()

    def on_enemy_died(self, enemy) -> None:
        super().on_enemy_died(enemy)

    def on_next_trigger_entered(self) -> None:
        super().on_next_trigger_entered()

    def on_debug_toggle(self, enabled: bool) -> None:
        super().on_debug_toggle(enabled)

    def dibujar_mundo(self, surface: pygame.Surface) -> None:
        """Extiende el mundo del framework con una barra de vida por
        enemigo, los glifos propios y demás capas que viven en espacio de
        MUNDO (se mueven con `self._camera.offset`). Nunca sobreescribe
        internals del framework directamente — solo dibuja encima, después
        de llamar a la implementación base.

        AUD-643 — por qué esto ya no se llama `draw()`. Diagnosticado con
        evidencia (`Claude - Uso General/playtest/repro_app_real.py`,
        capturas `AUD643_objetivo_real_*.png`): el letrero de objetivo (y,
        con él, TODO lo que este método agrega — barras de vida, íconos de
        llave/cofre, luciérnagas, la puerta trasera de madera, el marco de
        la puerta, el contorno de alerta de Sobel de AUD-645) nunca
        aparecía en el juego real aunque `_objetivo_
        cocinero.fase` sí llegaba a "visible" (la máquina de estados
        corre en `update()`, ajena a este bug). La causa: `App._draw()`
        (`src/engine/core/app.py:578-588,692-717`) NUNCA llama a
        `escena.draw()` para una `StageScene` — llama a
        `escena.dibujar_mundo(...)` y `escena.dibujar_ui(...)` por
        separado (el "camino de GPU" de AUD-343, activo tanto con
        renderizador GL como sin él: `_soporta(escena, "dibujar_mundo")`
        no depende de `usar_gl`). `DibujoDeEscenario.draw()` (la
        implementación heredada, `stage_parts/dibujo.py:46-62`) sí compone
        `dibujar_mundo()` + `dibujar_ui()` en ese orden, así que sobreescribir
        `draw()` funcionaba perfecto en headless (`render_real.py`,
        `sc.draw(surface)`, y el bot de `tests/playtest/bot.py`, que
        también llama `scene.draw()` directo) y nunca en `main.py --stage
        ...`, la única ruta que de verdad recorre un jugador. Repartir la
        extensión entre `dibujar_mundo`/`dibujar_ui` (en vez de `draw`)
        hace que las dos rutas —`sc.draw(...)` de las pruebas/headless (que
        sigue funcionando: la composición heredada llama a estos dos
        métodos por polimorfismo) y `App._draw()` del juego real— vean
        exactamente lo mismo. No hace falta sobreescribir `draw()`: la
        versión heredada ya hace `self.dibujar_mundo(surface);
        self.dibujar_ui(surface)`, y el despacho dinámico de Python resuelve
        esas llamadas contra ESTA clase.
        """
        super().dibujar_mundo(surface)
        # AUD-645 — Unidad VII: contorno de alerta por Sobel sobre el
        # sprite YA DIBUJADO del enemigo, antes de la barra de vida (que se
        # dibuja encima). Ver el docstring de _ContornoDeAlerta.
        self._contorno_alerta.actualizar_y_dibujar(surface, self._stage_data, self._camera.offset)
        self._draw_enemy_health_bars(surface)
        # AUD-639 — glifos propios de llave/cofre, encima del placeholder
        # genérico que ya pintó super().dibujar_mundo() (ver el comentario
        # de las constantes _COLOR_LLAVE_*/_COLOR_COFRE_* más arriba).
        self._dibujar_iconos_interactivos(surface)
        self._fireflies.draw(surface, self._camera.offset)
        # AUD-641 — la puerta trasera de la cocina, repintada como madera
        # encima del rectángulo plano que ya dibujó
        # `DrawingSystem._draw_interactables` en `super().dibujar_mundo()`
        # (mismo mecanismo que `_dibujar_llave`/`_dibujar_cofre` de AUD-639).
        if self._puerta_visual is not None:
            self._puerta_visual.draw(surface, self._camera.offset)
        # AUD-629 — el marco de la puerta va DESPUÉS de las entidades (ya
        # dibujadas por super().dibujar_mundo()): así el jugador se pierde
        # detrás del marco al cruzar el vano.
        self._marco_puerta.draw(surface, self._camera.offset)
        # AUD-646 — Unidad VII: lee (una sola vez) y aplica (cada
        # fotograma, blit barato) la "adaptación a la penumbra" AL FINAL de
        # dibujar_mundo, después de TODO lo demás del mundo (entidades,
        # contorno de alerta, iconos, puerta, marco). Antes (AUD-645) esto
        # vivía en dibujar_ui, ANTES de super().dibujar_ui() — ahí también
        # tiñe sólo lo ya pintado en `surface` en ese momento, pero
        # dibujar_ui es HUD/letreros: el overlay terminaba lavando la barra
        # de vida, los carteles y todo lo demás de la UI por igual, no sólo
        # el mundo (ver el docstring de _LecturaDeLuz para el diagnóstico
        # completo). Acá el mundo ya está 100% pintado y dibujar_ui todavía
        # no corrió, así que el teñido queda exclusivamente sobre el mundo.
        if self._room_transition is not None:
            self._lectura_de_luz.analizar_si_hace_falta(
                surface, self._room_transition.room, self.context.event_bus,
            )
            self._lectura_de_luz.dibujar_overlay(surface)

    def dibujar_ui(self, surface: pygame.Surface) -> None:
        """La mitad de pantalla (sin `self._camera.offset`) de la extensión
        de esta stage — ver el docstring de `dibujar_mundo` para el porqué
        de la partición (AUD-643). AUD-646: la "adaptación a la penumbra"
        de _LecturaDeLuz NO vive acá (ver el final de `dibujar_mundo`) —
        este método es sólo HUD/letreros, nunca el teñido del mundo."""
        super().dibujar_ui(surface)
        # El letrero de objetivo, en espacio de PANTALLA: es UI, no algo
        # que viva en el mundo.
        self._objetivo_cocinero.draw(surface)
        # AUD-650 — la barra de jefe, también en espacio de PANTALLA (no
        # se mueve con la sacudida de cámara, ver el docstring de
        # _SacudidaDeCamara).
        self._barra_jefe.draw(surface)
        # AUD-629 — el fundido a negro de la puerta va AL FINAL: tiene que
        # cubrir tanto al mundo como al resto de la UI de esta stage por
        # igual mientras está activo.
        if self._room_transition is not None:
            self._room_transition.draw(surface)

    def _draw_enemy_health_bars(self, surface: pygame.Surface) -> None:
        if self._stage_data is None:
            return
        offset = self._camera.offset
        for entity in self._stage_data.entity_list:
            if not (isinstance(entity, EnemyBase) and entity.is_alive):
                continue
            pct = max(0.0, min(1.0, entity.current_health / max(entity.max_health, 0.001)))
            if pct >= 1.0:
                continue  # solo se muestra una vez que efectivamente recibió daño
            bar_w = entity.rect.width
            x = int(entity.rect.x - offset.x)
            y = int(entity.rect.y - offset.y) - 6
            pygame.draw.rect(surface, (40, 10, 10), (x, y, bar_w, 3))
            # Unidad V — operación de espacio de color (ColorTools): el
            # matiz del relleno se desliza de verde (120 grados) con vida
            # completa a rojo (0 grados) a medida que baja pct, convertido
            # de HSV a RGB vía ColorTools.hsv_to_rgb, y luego horneado
            # sobre una pequeña superficie blanca con ColorTools.apply_tint
            # (Surface -> Surface) antes de dibujarla. Se observa
            # visualmente en el juego: la barra pasa de verde a amarillo a
            # rojo mientras el enemigo recibe daño.
            fill_w = max(1, int(bar_w * pct))
            # AUD-650 — factorizado a `_color_de_salud` (nivel de módulo)
            # para compartir exactamente esta fórmula con `_BarraDeJefe`.
            tint_rgb = _color_de_salud(pct)
            fill_surf = pygame.Surface((fill_w, 3))
            fill_surf.fill((255, 255, 255))
            fill_surf = ColorTools.apply_tint(fill_surf, tint_rgb)
            surface.blit(fill_surf, (x, y))

    def _dibujar_iconos_interactivos(self, surface: pygame.Surface) -> None:
        """Repinta llaves y cofres con un glifo propio, encima del
        placeholder genérico del framework.

        Por qué existe: `DrawingSystem._draw_interactables`
        (drawing_system.py:336-395) no distingue "esto es una llave" de
        "esto es un vaso de soda" — todo `Recogible` sin entrada en el
        catálogo de `Inventory` se pinta con el mismo cuadrado dorado
        (`_COLOR_RECOGIBLE`), y un `Cofre` es un rectángulo marrón que sólo
        cambia a gris al abrirse. La llave del depósito y el cofre que abre
        (ver `assets/maps/.../stage1_2_la_soda.tmx`, `Key_273`/`Chest_274`)
        quedaban indistinguibles de cualquier otro objeto del mapa.

        Fuente de datos y offset de cámara: mismo mecanismo que
        `_draw_enemy_health_bars` un poco más arriba — lee
        `self._interactables` (el `InteractableSystem` de la escena; lo
        reconstruye `StageScene.on_enter()`/`respawn()`, así que no hace
        falta cachearlo) y convierte cada `rect` de mundo a espacio de
        pantalla restando `self._camera.offset`. `getattr(sistema, ...,
        ())` por si la escena todavía no tiene `InteractableSystem` (antes
        de `on_stage_start`, o un motor distinto sin el sistema montado) —
        no debe romper el dibujado.
        """
        sistema = getattr(self, "_interactables", None)
        if sistema is None:
            return
        offset = self._camera.offset

        for objeto in getattr(sistema, "recogibles", ()):
            # Sólo las llaves (item_id que empieza con "llave_") se
            # repintan — el resto de los Recogibles del mapa (vasos,
            # cupones, servilletas...) se quedan con el cuadrado dorado de
            # siempre, que a ellos les queda bien.
            if objeto.recogido or not objeto.item_id.startswith("llave_"):
                continue
            r = pygame.Rect(
                int(objeto.rect.x - offset.x), int(objeto.rect.y - offset.y),
                objeto.rect.width, objeto.rect.height,
            )
            self._dibujar_llave(surface, r)

        for cofre in getattr(sistema, "cofres", ()):
            r = pygame.Rect(
                int(cofre.rect.x - offset.x), int(cofre.rect.y - offset.y),
                cofre.rect.width, cofre.rect.height,
            )
            self._dibujar_cofre(surface, r, cofre.abierto)

    def _dibujar_llave(self, surface: pygame.Surface, rect_pantalla: pygame.Rect) -> None:
        """Glifo de llave de 16×16: cabeza redonda + vástago con dos dientes.

        Se dibuja ENCIMA del cuadrado dorado que ya pintó
        `DrawingSystem._draw_interactables` en `super().dibujar_mundo()`
        (AUD-643 — antes `super().draw()`), sin taparlo antes con el color
        del tile de fondo: ese color cambia
        según en qué parte del mapa caiga la llave (tierra del camino,
        piso de la cocina...), así que repintar a mano arriesgaba
        desentonar con el suelo; el glifo, más grande que el hueco entre
        sus propios trazos, ya cubre casi todo el cuadrado de abajo.
        """
        x, y = rect_pantalla.topleft
        dorado = self._COLOR_LLAVE_DORADO
        contorno = self._COLOR_LLAVE_CONTORNO

        # Cabeza: círculo dorado con un "ojo" perforado en el centro (un
        # punto del color de contorno) para que se lea como anillo hueco —
        # el rasgo que distingue una llave de una simple moneda redonda.
        centro_cabeza = (x + 4, y + 8)
        radio_cabeza = 4
        pygame.draw.circle(surface, dorado, centro_cabeza, radio_cabeza)
        pygame.draw.circle(surface, contorno, centro_cabeza, radio_cabeza, 1)
        pygame.draw.circle(surface, contorno, centro_cabeza, 1)

        # Vástago: barra horizontal dorada con contorno de 1px, desde el
        # borde de la cabeza hasta cerca del borde derecho del ícono.
        vastago = pygame.Rect(x + 7, y + 7, 8, 3)
        pygame.draw.rect(surface, dorado, vastago)
        pygame.draw.rect(surface, contorno, vastago, 1)

        # Dos dientes: prongs cortos colgando del extremo derecho del
        # vástago, la seña visual de "esto es una llave, no una barra".
        for dx in (11, 13):
            diente = pygame.Rect(x + dx, y + 10, 2, 3)
            pygame.draw.rect(surface, dorado, diente)
            pygame.draw.rect(surface, contorno, diente, 1)

    def _dibujar_cofre(
        self, surface: pygame.Surface, rect_pantalla: pygame.Rect, abierto: bool,
    ) -> None:
        """Glifo de cofre de 16×16: cuerpo con listones, tapa curvada y
        cerrojo dorado; abierto levanta la tapa y aclara el interior.

        `abierto` decide todo el aspecto de la mitad superior del ícono: el
        cuerpo y los listones son iguales en los dos casos (el mueble no
        cambia), pero cerrado muestra una tapa curva con su cerrojo puesto
        y abierto la dibuja levantada —un cuadrilátero inclinado hacia
        atrás, como si girara sobre la bisagra del borde superior del
        cuerpo— dejando ver un interior más claro donde antes estaba la
        tapa. Es la señal que el jugador necesita para saber, de un
        vistazo, si ya vació este cofre.
        """
        x, y = rect_pantalla.topleft
        cuerpo = self._COLOR_COFRE_CUERPO
        liston = self._COLOR_COFRE_LISTON
        contorno = self._COLOR_COFRE_CONTORNO

        # Cuerpo: la mitad inferior del ícono, con dos listones horizontales
        # más claros — igual esté abierto o cerrado, el mueble es el mismo.
        cuerpo_rect = pygame.Rect(x, y + 7, 16, 9)
        pygame.draw.rect(surface, cuerpo, cuerpo_rect)
        pygame.draw.rect(surface, contorno, cuerpo_rect, 1)
        pygame.draw.line(surface, liston, (x + 1, y + 10), (x + 14, y + 10))
        pygame.draw.line(surface, liston, (x + 1, y + 13), (x + 14, y + 13))

        if abierto:
            # Interior más claro: el hueco que deja la tapa levantada,
            # visible sobre la parte superior del cuerpo.
            interior = pygame.Rect(x + 2, y + 9, 12, 6)
            pygame.draw.rect(surface, self._COLOR_COFRE_INTERIOR, interior)
            # Tapa levantada: un cuadrilátero que va del borde superior del
            # cuerpo (la "bisagra") hacia arriba y ligeramente hacia atrás,
            # simulando el giro sin necesitar rotación real de pygame.
            tapa = [
                (x + 2, y + 7), (x + 14, y + 7),
                (x + 15, y - 3), (x + 3, y - 3),
            ]
            pygame.draw.polygon(surface, self._COLOR_COFRE_TAPA, tapa)
            pygame.draw.polygon(surface, contorno, tapa, 1)
        else:
            # Tapa curvada en la mitad superior — el border_radius es lo
            # que la distingue de un simple rectángulo, la misma curva que
            # pide la consigna.
            tapa_rect = pygame.Rect(x, y, 16, 8)
            pygame.draw.rect(surface, self._COLOR_COFRE_TAPA, tapa_rect, border_radius=4)
            pygame.draw.rect(surface, contorno, tapa_rect, 1, border_radius=4)
            # Cerrojo dorado a caballo entre tapa y cuerpo — el punto donde
            # un cofre de verdad lleva el candado.
            cerrojo = pygame.Rect(x + 6, y + 6, 4, 5)
            pygame.draw.rect(surface, self._COLOR_COFRE_CERROJO, cerrojo)
            pygame.draw.rect(surface, contorno, cerrojo, 1)
