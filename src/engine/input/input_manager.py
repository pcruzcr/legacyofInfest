"""
Module: input_manager
System: engine
Academic Unit: N/A
Description: Unified input abstraction. Handles keyboard and gamepad
input through the ActionMap. Entities query actions, not raw keys
or buttons.
"""

from __future__ import annotations

import pygame

from src.engine.input.action_map import Action, DEFAULT_KEYBOARD_BINDINGS


class InputManager:
    """Unified input abstraction. Handles keyboard and gamepad input
    through the ActionMap. Entities query actions, not raw keys
    or buttons.
    """

    def __init__(self) -> None:
        """Initialise with default keyboard bindings."""
        self._key_bindings: dict[Action, list[int]] = DEFAULT_KEYBOARD_BINDINGS.copy()
        # State for this frame
        self._pressed: set[Action] = set()
        self._held: set[Action] = set()
        self._released: set[Action] = set()
        # Previous frame's held set for edge detection
        self._prev_held: set[Action] = set()

    def pump(self, events: list[pygame.event.Event]) -> None:
        """Called once per frame by App with the current event list.

        Updates internal pressed/held/released state based on
        KEYDOWN/KEYUP events.
        """
        # Clear frame-specific sets
        self._pressed.clear()
        self._released.clear()

        # Process events for edge detection
        for event in events:
            if event.type == pygame.KEYDOWN:
                action = self._key_to_action(event.key)
                if action is not None:
                    if action not in self._held:
                        self._pressed.add(action)
                    self._held.add(action)
            elif event.type == pygame.KEYUP:
                action = self._key_to_action(event.key)
                if action is not None:
                    if action in self._held:
                        self._held.remove(action)
                        self._released.add(action)

    def _key_to_action(self, key: int) -> Action | None:
        """Map a pygame key constant to an Action, or None if unbound."""
        for action, keys in self._key_bindings.items():
            if key in keys:
                return action
        return None

    def is_action_pressed(self, action: Action) -> bool:
        """True only on the frame the action was activated."""
        return action in self._pressed

    def is_action_held(self, action: Action) -> bool:
        """True for every frame the action is held."""
        return action in self._held

    def is_action_released(self, action: Action) -> bool:
        """True only on the frame the action was released."""
        return action in self._released