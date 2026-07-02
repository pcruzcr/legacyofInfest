"""
Module: input_manager
System: engine.input
Academic Unit: N/A
Description: Unified keyboard + controller input manager. Tracks pressed/held/released
states for abstract Actions defined in action_map.py.
"""
from __future__ import annotations
import pygame

from src.engine.input.action_map import (
    Action,
    DEFAULT_KEY_BINDINGS,
    CONTROLLER_DEADZONE,
    CONTROLLER_AXIS_LEFT_X,
    CONTROLLER_AXIS_LEFT_Y,
    _CONTROLLER_BUTTON_MAP,
)


class InputManager:
    """Tracks keyboard + controller input with pressed/held/released semantics."""

    def __init__(self) -> None:
        self._bindings: dict[Action, list[int]] = {
            action: list(keys) for action, keys in DEFAULT_KEY_BINDINGS.items()
        }
        self._pressed_this_frame: set[int] = set()
        self._held: set[int] = set()
        self._released_this_frame: set[int] = set()
        self._consumed_actions: set[Action] = set()
        self._raw_keys_pressed: set[int] = set()

        # Controller state
        self._joystick: pygame.joystick.Joystick | None = None
        self._init_joystick()
        self._controller_buttons_held: set[int] = set()
        self._controller_buttons_pressed: set[int] = set()
        self._controller_buttons_released: set[int] = set()
        self._controller_axis_left: float = 0.0
        self._controller_axis_right: float = 0.0
        self._controller_axis_up: bool = False
        self._controller_axis_down: bool = False

    def _init_joystick(self) -> None:
        """Initialize the first available joystick."""
        try:
            if pygame.joystick.get_count() > 0:
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()
        except Exception:
            self._joystick = None

    def pump(self, events: list[pygame.event.Event]) -> None:
        """Process raw pygame events. Called once per frame by App."""
        self._pressed_this_frame.clear()
        self._released_this_frame.clear()
        self._consumed_actions.clear()
        self._raw_keys_pressed.clear()
        self._controller_buttons_pressed.clear()
        self._controller_buttons_released.clear()

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key not in self._held:
                    self._pressed_this_frame.add(e.key)
                    self._raw_keys_pressed.add(e.key)
                self._held.add(e.key)
            elif e.type == pygame.KEYUP:
                self._held.discard(e.key)
                self._released_this_frame.add(e.key)
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button not in self._controller_buttons_held:
                    self._controller_buttons_pressed.add(e.button)
                self._controller_buttons_held.add(e.button)
            elif e.type == pygame.JOYBUTTONUP:
                self._controller_buttons_held.discard(e.button)
                self._controller_buttons_released.add(e.button)
            elif e.type == pygame.JOYAXISMOTION:
                self._poll_axes()

    def is_action_pressed(self, action: Action) -> bool:
        """True only on the frame the action's key was first pressed."""
        if action in self._consumed_actions:
            return False
        keys = self._bindings.get(action, [])
        if any(k in self._pressed_this_frame for k in keys):
            return True
        return self._action_from_controller(action)

    def is_action_held(self, action: Action) -> bool:
        """True every frame while the action's key is held down."""
        keys = self._bindings.get(action, [])
        if any(k in self._held for k in keys):
            return True
        return self._action_held_from_controller(action)

    def is_action_released(self, action: Action) -> bool:
        """True only on the frame the action's key was released."""
        keys = self._bindings.get(action, [])
        if any(k in self._released_this_frame for k in keys):
            return True
        return self._action_released_from_controller(action)

    def consume(self, action: Action) -> None:
        """Consume an action so is_pressed returns False for the rest of the frame."""
        self._consumed_actions.add(action)

    def rebind(self, action: Action, keys: list[int]) -> None:
        """Rebind an action to a new list of key constants."""
        self._bindings[action] = list(keys)

    def is_raw_key_pressed(self, key: int) -> bool:
        """True only on the frame this physical key was first pressed."""
        return key in self._raw_keys_pressed

    def _poll_axes(self) -> None:
        """Poll joystick axes and update directional state."""
        if self._joystick is None:
            return
        try:
            x = self._joystick.get_axis(CONTROLLER_AXIS_LEFT_X)
            y = self._joystick.get_axis(CONTROLLER_AXIS_LEFT_Y)
            self._controller_axis_left = x if abs(x) > CONTROLLER_DEADZONE else 0.0
            self._controller_axis_right = 0.0
            self._controller_axis_up = y < -CONTROLLER_DEADZONE
            self._controller_axis_down = y > CONTROLLER_DEADZONE
        except Exception:
            pass

    def _action_from_controller(self, action: Action) -> bool:
        """Check if any controller binding matches the action."""
        if action == Action.MOVE_LEFT:
            return self._controller_axis_left < 0
        if action == Action.MOVE_RIGHT:
            return self._controller_axis_left > 0
        if action == Action.JUMP:
            btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == Action.JUMP), None)
            return btn is not None and (btn in self._controller_buttons_pressed or self._controller_axis_up)
        if action == Action.CROUCH:
            btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == Action.CROUCH), None)
            return btn is not None and (btn in self._controller_buttons_held or self._controller_axis_down)
        btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == action), None)
        if btn is not None:
            return btn in self._controller_buttons_pressed
        return False

    def _action_held_from_controller(self, action: Action) -> bool:
        """Check if action is being held on controller."""
        if action == Action.MOVE_LEFT:
            return self._controller_axis_left < 0
        if action == Action.MOVE_RIGHT:
            return self._controller_axis_left > 0
        if action == Action.CROUCH:
            return self._controller_axis_down
        btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == action), None)
        if btn is not None:
            return btn in self._controller_buttons_held
        return False

    def _action_released_from_controller(self, action: Action) -> bool:
        """Check if action was released on controller."""
        if action in (Action.MOVE_LEFT, Action.MOVE_RIGHT):
            return abs(self._controller_axis_left) < CONTROLLER_DEADZONE
        if action == Action.CROUCH:
            return not self._controller_axis_down
        btn = next((b for b, a in _CONTROLLER_BUTTON_MAP.items() if a == action), None)
        if btn is not None:
            return btn in self._controller_buttons_released
        return False

    @staticmethod
    def is_raw_key_held(key: int) -> bool:
        """True every frame while this physical key is held down."""
        return bool(pygame.key.get_pressed()[key])
