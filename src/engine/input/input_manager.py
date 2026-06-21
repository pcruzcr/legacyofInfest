"""
Module: input_manager
System: engine
Academic Unit: Framework scaffold
Description: Translates raw pygame events into semantic ``Action`` queries.
``InputManager.pump()`` must be called once per frame with the current
event list.  The ``is_action_pressed`` / ``is_action_held`` /
``is_action_released`` methods then report the state of each action for
that frame.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.input.action_map import Action, DEFAULT_KEYBOARD_BINDINGS

if TYPE_CHECKING:
    pass


class InputManager:
    """Frame-rate-independent input state tracker.

    Tracks the current and previous keyboard state to distinguish
    *pressed-this-frame* from *held* and *released-this-frame*.
    """

    def __init__(self) -> None:
        """Create an InputManager with default keyboard bindings."""
        self._keyboard_bindings: dict[Action, list[int]] = dict(
            DEFAULT_KEYBOARD_BINDINGS
        )
        self._current_keys: set[int] = set()
        self._previous_keys: set[int] = set()

    def pump(self, events: list[pygame.event.Event]) -> None:
        """Update internal key state from the current frame's event list.

        Only ``KEYDOWN`` / ``KEYUP`` events are consumed; all others are
        ignored so that ``InputManager`` never interferes with other
        event consumers (e.g. ``EventBus``).
        """
        self._previous_keys = set(self._current_keys)
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._current_keys.add(event.key)
            elif event.type == pygame.KEYUP:
                self._current_keys.discard(event.key)

    def is_action_pressed(self, action: Action) -> bool:
        """``True`` only on the frame the action was first activated."""
        keys = self._keyboard_bindings.get(action, [])
        return any(k in self._current_keys for k in keys) and not any(
            k in self._previous_keys for k in keys
        )

    def is_action_held(self, action: Action) -> bool:
        """``True`` for every frame the action remains active."""
        keys = self._keyboard_bindings.get(action, [])
        return any(k in self._current_keys for k in keys)

    def is_action_released(self, action: Action) -> bool:
        """``True`` only on the frame the action was last deactivated."""
        keys = self._keyboard_bindings.get(action, [])
        return not any(k in self._current_keys for k in keys) and any(
            k in self._previous_keys for k in keys
        )
