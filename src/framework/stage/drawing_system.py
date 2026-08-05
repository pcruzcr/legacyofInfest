from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.framework.vfx.sombras import Sombra

logger = logging.getLogger(__name__)

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
                             ctx.camera.offset)

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

        for entity in stage.entity_list:
            if entity is None or not entity.is_visible or not entity.is_alive:
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
            for drawable, _depth in drawables:
                rect = getattr(drawable, "rect", None)
                if rect is not None and getattr(drawable, "proyecta_sombra", True):
                    self._sombra.dibujar(surface, rect, solidos, offset)

        for drawable, _depth in drawables:
            drawable.draw(surface, offset)

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

        fps = self._debug_font.render(f"Entities: {len(stage.entity_list)}", True, (255, 255, 255))
        surface.blit(fps, (5, settings.INTERNAL_HEIGHT - 60))
        cam_pos = self._debug_font.render(f"Cam: {int(offset.x)},{int(offset.y)}", True, (255, 255, 255))
        surface.blit(cam_pos, (5, settings.INTERNAL_HEIGHT - 40))
