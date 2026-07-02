from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage0(StageScene):
    """Stage 0 — executable documentation / tutorial stage.
    Demonstrates all framework systems across 7 zones (A–G)."""

    STAGE_ID: str = "stage0"
    STAGE_NAME: str = "STAGE 0  PROLOGUE"
    ZONE: int = 0
    TIME_LIMIT: int = 0
    BGM_TRACK: str = "bgm_stage0"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path("assets/maps/stage0/stage0.tmx"))
