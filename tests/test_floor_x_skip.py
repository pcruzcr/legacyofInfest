"""
Module: test_floor_x_skip
System: tests
Description: Regression — FIX-1/FIX-2: floor tiles (tile.top >=
player_rect.centery) must NOT block X-axis movement.
"""
from __future__ import annotations
import pygame
from src.engine.input.input_manager import InputManager
from src.engine.input.action_map import Action
from src.framework.entities.player import Player


def _make_player(x: float = 48.0, y: float = 0.0) -> Player:
    return Player(pygame.Vector2(x, y))


def _input_holding(*actions: Action) -> InputManager:
    im = InputManager()
    for action in actions:
        for key in im._bindings.get(action, []):
            im._held.add(key)
    return im


class TestFloorXSkip:
    def test_floor_does_not_block_x_movement(self) -> None:
        player = _make_player(x=50.0, y=160.0)
        im = _input_holding(Action.MOVE_RIGHT)
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, 192, 640, 16)]
        for _ in range(60):
            player.update(dt, floor, im)
        assert player.position.x > 60.0

    def test_wall_blocks_x_movement(self) -> None:
        player = _make_player(x=50.0, y=160.0)
        dt = 1.0 / 60.0
        wall = pygame.Rect(80, 144, 16, 64)
        floor = pygame.Rect(0, 192, 640, 16)
        player.velocity.x = 90.0
        for _ in range(90):
            player.update(dt, [wall, floor])
        assert player.rect.right <= wall.left + 2

    def test_x_skip_does_not_break_y_grounding(self) -> None:
        player = _make_player(x=50.0, y=160.0)
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, 192, 640, 16)]
        for _ in range(10):
            player.update(dt, floor)
        assert player.is_grounded
