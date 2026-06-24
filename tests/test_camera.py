"""
Tests for Camera (T7.1).
"""

from __future__ import annotations

import pytest
import pygame

from src.framework.stage.camera import Camera
from src.engine.core.settings import INTERNAL_WIDTH, INTERNAL_HEIGHT


class _StubEntity:
    """Minimal entity stand-in for Camera.follow tests."""

    def __init__(self, x: float, y: float) -> None:
        self.position = pygame.Vector2(x, y)


class TestCamera:
    """Camera smoke tests per 24_TEST_PLAN.md §9.2."""

    def test_follow_moves_offset_toward_target(self) -> None:
        """After update(dt) calls offset approaches target."""
        cam = Camera()
        entity = _StubEntity(300, 180)
        cam.follow(entity)

        for _ in range(120):
            cam.update(1.0 / 60.0)

        target_x = 300.0 - INTERNAL_WIDTH / 2.0
        target_y = entity.position.y - INTERNAL_HEIGHT / 2.0
        assert abs(cam.offset.x - target_x) < 5.0
        assert abs(cam.offset.y - target_y) < 5.0

    def test_world_to_screen_screen_to_world_inverse(self) -> None:
        """screen_to_world(world_to_screen(p)) == p."""
        cam = Camera()
        cam._offset = pygame.Vector2(100, 50)
        p = pygame.Vector2(250, 180)
        recovered = cam.screen_to_world(cam.world_to_screen(p))
        assert recovered.x == pytest.approx(p.x)
        assert recovered.y == pytest.approx(p.y)

    def test_no_target_no_crash(self) -> None:
        """update() with no target does not raise."""
        cam = Camera()
        cam.update(1.0 / 60.0)
        assert cam.offset == pygame.Vector2(0, 0)

    def test_parallax_offset_far_slower_than_terrain(self) -> None:
        """BG_Far offset is much smaller than Terrain offset."""
        cam = Camera()
        cam._offset = pygame.Vector2(100, 50)
        far = cam.get_parallax_offset("BG_Far")
        terrain = cam.get_parallax_offset("Terrain")
        assert far.x < terrain.x
        assert far.y < terrain.y

    def test_parallax_default_is_terrain(self) -> None:
        """get_parallax_offset() with no argument returns Terrain offset."""
        cam = Camera()
        cam._offset = pygame.Vector2(80, 40)
        default = cam.get_parallax_offset()
        terrain = cam.get_parallax_offset("Terrain")
        assert default == terrain
