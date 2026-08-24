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

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))

    def on_enter(self) -> None:
        super().on_enter()
        self._habilitar_fondo_transparente()

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
