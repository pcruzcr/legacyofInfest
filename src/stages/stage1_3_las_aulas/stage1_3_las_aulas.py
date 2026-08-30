"""
Module: stage1_3_las_aulas
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

Autor: Yariel — Zona 1, nivel 3 "Las Aulas"

Probar con:
   python main.py --stage stage1_3_las_aulas
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.math_utils import ease_out_bounce
from src.framework.processing.filter_tools import FilterTools
from src.framework.scenes.stage_scene import StageScene

# Importar registra los tipos propios en StageLoader, para que los objetos
# de esos tipos en el TMX se instancien solos.
from src.stages.stage1_3_las_aulas import estudiante_infectado  # noqa: F401  (Unidad II)
from src.stages.stage1_3_las_aulas.cuaderno_volador import CuadernoVolador  # (Unidad III)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage1_3_LasAulas(StageScene):
    """Zona 1 (Universidad) — nivel 3: Las Aulas.

    TODO(student): describir el contexto narrativo del nivel y los
    conceptos academicos que demuestra (Unidades II, III, IV y V).
    """

    STAGE_ID: str = "stage1_3_las_aulas"
    STAGE_NAME: str = "STAGE 1-3 — LAS AULAS"
    ZONE: int = 1

    TMX_PATH = "assets/maps/stage1_3_las_aulas/stage1_3_las_aulas.tmx"

    # ── Casillero interactivo (Practica II, Unidad VI) ──────────────
    # Mismas coordenadas que el objeto "Door" que coloca generar_mapa.py
    # (CASILLERO_COL/FILA ahi) y el tile CASILLERO que dibuja BG_NEAR: los
    # tres tienen que coincidir o la puerta animada queda flotando en otro
    # sitio que el rectangulo interactivo real.
    _CASILLERO_X = 62 * 16
    _CASILLERO_Y = 33 * 16
    _CASILLERO_ANCHO = 2 * 16
    _CASILLERO_ALTO = 3 * 16
    _CASILLERO_DURACION = 0.6  # segundos que tarda en abrirse del todo

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        self._casillero_animando = False
        self._casillero_t = 0.0

    # ── Fondo lejano segun su propio histograma (Practica II, Unidad VII) ──
    # Por debajo de esta luminancia media (0-255) el fondo "far" se trata
    # como zona en penumbra: se difumina mas fuerte (para que se lea como
    # "al fondo, entre bruma") y se le sube el brillo un poco para que no se
    # pierda contra el negro del canvas de mezcla de generar_fondos.py. Por
    # encima, un difuminado mas suave y sin tocar el brillo. El valor no es
    # arbitrario: se midio con compute_histogram() sobre el fondo real
    # (62.1/255) antes de fijar este umbral — ver README, seccion Unidad VII.
    _UMBRAL_PENUMBRA = 100.0

    def on_enter(self) -> None:
        super().on_enter()
        self._habilitar_fondo_transparente()
        self._procesar_fondo_lejano()
        # "CASILLERO_ABIERTO" lo emite InteractableSystem (framework, sin
        # tocar) cuando el jugador abre el objeto "Door" que puso
        # generar_mapa.py — ver su property "evento". Suscribirse aqui, en la
        # subclase, es la interaccion propia de EventBus que pide la Unidad
        # VI: el framework solo sabe que una puerta se abrio, la animacion
        # (Unidad VI: easing) es enteramente del escenario.
        self.context.event_bus.subscribe("CASILLERO_ABIERTO", self._on_casillero_abierto)

    def _procesar_fondo_lejano(self) -> None:
        """Difumina la capa "far" del parallax, con el kernel elegido por su
        propio histograma (Unidad VII).

        `stage_loader.py` guarda las 3 capas en `background_layers` en orden
        far/mid/near (ver `VELOCIDAD_DE_FONDO`), asi que la mas lejana es
        siempre el indice 0. `compute_histogram()` no es cosmetico aqui: su
        salida (la luminancia media) decide CUAL matriz de convolucion se
        aplica y si hace falta subir el brillo despues — es la propia
        rubrica, "compute_histogram() dirige la logica", no una decision fija
        de antemano.
        """
        if self._stage_data is None or not self._stage_data.background_layers:
            return
        lejos = self._stage_data.background_layers[0]

        histograma = FilterTools.compute_histogram(lejos)
        luminancia_media = sum(
            valor * cuenta for valor, cuenta in enumerate(histograma["luminance"])
        ) / histograma["total_pixels"]

        if luminancia_media < self._UMBRAL_PENUMBRA:
            # box_blur_5 (5x5, todos los pesos 1/25): difuminado mas fuerte
            # para una zona ya oscura, que se lee mejor borrosa que negra y
            # con ruido de compresion visible.
            kernel = FilterTools.get_standard_kernel("box_blur_5")
            resultado = FilterTools.apply_kernel(lejos, kernel)
            resultado = FilterTools.adjust_brightness(resultado, 1.15)
        else:
            # box_blur (3x3, pesos 1/9): difuminado suave, sin tocar brillo.
            kernel = FilterTools.get_standard_kernel("box_blur")
            resultado = FilterTools.apply_kernel(lejos, kernel)

        self._stage_data.background_layers[0] = resultado

    def _on_casillero_abierto(self) -> None:
        self._casillero_animando = True

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._casillero_animando and self._casillero_t < 1.0:
            self._casillero_t = min(1.0, self._casillero_t + dt / self._CASILLERO_DURACION)

    def _habilitar_fondo_transparente(self) -> None:
        """Hace que las zonas sin azulejo dejen ver el parallax (Unidad V).

        DrawingSystem dibuja en este orden:
            fill(BG_COLOR) -> _draw_background(fotos) -> map_layer.draw()

        pyscroll crea su BufferedRenderer con `alpha=False`, o sea un bufer
        OPACO: al dibujar el mapa pinta tambien las celdas vacias y borra el
        parallax que se acababa de pintar debajo.  Por eso los fondos del
        juego nunca se ven, aunque StageLoader los cargue.

        Se reconstruye el renderer con `alpha=True` para que las celdas sin
        azulejo queden transparentes.  Se hace aqui, en la subclase, para no
        modificar el framework.
        """
        if self._stage_data is None or self._stage_data.map_layer is None:
            return
        import pyscroll

        grupo = self._stage_data.map_layer
        anterior = grupo._map_layer
        grupo._map_layer = pyscroll.BufferedRenderer(
            anterior.data,
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
            clamp_camera=True,
            alpha=True,
        )

    # ── Optional lifecycle hooks ────────────────────────────────────
    # Override any of these to add custom behavior:

    def on_stage_start(self) -> None:
        """Se llama despues de cargar el nivel.
        IMPORTANTE: super() dispara el tutorial de la clase base; no quitarlo.
        TODO(student): aqui van las entidades propias y la trayectoria curva."""
        super().on_stage_start()

    def on_player_landed(self) -> None:
        """Called when the player first touches ground after being airborne.
        TODO(student): e.g., trigger a message, activate a hazard."""
        pass

    def on_enemy_died(self, enemy) -> None:
        """Called when an enemy dies.
        TODO(student): e.g., unlock a door, spawn a pickup."""
        pass

    def on_next_trigger_entered(self) -> None:
        """Called when the player touches NextTrigger.
        TODO(student): e.g., play a custom cutscene before stage ends."""
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        """F1 muestra u oculta la curva de Bezier de los cuadernos voladores,
        junto con sus 4 puntos de control (Unidad III).

        Verde = P0 y P3, por donde la curva SI pasa.
        Naranja = P1 y P2, que solo la atraen sin ser tocados.
        """
        if self._stage_data is None:
            return
        for entidad in self._stage_data.entity_list:
            if isinstance(entidad, CuadernoVolador):
                entidad.mostrar_curva = enabled

    # ── Correccion de scroll del mapa ───────────────────────────────
    def draw(self, surface: pygame.Surface) -> None:
        """Sincroniza el renderer de pyscroll con la camara antes de dibujar.

        StageScene le asigna `view_rect` directamente al BufferedRenderer de
        pyscroll, pero esa asignacion no invalida su bufer interno: las capas
        de azulejos quedan congeladas en la posicion inicial y solo se mueven
        las entidades.  pyscroll expone `center()` justamente para esto, asi
        que lo llamamos con el centro de la vista de la camara.

        Se resuelve aqui, sobreescribiendo draw() en la subclase, para no
        modificar ningun archivo del motor ni del framework.
        """
        if self._stage_data is not None and self._stage_data.map_layer is not None:
            camara = self._camera.offset
            self._stage_data.map_layer._map_layer.center((
                camara.x + settings.INTERNAL_WIDTH / 2,
                camara.y + settings.INTERNAL_HEIGHT / 2,
            ))
        super().draw(surface)
        self._dibujar_casillero_animado(surface)

    def _dibujar_casillero_animado(self, surface: pygame.Surface) -> None:
        """Puerta del casillero deslizandose hasta abrirse (Unidad VI).

        `ease_out_bounce` en vez de un movimiento lineal: la puerta pierde
        ancho rapido al principio y frena con un rebote pequeno al final, en
        vez de parar en seco. `t` recorre [0, 1] en `_CASILLERO_DURACION`
        segundos (ver update()); el ancho de la puerta cerrada es
        `ancho * (1 - ease_out_bounce(t))`, asi que en t=0 tapa todo el
        casillero (cerrado, el estado por defecto) y en t=1 desaparece del
        todo (casillero abierto). No hay atajo por t<=0: el panel cerrado
        tiene que verse desde el primer frame, antes de que el jugador
        interactue con nada.
        """
        progreso = ease_out_bounce(self._casillero_t)
        ancho_puerta = self._CASILLERO_ANCHO * (1.0 - progreso)
        if ancho_puerta <= 0.0:
            return
        x = self._CASILLERO_X - self._camera.offset.x
        y = self._CASILLERO_Y - self._camera.offset.y
        # Azul electrico de la paleta "aula moderna" (crear_tileset.py),
        # con un marco carbon para que se lea como puerta y no como un
        # rectangulo suelto.
        rect = pygame.Rect(int(x), int(y), max(1, int(ancho_puerta)), self._CASILLERO_ALTO)
        pygame.draw.rect(surface, (0, 85, 165), rect)
        pygame.draw.rect(surface, (58, 58, 58), rect, width=2)
