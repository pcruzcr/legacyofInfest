"""
Module: test_camera
System: tests
Description: Tests for Camera follow, world-to-screen conversion,
parallax, screen shake, map boundary clamping, and lock zones.
"""
from __future__ import annotations
import pygame
import pytest
from src.framework.stage.camera import Camera, _CameraLock


class DummyTarget:
    def __init__(self) -> None:
        self.rect = pygame.Rect(100, 50, 20, 20)
        self.velocity = pygame.Vector2(0, 0)


class TestCameraFollow:
    def test_follow_moves_offset_toward_target(self) -> None:
        cam = Camera()
        target = DummyTarget()
        cam.follow(target)
        cam.set_map_size(640, 224)
        for _ in range(60):
            cam.update(1.0 / 60.0)
        assert abs(cam.offset.x - 0.0) < 20.0
        assert abs(cam.offset.y - 0.0) < 20.0

    def test_world_to_screen_screen_to_world_inverse(self) -> None:
        cam = Camera()
        cam.offset = pygame.Vector2(50, 30)
        p = pygame.Vector2(123.0, 67.0)
        screen = cam.world_to_screen(p)
        world_back = cam.screen_to_world(screen)
        assert abs(world_back.x - p.x) < 0.001
        assert abs(world_back.y - p.y) < 0.001

    def test_layer_offset_parallax(self) -> None:
        cam = Camera()
        cam.offset = pygame.Vector2(100, 50)
        bg_offset = cam.layer_offset("BG_Far")
        assert bg_offset.x == pytest.approx(15.0)
        assert bg_offset.y == pytest.approx(7.5)

    def test_set_parallax_factor(self) -> None:
        cam = Camera()
        cam.set_parallax_factor("BG_Far", 0.5)
        assert cam._parallax_factors["BG_Far"] == 0.5

    def test_no_target_no_crash(self) -> None:
        cam = Camera()
        cam.update(1.0 / 60.0)


class TestCameraShake:
    def test_apply_shake_adds_offset(self) -> None:
        cam = Camera()
        target = DummyTarget()
        cam.follow(target)
        cam.set_map_size(640, 224)
        cam.offset = pygame.Vector2(0, 0)
        cam.apply_shake(amplitude=10.0, duration=0.1)
        cam.update(0.05)
        assert cam.offset.x != 0.0 or cam.offset.y != 0.0

    def test_shake_decays(self) -> None:
        cam = Camera()
        target = DummyTarget()
        cam.follow(target)
        cam.set_map_size(640, 224)
        cam.offset = pygame.Vector2(0, 0)
        cam.apply_shake(amplitude=10.0, duration=0.1)
        cam.update(0.15)
        assert cam._shake_timer <= 0


class TestCameraBounds:
    def test_map_boundary_clamping(self) -> None:
        cam = Camera()
        target = DummyTarget()
        target.rect.centerx = 2000
        target.rect.centery = 1000
        cam.follow(target)
        map_w = 3000
        map_h = 2000
        cam.set_map_size(map_w, map_h)
        from src.engine.core import settings
        for _ in range(60):
            cam.update(1.0 / 60.0)
        assert cam.offset.x <= map_w - settings.INTERNAL_WIDTH
        assert cam.offset.y <= map_h - settings.INTERNAL_HEIGHT


class TestCameraLockZones:
    def test_lock_x_axis(self) -> None:
        cam = Camera()
        target = DummyTarget()
        cam.follow(target)
        lock = _CameraLock(pygame.Rect(80, 40, 40, 40), lock_x=True, lock_y=False)
        cam.set_camera_locks([lock])
        cam.update(1.0 / 60.0)
        assert cam._locked_x is True

    def test_no_locks_no_crash(self) -> None:
        cam = Camera()
        cam.set_camera_locks([])
        assert cam._locked_x is False
