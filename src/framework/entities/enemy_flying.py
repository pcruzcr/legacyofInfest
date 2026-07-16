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

import logging
import math

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
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
        **kwargs,
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
        self.rect.height = 14

        # Cached surfaces
        self._dive_warn_surf: pygame.Surface | None = None
        self._dive_warn_size: tuple[int, int] = (0, 0)

        # Y-tracking offset for alert mode (persistent across strategy resets)
        self._y_track_offset: float = 0.0

        # Dive bomb state
        self._dive_timer: float = 0.0
        self._dive_cooldown: float = 0.0
        self._is_diving: bool = False
        self._dive_speed: float = flight_speed * 3.0
        self._dive_angle: float = 0.0

        # Homing projectile state
        self._spread_cooldown: float = 0.0
        self._can_shoot: bool = False

        # Load sprites
        self._load_zone_sprites(zone, 14, 10)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("fly", f"enemy_fly_{zone_key}.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, fw, fh)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logging.warning("enemy_flying: failed to load sprite %s", path)

    # ──────────────────────────────────────────────
    # Behavior implementations (Strategy delegation)
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Delegate patrol movement to the current flight strategy."""
        self._y_track_offset = 0.0
        self._strategy.execute(self, dt)

    def _alert_behavior(self, dt: float) -> None:
        """Delegate alert movement, then track player Y axis.
        Uses dive bomb and spread attack patterns."""
        self._y_track_offset = 0.0
        self._dive_cooldown = max(0.0, self._dive_cooldown - dt)
        self._spread_cooldown = max(0.0, self._spread_cooldown - dt)

        # Dive bomb — swoop down at player
        if self._is_diving:
            self._dive_timer -= dt
            if self._dive_timer <= 0:
                self._is_diving = False
                self._dive_cooldown = 3.0
            else:
                self.position.x += math.cos(self._dive_angle) * self._dive_speed * dt
                self.position.y += math.sin(self._dive_angle) * self._dive_speed * dt
                return

        # Start dive when above player at medium range
        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.rect.centerx
            dy = self._player_ref.centery - self.rect.centery
            dist = math.sqrt(dx * dx + dy * dy)
            if (dy < -20 and 60 <= dist <= 150 and self._dive_cooldown <= 0
                    and not self._is_diving):
                self._is_diving = True
                self._dive_timer = 0.5
                self._dive_angle = math.atan2(dy, dx)
                return

        self._strategy.execute(self, dt, speed_mult=1.5)
        self._face_player()
        if self._player_ref is not None:
            track_dy = self._player_ref.centery - (self.position.y + self._y_track_offset + self.rect.height / 2)
            if abs(track_dy) > 4:
                track_speed = self.flight_speed * 0.4
                sign = 1.0 if track_dy >= 0 else -1.0
                self._y_track_offset += sign * track_speed * dt
            self._y_track_offset *= 0.98 ** (dt * 60.0)
        else:
            self._y_track_offset *= 0.9 ** (dt * 60.0)
        self.position.y += self._y_track_offset

    # ──────────────────────────────────────────────
    # Required overrides
    # ──────────────────────────────────────────────

    def _get_animation_key(self) -> str:
        return "fly"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(6, 4, 20, 14)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if self._is_diving:
            progress = 1.0 - (self._dive_timer / 0.5)
            sx = int(self.position.x - camera_offset.x - 12)
            sy = int(self.position.y - camera_offset.y + 20 + progress * 40)
            radius = 12 + int(progress * 8)
            alpha = int(200 - progress * 150)
            size = (radius * 2, radius * 2)
            if (self._dive_warn_surf is None
                    or self._dive_warn_size != size):
                self._dive_warn_surf = pygame.Surface(size, pygame.SRCALPHA)
                self._dive_warn_size = size
            warn = self._dive_warn_surf
            warn.fill((0, 0, 0, 0))
            pygame.draw.circle(warn, (255, 255, 0, alpha), (radius, radius), radius, 2)
            if progress > 0.5:
                pygame.draw.circle(warn, (255, 200, 0, alpha // 2), (radius, radius), radius - 2)
            surface.blit(warn, (sx, sy))
