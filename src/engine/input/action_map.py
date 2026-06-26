"""
Module: action_map
System: engine
Academic Unit: N/A
Description: Action enumeration and default keyboard/controller bindings.
All player controls are routed through the InputManager using these
abstract action names. The player entity never queries Pygame directly.
"""

from __future__ import annotations

import pygame
from enum import Enum


class Action(str, Enum):
    """Abstract input actions. Values are the string names used in EventBus."""

    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    JUMP = "JUMP"
    CROUCH = "CROUCH"
    SHORT_ATTACK = "SHORT_ATTACK"
    LONG_ATTACK = "LONG_ATTACK"
    PAUSE = "PAUSE"
    CONFIRM = "CONFIRM"
    CANCEL = "CANCEL"


# Default keyboard bindings (pygame key constants)
# Per 03_ARCHITECTURE.md §2.3 table
DEFAULT_KEYBOARD_BINDINGS: dict[Action, list[int]] = {
    Action.MOVE_LEFT: [pygame.K_LEFT, pygame.K_a],
    Action.MOVE_RIGHT: [pygame.K_RIGHT, pygame.K_d],
    Action.JUMP: [pygame.K_SPACE, pygame.K_w, pygame.K_UP],
    Action.CROUCH: [pygame.K_DOWN, pygame.K_s],
    Action.SHORT_ATTACK: [pygame.K_z, pygame.K_j],
    Action.LONG_ATTACK: [pygame.K_x, pygame.K_k],
    Action.PAUSE: [pygame.K_ESCAPE, pygame.K_p],
    Action.CONFIRM: [pygame.K_RETURN, pygame.K_z],
    Action.CANCEL: [pygame.K_BACKSPACE, pygame.K_x],
}

# Default controller bindings (pygame joystick button indices)
# Xbox-style: A=0, B=1, X=2, Y=3, LB=4, RB=5, Back=6, Start=7
# PS-style: Cross=0, Circle=1, Square=2, Triangle=3, L1=4, R1=5, Share=6, Options=7
DEFAULT_CONTROLLER_BINDINGS: dict[Action, list[int]] = {
    Action.MOVE_LEFT: [],  # Handled via axis
    Action.MOVE_RIGHT: [],  # Handled via axis
    Action.JUMP: [0],  # A / Cross
    Action.CROUCH: [1],  # B / Circle
    Action.SHORT_ATTACK: [2],  # X / Square
    Action.LONG_ATTACK: [3],  # Y / Triangle
    Action.PAUSE: [7],  # Start / Options
    Action.CONFIRM: [0],  # A / Cross
    Action.CANCEL: [1],  # B / Circle
}