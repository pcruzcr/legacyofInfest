from __future__ import annotations

from pathlib import Path

from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.stage_loader import StageLoader

StageLoader.register_entity("Walker", EnemyWalker)


class Stage0(StageScene):
    """Stage 0 — tutorial/intro level."""

    def __init__(self) -> None:
        super().__init__(Path("assets/maps/stage0/stage0.tmx"))
