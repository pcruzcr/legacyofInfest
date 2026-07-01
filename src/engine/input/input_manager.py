"""
Module: input_manager
System: engine.input
Academic Unit: N/A
Description: Unified keyboard input manager. Tracks pressed/held/released
states for abstract Actions defined in action_map.py.
"""
from __future__ import annotations
import pygame

from src.engine.input.action_map import Action, DEFAULT_KEY_BINDINGS


class InputManager:
    """Tracks keyboard input with pressed/held/released semantics."""

    def __init__(self) -> None:
        self._bindings: dict[Action, list[int]] = {
            action: list(keys) for action, keys in DEFAULT_KEY_BINDINGS.items()
        }
        self._pressed_this_frame: set[int] = set()
        self._held: set[int] = set()
        self._released_this_frame: set[int] = set()
        self._consumed_actions: set[Action] = set()
        self._raw_keys_pressed: set[int] = set()

    def pump(self, events: list[pygame.event.Event]) -> None:
        """Process raw pygame events. Called once per frame by App."""
        self._pressed_this_frame.clear()
        self._released_this_frame.clear()
        self._consumed_actions.clear()
        self._raw_keys_pressed.clear()

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key not in self._held:
                    self._pressed_this_frame.add(e.key)
                    self._raw_keys_pressed.add(e.key)
                self._held.add(e.key)
            elif e.type == pygame.KEYUP:
                self._held.discard(e.key)
                self._released_this_frame.add(e.key)

    def is_action_pressed(self, action: Action) -> bool:
        """True only on the frame the action's key was first pressed."""
        if action in self._consumed_actions:
            return False
        keys = self._bindings.get(action, [])
        return any(k in self._pressed_this_frame for k in keys)

    def is_action_held(self, action: Action) -> bool:
        """True every frame while the action's key is held down."""
        keys = self._bindings.get(action, [])
        return any(k in self._held for k in keys)

    def is_action_released(self, action: Action) -> bool:
        """True only on the frame the action's key was released."""
        keys = self._bindings.get(action, [])
        return any(k in self._released_this_frame for k in keys)

    def consume(self, action: Action) -> None:
        """Consume an action so is_pressed returns False for the rest of the frame."""
        self._consumed_actions.add(action)

    def rebind(self, action: Action, keys: list[int]) -> None:
        """Rebind an action to a new list of key constants."""
        self._bindings[action] = list(keys)

    def is_raw_key_pressed(self, key: int) -> bool:
        """True only on the frame this physical key was first pressed."""
        return key in self._raw_keys_pressed

    @staticmethod
    def is_raw_key_held(key: int) -> bool:
        """True every frame while this physical key is held down."""
        return bool(pygame.key.get_pressed()[key])
