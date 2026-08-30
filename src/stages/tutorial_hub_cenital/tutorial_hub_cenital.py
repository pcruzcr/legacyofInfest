"""
Module: tutorial_hub_cenital
System: stage (variante cenital / top-down)
Academic Unit: II-IV

Mismo hub que tutorial_hub pero con vista=cenital: movimiento en 2 ejes,
sin gravedad, parallax idéntico y todas las mecánicas (combo, parry,
cinta, plataforma) adaptadas al perfil cenital. Demuestra que el motor
funciona en vista lateral y en vista superior con el mismo contenido.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class TutorialHubCenital(StageScene):
    """Variante cenital del hub tutorial — scrolling top-down."""

    STAGE_ID: str = "tutorial_hub_cenital"
    STAGE_NAME: str = "TUTORIAL CENITAL"
    ZONE: int = 0

    TMX_PATH = settings.ASSETS_DIR / "maps/tutorial_hub_cenital/tutorial_hub_cenital.tmx"

    SALAS = (
        ("Movimiento 2D", "flechas/WASD + stick en dos ejes, sin gravedad"),
        ("Combate", "mismo combo 0.5s en cenital"),
        ("Defensa", "parry y dash en 2D"),
        ("Mundo", "cinta y plataforma en vista superior"),
        ("Jefe lite", "telegrafía en 2D"),
    )

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)

    def on_stage_start(self) -> None:
        super().on_stage_start()
        self.context.event_bus.emit(
            "SHOW_MESSAGE",
            text="Tutorial cenital: mismos retos, vista desde arriba. ¡Mismas recompensas!",
            duration=6.0,
        )
