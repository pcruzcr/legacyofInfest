"""
Module: enemy_shooter
System: framework
Academic Unit: Enemy framework
Description: EnemyShooter and Projectile for ranged attacks.
Matches 05_ENEMY_SPEC.md §5 and 22_API_CONTRACTS.md §10.4.
"""

from __future__ import annotations

import math

import pygame

from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase, EnemyState


class Projectile(BaseEntity):
    """Lightweight projectile entity fired by EnemyShooter."""

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: float,
        lifetime: float = 3.0,
    ) -> None:
        """Spawn a projectile at *spawn_position* moving at *velocity*."""
        super().__init__(spawn_position)
        self.velocity: pygame.Vector2 = velocity
        self.damage: float = damage
        self._lifetime: float = lifetime
        self._age: float = 0.0
        self.hurtbox: pygame.Rect = pygame.Rect(
            int(spawn_position.x) - 2,
            int(spawn_position.y) - 2,
            4,
            4,
        )

    def update(self, dt: float) -> None:
        """Move, age, and expire if lifetime exceeded."""
        self._age += dt
        if self._age >= self._lifetime:
            self.is_active = False
            return
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.hurtbox.center = (int(self.position.x), int(self.position.y))

    def draw(
        self, surface: pygame.Surface, camera_offset: pygame.Vector2
    ) -> None:
        """Render as a small glowing orb."""
        sx = int(self.position.x - camera_offset.x)
        sy = int(self.position.y - camera_offset.y)
        pygame.draw.circle(surface, (255, 200, 60), (sx, sy), 2)


class EnemyShooter(EnemyBase):
    """Stationary/slow-patrol enemy that fires projectiles at the player."""

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        fire_rate: float = 0.5,
        projectile_speed: float = 120.0,
        projectile_damage: float = 0.5,
        patrol_length: float = 0.0,
        max_health: float = 3.0,
        damage_on_contact: float = 0.25,
    ) -> None:
        """Spawn a shooter enemy at *spawn_position*."""
        super().__init__(
            spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=200.0,
            detection_range_y=64.0,
        )
        self.fire_rate: float = fire_rate
        self.projectile_speed: float = projectile_speed
        self.projectile_damage: float = projectile_damage
        self.patrol_length: float = patrol_length

        self._fire_cooldown: float = 0.0
        self._patrol_origin_x: float = spawn_position.x
        self._projectiles: list[Projectile] = []
        self._target_position: pygame.Vector2 = spawn_position.copy()

    @property
    def projectiles(self) -> list[Projectile]:
        """Read-only view of active projectiles."""
        return [p for p in self._projectiles if p.is_active]

    def set_target(self, target_pos: pygame.Vector2) -> None:
        """Set the player's current position for aim calculations."""
        self._target_position = target_pos

    def _patrol_behavior(self, dt: float) -> None:
        """Slow patrol if patrol_length > 0, otherwise idle."""
        if self.patrol_length <= 0:
            return
        speed = 20.0
        self.position.x += speed * self.facing_direction * dt
        dist = abs(self.position.x - self._patrol_origin_x)
        if dist >= self.patrol_length / 2:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        """Face player, manage fire cooldown, fire projectiles."""
        dx = self._target_position.x - self.position.x
        if abs(dx) > 2.0:
            self.facing_direction = 1 if dx > 0 else -1

        if self.state != EnemyState.FIRING:
            self.state = EnemyState.ALERT

        self._fire_cooldown -= dt
        if self._fire_cooldown <= 0:
            self._fire()

    def _fire(self) -> None:
        """Create a projectile aimed at the target position."""
        active_count = sum(1 for p in self._projectiles if p.is_active)
        if active_count >= 3:
            return

        dx = self._target_position.x - self.position.x
        dy = self._target_position.y - self.position.y
        angle = math.atan2(dy, dx)
        vx = math.cos(angle) * self.projectile_speed
        vy = math.sin(angle) * self.projectile_speed

        muzzle_x = self.position.x + self.facing_direction * 12
        muzzle_y = self.position.y

        proj = Projectile(
            spawn_position=pygame.Vector2(muzzle_x, muzzle_y),
            velocity=pygame.Vector2(vx, vy),
            damage=self.projectile_damage,
        )
        self._projectiles.append(proj)
        self._fire_cooldown = 1.0 / self.fire_rate
        self.state = EnemyState.FIRING

    def _get_animation_state(self) -> str:
        """Return animation key."""
        if self.state == EnemyState.ALERT:
            return "aim"
        if self.state == EnemyState.FIRING:
            return "fire"
        if self.state == EnemyState.HURT:
            return "hurt"
        if self.state == EnemyState.DYING:
            return "die"
        return "idle"

    def _build_hitbox(self) -> pygame.Rect:
        """No active attack hitbox — contact damage only."""
        return pygame.Rect(0, 0, 0, 0)

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox: offset (4, 2), 24x30."""
        return pygame.Rect(4, 2, 24, 30)

    def _die(self) -> None:
        """On death, expire all projectiles."""
        for p in self._projectiles:
            p.is_active = False
        super()._die()

    def update(self, dt: float) -> None:
        """Update shooter and all active projectiles."""
        super().update(dt)
        for p in self._projectiles:
            if p.is_active:
                p.update(dt)
