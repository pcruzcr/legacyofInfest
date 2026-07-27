"""
Module: action_map
System: engine.input
Academic Unit: N/A
Description: Action enum and keyboard bindings for abstract input actions.
"""
from __future__ import annotations

from enum import Enum, auto

import pygame


class Action(Enum):
    """Abstract game actions. Bindings map physical keys to these actions."""
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    JUMP = auto()
    CROUCH = auto()
    SHORT_ATTACK = auto()
    LONG_ATTACK = auto()
    DASH = auto()
    GRAB = auto()
    CONFIRM = auto()
    CANCEL = auto()
    PAUSE = auto()
    # Learning overlay panels (ARC-034)
    LEARN_MATH = auto()
    LEARN_PHYSICS = auto()
    LEARN_COLLISION = auto()
    LEARN_FSM = auto()
    LEARN_RENDER = auto()
    LEARN_AUDIO = auto()
    LEARN_PERF = auto()
    LEARN_CONTROLS = auto()
    LEARN_HELP = auto()
    OPEN_BESTIARY = auto()
    # AUD-022: AudioManager.toggle_mute()/is_muted existed with no callers, so
    # the game had no working mute at all. M is the conventional binding.
    TOGGLE_MUTE = auto()


# Default keyboard bindings: Action -> list of pygame key constants
DEFAULT_KEY_BINDINGS: dict[Action, list[int]] = {
    Action.MOVE_LEFT: [pygame.K_LEFT, pygame.K_a],
    Action.MOVE_RIGHT: [pygame.K_RIGHT, pygame.K_d],
    Action.MOVE_UP: [pygame.K_UP, pygame.K_w],
    Action.MOVE_DOWN: [pygame.K_DOWN, pygame.K_s],
    Action.JUMP: [pygame.K_SPACE, pygame.K_UP, pygame.K_w],
    Action.CROUCH: [pygame.K_DOWN, pygame.K_s],
    Action.DASH: [pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LALT],
    Action.GRAB: [pygame.K_g, pygame.K_c],
    Action.SHORT_ATTACK: [pygame.K_z, pygame.K_j],
    Action.LONG_ATTACK: [pygame.K_x, pygame.K_k],
    Action.CONFIRM: [pygame.K_RETURN, pygame.K_SPACE, pygame.K_z],
    Action.CANCEL: [pygame.K_ESCAPE, pygame.K_x],
    Action.PAUSE: [pygame.K_ESCAPE, pygame.K_p],
    Action.LEARN_MATH: [pygame.K_F2],
    Action.LEARN_PHYSICS: [pygame.K_F3],
    Action.LEARN_COLLISION: [pygame.K_F4],
    Action.LEARN_FSM: [pygame.K_F5],
    Action.LEARN_RENDER: [pygame.K_F6],
    Action.LEARN_AUDIO: [pygame.K_F7],
    Action.LEARN_PERF: [pygame.K_F8],
    Action.LEARN_CONTROLS: [pygame.K_F9],
    Action.LEARN_HELP: [pygame.K_F10],
    Action.OPEN_BESTIARY: [pygame.K_TAB],
    Action.TOGGLE_MUTE: [pygame.K_m],
}

# Controller axis/deadzone constants
CONTROLLER_DEADZONE: float = 0.25
CONTROLLER_AXIS_LEFT_X: int = 0
CONTROLLER_AXIS_LEFT_Y: int = 1
_CONTROLLER_BUTTON_MAP: dict[int, Action] = {
    0: Action.JUMP,           # A
    1: Action.SHORT_ATTACK,   # B
    2: Action.LONG_ATTACK,    # X
    3: Action.CROUCH,         # Y
    4: Action.GRAB,           # LB
    7: Action.PAUSE,          # START
    6: Action.CANCEL,         # SELECT/BACK
}
