"""
Module: enemy_shooter
System: framework.entities
Academic Unit: Unit II (Vectors, Trigonometry), Unit IV (Sprite Animation)
Description: Shooter enemy that fires projectiles at the player when
detected. Uses atan2 for angle calculation. Projectile is a lightweight
sub-entity with velocity, lifetime, and collision.
"""
from __future__ import annotations

import math

import pygame

from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase, EnemyState


class Projectile(BaseEntity):
    """
    Lightweight projectile entity fired by EnemyShooter.
    Travels in a straight line at constant velocity.
    Expires after lifetime or on collision.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: float,
        lifetime: float = 3.0,
    ) -> None:
        """Initialize the projectile."""
        super().__init__(spawn_position)
        self.velocity: pygame.Vector2 = velocity
        self.damage: float = damage
        self._lifetime: float = lifetime
        self._elapsed: float = 0.0
        self._expired: bool = False

        # Small circular hitbox
        self.rect = pygame.Rect(
            int(self.position.x) - 2,
            int(self.position.y) - 2,
            4,
            4,
        )
        self.layer = 5

    def update(self, dt: float) -> None:
        """Move projectile and check expiration."""
        if self._expired:
            self.is_active = False
            return

        self._elapsed += dt
        if self._elapsed >= self._lifetime:
            self._expired = True
            self.is_active = False
            return

        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.rect.center = (int(self.position.x), int(self.position.y))

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """Draw the projectile as a small yellow circle."""
        if not self.is_visible or self._expired:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        pygame.draw.circle(surface, (255, 255, 0), (screen_x, screen_y), 4)
        pygame.draw.circle(
            surface, (255, 255, 255), (screen_x, screen_y), 4, 1
        )

    def on_collision(self) -> None:
        """Handle collision with a solid tile or player."""
        self._expired = True
        self.is_active = False


class EnemyShooter(EnemyBase):
    """
    Shooter enemy — fires projectiles at the player when detected.
    May be stationary or perform slow patrol.
    """

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
        """Initialize the shooter enemy."""
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=200.0,
            detection_range_y=64.0,
        )

        self.fire_rate: float = fire_rate  # shots per second
        self.projectile_speed: float = projectile_speed
        self.projectile_damage: float = projectile_damage
        self.patrol_length: float = patrol_length
        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self._fire_cooldown: float = 0.0
        self._active_projectiles: list[Projectile] = []
        self._max_projectiles: int = 3
        self._player_ref: pygame.Rect | None = None

        # Rect size
        self.rect.width = 16
        self.rect.height = 24

    def set_player_ref(self, player_rect: pygame.Rect) -> None:
        """Provide the player rect for aiming."""
        self._player_ref = player_rect

    def get_projectiles(self) -> list[Projectile]:
        """Return the list of active projectiles."""
        return self._active_projectiles

    def clear_expired_projectiles(self) -> None:
        """Remove expired projectiles from the active list."""
        self._active_projectiles = [
            p for p in self._active_projectiles if p.is_active
        ]

    # ──────────────────────────────────────────────
    # Behavior implementations
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Slow horizontal movement or stationary."""
        speed = self.facing_direction * 20.0 * dt
        if self.patrol_length > 0:
            self.position.x += speed
            distance = abs(self.position.x - self._patrol_origin.x)
            if distance >= self.patrol_length / 2:
                self.facing_direction *= -1
            self.rect.x = int(self.position.x)
            self.rect.y = int(self.position.y)

    def _alert_behavior(self, dt: float) -> None:
        """Face player and fire projectiles."""
        # Face the player
        if self._player_ref is not None:
            if self._player_ref.centerx < self.rect.centerx:
                self.facing_direction = -1
            else:
                self.facing_direction = 1

        # Fire rate
        self._fire_cooldown -= dt
        if self._fire_cooldown <= 0:
            self._fire()
            self._fire_cooldown = 1.0 / self.fire_rate

        # Slow patrol while alert
        if self.patrol_length > 0:
            self.position.x += self.facing_direction * 20.0 * dt
            self.rect.x = int(self.position.x)
            self.rect.y = int(self.position.y)

    def _fire(self) -> None:
        """Fire a projectile toward the player."""
        if len(self._active_projectiles) >= self._max_projectiles:
            return

        if self._player_ref is None:
            return

        # Calculate angle to player (atan2)
        dx = self._player_ref.centerx - self.rect.centerx
        dy = self._player_ref.centery - self.rect.centery
        angle = math.atan2(dy, dx)

        # Create projectile velocity
        vel = pygame.Vector2(
            math.cos(angle) * self.projectile_speed,
            math.sin(angle) * self.projectile_speed,
        )

        spawn_pos = pygame.Vector2(
            self.rect.centerx + (self.facing_direction * 10),
            self.rect.centery,
        )

        projectile = Projectile(
            spawn_position=spawn_pos,
            velocity=vel,
            damage=self.projectile_damage,
            lifetime=3.0,
        )
        self._active_projectiles.append(projectile)

    def _get_animation_state(self) -> str:
        """Return animation key for current state."""
        if self.state == EnemyState.ALERT:
            return "aim"
        return "idle"

    def _build_hitbox(self) -> pygame.Rect:
        """Shooter has no active attack hitbox."""
        return pygame.Rect(0, 0, 0, 0)

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox rect."""
        return pygame.Rect(4, 2, 24, 30)

    # ──────────────────────────────────────────────
    # Custom draw (purple placeholder)
    # ──────────────────────────────────────────────

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """Draw the shooter as a purple rectangle with white border."""
        if not self.is_visible or not self.is_alive:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        pygame.draw.rect(
            surface,
            (150, 0, 200),
            (screen_x, screen_y, self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, self.rect.width, self.rect.height),
            1,
        )

        # Draw active projectiles
        self.clear_expired_projectiles()
        for p in self._active_projectiles:
            p.draw(surface, camera_offset)

    def update(self, dt: float) -> None:
        """Extend base update with projectile updates."""
        super().update(dt)
        # Update projectiles
        for p in self._active_projectiles:
            p.update(dt)
        self.clear_expired_projectiles()