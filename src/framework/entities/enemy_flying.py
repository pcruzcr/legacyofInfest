"""
Module: enemy_flying
System: framework
Academic Unit: Enemy framework
Description: EnemyFlying — airborne enemy with sine-wave flight.
Matches 05_ENEMY_SPEC.md §4 and 22_API_CONTRACTS.md §10.3.
Bézier and patrol modes are stubbed (deferred to Phase 8).
"""

from __future__ import annotations

import math

import pygame

from src.framework.entities.enemy_base import EnemyBase, EnemyState


class EnemyFlying(EnemyBase):
    """Airborne enemy that follows a computed flight path.

    Sine mode is fully implemented. Bézier and patrol modes raise
    ``NotImplementedError`` and will be completed in Phase 8 (T8.6).
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
        """Spawn a flying enemy with the given flight parameters."""
        super().__init__(
            spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=180.0,
            detection_range_y=96.0,
        )
        self.flight_mode: str = flight_mode
        self.flight_speed: float = flight_speed
        self.sine_amplitude: float = sine_amplitude
        self.sine_frequency: float = sine_frequency
        self.waypoints: list[tuple[float, float]] = waypoints or []

        self._origin_y: float = spawn_position.y
        self._elapsed_time: float = 0.0

        self.detection_range_x = 180.0
        self.detection_range_y = 96.0

    def _patrol_behavior(self, dt: float) -> None:
        """Follow the defined flight path."""
        if self.flight_mode == "sine":
            self._sine_patrol(dt)
        elif self.flight_mode == "bezier":
            raise NotImplementedError(
                "Bézier mode not yet implemented (deferred to Phase 8)"
            )
        elif self.flight_mode == "patrol":
            raise NotImplementedError(
                "Patrol mode not yet implemented (deferred to Phase 8)"
            )

    def _alert_behavior(self, dt: float) -> None:
        """Accelerate path speed by 1.5x."""
        if self.flight_mode == "sine":
            self._sine_patrol(dt, speed_mult=1.5)
        else:
            self._patrol_behavior(dt)

    def _sine_patrol(self, dt: float, speed_mult: float = 1.0) -> None:
        """Sine-wave oscillation: horizontal + sinusoidal vertical."""
        speed = self.flight_speed * speed_mult
        self._elapsed_time += dt
        self.position.x += speed * self.facing_direction * dt
        self.position.y = (
            self._origin_y
            + self.sine_amplitude
            * math.sin(
                2 * math.pi * self.sine_frequency * self._elapsed_time
            )
        )

    def _get_animation_state(self) -> str:
        """Return animation key."""
        if self.state == EnemyState.ALERT:
            return "alert"
        if self.state == EnemyState.HURT:
            return "hurt"
        if self.state == EnemyState.DYING:
            return "die"
        return "fly"

    def _build_hitbox(self) -> pygame.Rect:
        """Flying enemy has no attack hitbox — returns empty."""
        return pygame.Rect(0, 0, 0, 0)

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox: offset (6, 4), 20x20."""
        return pygame.Rect(6, 4, 20, 20)
