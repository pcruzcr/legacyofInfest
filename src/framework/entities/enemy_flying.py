"""
Module: enemy_flying
System: framework.entities
Academic Unit: Unit III (Curve Mathematics, Sine-wave Motion)
Description: Flying enemy that travels through the air along a computed
path. Supports sine-wave oscillation, Bézier (spline through waypoints),
and linear waypoint patrol modes.
"""
from __future__ import annotations

import math

import pygame

from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.processing.curve_tools import CurveTools


class EnemyFlying(EnemyBase):
    """
    Flying enemy — sine-wave, Bézier spline, or waypoint flight path.
    Inherits from EnemyBase.
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
        zone: int = 0,
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

        # Path mode state (bezier / patrol)
        self._path_progress: float = 0.0
        self._waypoint_index: int = 0
        self._path_waypoints: list[pygame.Vector2] = []
        if waypoints:
            self._path_waypoints = [
                pygame.Vector2(w) for w in waypoints
            ]
        else:
            # Default waypoints: a diamond shape around origin
            cx, cy = float(spawn_position.x), float(spawn_position.y)
            self._path_waypoints = [
                pygame.Vector2(cx - 64, cy),
                pygame.Vector2(cx, cy - 48),
                pygame.Vector2(cx + 64, cy),
                pygame.Vector2(cx, cy + 48),
            ]

        # Rect size
        self.rect.width = 20
        self.rect.height = 20

        # Validate mode
        if self.flight_mode not in ("sine", "bezier", "patrol"):
            self.flight_mode = "sine"

        # Load sprites
        self._load_zone_sprites(zone, "fly", 14, 10)

    # ──────────────────────────────────────────────
    # Behavior implementations
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Execute flight behavior based on flight_mode."""
        if self.flight_mode == "sine":
            self._sine_patrol(dt)
        elif self.flight_mode == "bezier":
            self._bezier_patrol(dt)
        elif self.flight_mode == "patrol":
            self._waypoint_patrol(dt)

    def _alert_behavior(self, dt: float) -> None:
        """Accelerate path speed by 1.5x when alert."""
        speed_mult = 1.5
        if self.flight_mode == "sine":
            self._sine_patrol(dt, speed_mult=speed_mult)
        elif self.flight_mode == "bezier":
            self._bezier_patrol(dt, speed_mult=speed_mult)
        elif self.flight_mode == "patrol":
            self._waypoint_patrol(dt, speed_mult=speed_mult)

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

    def _bezier_patrol(self, dt: float, speed_mult: float = 1.0) -> None:
        """
        Bézier path traversal: follow a smooth closed curve through all
        waypoints using Catmull-Rom spline segments.
        """
        if not self._path_waypoints:
            return

        arc_length = self.flight_speed * speed_mult * dt
        total_path = 64.0 * max(len(self._path_waypoints), 1)
        self._path_progress += arc_length / total_path

        # Loop when done
        if self._path_progress > 1.0:
            self._path_progress -= 1.0

        pos = CurveTools.build_bezier_path(
            self._path_waypoints, self._path_progress
        )
        self.position.x = pos.x
        self.position.y = pos.y
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def _waypoint_patrol(self, dt: float, speed_mult: float = 1.0) -> None:
        """Linear waypoint patrol: move from waypoint to waypoint in order."""
        if len(self._path_waypoints) < 2:
            return

        target = self._path_waypoints[self._waypoint_index]
        dx = target.x - self.position.x
        dy = target.y - self.position.y
        dist = math.sqrt(dx * dx + dy * dy)

        step = self.flight_speed * speed_mult * dt

        if dist <= step:
            # Reached waypoint — advance to next
            self.position.x = target.x
            self.position.y = target.y
            self._waypoint_index += 1
            if self._waypoint_index >= len(self._path_waypoints):
                self._waypoint_index = 0
            # Face direction of travel
            next_target = self._path_waypoints[self._waypoint_index]
            if next_target.x != self.position.x:
                self.facing_direction = 1 if next_target.x > self.position.x else -1
        else:
            # Move toward target
            self.position.x += (dx / dist) * step
            self.position.y += (dy / dist) * step
            self.facing_direction = 1 if dx > 0 else -1

        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def _get_animation_state(self) -> str:
        """Return animation key for current state."""
        if self.state == EnemyState.DYING:
            return "die"
        if self.state == EnemyState.HURT:
            return "hurt"
        return "fly"

    def _build_hitbox(self) -> pygame.Rect:
        """Flying enemy has no active attack hitbox."""
        return pygame.Rect(0, 0, 0, 0)

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox rect."""
        return pygame.Rect(6, 4, 20, 20)
