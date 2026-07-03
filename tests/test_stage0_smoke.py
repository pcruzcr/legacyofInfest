"""
Module: test_stage0_smoke
System: tests
Academic Unit: N/A
Description: Automatable smoke tests for Stage 0 integration.
These verify that Stage 0 loads without exceptions and matches the
design document (07_STAGE0_DESIGN.md) in key structural properties.
"""
from pathlib import Path

import pygame
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.stage.stage_loader import StageLoader, StageData

STAGE0_TMX = Path("assets/maps/stage0/stage0.tmx")


class TestStage0Smoke:
    """Smoke tests for Stage 0 loading and structural integrity."""

    def setup_method(self) -> None:
        _init_pygame_display()
        StageLoader._entity_registry.clear()
        StageLoader.register_entity("Walker", EnemyWalker)
        StageLoader.register_entity("Flying", EnemyFlying)
        StageLoader.register_entity("Shooter", EnemyShooter)

    def test_stage0_loads_without_exception(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert isinstance(data, StageData)

    def test_stage0_has_five_checkpoints(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert len(data.checkpoints) == 5

    def test_stage0_has_next_trigger(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert data.next_trigger is not None

    def test_stage0_enemy_count_matches_design(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert len(data.entity_list) == 12


def _init_pygame_display():
    """Ensure a pygame display is available for pytmx image loading."""
    if not pygame.display.get_init():
        pygame.display.init()
        pygame.display.set_mode((1, 1))
