"""
Module: action_map
System: engine
Academic Unit: Framework scaffold
Description: Action enumeration and default input binding tables.
The ``Action`` enum lists every semantic action the engine recognises;
``DEFAULT_KEYBOARD_BINDINGS`` and ``DEFAULT_CONTROLLER_BINDINGS`` map
each action to the corresponding pygame key / joystick button indices.
"""

from enum import Enum

import pygame


class Action(str, Enum):
    """Semantic action identifiers consumed by ``InputManager``."""

    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    JUMP = "JUMP"
    CROUCH = "CROUCH"
    SHORT_ATTACK = "SHORT_ATTACK"
    LONG_ATTACK = "LONG_ATTACK"
    PAUSE = "PAUSE"
    CONFIRM = "CONFIRM"
    CANCEL = "CANCEL"


#: Default keyboard bindings (pygame key constants).
DEFAULT_KEYBOARD_BINDINGS: dict[Action, list[int]] = {
    Action.MOVE_LEFT: [pygame.K_LEFT, pygame.K_a],
    Action.MOVE_RIGHT: [pygame.K_RIGHT, pygame.K_d],
    Action.JUMP: [pygame.K_SPACE, pygame.K_w, pygame.K_UP],
    Action.CROUCH: [pygame.K_DOWN, pygame.K_s],
    Action.SHORT_ATTACK: [pygame.K_j],
    Action.LONG_ATTACK: [pygame.K_k],
    Action.PAUSE: [pygame.K_ESCAPE, pygame.K_p],
    Action.CONFIRM: [pygame.K_RETURN, pygame.K_z],
    Action.CANCEL: [pygame.K_x, pygame.K_BACKSPACE],
}

#: Default controller bindings (joystick button indices).
#: Button indices follow the SDL gamepad layout; values may be remapped
#: by the player at runtime in a later phase.
DEFAULT_CONTROLLER_BINDINGS: dict[Action, list[int]] = {
    Action.MOVE_LEFT: [14],       # D-pad left / left stick left
    Action.MOVE_RIGHT: [15],      # D-pad right / left stick right
    Action.JUMP: [0],             # A / ×
    Action.CROUCH: [1],           # B / ○
    Action.SHORT_ATTACK: [2],     # X / □
    Action.LONG_ATTACK: [3],      # Y / △
    Action.PAUSE: [9],            # Start
    Action.CONFIRM: [0],          # A / ×
    Action.CANCEL: [1],           # B / ○
}
