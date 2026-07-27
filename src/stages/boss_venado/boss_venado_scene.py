from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class BossVenadoScene(StageScene):
    STAGE_ID: str = "boss_venado"
    STAGE_NAME: str = "VENADO"
    ZONE: int = 0
    TMX_PATH = settings.ASSETS_DIR / "maps/boss_venado/boss_venado.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
