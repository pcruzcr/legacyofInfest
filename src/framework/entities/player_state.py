"""
Module: player_state
System: framework
Academic Unit: Player character
Description: ``PlayerState`` enum and transition logic for the player
finite state machine.
"""

from __future__ import annotations

from enum import Enum


class PlayerState(str, Enum):
    """Player finite state machine states."""

    IDLE = "IDLE"
    WALKING = "WALKING"
    JUMPING = "JUMPING"
    FALLING = "FALLING"
    CROUCHING = "CROUCHING"
    SHORT_ATTACK = "SHORT_ATTACK"
    LONG_ATTACK = "LONG_ATTACK"
    HURT = "HURT"
    DYING = "DYING"
