"""
Module: test_input_manager
System: tests
Description: Tests for InputManager: pressed/held/released semantics and action mapping.
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.input.input_manager import InputManager
from src.engine.input.action_map import Action


@pytest.fixture
def manager() -> InputManager:
    return InputManager()


def simulate_key(manager: InputManager, key: int, down: bool) -> None:
    etype = pygame.KEYDOWN if down else pygame.KEYUP
    event = pygame.event.Event(etype, {"key": key})
    manager.pump([event])


class TestInputManager:
    def test_is_action_just_pressed_true_on_keydown(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        assert manager.is_action_just_pressed(Action.MOVE_LEFT)

    def test_is_action_just_pressed_false_after_consume(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        manager.consume(Action.MOVE_LEFT)
        assert not manager.is_action_just_pressed(Action.MOVE_LEFT)

    def test_is_action_held_true_while_key_down(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_RIGHT, True)
        assert manager.is_action_held(Action.MOVE_RIGHT)
        manager.pump([])
        assert manager.is_action_held(Action.MOVE_RIGHT)

    def test_is_action_held_false_after_release(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_RIGHT, True)
        simulate_key(manager, pygame.K_RIGHT, False)
        assert not manager.is_action_held(Action.MOVE_RIGHT)

    def test_is_action_released_true_on_keyup(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_SPACE, True)
        simulate_key(manager, pygame.K_SPACE, False)
        assert manager.is_action_released(Action.JUMP)

    def test_is_action_just_pressed_false_for_unbound_action(self, manager: InputManager) -> None:
        manager.pump([])
        assert not manager.is_action_just_pressed(Action.PAUSE)

    def test_rebind_changes_key(self, manager: InputManager) -> None:
        manager.rebind(Action.JUMP, [pygame.K_q])
        simulate_key(manager, pygame.K_q, True)
        assert manager.is_action_just_pressed(Action.JUMP)
        simulate_key(manager, pygame.K_SPACE, True)
        assert not manager.is_action_just_pressed(Action.JUMP)

    def test_is_action_just_pressed_only_one_frame(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        assert manager.is_action_just_pressed(Action.MOVE_LEFT)
        manager.pump([])
        assert not manager.is_action_just_pressed(Action.MOVE_LEFT)

    def test_is_action_held_returns_true_after_multiple_frames(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        assert manager.is_action_held(Action.MOVE_LEFT)
        manager.pump([])
        assert manager.is_action_held(Action.MOVE_LEFT)
        manager.pump([])
        assert manager.is_action_held(Action.MOVE_LEFT)

    def test_default_bindings_exist_for_all_actions(self, manager: InputManager) -> None:
        for action in Action:
            assert action in manager._bindings
            assert len(manager._bindings[action]) > 0
