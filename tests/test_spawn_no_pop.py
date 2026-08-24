"""
Module: test_spawn_no_pop
System: tests
Description: Regression — FIX-3: player spawns at correct y (160 for
stage0) so feet align with floor at y=192, eliminating 32px pop-in.
"""
from __future__ import annotations

import pygame

from src.framework.entities.player import Player


class TestSpawnNoPop:
    STAGE0_SPAWN_Y = 160.0
    STAGE0_FLOOR_Y = 192

    def test_spawn_y_is_160(self) -> None:
        player = Player(pygame.Vector2(48.0, self.STAGE0_SPAWN_Y))
        assert abs(player.position.y - self.STAGE0_SPAWN_Y) < 0.1

    def test_feet_align_with_floor_after_landing(self) -> None:
        player = Player(pygame.Vector2(48.0, self.STAGE0_SPAWN_Y))
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, self.STAGE0_FLOOR_Y, 640, 16)]
        for _ in range(10):
            player.update(dt, floor)
        expected_bottom = self.STAGE0_FLOOR_Y
        assert player.rect.bottom == expected_bottom

    def test_no_initial_pop_when_standing_on_floor(self) -> None:
        player = Player(pygame.Vector2(48.0, self.STAGE0_SPAWN_Y))
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, self.STAGE0_FLOOR_Y, 640, 16)]
        prev_y = player.position.y
        for _ in range(5):
            player.update(dt, floor)
            delta = abs(player.position.y - prev_y)
            assert delta < 2.0
            prev_y = player.position.y
