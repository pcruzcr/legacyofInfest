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
    JUMP = auto()
    CROUCH = auto()
    SHORT_ATTACK = auto()
    LONG_ATTACK = auto()
    CONFIRM = auto()
    CANCEL = auto()
    PAUSE = auto()


# Default keyboard bindings: Action -> list of pygame key constants
DEFAULT_KEY_BINDINGS: dict[Action, list[int]] = {
    Action.MOVE_LEFT: [pygame.K_LEFT, pygame.K_a],
    Action.MOVE_RIGHT: [pygame.K_RIGHT, pygame.K_d],
    Action.JUMP: [pygame.K_SPACE, pygame.K_UP, pygame.K_w],
    Action.CROUCH: [pygame.K_DOWN, pygame.K_s],
    Action.SHORT_ATTACK: [pygame.K_z, pygame.K_j],
    Action.LONG_ATTACK: [pygame.K_x, pygame.K_k],
    Action.CONFIRM: [pygame.K_RETURN, pygame.K_SPACE, pygame.K_z],
    Action.CANCEL: [pygame.K_ESCAPE, pygame.K_x],
    Action.PAUSE: [pygame.K_ESCAPE, pygame.K_p],
}
