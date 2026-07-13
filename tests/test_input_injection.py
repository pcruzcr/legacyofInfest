"""
Module: test_input_injection
System: tests
Description: Regression — FIX-5: input_manager is injected as 3rd arg
to player.update() and state machine uses is_action_held/is_action_just_pressed.
"""
from __future__ import annotations
import pygame
from src.engine.input.input_manager import InputManager
from src.engine.input.action_map import Action
from src.framework.entities.player import Player


class TestInputInjection:
    def _make_input_manager(self, **held_actions: object) -> InputManager:
        im = InputManager()
        actions = held_actions.get("held", [])
        assert isinstance(actions, list)
        for action in actions:
            assert isinstance(action, Action)
            for key in im._bindings.get(action, []):
                im._held.add(key)
        pressed = held_actions.get("pressed", [])
        assert isinstance(pressed, list)
        for action in pressed:
            assert isinstance(action, Action)
            for key in im._bindings.get(action, []):
                im._pressed_this_frame.add(key)
        return im

    def test_move_right_with_injected_input(self) -> None:
        player = Player(pygame.Vector2(48.0, 160.0))
        im = self._make_input_manager(held=[Action.MOVE_RIGHT])
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, 192, 640, 16)]
        for _ in range(10):
            player.update(dt, floor, im)
        assert player.position.x > 50.0
        assert player.state.value == "WALKING"

    def test_move_left_with_injected_input(self) -> None:
        player = Player(pygame.Vector2(200.0, 160.0))
        im = self._make_input_manager(held=[Action.MOVE_LEFT])
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, 192, 640, 16)]
        for _ in range(10):
            player.update(dt, floor, im)
        assert player.position.x < 195.0

    def test_no_input_falls_back_to_idle(self) -> None:
        player = Player(pygame.Vector2(48.0, 160.0))
        dt = 1.0 / 60.0
        floor = [pygame.Rect(0, 192, 640, 16)]
        for _ in range(10):
            player.update(dt, floor, None)
        assert player.state.value in ("IDLE", "FALLING")
