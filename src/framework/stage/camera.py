"""
Module: camera
System: framework.stage
Description: 2D camera with smooth LERP following, parallax support,
screen shake, map clamping, and camera lock zones.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings

if TYPE_CHECKING:
    from src.framework.entities.base_entity import BaseEntity


class _CameraLock:
    """Simple camera lock for constraining axes."""
    def __init__(self, rect: pygame.Rect, lock_x: bool = False, lock_y: bool = False) -> None:
        self.rect = rect
        self.lock_x = lock_x
        self.lock_y = lock_y


class Camera:
    """
    The game camera. Follows a target entity with configurable LERP smoothing,
    per-layer parallax, map boundary clamping, screen shake, and camera lock zones.
    """

    def __init__(self) -> None:
        self.offset: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self._target: BaseEntity | None = None
        self.lerp_speed: float = 8.0
        self._map_w: int = 0
        self._map_h: int = 0
        self._is_locked_x: bool = False
        self._is_locked_y: bool = False
        self._shake_timer: float = 0.0
        self._shake_amplitude: float = 0.0
        self._shake_offset: pygame.Vector2 = pygame.Vector2(0.0, 0.0)

        # Parallax factors (multiplied against camera offset per layer name)
        self._parallax_factors: dict[str, float] = {
            "BG_Far": 0.15,
            "BG_Mid": 0.40,
            "BG_Near": 0.70,
            "Terrain": 1.0,
        }

    def follow(self, target: BaseEntity) -> None:
        """Set the camera to follow this entity."""
        self._target = target

    def set_map_size(self, width: int, height: int) -> None:
        """Set map pixel dimensions for boundary clamping."""
        self._map_w = max(width, 1)
        self._map_h = max(height, 1)

    def set_camera_locks(self, locks: list[_CameraLock] | None) -> None:
        """Set camera lock zones (freeze X or Y axis in certain rooms)."""
        if locks is not None:
            self._is_locked_x = any(line.lock_x for line in locks)
            self._is_locked_y = any(line.lock_y for line in locks)

    def apply_shake(self, amplitude: float = 2.0, duration: float = 0.1) -> None:
        """Trigger a screen shake. Overwrites current shake if new amplitude is larger."""
        if amplitude > self._shake_amplitude:
            self._shake_amplitude = amplitude
        self._shake_timer = max(self._shake_timer, duration)

    def parallax_factor(self, layer_name: str) -> float:
        """Return the parallax multiplier for the given layer name."""
        return self._parallax_factors.get(layer_name, 1.0)

    def set_parallax_factor(self, layer_name: str, factor: float) -> None:
        """Set the parallax multiplier for a given layer name."""
        self._parallax_factors[layer_name] = factor

    def layer_offset(self, layer_name: str) -> pygame.Vector2:
        """Return the camera offset adjusted for parallax on the given layer."""
        factor = self._parallax_factors.get(layer_name, 1.0)
        return self.offset * factor

    def world_to_screen(self, world_pos: pygame.Vector2) -> pygame.Vector2:
        """Convert a world position to screen position."""
        return world_pos - self.offset

    def screen_to_world(self, screen_pos: pygame.Vector2) -> pygame.Vector2:
        """Convert a screen position to world position."""
        return screen_pos + self.offset

    def update(self, dt: float) -> None:
        """
        Smoothly follow the target using LERP, apply screen shake,
        and clamp to map boundaries.
        BUG-043 FIX: Use temporary offset for shake instead of modifying self.offset directly.
        BUG-044 FIX: Frame-rate-independent LERP using 1 - (1 - speed) ** dt.
        """
        if self._target is None:
            return

        target_x = self._target.rect.centerx
        target_y = self._target.rect.centery

        # Look-ahead based on player velocity
        # `getattr` con defecto `None` en vez de `hasattr` + acceso: la versión
        # anterior usaba `0.0` como valor ausente y luego comprobaba el tipo,
        # de modo que el mismo nombre era a veces un vector y a veces un
        # número. El `isinstance` de abajo ya decide si hay velocidad usable.
        velocity = getattr(self._target, "velocity", None)
        look_ahead = velocity.x * 0.3 if isinstance(velocity, pygame.Vector2) else 0.0
        if not self._is_locked_x or not self._is_locked_y:
            # BUG-045 FIX: Clamp look_ahead to prevent pushing target past map boundaries
            if look_ahead > 0:
                look_ahead = min(look_ahead, float(self._map_w) - float(target_x))
            else:
                look_ahead = max(look_ahead, -float(target_x))
            target_x += look_ahead
        target_y = max(0.0, min(float(target_y), float(self._map_h)))

        # BUG-044 FIX: Frame-rate-independent LERP using 1 - (1 - speed)**(dt*60)
        lerp_base = max(0.0, min(1.0, self.lerp_speed / 60.0))
        lerp_factor = 1.0 - (1.0 - lerp_base) ** (dt * 60.0)

        screen_w = settings.INTERNAL_WIDTH
        screen_h = settings.INTERNAL_HEIGHT
        if not self._is_locked_x:
            self.offset.x += (
                target_x - self.offset.x - screen_w // 2
            ) * lerp_factor
        if not self._is_locked_y:
            self.offset.y += (
                target_y - self.offset.y - screen_h // 2
            ) * lerp_factor

        # BUG-043 FIX: Remove previous shake offset before computing new one
        self.offset -= self._shake_offset
        self._shake_offset.update(0.0, 0.0)

        # Screen shake computed as temporary offset
        if self._shake_timer > 0:
            self._shake_timer -= dt
            sx = random.uniform(-1.0, 1.0) * self._shake_amplitude
            sy = random.uniform(-1.0, 1.0) * self._shake_amplitude
            self._shake_offset.update(sx, sy)
        else:
            self._shake_amplitude = 0.0

        # Clamp to map boundaries
        screen_w = settings.INTERNAL_WIDTH
        screen_h = settings.INTERNAL_HEIGHT
        self.offset.x = max(0.0, min(self.offset.x, self._map_w - screen_w))
        self.offset.y = max(0.0, min(self.offset.y, self._map_h - screen_h))

        # Apply shake offset to final view (temporary, does not persist to next frame)
        self.offset += self._shake_offset