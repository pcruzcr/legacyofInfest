"""
Module: enemy_base
System: framework
Academic Unit: Enemy framework
Description: EnemyBase abstract class and EnemyState enum.
Implements the contract from 22_API_CONTRACTS.md §10.1 and
05_ENEMY_SPEC.md §2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

import pygame

from src.engine.core.event_bus import EventBus
from src.framework.entities.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyState(str, Enum):
    """Enemy finite state machine states."""

    PATROL = "PATROL"
    ALERT = "ALERT"
    HURT = "HURT"
    DYING = "DYING"


class EnemyBase(BaseEntity, ABC):
    """Abstract root class for all enemies.

    Subclasses must implement the five abstract methods listed below.
    Provided methods (apply_hit, _die, etc.) must not be overridden.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float,
        damage_on_contact: float = 0.5,
        contact_knockback: float = 120.0,
        detection_range_x: float = 160.0,
        detection_range_y: float = 64.0,
    ) -> None:
        """Spawn enemy at *spawn_position* with the given stats."""
        super().__init__(spawn_position)
        self.max_health: float = max_health
        self.current_health: float = max_health
        self.is_alive: bool = True
        self.facing_direction: int = 1
        self.state: EnemyState = EnemyState.PATROL

        self.damage_on_contact: float = damage_on_contact
        self.contact_knockback: float = contact_knockback
        self.detection_range_x: float = detection_range_x
        self.detection_range_y: float = detection_range_y
        self.deaggro_margin: float = 32.0

        self._invincibility_timer: float = 0.0
        self._hurt_timer: float = 0.0
        self._death_timer: float = 0.0
        self._contact_cooldown: float = 0.0

        self.rect: pygame.Rect = pygame.Rect(0, 0, 16, 16)
        self.hitbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.hurtbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        self.death_sfx: str = "sfx_enemy_die"
        self.hit_sfx: str = "sfx_enemy_hit"

    # --- Required overrides ---

    @abstractmethod
    def _patrol_behavior(self, dt: float) -> None:
        """Movement/AI when no player detected."""

    @abstractmethod
    def _alert_behavior(self, dt: float) -> None:
        """AI when player is within detection range."""

    @abstractmethod
    def _get_animation_state(self) -> str:
        """Return animation key for current state."""

    @abstractmethod
    def _build_hitbox(self) -> pygame.Rect:
        """Return LOCAL-space hitbox rect."""

    @abstractmethod
    def _build_hurtbox(self) -> pygame.Rect:
        """Return LOCAL-space hurtbox rect."""

    # --- Provided methods (do not override) ---

    def apply_hit(
        self, damage: float, source_position: tuple[float, float]
    ) -> None:
        """Apply damage from player attack.

        1. Subtract damage, clamp to 0.
        2. If health <= 0: state = DYING, emit ENEMY_DIED.
        3. Else: state = HURT, start hurt timer.
        """
        if self.state == EnemyState.DYING:
            return
        if self._invincibility_timer > 0:
            return

        self.current_health -= damage
        if self.current_health <= 0.0:
            self.current_health = 0.0
            self.state = EnemyState.DYING
            self._death_timer = 0.5
            EventBus.emit(
                "ENEMY_DIED",
                entity_id=id(self),
                position=(self.position.x, self.position.y),
            )
        else:
            self.state = EnemyState.HURT
            self._hurt_timer = 0.25
            self._invincibility_timer = 0.5
            EventBus.emit("ENEMY_HIT", entity_id=id(self))

    def _die(self) -> None:
        """Handle death completion; mark inactive for removal."""
        self.is_alive = False
        self.is_active = False

    def _update_invincibility(self, dt: float) -> None:
        """Tick down invincibility timer."""
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt

    def _check_player_contact(self, player: "Player") -> None:
        """If hurtboxes overlap and player not invincible, deal contact."""
        if self.state == EnemyState.DYING:
            return
        if self._contact_cooldown > 0:
            return
        if not hasattr(player, "apply_damage"):
            return

        if self.hurtbox.colliderect(player.get_hurtbox()):
            if (
                hasattr(player, "_invincibility_timer")
                and player._invincibility_timer > 0
            ):
                return
            player.apply_damage(
                self.damage_on_contact, source=self.rect.center
            )
            self._contact_cooldown = 0.3

    def _update_rects(self) -> None:
        """Recompute world-space hitbox, hurtbox, and base rect."""
        self.hitbox = self._build_hitbox()
        self.hurtbox = self._build_hurtbox()
        self.hitbox.topleft = (
            self.hitbox.x + self.position.x,
            self.hitbox.y + self.position.y,
        )
        self.hurtbox.topleft = (
            self.hurtbox.x + self.position.x,
            self.hurtbox.y + self.position.y,
        )
        self.rect.topleft = (
            int(self.position.x),
            int(self.position.y),
        )

    def update(self, dt: float) -> None:
        """Master update: tick timers, run FSM, update rects, check contact."""
        if self.state == EnemyState.DYING:
            self._death_timer -= dt
            if self._death_timer <= 0:
                self._die()
            return

        self._update_invincibility(dt)
        self._run_state_machine(dt)
        self._update_rects()

        if self._contact_cooldown > 0:
            self._contact_cooldown -= dt

    def _run_state_machine(self, dt: float) -> None:
        """Dispatch to behavior based on current state."""
        if self.state == EnemyState.PATROL:
            self._patrol_behavior(dt)
        elif self.state == EnemyState.ALERT:
            self._alert_behavior(dt)
        elif self.state == EnemyState.HURT:
            self._hurt_timer -= dt
            if self._hurt_timer <= 0:
                self.state = EnemyState.PATROL

    def draw(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2
    ) -> None:
        """Render the enemy using the animation controller."""
        self._draw_impl(surface, camera_offset)

    def _draw_impl(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2
    ) -> None:
        """Placeholder draw — subclasses override with sprite rendering."""
        if (
            self._invincibility_timer > 0
            and int(self._invincibility_timer * 60 / 4) % 2 == 0
        ):
            return
        screen_rect = self.rect.move(
            -int(camera_offset.x), -int(camera_offset.y)
        )
        pygame.draw.rect(surface, (120, 160, 120), screen_rect)
