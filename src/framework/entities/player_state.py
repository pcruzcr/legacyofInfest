"""
Module: player_state
System: framework.entities
Academic Unit: Unit II (Vectors, Collision)
Description: PlayerStateData dataclass — single source of truth for all
mutable player gameplay state. Extracted from ~45 ad-hoc instance variables
in Player.__init__ for serialization, death-reset, and testability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.framework.entities.enemy_base import EnemyBase


@dataclass
class PlayerStateData:
    # Physics
    coyote_counter: int = 0
    jump_cut_applied: bool = False

    # Attack state
    attack_timer: float = 0.0
    attack_active_frames: list[int] = field(default_factory=list)
    attack_current_frame: int = 0
    active_hitbox: pygame.Rect | None = None
    hitbox_consumed: bool = False
    cooldown_timer: float = 0.0

    # Combo state (private)
    combo_air_hits: int = 0
    crouching_at_attack_start: bool = False

    # Special meter
    damage_mult: float = 1.0

    # Slide state
    slide_speed: float = 300.0
    slide_duration: float = 0.4

    # Dash state
    air_dash_count: int = 0
    dash_timer: float = 0.0
    dash_cooldown: float = 0.0

    # Air jump state
    air_jumps_used: int = 0
    swim_boosts: int = 0

    # Damage state
    health: float = 100.0
    invincibility_timer: float = 0.0
    knockback_timer: float = 0.0
    flash_timer: float = 0.0
    flash_visible: bool = True

    # Jump buffering
    prev_foot_y: float = 0.0
    pending_jump: bool = False
    pending_jump_timer: float = 0.0

    # Parry
    parry_window: float = 0.0
    parry_active: bool = False
    parry_success: bool = False

    # Grab/Throw
    grab_target: EnemyBase | None = None
    grab_timer: float = 0.0

    # Charge attack
    charge_timer: float = 0.0
    charge_level: int = 0
    charging: bool = False

    # Wall slide/jump
    wall_side: int = 0
    wall_slide_timer: float = 0.0
    can_wall_jump: bool = False
    can_ledge_grab: bool = False
    ledge_grab_timer: float = 0.0

    def reset(self) -> None:
        """Reset all state to defaults (used on respawn)."""
        self.coyote_counter = 0
        self.jump_cut_applied = False
        self.attack_timer = 0.0
        self.attack_active_frames.clear()
        self.attack_current_frame = 0
        self.active_hitbox = None
        self.hitbox_consumed = False
        self.cooldown_timer = 0.0
        self.combo_air_hits = 0
        self.crouching_at_attack_start = False
        self.damage_mult = 1.0
        self.slide_speed = 300.0
        self.slide_duration = 0.4
        self.air_dash_count = 0
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.air_jumps_used = 0
        self.swim_boosts = 0
        self.invincibility_timer = 0.0
        self.knockback_timer = 0.0
        self.flash_timer = 0.0
        self.flash_visible = True
        self.prev_foot_y = 0.0
        self.pending_jump = False
        self.pending_jump_timer = 0.0
        self.parry_window = 0.0
        self.parry_active = False
        self.parry_success = False
        self.grab_target = None
        self.grab_timer = 0.0
        self.charge_timer = 0.0
        self.charge_level = 0
        self.charging = False
        self.wall_side = 0
        self.wall_slide_timer = 0.0
        self.can_wall_jump = False
        self.can_ledge_grab = False
        self.ledge_grab_timer = 0.0
