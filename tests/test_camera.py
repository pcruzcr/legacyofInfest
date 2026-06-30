"""
Module: test_camera
System: tests
Academic Unit: N/A
Description: Tests for Camera follow, world-to-screen conversion.
"""
import pygame

from src.framework.stage.camera import Camera


class DummyTarget:
    """Minimal target with a rect center for camera follow tests."""
    def __init__(self) -> None:
        self.rect = pygame.Rect(100, 50, 20, 20)


class TestCameraFollow:
    """Tests for camera following behavior."""

    def test_follow_moves_offset_toward_target(self) -> None:
        cam = Camera()
        target = DummyTarget()
        cam.follow(target)
        cam.set_map_size(640, 224)
        for _ in range(60):
            cam.update(1.0 / 60.0)
        assert abs(cam.offset.x - 0.0) < 20.0, (
            "Camera should approach target X within lerp distance"
        )
        assert abs(cam.offset.y - 0.0) < 20.0, (
            "Camera should approach target Y within lerp distance"
        )

    def test_world_to_screen_screen_to_world_inverse(self) -> None:
        cam = Camera()
        cam.offset = pygame.Vector2(50, 30)
        p = pygame.Vector2(123.0, 67.0)
        screen = cam.world_to_screen(p)
        world_back = cam.screen_to_world(screen)
        assert abs(world_back.x - p.x) < 0.001
        assert abs(world_back.y - p.y) < 0.001
