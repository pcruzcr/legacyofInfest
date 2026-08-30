"""
Module: stage1_1
System: stage (student assignment)
Academic Unit: II (Vectores), III (Curvas), IV (Escena/Z-order), V (Color)
Description: Escenario 1-1 "La Entrada" — sendero de montaña selvática que
sube hacia la Universidad Invenio. Demuestra matemática vectorial explícita
(JungleFrog y su proyectil), trayectorias Bézier definidas en Tiled
(CanopyBird) y una pasada de color ámbar de atardecer con ColorTools.

Estudiante: Fabrizio Espinoza Arce
Diseño de referencia: docs/16_WORLD_DESIGN.md §3.2

Ejecutar con:
   python main.py --stage stage1_1
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.stage_loader import StageLoader
from src.stages.stage1_1.animation.sol_poniente import (
    EVENTO_SOL_EN_EL_HORIZONTE,
    SolPoniente,
)
from src.stages.stage1_1.entities.canopy_bird import CanopyBird
from src.stages.stage1_1.entities.jungle_frog import JungleFrog
from src.stages.stage1_1.overlays.debug_overlay import DebugOverlay
from src.stages.stage1_1.processing.adaptacion_visual import AdaptacionVisual
from src.stages.stage1_1.processing.enfoque_bordes import EnfoqueBordes
from src.stages.stage1_1.processing.sunset_light import SunsetLight

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage1_1_LaEntrada(StageScene):
    """Escenario 1-1 — La Entrada (Zona 1, Universidad Invenio).

    Un sendero largo y solitario que asciende por la montaña selvática.
    Dosel denso arriba, roca y raíz abajo; el camino se angosta conforme se
    avanza. Sin fosos: el castigo es únicamente el contacto con enemigos
    (docs/16_WORLD_DESIGN.md §3.2).

    Conceptos académicos demostrados:
      · Unidad II  — vec2_distance dispara la IA de la rana por proximidad;
                     vec2_normalize da rapidez constante al proyectil;
                     vec2_dot resuelve la orientación del sprite.
      · Unidad III — el ave del dosel recorre una Bézier cúbica cuyos puntos
                     de control se definen como objetos Waypoint en Tiled.
      · Unidad IV  — las 8 capas obligatorias del TMX y el orden de dibujo.
      · Unidad V   — tinte ámbar derivado por conversión HSV y compuesto con
                     alpha blend, que se profundiza conforme el jugador avanza.
    """

    STAGE_ID: str = "stage1_1"
    STAGE_NAME: str = "1-1  LA ENTRADA"
    ZONE: int = 1
    #: Lo que manda es la propiedad `time_limit` del .tmx; esta constante es
    #: el respaldo del framework. Se suben las dos a 300 s: con 180 no daba
    #: tiempo de explorar el nivel ni de recorrer la lista de pruebas del
    #: enunciado, y al llegar a cero el jugador muere.
    TIME_LIMIT: int = 300
    BGM_TRACK: str = "bgm_stage0"
    TILE: int = 16

    TMX_PATH = "assets/maps/stage1_1/stage1_1.tmx"

    # Interruptor de enemigos — AYUDA TEMPORAL DE DESARROLLO.
    #
    # Permite recorrer el nivel sin combate mientras se ajusta la geometría
    # y el aspecto. Los enemigos se quitan en tiempo de ejecución: el .tmx
    # NO cambia, así que scripts/grade_stage.py sigue contando sus 11
    # enemigos y dando 126/130.
    #
    # Para jugar sin bichos, sin tocar código:
    #     $env:SIN_BICHOS = "1"
    # o con el script:
    #     .\claude-workspace\jugar.ps1 -SinBichos
    #
    # El valor por defecto del entregable es CON enemigos.
    ENEMIGOS_ACTIVOS: bool = True

    # ── Cartelitos de controles al empezar ──────────────────────────
    # (texto, segundos en pantalla). Se emiten como SHOW_MESSAGE; la
    # MessageBox del motor los ENCOLA, así que salen uno tras otro sin
    # pisarse (message_box.py:75 y :127-128).
    #
    # NO SE REPITE LO QUE EL MOTOR YA ENSEÑA. `TutorialScene` tiene cuatro
    # páginas accesibles desde la pantalla de título que cubren mover,
    # saltar, agacharse, los dos ataques, el dash, el parry, el agarre, el
    # ultimate y el combo aéreo. Repetir aquí esos controles entrena al
    # jugador a ignorar los carteles.
    #
    # Aquí sólo van las tres cosas que ese tutorial NO puede saber: hacia
    # dónde se va en este escenario, qué obstáculo propio tiene, y la tecla
    # de diagnóstico que sólo existe en este nivel.
    #
    # OJO CON EL LARGO: cada tip cabe en UNA línea del cuadro de mensajes.
    # `tests/test_tips.py` lo comprueba con el partidor real del motor y a
    # la MAYOR escala de accesibilidad, que es el peor caso.
    TIPS_INICIO: tuple[tuple[str, float], ...] = (
        ("Sendero a la Universidad Invenio. Subi a la entrada.", 4.0),
        ("Salta de piedra en piedra para cruzar el sendero.", 5.0),
        ("F1 dibuja las curvas de las aves y los vectores.", 5.0),
    )

    #: Segundos de espera antes de soltar los tips, contados desde que
    #: arranca el nivel. El banner de entrada dura 2,9 s y ocupa la misma
    #: zona de pantalla que la caja de mensajes.
    RETARDO_TIPS: float = 4.0

    @classmethod
    def tips_de_inicio(cls) -> tuple[tuple[str, float], ...]:
        return cls.TIPS_INICIO

    def __init__(self, context: GameContext) -> None:
        # AUD-591 — el registro de las dos entidades propias vivía aquí
        # dentro y el validador lo llevaba años avisando: las herramientas que
        # abren el TMX sin construir la escena (previsualizador, calificador)
        # no ejecutan `__init__`, así que resolvían esos tipos con la clase
        # del bestiario. Ahora registra el módulo al importarse (ver abajo),
        # como hacen boss_paburu (AUD-151) y stage1_3_las_aulas.
        #
        # Se registran sobre dos especies REALES del bestiario del framework
        # (`bestiary_registry.SPECIES`): "ShooterFrog" es la rana dardo y
        # "FlyingBird" el ave de selva, que es exactamente lo que son estas
        # dos clases. Antes se usaban "Skitter" y "Bat", dos nombres que
        # estaban en la lista del calificador y que ninguna clase reclamaba.
        # Dejó de valer: el cargador ahora ABORTA el nivel entero ante un
        # type que no esté registrado, y el calificador carga el TMX por su
        # cuenta sin pasar por esta escena. Con los nombres inventados el
        # nivel no se podía analizar y se perdían de golpe los 30 puntos de
        # diseño.
        #
        # Registrar sobre una especie existente la sustituye para todo el
        # proceso, no solo para este escenario. Es aceptable porque ningún
        # otro escenario del juego coloca estas dos especies, pero conviene
        # saberlo: `register_entity` escribe en un diccionario de clase y no
        # tiene contrapartida para deshacerlo.
        super().__init__(context, Path(self.TMX_PATH))
        self._sunset = SunsetLight()
        self._overlay = DebugOverlay()
        self._sol = SolPoniente()
        self._adaptacion = AdaptacionVisual()
        self._enfoque = EnfoqueBordes()
        # Los tips esperan a que el banner de entrada libere la pantalla.
        self._tips_pendientes: list[tuple[str, float]] = []
        self._tiempo_en_escena: float = 0.0

    # ── Hooks de ciclo de vida ──────────────────────────────────────

    # ── Unidad IV — scroll del tilemap ──────────────────────────────

    @staticmethod
    def sincronizar_scroll(map_layer: Any, camera_offset: pygame.Vector2) -> None:
        """Desplaza el mapa de tiles para que acompañe a la cámara.

        POR QUÉ EXISTE ESTE MÉTODO
        --------------------------
        `StageScene.update()` mueve el mapa asignando directamente
        `map_layer._map_layer.view_rect` (stage_scene.py:268 y :1004). En pyscroll
        eso cambia el valor del rectángulo pero **no reposiciona el búfer
        interno de tiles**, así que `draw()` vuelve a pintar exactamente lo
        mismo: el fondo se queda clavado mientras las entidades sí se
        mueven con `camera.offset`.

        El desplazamiento real solo ocurre llamando `center()`, que
        recalcula el offset del búfer y repinta los tiles que entran en
        vista. Comprobado con pyscroll 2.30, y reproducible igual en el
        `stage0.tmx` del profesor — no es un problema de este escenario.

        `stage_scene.py` es del profesor y no se toca: se corrige desde
        aquí, llamando a la API correcta después de que corra su update.

        CONVERSIÓN: `center()` espera el CENTRO de la vista y
        `camera.offset` es la esquina superior izquierda, así que hay que
        sumarle media pantalla.
        """
        if map_layer is None:
            return
        map_layer.center((
            camera_offset.x + settings.INTERNAL_WIDTH // 2,
            camera_offset.y + settings.INTERNAL_HEIGHT // 2,
        ))


    def update(self, dt: float) -> None:
        super().update(dt)
        self._bombear_tips(dt)
        # El sol avisa UNA vez al tocar el horizonte. Se consulta después del
        # update del motor para que `stage_progress()` ya refleje la posición
        # de este fotograma.
        self._sol.revisar_horizonte(self.stage_progress(), self.context.event_bus)
        # Unidad VII — la tecla de enfoque se lee aquí; el filtro se aplica
        # en draw(), que es donde existe el fotograma sobre el que operar.
        self._enfoque.actualizar(EnfoqueBordes.leer_teclado())

        if self._stage_data is not None:
            self.sincronizar_scroll(
                self._stage_data.map_layer, self._camera.offset,
            )

        self._animar_cartel_final(dt)

    def _animar_cartel_final(self, dt: float) -> None:
        """Anima el cartel «STAGE COMPLETE», que el motor deja congelado.

        EL DEFECTO, MEDIDO. Al tocar la salida el escenario hace dos cosas en
        el mismo fotograma (`stage_scene.py:1188-1191`): pone
        `stage_complete = True` y lanza el cartel. Pero el bloque que anima la
        interfaz está guardado por esa misma bandera
        (`stage_scene.py:797`)::

            if not self._game_over and not self._progression.stage_complete:
                ...
                self._update_hud_ui(dt)    # unico sitio que anima el cartel
                self._update_timers(dt)    # y el otro

        O sea que al completar el nivel deja de actualizarse justo lo que
        tenia que animar el cartel de nivel completado. Se queda en su estado
        inicial `slide_in` con el desplazamiento de partida —1600, que son dos
        anchos de pantalla— y `draw()` lo pinta en `bx = 1600 - 800 = 800`:
        una pantalla entera a la derecha, fuera de cuadro. Se dibuja los 174
        fotogramas y no se ve ni uno.

        Medido con el jugador puesto en la salida::

            f    t       completo  timer  estado     offset
            0    0.00s   True      2.88   slide_in   1600.0
            90   1.50s   True      1.38   slide_in   1600.0
            180  3.00s   True     -0.02   slide_in   1600.0

        Congelado los tres segundos. El cartel del NOMBRE del nivel, en
        cambio, funciona perfecto —`slide_in` -> `hold` en `bx = 0` ->
        `slide_out`—, porque en el arranque la bandera es falsa. El sistema de
        carteles esta sano; lo unico roto es el caso del final.

        Y hay una pista de que es un descuido y no una decision: dentro de
        `_update_timers` hay un `if self._progression.stage_complete:`. Es
        codigo inalcanzable — solo se llama cuando la bandera es falsa, y su
        cuerpo exige que sea verdadera. Alguien escribio el manejo del final y
        la condicion de fuera lo dejo muerto.

        POR QUE SE ARREGLA DESDE AQUI. El defecto es del motor y la regla del
        repositorio es reportarlo, no tocarlo — va como F-016 en
        `claude-workspace/12-REPORTE-DE-BUGS.md`. Esto no lo corrige: llama al
        `update` que el motor se salta, desde el escenario propio, que es
        codigo mio. Si algun dia el motor lo arregla, esta llamada se vuelve
        inofensiva: `ScreenBanner.update` sale sola cuando el estado es
        `idle`, y llamarla dos veces en el mismo fotograma solo adelantaria la
        animacion, cosa que no puede pasar porque la del motor sigue sin
        ejecutarse mientras la bandera este puesta.
        """
        if self._banner is None:
            return
        if self._progression.stage_complete:
            self._banner.update(dt)

    # ── Corrección: spawn inválido de una partida guardada vieja ────

    @staticmethod
    def spawn_es_valido(
        posicion: pygame.Vector2,
        alto_jugador: int,
        solidos: list[pygame.Rect],
        margen: float = 64.0,
    ) -> bool:
        """¿Hay suelo sólido bajo los pies, a menos de `margen` píxeles?

        EL FALLO QUE COMPENSA
        ---------------------
        `StageScene.on_enter()` reposiciona al jugador en el checkpoint de
        la partida guardada (stage_scene.py:170) sin comprobar que esa
        coordenada siga siendo válida. Si el mapa cambió desde que se
        guardó —que es lo normal mientras se diseña— el jugador aparece en
        el aire y cae. Como solo pasa cuando hay partida cargada, el
        síntoma es intermitente.

        Caso real observado: `saves/slot_1.json` guardaba
        `checkpoint_y = 243` de una versión anterior del mapa; en la nueva,
        el suelo de esa columna está en y = 512. El jugador nacía 269 px
        por encima del suelo.
        """
        pies = posicion.y + alto_jugador
        for r in solidos:
            if r.left <= posicion.x < r.right and r.top >= pies - 1:
                if r.top - pies <= margen:
                    return True
        return False

    # ── Interruptor de enemigos ─────────────────────────────────────

    @staticmethod
    def filtrar_enemigos(entidades: list[Any]) -> list[Any]:
        """Devuelve la lista sin ninguna instancia de EnemyBase."""
        from src.framework.entities.enemy_base import EnemyBase
        return [e for e in entidades if not isinstance(e, EnemyBase)]

    @classmethod
    def enemigos_habilitados(cls) -> bool:
        """La variable de entorno SIN_BICHOS tiene prioridad sobre la
        constante, para poder alternar sin editar código."""
        if os.environ.get("SIN_BICHOS", "").strip() in ("1", "true", "True"):
            return False
        return cls.ENEMIGOS_ACTIVOS

    def on_exit(self) -> None:
        """Se da de baja del evento propio antes de dejar el escenario.

        El `EventBus` es global y vive más que la escena: dejar la suscripción
        puesta significa que un `SolPoniente` muerto siga contestando en el
        siguiente nivel.
        """
        self.context.event_bus.unsubscribe(
            EVENTO_SOL_EN_EL_HORIZONTE, self._al_ponerse_el_sol)
        super().on_exit()

    def _al_ponerse_el_sol(self, **datos: object) -> None:
        """Reacción al evento propio del escenario (Unidad VI)."""
        from src.engine.core.events import Events
        self.context.event_bus.emit(
            Events.SHOW_MESSAGE,
            text="El sol se mete tras el cerro. Apura el paso.",
            duration=4.0,
        )

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """Unidad VI — el sol, animado con easing, DETRÁS del mapa.

        `StageScene.dibujar_fondo()` (AUD-162) se llama después del parallax y
        antes de las baldosas, así que las colinas de `BG_Far` tapan el disco:
        el sol *se pone tras el paisaje*. Desde `draw()` se pintaría encima de
        todo y flotaría delante de las montañas.
        """
        super().dibujar_fondo(surface, offset)
        self._sol.draw(surface, self.stage_progress())

    def on_stage_start(self) -> None:
        """Se llama tras cargar el escenario y completar el setup."""
        super().on_stage_start()

        # Unidad VI — la otra mitad de la interacción. Emitir un evento que
        # nadie escucha no es una interacción: es un `print`. El escenario se
        # suscribe a su PROPIO evento (el del sol) y responde.
        self._sol.reiniciar()
        self._adaptacion.reiniciar()
        self.context.event_bus.subscribe(
            EVENTO_SOL_EN_EL_HORIZONTE, self._al_ponerse_el_sol)

        # No se emiten aquí: quedarían tapados por el banner de entrada.
        # update() los suelta al cumplirse RETARDO_TIPS.
        self._tips_pendientes = list(self.tips_de_inicio())
        self._tiempo_en_escena = 0.0

        # Descartar el checkpoint de una partida guardada que ya no encaja
        # con la geometría actual del mapa (ver spawn_es_valido).
        if self._player is not None and self._stage_data is not None:
            if not self.spawn_es_valido(
                self._player.position,
                self._player.rect.height,
                self._stage_data.collision_rects,
            ):
                seguro = self._stage_data.spawn_point
                print(f"[stage1_1] checkpoint guardado inválido en "
                      f"{tuple(int(v) for v in self._player.position)}: no hay "
                      f"suelo debajo. Reubicando en {tuple(int(v) for v in seguro)}")
                self._player.position.update(seguro)
                self._player.rect.topleft = (int(seguro.x), int(seguro.y))
                self._player.velocity.update(0.0, 0.0)
                self._player.set_spawn(pygame.Vector2(seguro))
                self._checkpoint_position = pygame.Vector2(seguro)

        if not self.enemigos_habilitados() and self._stage_data is not None:
            antes = len(self._stage_data.entity_list)
            self._stage_data.entity_list = self.filtrar_enemigos(
                self._stage_data.entity_list,
            )
            quitados = antes - len(self._stage_data.entity_list)
            print(f"[stage1_1] SIN BICHOS: {quitados} enemigos "
                  f"desactivados (el .tmx no cambia)")

    @classmethod
    def puede_mostrar_tips(cls, transcurrido: float) -> bool:
        """¿Pasaron ya los segundos de espera desde que arrancó el nivel?

        El banner "1-1 LA ENTRADA" ocupa el centro de la pantalla durante
        2,9 s (0,5 de entrada + 2,0 sostenido + 0,4 de salida,
        screen_banner.py:21-23), y la caja de mensajes se dibuja en la
        misma zona. Con 4 s el banner ya salió y queda un margen cómodo.
        """
        return transcurrido >= cls.RETARDO_TIPS

    def _bombear_tips(self, dt: float) -> None:
        """Suelta los tips pendientes al cumplirse el retardo de entrada.

        Se usa `Events.SHOW_MESSAGE` porque la `MessageBox` del motor lo
        escucha y ENCOLA los mensajes cuando ya hay uno visible
        (message_box.py:75 y :127-128): basta emitirlos todos de golpe y salen en
        orden, uno tras otro. Es el mismo evento que usa el profesor en
        src/stages/stage0/stage0.py:177.
        """
        if not self._tips_pendientes:
            return
        self._tiempo_en_escena += dt
        if not self.puede_mostrar_tips(self._tiempo_en_escena):
            return

        from src.engine.core.events import Events
        for texto, duracion in self._tips_pendientes:
            self.context.event_bus.emit(
                Events.SHOW_MESSAGE, text=texto, duration=duracion,
            )
        self._tips_pendientes = []

    def on_player_landed(self) -> None:
        """Se llama cuando el jugador toca suelo tras estar en el aire."""
        pass

    def on_enemy_died(self, enemy) -> None:
        """Se llama cuando muere un enemigo."""
        pass

    def on_next_trigger_entered(self) -> None:
        """Se llama cuando el jugador toca el NextTrigger (fin del nivel)."""
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        """Se llama al pulsar F1. Alterna el overlay de curvas y vectores.

        Solo cambia el estado; el dibujo va en draw(), que corre cada
        fotograma. Pintar aquí directamente —como hace stage0.py:187— no
        sirve: lo que se dibuje se pierde en el siguiente fotograma.
        """
        self._overlay.toggle(enabled)

    # ── Unidad V — pase de luz de atardecer ─────────────────────────

    def stage_progress(self) -> float:
        """Avance horizontal del jugador por el sendero, en [0, 1].

        Alimenta la intensidad del atardecer: el mundo se calienta y
        oscurece conforme se sube hacia la universidad, así que el color
        también funciona como indicador de progreso.
        """
        if self._player is None or self._stage_data is None:
            return 0.0
        ancho = self._stage_data.map_pixel_size[0]
        if ancho <= 0:
            return 0.0
        return max(0.0, min(1.0, self._player.position.x / ancho))

    def draw(self, surface: pygame.Surface) -> None:
        """El motor dibuja TODAS las capas de tiles de una sola pasada antes
        que las entidades (drawing_system.py:221, dentro de su unico `draw`), así que FG_Overlay no
        queda por encima del jugador. Este override es el punto donde se
        añade lo que sí debe ir al frente — empezando por el pase de color
        de la Unidad V. Mismo patrón que usa el profesor en
        src/stages/stage0/stage0.py:182-185.
        """
        super().draw(surface)
        self._sunset.apply(surface, self.stage_progress())

        # ── Unidad VII ────────────────────────────────────────────────
        #
        # El ORDEN importa. La adaptación mide DESPUÉS del tinte ámbar de la
        # Unidad V porque lo que tiene que corregir es lo que el jugador ve
        # de verdad, no la escena sin teñir: el tinte es justamente una de
        # las cosas que apagan el contraste al final del nivel.
        self._adaptacion.actualizar(surface)
        self._adaptacion.apply(surface)

        # Y el realce de contornos va al final del pase de color, para que
        # los bordes que dibuja no se vuelvan a corregir ni a teñir: son una
        # lectura de la escena, no parte de ella.
        self._enfoque.apply(surface)

        # El overlay va DESPUÉS del pase de color: son líneas de diagnóstico
        # y deben conservar su color puro, sin teñirse de ámbar.
        if self._overlay.enabled and self._stage_data is not None:
            entidades = self._stage_data.entity_list
            self._overlay.draw(
                surface,
                self._camera.offset,
                [e for e in entidades if isinstance(e, CanopyBird)],
                [e for e in entidades if isinstance(e, JungleFrog)],
            )


# AUD-591 — el registro de las dos entidades propias vivía dentro de
# `Stage1_1_LaEntrada.__init__` y el validador lo llevaba años avisando
# («registro dentro de una función»): las herramientas que abren el TMX sin
# construir la escena —previsualizador, calificador, validador— no ejecutan
# `__init__`, así que resolvían "ShooterFrog" y "FlyingBird" con la clase del
# bestiario y salía un pájaro genérico donde debía estar el CanopyBird de la
# Unidad III, sin que nada fallara. Registrar al importar el módulo hace que
# jugar, previsualizar, calificar y validar vean el mismo mundo; es lo que el
# propio aviso ordena y lo que ya practican boss_paburu (AUD-151) y
# stage1_3_las_aulas. El porqué de los nombres elegidos está comentado en
# `Stage1_1_LaEntrada.__init__`.
StageLoader.register_entity("ShooterFrog", JungleFrog)
StageLoader.register_entity("FlyingBird", CanopyBird)
