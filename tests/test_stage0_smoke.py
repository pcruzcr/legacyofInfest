"""
Module: test_stage0_smoke
System: tests
Description: Automatable smoke tests for Stage 0 integration.
These verify that Stage 0 loads without exceptions and matches the
design document (07_STAGE0_DESIGN.md) in key structural properties.
"""
from __future__ import annotations

from pathlib import Path

import pygame

from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.entities.enemy_walker import EnemyWalker
from src.framework.stage.stage_loader import StageData, StageLoader

STAGE0_TMX = Path("assets/maps/stage0/stage0.tmx")


class TestStage0Smoke:
    def setup_method(self) -> None:
        _init_pygame_display()
        StageLoader._entity_registry.clear()
        StageLoader.register_entity("Walker", EnemyWalker)
        StageLoader.register_entity("Flying", EnemyFlying)
        StageLoader.register_entity("Shooter", EnemyShooter)

    def test_stage0_loads_without_exception(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert isinstance(data, StageData)

    def test_stage0_has_checkpoints(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert len(data.checkpoints) >= 1

    def test_stage0_has_next_trigger(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert data.next_trigger is not None

    def test_stage0_has_enemies(self) -> None:
        data = StageLoader.load(STAGE0_TMX)
        assert len(data.entity_list) >= 1


def _init_pygame_display() -> None:
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
