"""
Module: enemy_flying
System: framework.entities
Academic Unit: Unit III (Curve Mathematics, Sine-wave Motion)
Description: Flying enemy that travels through the air along a computed
path. Supports sine-wave oscillation, Bézier (spline through waypoints),
and linear waypoint patrol modes via the Strategy Pattern.

STRATEGY PATTERN (Fase 3): Each flight mode (sine, bezier, patrol) is a
separate strategy class implementing IFlightStrategy. EnemyFlying delegates
both _patrol_behavior and _alert_behavior to its strategy, making it
trivially extensible with new movement algorithms.
"""
from __future__ import annotations

import pygame

from src.framework.entities.enemy_base import EnemyBase
from src.framework.entities.flight_strategies import IFlightStrategy, make_strategy



class EnemyFlying(EnemyBase):
    """
    Flying enemy — sine-wave, Bézier spline, or waypoint flight path.
    Inherits from EnemyBase. Movement algorithm selected via Strategy Pattern.
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
            hurt_duration=0.3,
            invincibility_duration=0.3,
        )

        self.flight_mode: str = flight_mode
        self.flight_speed: float = flight_speed
        self.sine_amplitude: float = sine_amplitude
        self.sine_frequency: float = sine_frequency
        self.waypoints: list[tuple[float, float]] | None = waypoints

        # Strategy Pattern: delegate movement to the selected strategy
        self._strategy: IFlightStrategy = make_strategy(flight_mode)

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

        # Load sprites
        self._load_zone_sprites(zone, "fly", 14, 10)

    # ──────────────────────────────────────────────
    # Behavior implementations (Strategy delegation)
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Delegate patrol movement to the current flight strategy."""
        self._strategy.execute(self, dt)

    def _alert_behavior(self, dt: float) -> None:
        """Delegate alert movement, then track player Y axis."""
        self._strategy.execute(self, dt, speed_mult=1.5)
        self._face_player()
        if self._player_ref is not None:
            dy = self._player_ref.centery - self.rect.centery
            track_speed = self.flight_speed * 0.5
            if abs(dy) > 4:
                self.position.y += (track_speed * dt) if dy > 0 else -(track_speed * dt)

    # ──────────────────────────────────────────────
    # Required overrides
    # ──────────────────────────────────────────────

    def _get_animation_key(self) -> str:
        return "fly"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(6, 4, 20, 20)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()
