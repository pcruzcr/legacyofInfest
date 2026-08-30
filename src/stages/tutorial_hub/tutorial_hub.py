"""
Module: tutorial_hub
System: stage (tutorial guiado)
Academic Unit: II-IV

Hub tutorial de 5 salas con recompensas (monedas, puntos, XP, logros).
Reemplaza al tutorial de texto: cada sala enseña una mecánica con mensaje +
práctica + enemigo/riesgo + checkpoint + moneda + objetivo. Al completar
los 5 objetivos se desbloquea logro `tutorial_master`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class TutorialHub(StageScene):
    """Escenario hub tutorial — 5 salas, curva 1→5, con parallax y 2.5D por Y."""

    STAGE_ID: str = "tutorial_hub"
    STAGE_NAME: str = "TUTORIAL GUIADO"
    ZONE: int = 0

    TMX_PATH = settings.ASSETS_DIR / "maps/tutorial_hub/tutorial_hub.tmx"

    SALAS: tuple[tuple[str, str], ...] = (
        ("Movimiento", "flechas/WASD + salto + coyote"),
        ("Combate", "Z/J corto, X/K largo, combo 0.5s"),
        ("Defensa", "parry agachado+Z, dash SHIFT/mouse medio"),
        ("Mundo", "cinta, plataforma móvil, agua"),
        ("Jefe lite", "telegrafía y ventana de castigo"),
    )

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)

    def on_stage_start(self) -> None:
        super().on_stage_start()
        self.context.event_bus.emit(
            "SHOW_MESSAGE",
            text="Tutorial guiado: 5 salas. Cada una da moneda y XP. ¡Completa los objetivos!",
            duration=6.0,
        )

    def on_enemy_died(self, enemy) -> None:  # type: ignore[override]
        super().on_enemy_died(enemy)
        # La sala 2 da XP extra por combo; el sistema base ya da Score/XP/Bestiary
        # vía StageScene -> ScoreSystem/ExperienceSystem/AchievementSystem.

    def draw(self, surface) -> None:  # type: ignore[override]
        super().draw(surface)
