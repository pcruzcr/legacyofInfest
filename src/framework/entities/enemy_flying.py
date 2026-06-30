"""
Module: enemy_flying
System: framework.entities
Academic Unit: Unit III (Curve Mathematics, Sine-wave Motion)
Description: Flying enemy that travels through the air along a computed
path. Default mode is sine-wave oscillation. Bézier and patrol modes
require Phase 8 CurveTools and are stubbed with NotImplementedError.
"""
from __future__ import annotations

import math

import pygame

from src.framework.entities.enemy_base import EnemyBase, EnemyState


class EnemyFlying(EnemyBase):
    """
    Flying enemy — sine-wave or waypoint flight path.
    Inherits from EnemyBase. Sine mode is fully implemented;
    Bézier and patrol modes require Phase 8 CurveTools.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        flight_mode: str = "sine",
        flight_speed: float = 60.0,
        sine_amplitude: float = 28.0,
        sine_frequency: float = 1.5,
        waypoints: list[tuple[float, float]] | None = None,
        max_health: float = 1.5,
        damage_on_contact: float = 0.5,
    ) -> None:
        """Initialize the flying enemy."""
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=180.0,
            detection_range_y=96.0,
        )

        self.flight_mode: str = flight_mode
        self.flight_speed: float = flight_speed
        self.sine_amplitude: float = sine_amplitude
        self.sine_frequency: float = sine_frequency
        self.waypoints: list[tuple[float, float]] | None = waypoints

        # Sine mode state
        self._origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self._t: float = 0.0

        # Rect size
        self.rect.width = 20
        self.rect.height = 20

        # Validate mode
        if self.flight_mode not in ("sine", "bezier", "patrol"):
            self.flight_mode = "sine"

    # ──────────────────────────────────────────────
    # Behavior implementations
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Execute flight behavior based on flight_mode."""
        if self.flight_mode == "sine":
            self._sine_patrol(dt)
        elif self.flight_mode == "bezier":
            raise NotImplementedError(
                "EnemyFlying Bézier mode requires Phase 8 CurveTools. "
                "See KNOWN_GAPS.md GAP-001"
            )
        elif self.flight_mode == "patrol":
            raise NotImplementedError(
                "EnemyFlying patrol mode requires Phase 8 CurveTools. "
                "See KNOWN_GAPS.md GAP-001"
            )

    def _alert_behavior(self, dt: float) -> None:
        """Accelerate path speed by 1.5x when alert."""
        speed_mult = 1.5
        if self.flight_mode == "sine":
            self._sine_patrol(dt, speed_mult=speed_mult)

    def _sine_patrol(self, dt: float, speed_mult: float = 1.0) -> None:
        """
        Sine-wave movement: horizontal movement with sinusoidal
        vertical oscillation.
        """
        self._t += dt

        # Horizontal movement
        self.position.x += (
            self.facing_direction * self.flight_speed * speed_mult * dt
        )

        # Vertical sine oscillation
        self.position.y = (
            self._origin.y
            + self.sine_amplitude
            * math.sin(2.0 * math.pi * self.sine_frequency * self._t)
        )

        # Reverse at boundaries (simple bounce)
        dx = self.position.x - self._origin.x
        if abs(dx) > 96.0:
            self.facing_direction *= -1

        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def _get_animation_state(self) -> str:
        """Return animation key for current state."""
        if self.state == EnemyState.ALERT:
            return "alert"
        return "fly"

    def _build_hitbox(self) -> pygame.Rect:
        """Flying enemy has no active attack hitbox."""
        return pygame.Rect(0, 0, 0, 0)

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox rect."""
        return pygame.Rect(6, 4, 20, 20)

    # ──────────────────────────────────────────────
    # Custom draw (orange placeholder)
    # ──────────────────────────────────────────────

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """Draw the flying enemy as an orange rectangle with white border."""
        if not self.is_visible or not self.is_alive:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        pygame.draw.rect(
            surface,
            (255, 150, 0),
            (screen_x, screen_y, self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, self.rect.width, self.rect.height),
            1,
        )