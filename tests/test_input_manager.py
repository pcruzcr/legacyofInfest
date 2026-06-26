"""Tests for InputManager pressed/held/released semantics.

See 24_TEST_PLAN.md section 4.3 for test specifications.
"""

import pygame

from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager


def test_pressed_only_first_frame():
    """is_action_pressed() is True on the frame of the event,
    False next frame."""
    mgr = InputManager()
    mgr.pump([])
    assert not mgr.is_action_pressed(Action.JUMP)

    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    ]
    mgr.pump(events)
    assert mgr.is_action_pressed(Action.JUMP)
    assert mgr.is_action_held(Action.JUMP)

    mgr.pump([])
    assert not mgr.is_action_pressed(Action.JUMP)
    assert mgr.is_action_held(Action.JUMP)


def test_held_while_down():
    """is_action_held() is True for every frame the key remains down."""
    mgr = InputManager()
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)]
    mgr.pump(events)
    assert mgr.is_action_held(Action.MOVE_LEFT)

    for _ in range(5):
        mgr.pump([])
        assert mgr.is_action_held(Action.MOVE_LEFT)


def test_released_only_on_keyup_frame():
    """is_action_released() is True only on the frame of the keyup event."""
    mgr = InputManager()
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j)]
    mgr.pump(events)
    assert not mgr.is_action_released(Action.SHORT_ATTACK)

    keyup_events = [pygame.event.Event(pygame.KEYUP, key=pygame.K_j)]
    mgr.pump(keyup_events)
    assert mgr.is_action_released(Action.SHORT_ATTACK)

    mgr.pump([])
    assert not mgr.is_action_released(Action.SHORT_ATTACK)


def test_no_action_when_unbound_key_pressed():
    """A keydown for a key not bound to any Action does not trigger actions."""
    mgr = InputManager()
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1)]
    mgr.pump(events)
    assert not mgr.is_action_pressed(Action.JUMP)
    assert not mgr.is_action_held(Action.JUMP)
    assert not mgr.is_action_released(Action.JUMP)