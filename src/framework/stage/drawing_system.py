from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.render.sprite_batch import SpriteBatch
from src.framework.stage import culling
from src.framework.stage.profundidad import EscalaPorProfundidad
from src.framework.vfx.sombras import Sombra

logger = logging.getLogger(__name__)

#: AUD-279 — margen de dibujado, en píxeles alrededor del encuadre.
#:
#: Más pequeño que el de simulación (400) porque responde a otra pregunta: no
#: «¿puede esto afectar a lo que veo dentro de tres segundos?», sino «¿asoma
#: ahora mismo por el borde?». 64 px es cuatro veces el lado de una baldosa y
#: cubre de sobra al sprite más grande del bestiario.
_MARGEN_DIBUJADO: int = 64

if TYPE_CHECKING:
    from src.engine.ui.hud import HUD
    from src.engine.ui.message_box import MessageBox
    from src.engine.ui.screen_banner import ScreenBanner
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData
    from src.framework.ui.dialogue_system import DialogueSystem
    from src.framework.ui.learning_overlay import LearningOverlay
    from src.framework.ui.tutorial_overlay import TutorialOverlay
    from src.framework.vfx.ambient_particles import AmbientParticleSystem
    from src.framework.vfx.damage_numbers import DamageNumberManager
    from src.framework.vfx.particle_system import ParticleSystem
    from src.framework.vfx.trail_system import TrailSystem
    from src.framework.vfx.weather_system import WeatherSystem


@dataclass
class DrawContext:
    surface: pygame.Surface
    stage: StageData | None = None
    player: Player | None = None
    checkpoints: list[Any] | None = None
    camera: Camera | None = None
    hud: HUD | None = None
    msg_box: MessageBox | None = None
    banner: ScreenBanner | None = None
    paused: bool = False
    pause_selected: int = 0
    pause_options: list[str] | None = None
    particle_system: ParticleSystem | None = None
    damage_numbers: DamageNumberManager | None = None
    ambient_particles: AmbientParticleSystem | None = None
    weather_system: WeatherSystem | None = None
    trail_system: TrailSystem | None = None
    #: Estela de enemigos, separada de la del jugador para que las dos
    #: puedan ser continuas (comparten temporizador de intervalo).
    enemy_trail_system: TrailSystem | None = None
    tutorial_overlay: TutorialOverlay | None = None
    learning_overlay: LearningOverlay | None = None
    dialogue_system: DialogueSystem | None = None
    #: F4.1 — recogibles, cerraduras, cofres y disparadores.
    interactables: Any | None = None
    debug: bool = False
    #: AUD-285 — el mundo ECS, **sólo** para dibujar conos de visión con F1.
    #:
    #: Los conos no son entidades: viven como componente `ConoDeVision` en el
    #: `World`, y sin esta referencia el gizmo no tendría de dónde sacarlos. Se
    #: pasa como `Any` y se lee con `getattr` para que el sistema de dibujado no
    #: dependa del ECS por una herramienta de depuración.
    mundo: Any | None = None
    #: AUD-162 — pintura propia del escenario, DETRÁS del mapa de baldosas.
    #:
    #: Un escenario podía dibujar encima de todo —sobreescribiendo `draw()` y
    #: llamando a `super()` primero— y no podía dibujar **detrás**: lo primero
    #: que hace este método es `surface.fill(BG_COLOR)`, así que cualquier cosa
    #: pintada antes se borraba.
    #:
    #: El 4-1 necesita justo eso: una luna que baja y las siluetas de los
    #: espíritus vencidos, que por canon están «en el fondo» y «no atacan,
    #: testifican». Sin este gancho habría que meterlas en el motor —una luna
    #: en `DrawingSystem` sería una mecánica de un solo nivel viviendo en el
    #: sitio de todos— o dibujarlas encima del jugador, que las convertiría en
    #: primer plano y contradiría el canon.
    #:
    #: Recibe `(surface, offset)` y se llama después del parallax y antes del
    #: mapa. Un escenario que no lo use no paga nada.
    fondo_del_escenario: Any | None = None


class DrawingSystem:
    def __init__(self) -> None:
        self._bg_tiles: dict[tuple[int, int, int], pygame.Surface] = {}
        self._pause_overlay: pygame.Surface | None = None
        self._pause_font = pygame.font.Font(None, 20)
        self._debug_font = pygame.font.Font(None, 14)
        #: AUD-135 — lienzo del agua, cacheado al tamaño de la pantalla.
        self._agua_cache: pygame.Surface | None = None
        self._peligro_cache: pygame.Surface | None = None
        #: AUD-273 — la sombra bajo los pies. Sin ella, un salto largo sobre un
        #: hueco es una apuesta: la cámara sigue al personaje y en el pico del
        #: salto el suelo queda fuera de la vista útil.
        self._sombra = Sombra()

    def draw(self, ctx: DrawContext) -> None:
        surface = ctx.surface
        stage = ctx.stage
        player = ctx.player
        checkpoints = ctx.checkpoints or []
        camera = ctx.camera
        surface.fill(settings.BG_COLOR)

        if stage is None:
            return

        if camera is None:
            return

        offset = camera.offset

        # Draw order, back to front. Parallax backdrops first, then the tile
        # map, then world-space effects, then entities, then screen-space UI.
        self._draw_background(surface, stage, camera)
        if ctx.fondo_del_escenario is not None:
            # AUD-162 — el escenario pinta su propio fondo aquí, entre el
            # parallax y el mapa. Un fallo suyo no puede tumbar el fotograma:
            # es decoración, y el nivel tiene que seguir jugándose.
            try:
                ctx.fondo_del_escenario(surface, offset)
            except Exception:
                logger.warning(
                    "el fondo propio del escenario falló; se sigue dibujando",
                    exc_info=True,
                )
        self._draw_stage_layers(surface, stage, camera)

        if ctx.particle_system:
            ctx.particle_system.draw(surface, offset)
        if ctx.weather_system:
            ctx.weather_system.draw(surface, offset)
        if ctx.ambient_particles:
            ctx.ambient_particles.draw(surface, offset)

        # F4.1: los objetos se dibujan ANTES que las entidades, para que el
        # jugador pase por delante de una llave del suelo y no al revés.
        if ctx.interactables is not None:
            self._draw_interactables(surface, ctx.interactables, offset)

        self._draw_entities(surface, stage, player, checkpoints, offset)

        # AUD-135 — la inundación, DESPUÉS de las entidades y por delante de
        # ellas: el jugador tiene que verse sumergido, no flotando encima de un
        # rectángulo azul. Una zona de daño que no se ve es una trampa; una que
        # sube y no se ve es peor, porque cambia sin avisar.
        self._draw_inundaciones(surface, stage, offset)
        self._draw_zonas_de_dano(surface, stage, offset)

        if ctx.enemy_trail_system:
            ctx.enemy_trail_system.draw(surface, offset)
        if ctx.trail_system:
            ctx.trail_system.draw(surface, offset)
        if ctx.damage_numbers:
            ctx.damage_numbers.draw(surface, offset)

    #: Agua de la inundación: turquesa oscuro y translúcido. El alfa es lo que
    #: hace que se siga viendo el nivel debajo, que es lo que el jugador
    #: necesita para planear la subida.
    _COLOR_INUNDACION = (40, 120, 170, 110)
    _COLOR_SUPERFICIE = (150, 220, 240)

    def _draw_inundaciones(
        self, surface: pygame.Surface, stage: Any, offset: pygame.Vector2,
    ) -> None:
        """Dibuja las `HazardZone` que suben. De las fijas se ocupa
        `_draw_zonas_de_dano`.

        Aquí ponía que una zona fija «se dibuja con tiles: el diseñador pinta
        pinchos o lava y el rectángulo sólo marca dónde duele». Ese contrato no
        estaba escrito en ninguna parte y no se cumplía — ver AUD-228 —, así que
        las fijas se pintan también, con otro color y otro pulso. Una que sube
        no puede apoyarse en tiles en ningún caso, porque los tiles no se mueven.

        La superficie se cachea una vez al tamaño de la pantalla y luego se
        recorta con `area=`. Repintar un rectángulo con alfa cada fotograma
        costaría una asignación por fotograma, que es justo lo que AUD-023
        vino a quitar.
        """
        zonas = [
            hz for hz in getattr(stage, "hazard_zones", ())
            if getattr(hz, "sube_de_verdad", False)
        ]
        if not zonas:
            return

        ancho, alto = surface.get_size()
        agua = self._agua_cache
        if agua is None or agua.get_size() != (ancho, alto):
            agua = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            agua.fill(self._COLOR_INUNDACION)
            self._agua_cache = agua

        pantalla = surface.get_rect()
        for hz in zonas:
            r = hz.rect.move(-int(offset.x), -int(offset.y))
            visible = r.clip(pantalla)
            if visible.width <= 0 or visible.height <= 0:
                continue
            surface.blit(agua, visible.topleft, pygame.Rect(0, 0, visible.width, visible.height))
            # La línea de superficie: sin ella el borde del agua se pierde
            # contra el fondo y no se puede juzgar si una plataforma ya está
            # cubierta, que es la única decisión que el jugador toma aquí.
            if pantalla.top <= r.top <= pantalla.bottom:
                pygame.draw.line(
                    surface, self._COLOR_SUPERFICIE,
                    (visible.left, r.top), (visible.right, r.top), 2,
                )

    #: Rojo de aviso para las zonas de daño fijas. Deliberadamente distinto del
    #: turquesa de la inundación: son dos cosas distintas y el jugador tiene que
    #: poder separarlas de un vistazo.
    _COLOR_PELIGRO = (215, 70, 55, 255)
    _COLOR_BORDE_PELIGRO = (255, 160, 120)

    def _draw_zonas_de_dano(
        self, surface: pygame.Surface, stage: StageData,
        offset: pygame.Vector2,
    ) -> None:
        """Pinta las zonas de daño **fijas** (AUD-228).

        Hasta ahora el motor sólo dibujaba las que suben. El contrato implícito
        para las fijas era que el diseñador pintara pinchos o lava en las
        baldosas y que el rectángulo sólo marcara dónde duele — pero ese
        contrato no estaba escrito en ninguna parte y no se cumplía. Los dos
        únicos mapas del proyecto con una `HazardZone` fija son `stage0`, que es
        el que los estudiantes copian, y `stage3_3_el_patio`, y **ninguno de los
        dos** tenía arte debajo: se perdía salud desde un rectángulo invisible.

        El comentario de `_draw_inundaciones` ya decía la regla —«una zona de
        daño que no se ve es una trampa»— y sólo se la aplicaba al agua.

        Late en vez de estar fija porque un tinte quieto se lee como parte del
        decorado, y lo que hay que comunicar es que eso está **activo**. Un mapa
        que sí trae su propio arte apaga esto con `visible=false` en el TMX.
        """
        zonas = [
            hz for hz in getattr(stage, "hazard_zones", ())
            if not getattr(hz, "sube_de_verdad", False)
            and getattr(hz, "avisar", True)
            and getattr(hz, "activa", True)
        ]
        if not zonas:
            return

        ancho, alto = surface.get_size()
        tinte = self._peligro_cache
        if tinte is None or tinte.get_size() != (ancho, alto):
            # Una sola superficie, cacheada al tamaño de la pantalla y recortada
            # con `area=`. Repintar un rectángulo con alfa cada fotograma es la
            # asignación por fotograma que AUD-023 vino a quitar.
            tinte = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            tinte.fill(self._COLOR_PELIGRO)
            self._peligro_cache = tinte

        # El pulso viene del reloj de SDL y no de un `dt` acumulado: este método
        # no recibe delta, y pedirlo obligaría a tocar la firma de `draw` y las
        # 26 escenas que la usan.
        fase = (pygame.time.get_ticks() % 1400) / 1400.0
        tinte.set_alpha(int(48 + 42 * (1.0 - abs(fase * 2.0 - 1.0))))

        pantalla = surface.get_rect()
        for hz in zonas:
            r = hz.rect.move(-int(offset.x), -int(offset.y))
            visible = r.clip(pantalla)
            if visible.width <= 0 or visible.height <= 0:
                continue
            surface.blit(
                tinte, visible.topleft,
                pygame.Rect(0, 0, visible.width, visible.height),
            )
            # El borde superior, opaco: es el que dice exactamente dónde empieza
            # a doler, y es la única decisión que el jugador toma aquí.
            if pantalla.top <= r.top <= pantalla.bottom:
                pygame.draw.line(
                    surface, self._COLOR_BORDE_PELIGRO,
                    (visible.left, r.top), (visible.right, r.top), 1,
                )

    #: Colores de los objetos interactivos. Se dibujan con formas planas y no
    #: con sprites porque el motor no puede suponer qué arte tiene cada
    #: escenario: un rectángulo del color correcto siempre se ve, y el
    #: estudiante puede sustituirlo por su propio sprite cuando lo tenga.
    _COLOR_RECOGIBLE = (240, 210, 90)
    _COLOR_CERRADA = (150, 110, 70)
    _COLOR_JAULA = (120, 120, 135)
    _COLOR_COFRE = (185, 140, 70)
    _COLOR_ABIERTO = (90, 90, 100)

    def _draw_interactables(
        self, surface: pygame.Surface, sistema: Any, offset: pygame.Vector2,
    ) -> None:
        """Llaves, puertas, jaulas y cofres.

        Los disparadores **no se dibujan**: son zonas invisibles a propósito,
        igual que `MessageTrigger`. Verlos rompería la sorpresa que el
        diseñador buscaba al ponerlos.
        """
        # AUD-234 — cada objeto del catálogo se pinta de su color.
        #
        # Todos salían del mismo amarillo, así que una moneda de oro, una
        # llave roja y una vasija de corazón eran tres rectángulos idénticos.
        # Desde AUD-218 los enemigos sueltan monedas y el suelo se llena de
        # recogibles: sin distinguirlos, el jugador no sabe si eso de ahí es la
        # llave que le falta o el cambio de matar a un esbirro.
        #
        # `ItemDef.icon_color` llevaba desde el principio en el catálogo y sólo
        # lo leía el aviso de recogida. Un `item_id` libre —el que invente un
        # estudiante— no está en el catálogo y conserva el color de siempre,
        # así que ninguno de los niveles entregados cambia de aspecto.
        from src.engine.core.inventory import get_inventory
        inventario = get_inventory()
        for objeto in getattr(sistema, "recogibles", ()):
            if objeto.recogido:
                continue
            r = objeto.rect.move(-offset.x, -offset.y)
            defn = inventario.get_def(objeto.item_id)
            color = defn.icon_color if defn is not None else self._COLOR_RECOGIBLE
            pygame.draw.rect(surface, color, r, border_radius=3)
            pygame.draw.rect(surface, (60, 50, 20), r, 1, border_radius=3)

        for cerradura in getattr(sistema, "cerraduras", ()):
            r = cerradura.rect.move(-offset.x, -offset.y)
            if cerradura.abierta:
                # Abierta se dibuja como marco: el hueco se ve atravesable, que
                # es la información que el jugador necesita.
                pygame.draw.rect(surface, self._COLOR_ABIERTO, r, 2)
                continue
            color = self._COLOR_JAULA if cerradura.clase == "jaula" else self._COLOR_CERRADA
            pygame.draw.rect(surface, color, r)
            pygame.draw.rect(surface, (40, 30, 20), r, 2)
            if cerradura.clase == "jaula":
                # Barrotes: hacen la jaula distinguible de una puerta de un
                # vistazo, sin depender del color.
                for x in range(r.left + 6, r.right - 2, 8):
                    pygame.draw.line(surface, (40, 40, 50), (x, r.top + 2), (x, r.bottom - 2), 2)

        for cofre in getattr(sistema, "cofres", ()):
            r = cofre.rect.move(-offset.x, -offset.y)
            pygame.draw.rect(
                surface, self._COLOR_ABIERTO if cofre.abierto else self._COLOR_COFRE, r,
                border_radius=2,
            )
            pygame.draw.rect(surface, (60, 40, 20), r, 2, border_radius=2)
            if not cofre.abierto:
                pygame.draw.line(
                    surface, (60, 40, 20),
                    (r.left + 2, r.centery), (r.right - 2, r.centery), 2,
                )

    def draw_ui(self, ctx: DrawContext) -> None:
        """Interfaz en espacio de pantalla. Se dibuja DESPUÉS de la luz.

        AUD-090 — la iluminación estaba oscureciendo la interfaz
        --------------------------------------------------------
        Hasta ahora todo esto se pintaba dentro de `draw`, es decir, **antes**
        de `LightSystem.render` y `PostProcessing.apply`. Mientras el brillo
        ambiente valía 1,0 daba igual: multiplicar por uno no hace nada. Al
        encender la iluminación en la fase 1 y bajarlo a 0,59, la luz del mundo
        empezó a multiplicar también el HUD.

        Medido en Stage 0: el HUD perdía el **58 %** de su brillo, y el
        indicador de combo pasaba de 406 píxeles amarillos a **cero**. El
        jugador veía subir el daño y no veía el «COMBO x3».

        Es un defecto que introduje yo al encender la luz, y su forma es la de
        siempre en este proyecto: el código del combo era correcto, la llamada
        estaba, el valor llegaba al HUD. Lo que fallaba era el orden.

        Una interfaz es espacio de pantalla: la luz de una antorcha del nivel
        no puede alcanzarla, igual que no la alcanza la niebla ni el clima.
        """
        surface = ctx.surface
        if ctx.stage is None or ctx.camera is None:
            return

        if ctx.learning_overlay:
            ctx.learning_overlay.draw(surface)
        if ctx.tutorial_overlay:
            ctx.tutorial_overlay.draw(surface)
        if ctx.dialogue_system:
            # Espacio de pantalla, no de mundo: el cuadro de diálogo se ancla
            # al viewport y no toma desplazamiento de cámara (AUD-039).
            ctx.dialogue_system.draw(surface)

        if ctx.hud:
            ctx.hud.draw(surface)
        if ctx.msg_box:
            ctx.msg_box.draw(surface)
        if ctx.banner:
            ctx.banner.draw(surface)

        if ctx.paused:
            self._draw_pause_menu(surface, ctx.pause_selected, ctx.pause_options or [])

        if ctx.debug:
            self._draw_debug(surface, ctx.stage, ctx.player, ctx.camera,
                             ctx.camera.offset, ctx.mundo)

    # Parallax speed per backdrop layer, far to near. Index 0 is the most
    # distant layer and therefore moves least.
    _PARALLAX_FACTORS: tuple[float, ...] = (0.15, 0.35, 0.6, 0.8)

    def _draw_background(
        self, surface: pygame.Surface, stage: StageData, camera: Camera,
    ) -> None:
        """Blit the parallax backdrop layers behind the tile map.

        Rewritten (AUD-039). The previous implementation called
        ``stage.draw_background(...)`` guarded by ``hasattr`` — and ``StageData``
        has no such method, so the guard was permanently False and no backdrop
        was ever drawn. A second helper iterated ``stage.background_objects``,
        an attribute that does not exist either, which is what raised
        ``AttributeError`` on the first gameplay frame.

        What the loader actually produces is ``stage.background_layers``: a list
        of ``pygame.Surface`` ordered far to near. That is what we draw.
        """
        layers = getattr(stage, "background_layers", None)
        if not layers:
            return

        view_w = surface.get_width()
        view_h = surface.get_height()
        # AUD-329 — el wrap del parallax NO se bachea, y no es un pendiente.
        #
        # Se intentó con `SpriteBatch` y se midió en el mapa real: con las
        # tres capas de 4-1 y seis copias por fotograma, el lote costaba
        # 2,4-3,0 ms y el blit a blit 0,8-1,4 ms. Se revirtió.
        #
        # AUD-330 — esa diferencia no se reproduce. Re-medida en la misma
        # máquina, con áreas de vista completa y N de 2 a 20, el lote empata
        # (0,97-1,03×) y con recortes de 32 px gana ya desde dos llamadas
        # (0,73-0,82×). El 2-3× de AUD-329 era carga de máquina, la misma que
        # hacía flak-ear el test del presupuesto de fotograma.
        #
        # Se mantiene el blit suelto, y el motivo correcto es el empate: seis
        # llamadas de pantalla completa son seis, no crecen con el contenido,
        # y un lote que no gana es código que sobra. El umbral automático de
        # `SpriteBatch` queda en 1 — agrupar siempre — porque es lo que la
        # medición entera sostiene.
        for index, layer in enumerate(layers):
            if not isinstance(layer, pygame.Surface):
                continue
            # AUD-272 — la velocidad la publica el cargador, atada al **nombre**
            # de la capa. La tabla por índice se queda como respaldo para un
            # `StageData` construido a mano, que es lo que hacen varias
            # entregas y varias pruebas.
            factores = getattr(stage, "background_factors", None) or ()
            if index < len(factores):
                factor = float(factores[index])
            else:
                factor = self._PARALLAX_FACTORS[
                    min(index, len(self._PARALLAX_FACTORS) - 1)]
            layer_w = layer.get_width()
            layer_h = layer.get_height()
            if layer_w <= 0 or layer_h <= 0:
                continue
            # AUD-225: el desplazamiento vertical no estaba acotado. Se
            # calculaba `-offset.y * factor * 0.5` y luego se pegaba **una**
            # copia extra debajo, lo que bastaba para los mapas de 38 filas
            # —donde la cámara apenas se mueve en vertical— y para ninguno más.
            #
            # El 4-1 pasó a ser un pozo de 240 filas: con la cámara a 3.000 px
            # de profundidad el fondo subía 900 px y por debajo no quedaba
            # cielo, sólo el color de borrado.
            #
            # Se acota en vez de repetir, y no es lo mismo. `_try_append_bg`
            # escala **todas** las capas al tamaño de la pantalla, así que
            # repetir en vertical significa ver el mismo horizonte una vez por
            # pantalla de profundidad —una costura cada 600 px— y además cuesta
            # cuatro pegados por capa en lugar de dos. Acotado, el cielo se
            # queda donde está mientras se baja, que es lo que hace un cielo.
            #
            # El eje horizontal sí se envuelve: ahí la repetición es la que
            # permite que una capa más estrecha que el mapa cubra el recorrido.
            shift_x = int(camera.offset.x * factor) % layer_w
            margen = max(0, layer_h - view_h)
            y = -min(margen, max(0, int(camera.offset.y * factor * 0.5)))
            x = -shift_x
            while x < view_w:
                surface.blit(layer, (x, y))
                x += layer_w

    def _draw_stage_layers(
        self, surface: pygame.Surface, stage: StageData, camera: Camera,
    ) -> None:
        """Render the tile map.

        AUD-039: this used to look for ``stage.tile_layer`` and
        ``stage.top_layer``, neither of which exists. ``StageLoader`` builds a
        ``pyscroll.PyscrollGroup`` and stores it as ``stage.map_layer``; nothing
        in the codebase ever drew it, so **the tile map has never appeared on
        screen**. Both lookups used ``getattr(..., None)`` and silently did
        nothing, which is why this went unnoticed for so long — a missing
        attribute raises, a defaulted one just quietly renders an empty world.
        """
        map_layer = getattr(stage, "map_layer", None)
        if map_layer is None:
            return

        # pyscroll centres on a world point; the camera stores a top-left
        # offset, so convert.
        centre = (
            int(camera.offset.x + surface.get_width() // 2),
            int(camera.offset.y + surface.get_height() // 2),
        )
        try:
            map_layer.center(centre)
            # PyscrollGroup.draw takes only the target surface.
            map_layer.draw(surface)
        except (AttributeError, TypeError, pygame.error):
            # A stage built without a real pyscroll group (tests, student
            # templates in progress) must not take the whole frame down. Logged
            # at warning, not debug: if the map stops rendering in a real build
            # that is a headline failure, and burying it at debug is how the
            # previous silent-getattr version hid the same problem (AUD-039).
            logger.warning(
                "DrawingSystem: tile map could not be drawn — the world will "
                "render empty", exc_info=True,
            )

    def _draw_entities(
        self, surface: pygame.Surface, stage: StageData,
        player: Player | None, checkpoints: list[Any],
        offset: pygame.Vector2,
    ) -> None:
        """Dibuja jugador, enemigos y checkpoints ordenados por profundidad.

        AUD-067: al reescribir este módulo perdí dos cosas de golpe.

        **El jugador.** Este bucle recorría `stage.entity_list`, que contiene
        sólo enemigos. El personaje no se dibujaba en ninguna parte: se veía el
        escenario moverse, el polvo del dash, la cámara siguiéndolo — todo
        menos al protagonista. `ctx.player` quedó usándose únicamente en el
        overlay de depuración, que pinta un rectángulo cian; por eso con F1 se
        "veía" algo y sin F1 no.

        **El orden por profundidad.** El original construía una lista de
        dibujables y la ordenaba por `rect.centery`, de modo que lo que está
        más abajo en pantalla —más cerca de la cámara— se pinta encima. Sin
        eso, el orden lo decidía la lista de entidades del TMX: un enemigo del
        fondo podía taparle la cara al jugador según en qué orden lo colocara
        el mapa.

        Los checkpoints entran en la misma ordenación, no después. Antes se
        dibujaban al final, encima de todo, así que un checkpoint tapaba al
        jugador que estaba delante de él.
        """
        drawables: list[tuple[Any, int]] = []

        if player is not None:
            drawables.append((player, player.rect.centery))

        # AUD-279 — lo que no toca la pantalla no entra en la lista.
        #
        # `blit` ya recorta solo, así que saltarse el dibujado de un enemigo
        # lejano ahorra poco. Lo que ahorra de verdad es todo lo que este método
        # hace **por dibujable** antes de dibujarlo: una sombra proyectada
        # contra todos los sólidos del mapa (AUD-273) y, con 2.5D activo, un
        # `transform.scale` del sprite (AUD-277). Eso sí se paga entero aunque
        # el resultado caiga fuera del encuadre.
        #
        # El margen aquí es de un cuarto del que usa la simulación: dibujar es
        # una decisión de este fotograma, y basta con cubrir el sprite más
        # grande que pueda asomar por el borde.
        zona = culling.zona_de_dibujado(offset, _MARGEN_DIBUJADO)
        for entity in stage.entity_list:
            if entity is None or not entity.is_visible or not entity.is_alive:
                continue
            if not culling.dentro(entity.rect, zona):
                continue
            drawables.append((entity, entity.rect.centery))

        for checkpoint in checkpoints:
            if hasattr(checkpoint, "draw"):
                drawables.append((checkpoint, checkpoint.rect.centery))

        drawables.sort(key=lambda pair: pair[1])

        # AUD-273 — las sombras van **todas antes** que las entidades, no cada
        # una justo antes de la suya. Intercaladas, la sombra de un enemigo
        # cercano se pintaría encima de otro que está detrás y más abajo, y se
        # leería como una mancha flotando sobre su cabeza.
        solidos = getattr(stage, "collision_rects", None) or []
        if solidos:
            # AUD-302 — las sombras van en un lote. Son todas iguales salvo la
            # talla, y con la caché de elipses la mayoría comparten superficie:
            # N llamadas de Python se convierten en una.
            lote = SpriteBatch()
            for drawable, _depth in drawables:
                rect = getattr(drawable, "rect", None)
                if rect is not None and getattr(drawable, "proyecta_sombra", True):
                    self._sombra.dibujar(surface, rect, solidos, offset, lote)
            lote.volcar(surface)

        escala = self._escala_de_profundidad(stage)
        for drawable, _depth in drawables:
            # AUD-289 — el `draw` de una entidad de estudiante también puede
            # lanzar, y aquí el daño sería peor que en el `update`: media escena
            # ya está pintada, así que el fotograma se quedaría a medias sobre
            # el anterior y el resultado no se parece a un error, se parece a un
            # fallo de vídeo. Se salta esa entidad y se sigue pintando.
            #
            # No se retira aquí: quien decide qué entidades hay en el nivel es la
            # escena, y un sistema de dibujado que borra entidades es la clase de
            # atajo que después nadie sabe de dónde salió.
            try:
                if escala.activa:
                    self._dibujar_con_profundidad(surface, drawable, offset, escala)
                else:
                    drawable.draw(surface, offset)
            except Exception:
                if not getattr(settings, "AISLAR_FALLOS_DE_ENTIDAD", True):
                    raise
                logger.exception("%s falló al dibujarse; se salta este fotograma",
                                 type(drawable).__name__)

    def _escala_de_profundidad(self, stage: Any) -> EscalaPorProfundidad:
        """La escala 2.5D de este escenario, cacheada por escenario (AUD-277).

        Se cachea porque `activa` se consulta una vez por entidad y por
        fotograma, y construir el objeto cada vez sería pagar por una
        funcionalidad que casi ningún mapa enciende.
        """
        if getattr(self, "_prof_stage", None) is not stage:
            alto = getattr(stage, "map_pixel_size", (0, 0))[1]
            self._prof_stage = stage
            self._prof = EscalaPorProfundidad(
                mapa_alto=alto,
                minimo=float(getattr(stage, "profundidad_min", 1.0)),
                maximo=float(getattr(stage, "profundidad_max", 1.0)),
            )
        return self._prof

    def _dibujar_con_profundidad(
        self, surface: pygame.Surface, drawable: Any,
        offset: pygame.Vector2, escala: EscalaPorProfundidad,
    ) -> None:
        """Dibuja la entidad a su escala, en una superficie aparte.

        Se pinta a un lienzo del tamaño de la entidad y se escala eso, en vez
        de pedirle a la entidad que se dibuje pequeña: las entidades de las
        veintiséis entregas no saben de escala y no van a aprender — su
        `draw(surface, offset)` es el contrato, y esto lo respeta.

        Se ancla por los **pies**: una entidad que encoge desde su esquina
        superior flotaría sobre el suelo, y el suelo es lo único que el jugador
        usa para juzgar dónde está algo.
        """
        rect = getattr(drawable, "rect", None)
        if rect is None or rect.width <= 0 or rect.height <= 0:
            drawable.draw(surface, offset)
            return
        factor = escala.escala_en(rect.bottom)
        if abs(factor - 1.0) < 0.01:
            drawable.draw(surface, offset)      # no merece la pena el rodeo
            return

        lienzo = pygame.Surface(rect.size, pygame.SRCALPHA)
        # Se le pasa un desplazamiento que sitúa a la entidad en el origen del
        # lienzo: así `draw` no tiene que saber que está dibujando aparte.
        drawable.draw(lienzo, pygame.Vector2(rect.x, rect.y))
        ancho = max(1, int(rect.width * factor))
        alto = max(1, int(rect.height * factor))
        escalado = pygame.transform.scale(lienzo, (ancho, alto))
        surface.blit(escalado, (
            int(rect.centerx - ancho / 2 - offset.x),
            int(rect.bottom - alto - offset.y),
        ))

    def _draw_pause_menu(
        self, surface: pygame.Surface, selected: int, options: list[str],
    ) -> None:
        if self._pause_overlay is None:
            self._pause_overlay = pygame.Surface(
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            )
        self._pause_overlay.set_alpha(160)
        self._pause_overlay.fill((0, 0, 0))
        surface.blit(self._pause_overlay, (0, 0))

        cx = settings.INTERNAL_WIDTH // 2
        cy = settings.INTERNAL_HEIGHT // 2 - (len(options) * 30) // 2
        for i, opt in enumerate(options):
            color = (255, 255, 100) if i == selected else (200, 200, 200)
            label = f"> {opt}" if i == selected else f"  {opt}"
            text = self._pause_font.render(label, True, color)
            surface.blit(text, (cx - text.get_width() // 2, cy + i * 30))

    def _draw_debug(
        self, surface: pygame.Surface, stage: StageData | None,
        player: Player | None, camera: Camera, offset: pygame.Vector2,
        mundo: Any | None = None,
    ) -> None:
        if stage is None:
            return
        for entity in stage.entity_list:
            if entity is None:
                continue
            screen_x = int(entity.position.x - offset.x)
            screen_y = int(entity.position.y - offset.y)
            rect = getattr(entity, 'rect', None)
            if rect is not None:
                pygame.draw.rect(surface, (0, 255, 0), (screen_x, screen_y, rect.width, rect.height), 1)
            hurtbox = getattr(entity, 'hurtbox', None)
            if hurtbox is not None:
                hx = int(hurtbox.x - offset.x)
                hy = int(hurtbox.y - offset.y)
                pygame.draw.rect(surface, (255, 0, 0), (hx, hy, hurtbox.width, hurtbox.height), 1)
            hitbox = getattr(entity, 'hitbox', None)
            if hitbox is not None:
                hx2 = int(hitbox.x - offset.x)
                hy2 = int(hitbox.y - offset.y)
                pygame.draw.rect(surface, (0, 0, 255), (hx2, hy2, hitbox.width, hitbox.height), 1)
        if player is not None and hasattr(player, 'rect') and player.rect is not None:
            px = int(player.position.x - offset.x)
            py = int(player.position.y - offset.y)
            pygame.draw.rect(surface, (0, 255, 255), (px, py, player.rect.width, player.rect.height), 2)

        # AUD-285 — los dos gizmos que faltaban.
        #
        # Las cajas dicen dónde está algo; ninguna dice **hacia dónde va** ni
        # **qué está viendo**. Los dos datos existen y no se podían mirar: la
        # velocidad, para diagnosticar un enemigo que se queda pegado a una
        # pared o un knockback que sale al revés; el cono, para entender por
        # qué un guardia detecta a través de media pantalla.
        self._dibujar_velocidades(surface, stage, player, offset)
        self._dibujar_conos(surface, mundo, offset)

        fps = self._debug_font.render(f"Entities: {len(stage.entity_list)}", True, (255, 255, 255))
        surface.blit(fps, (5, settings.INTERNAL_HEIGHT - 60))
        cam_pos = self._debug_font.render(f"Cam: {int(offset.x)},{int(offset.y)}", True, (255, 255, 255))
        surface.blit(cam_pos, (5, settings.INTERNAL_HEIGHT - 40))

    #: AUD-285 — segundos de velocidad que representa el vector dibujado.
    #:
    #: Un cuarto de segundo: la flecha marca **dónde estaría dentro de 250 ms**
    #: si nada la parase. Dibujar la velocidad a escala 1 daría flechas de 500 px
    #: para una caída normal, que taparían el nivel; a escala arbitraria, la
    #: longitud no significaría nada. Así la flecha es una predicción legible.
    _GIZMO_SEGUNDOS: float = 0.25

    def _dibujar_velocidades(
        self, surface: pygame.Surface, stage: StageData,
        player: Player | None, offset: pygame.Vector2,
    ) -> None:
        """Una flecha por entidad con velocidad, del centro hacia donde va."""
        cuerpos = list(stage.entity_list)
        if player is not None:
            cuerpos.append(player)
        for cuerpo in cuerpos:
            if cuerpo is None:
                continue
            velocidad = getattr(cuerpo, "velocity", None)
            rect = getattr(cuerpo, "rect", None)
            if velocidad is None or rect is None:
                continue
            if abs(velocidad.x) < 1.0 and abs(velocidad.y) < 1.0:
                # Parado. Dibujar un punto por cada entidad quieta llena la
                # pantalla de basura y esconde las que sí se mueven.
                continue
            origen = (int(rect.centerx - offset.x), int(rect.centery - offset.y))
            destino = (int(origen[0] + velocidad.x * self._GIZMO_SEGUNDOS),
                       int(origen[1] + velocidad.y * self._GIZMO_SEGUNDOS))
            pygame.draw.line(surface, (255, 0, 255), origen, destino, 1)
            pygame.draw.circle(surface, (255, 0, 255), destino, 2)

    def _dibujar_conos(
        self, surface: pygame.Surface, mundo: Any | None, offset: pygame.Vector2,
    ) -> None:
        """El cono de visión de cada vigilante, y si te está viendo.

        Rojo cuando ve al jugador y amarillo cuando no: es la única forma de
        contestar «¿por qué me ha detectado?» sin leer el código. El cono se
        dibuja con el **barrido ya aplicado**, o sea mirando adonde mira ahora,
        y no en su orientación de reposo — que es justo la diferencia entre un
        gizmo útil y uno que miente.
        """
        if mundo is None:
            return
        try:
            from src.framework.ecs.components import ConoDeVision, Transform
        except ImportError:  # pragma: no cover - el ECS siempre está
            return
        for entidad, cono in mundo.cada(ConoDeVision):
            t = mundo.obtener(entidad, Transform)
            if t is None:
                continue
            centro = pygame.Vector2(t.rect.center) - offset
            base = math.atan2(cono.mira.y, cono.mira.x)
            oscilacion = math.radians(
                math.sin(math.radians(cono._fase)) * cono.barrido,
            ) if cono.barrido > 0.0 else 0.0
            semi = math.radians(cono.semiangulo)
            color = (255, 60, 60) if cono.ve_al_jugador else (220, 220, 60)
            puntos = [centro]
            # Cinco radios bastan para leer la apertura sin pagar un polígono
            # denso por cada vigilante en una herramienta de depuración.
            for i in range(5):
                ang = base + oscilacion - semi + (2 * semi) * i / 4.0
                puntos.append(centro + pygame.Vector2(
                    math.cos(ang), math.sin(ang)) * cono.alcance)
            pygame.draw.lines(surface, color, True,
                              [(int(p.x), int(p.y)) for p in puntos], 1)
