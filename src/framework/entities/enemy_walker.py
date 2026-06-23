"""
Module: enemy_walker
System: framework
Academic Unit: Enemy framework
Description: EnemyWalker — ground-bound patrol enemy.
Matches 05_ENEMY_SPEC.md §3 and 22_API_CONTRACTS.md §10.2.
"""

from __future__ import annotations

import pygame

from src.framework.entities.enemy_base import EnemyBase, EnemyState


class EnemyWalker(EnemyBase):
    """Ground-bound enemy that patrols horizontally with ledge detection."""

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_length: float = 96.0,
        facing: str = "right",
        patrol_speed: float = 45.0,
        alert_speed: float = 75.0,
        damage_on_contact: float = 0.5,
        max_health: float = 2.0,
    ) -> None:
        """Spawn a walker at *spawn_position* with given patrol parameters."""
        super().__init__(
            spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
        )
        self.patrol_origin: pygame.Vector2 = spawn_position.copy()
        self.patrol_length: float = patrol_length
        self.patrol_speed: float = patrol_speed
        self.alert_speed: float = alert_speed

        self.facing_direction: int = 1 if facing == "right" else -1
        self.detection_range_x = 160.0
        self.detection_range_y = 48.0

        self._collision_rects: list[pygame.Rect] = []

    def _patrol_behavior(self, dt: float) -> None:
        """Move at patrol speed, reverse at limits or ledges."""
        self.position.x += self.patrol_speed * self.facing_direction * dt
        # Patrol limit reversal
        dist = abs(self.position.x - self.patrol_origin.x)
        if dist >= self.patrol_length / 2:
            self.facing_direction *= -1
        # Ledge detection
        probe_x = self.position.x + (
            self.facing_direction * (self.rect.width / 2 + 2)
        )
        probe_y = self.position.y + self.rect.height + 4
        has_floor = False
        for r in self._collision_rects:
            if r.left <= probe_x <= r.right and r.top <= probe_y <= r.bottom:
                has_floor = True
                break
        if not has_floor and self._collision_rects:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        """Move toward player at alert speed."""
        if hasattr(self, "_target_x") and self._target_x is not None:
            target_x = self._target_x
            dx = target_x - self.position.x
            if abs(dx) < 2.0:
                return
            self.facing_direction = 1 if dx > 0 else -1
            self.position.x += (
                self.alert_speed * self.facing_direction * dt
            )

    def _get_animation_state(self) -> str:
        """Return animation key."""
        if self.state == EnemyState.ALERT:
            return "alert"
        if self.state == EnemyState.HURT:
            return "hurt"
        if self.state == EnemyState.DYING:
            return "die"
        return "walk"

    def _build_hitbox(self) -> pygame.Rect:
        """Walker has no attack hitbox — returns empty."""
        return pygame.Rect(0, 0, 0, 0)

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox: offset (4, 2), 24x28."""
        return pygame.Rect(4, 2, 24, 28)

    def set_collision_rects(self, rects: list[pygame.Rect]) -> None:
        """Provide platform collision rects for ledge detection."""
        self._collision_rects = rects

    def set_target_x(self, target_x: float) -> None:
        """Set the player's X position for ALERT movement."""
        self._target_x = target_x
