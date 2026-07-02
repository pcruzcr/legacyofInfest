"""
Module: enemy_walker
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit III (State Machines)
Description: Ground-bound enemy that patrols horizontally along a defined
segment. Reverses at patrol limits or ledge edges. Accelerates toward
player when detected.
"""
from __future__ import annotations

import pygame

from src.framework.entities.enemy_base import EnemyBase


class EnemyWalker(EnemyBase):
    """
    Walker enemy — horizontal patrol with ledge detection.
    Inherits from EnemyBase. Implements _patrol_behavior and _alert_behavior.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_length: float = 96.0,
        facing: str = "right",
        patrol_speed: float = 45.0,
        alert_speed: float = 75.0,
        damage_on_contact: float = 0.5,
        max_health: float = 2.0,
        zone: int = 0,
    ) -> None:
        """Initialize the walker enemy."""
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=160.0,
            detection_range_y=48.0,
        )

        self.patrol_length: float = patrol_length
        self.patrol_speed: float = patrol_speed
        self.alert_speed: float = alert_speed
        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self._collision_rects: list[pygame.Rect] = []

        # Set initial facing direction
        self.facing_direction = 1 if facing == "right" else -1

        # Set rect size
        self.rect.width = 24
        self.rect.height = 28

        # Load sprites
        self._load_zone_sprites(zone, "walk", 16, 12)

    def set_collision_rects(self, rects: list[pygame.Rect]) -> None:
        """Provide collision rects for ledge detection."""
        self._collision_rects = rects

    # ──────────────────────────────────────────────
    # Behavior implementations
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Move at patrol speed. Reverse at patrol limit or ledge edge."""
        reversed_this_frame = False

        # Ledge detection: probe ahead and below before moving
        if self._collision_rects:
            probe_x = self.position.x + (
                self.facing_direction * (self.rect.width // 2 + 2)
            )
            probe_y = self.position.y + self.rect.height + 4
            has_floor = any(
                r.collidepoint(probe_x, probe_y)
                for r in self._collision_rects
            )
            if not has_floor:
                self.facing_direction *= -1
                reversed_this_frame = True

        # Patrol limit reversal (skip if already reversed for ledge)
        if not reversed_this_frame:
            distance = abs(self.position.x - self._patrol_origin.x)
            if distance >= self.patrol_length / 2:
                self.facing_direction *= -1

        # Move
        self.position.x += self.facing_direction * self.patrol_speed * dt

    def _alert_behavior(self, dt: float) -> None:
        """Move toward player at alert speed."""
        self._face_player()
        self.position.x += self.facing_direction * self.alert_speed * dt

    def _get_animation_key(self) -> str:
        """Return animation key for non-DYING, non-HURT state."""
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox rect."""
        return pygame.Rect(4, 2, 24, 28)

    # Sprite rendering handled by EnemyBase.draw()
