from __future__ import annotations

from pathlib import Path

from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.stage_loader import StageLoader

# Register entity types for Stage 0 TMX object parsing
StageLoader.register_entity("Walker", EnemyWalker)
StageLoader.register_entity("Flying", EnemyFlying)
StageLoader.register_entity("Shooter", EnemyShooter)


class Stage0(StageScene):
    """Stage 0 — executable documentation / tutorial stage.
    Demonstrates all framework systems across 7 zones (A–G)."""

    STAGE_ID: str = "stage0"
    STAGE_NAME: str = "STAGE 0  PROLOGUE"
    ZONE: int = 0
    TIME_LIMIT: int = 0
    BGM_TRACK: str = "bgm_stage0"

    def __init__(self) -> None:
        super().__init__(Path("assets/maps/stage0/stage0.tmx"))
