"""
Module: stage3_3_el_patio
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

Zone 3 (Sede Heredia), Stage 3-3 — El Patio.
Student: Rebeca.

Test with:
   python main.py --stage stage3_3_el_patio
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.framework.scenes.stage_scene import StageScene
from src.stages.stage3_3_el_patio.fountain import Fountain

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage3_3ElPatio(StageScene):
    """Un patio interior con una fuente central, rodeado de aves en alerta.
    Demuestra: vectores explicitos (Unidad II), curvas (Unidad III),
    representacion de escena via TMX (Unidad IV) y color (Unidad V)."""

    STAGE_ID: str = "stage3_3_el_patio"
    STAGE_NAME: str = "3-3  EL PATIO"
    ZONE: int = 3

    TMX_PATH = "assets/maps/stage3_3_el_patio/stage3_3_el_patio.tmx"

    # Debe coincidir con el objeto Platform_Fountain del TMX (x=784, y=544,
    # width=64) -> centro en x = 784 + 64/2 = 816.
    FOUNTAIN_POS = pygame.Vector2(816, 544)

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        self._fountain: Fountain | None = None

    # ── Optional lifecycle hooks ────────────────────────────────────
    # Override any of these to add custom behavior:

    def on_stage_start(self) -> None:
        """Called after the stage loads and setup completes."""
        self._fountain = Fountain(self.FOUNTAIN_POS)

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._fountain is not None:
            self._fountain.update(dt, self._player)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if self._fountain is not None:
            self._fountain.draw(surface, self._camera.offset)

    def on_player_landed(self) -> None:
        """Called when the player first touches ground after being airborne.
        Not used in this stage."""
        pass

    def on_enemy_died(self, enemy) -> None:
        """Called when an enemy dies. Not used in this stage."""
        pass

    def on_next_trigger_entered(self) -> None:
        """Called when the player touches NextTrigger. Not used in this stage."""
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        """Called when F1 is pressed to toggle debug overlay.
        Not used in this stage."""
        pass
