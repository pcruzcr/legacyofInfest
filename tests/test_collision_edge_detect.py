"""
Module: test_collision_edge_detect
System: tests
Description: Regression — FIX-2: inflated rect catches edge-aligned
overlaps (bottom == floor.top) that pygame.colliderect misses.
"""
from __future__ import annotations
import pygame
from src.framework.entities.player import Player


class TestCollisionEdgeDetect:
    def test_edge_aligned_floor_detected(self) -> None:
        player = Player(pygame.Vector2(48.0, 160.0))
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, 192, 640, 16)]
        for _ in range(5):
            player.update(dt, floor)
        assert player.is_grounded

    def test_edge_aligned_platform_detected(self) -> None:
        player = Player(pygame.Vector2(280.0, 128.0))
        dt = 1.0 / 60.0
        platform = [pygame.Rect(272, 160, 96, 16)]
        for _ in range(60):
            player.update(dt, platform)
            if player.is_grounded:
                break
        assert player.is_grounded
        assert player.rect.bottom == 160

    def test_collided_y_only_snaps_when_collision_occurs(self) -> None:
        player = Player(pygame.Vector2(48.0, 100.0))
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, 200, 640, 16)]
        prev_y = player.position.y
        player.update(dt, floor)
        delta = player.position.y - prev_y
        assert delta > 0
