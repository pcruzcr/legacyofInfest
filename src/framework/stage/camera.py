"""
Module: camera
System: framework.stage
Academic Unit: Unit II (Vectors, Transformations)
Description: Viewport camera that follows a target entity (the player).
Converts world-space coordinates to screen-space coordinates via
offset. Supports map boundary clamping and per-layer parallax factors.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings

if TYPE_CHECKING:
    from src.framework.entities.base_entity import BaseEntity


_CAMERA_LOCK_EPSILON = 0.5


class _CameraLock:
    """Lightweight camera lock zone (no dependency on stage_loader)."""
    def __init__(self, rect: pygame.Rect, lock_x: bool, lock_y: bool) -> None:
        self.rect = rect
        self.lock_x = lock_x
        self.lock_y = lock_y


class Camera:
    """Viewport camera that follows a target entity with smooth LERP."""

    def __init__(self, lerp_speed: float = 8.0) -> None:
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)
        self._target: BaseEntity | None = None
        self._map_width: int = 0
        self._map_height: int = 0
        self.lerp_speed: float = lerp_speed
        self._parallax_factors: dict[str, float] = {
            "BG_Far": 0.15,
            "BG_Mid": 0.40,
            "BG_Near": 0.70,
            "Terrain": 1.0,
            "Terrain_Detail": 1.0,
            "FG_Overlay": 1.0,
        }
        self._locked_x: bool = False
        self._locked_y: bool = False
        self._lock_rect: pygame.Rect | None = None
        self._shake_timer: float = 0.0
        self._shake_amplitude: float = 0.0
        self.look_ahead_x: float = 0.0
        self.look_ahead_y: float = 0.0

    def follow(self, target: BaseEntity) -> None:
        """Set the entity the camera follows."""
        self._target = target

    def set_map_size(self, width_px: int, height_px: int) -> None:
        """Set the total map dimensions in pixels for boundary clamping."""
        self._map_width = width_px
        self._map_height = height_px

    def set_camera_locks(self, locks: list[Any]) -> None:
        """Set camera lock zones from a list of CameraLock-like objects."""
        self._locked_x = False
        self._locked_y = False
        self._lock_rect = None
        if not locks or self._target is None:
            return
        target_rect = self._target.rect
        for lock in locks:
            if lock.rect.colliderect(target_rect):
                self._locked_x = lock.lock_x
                self._locked_y = lock.lock_y
                self._lock_rect = lock.rect
                break

    def apply_shake(self, amplitude: float = 2.0, duration: float = 0.1) -> None:
        """Apply a screen shake offset that decays over `duration` seconds."""
        self._shake_timer = duration
        self._shake_amplitude = amplitude

    def update(self, dt: float) -> None:
        """Smoothly move the camera toward the target, clamped to map bounds."""
        if self._target is None:
            return

        target_x = self._target.rect.centerx - settings.INTERNAL_WIDTH / 2
        target_y = self._target.rect.centery - settings.INTERNAL_HEIGHT / 2
        # Look-ahead: shift target by player velocity
        if hasattr(self._target, "velocity"):
            self.look_ahead_x += (self._target.velocity.x * 0.12 - self.look_ahead_x) * dt * 4.0
            self.look_ahead_y += (self._target.velocity.y * 0.08 - self.look_ahead_y) * dt * 4.0
            target_x += self.look_ahead_x
            target_y += self.look_ahead_y

        if self._map_width > 0:
            target_x = max(0, min(target_x, self._map_width - settings.INTERNAL_WIDTH))
        if self._map_height > 0:
            target_y = max(0, min(target_y, self._map_height - settings.INTERNAL_HEIGHT))

        # Camera lock zones freeze one or both axes
        if self._locked_x:
            target_x = self.offset.x
        if self._locked_y:
            target_y = self.offset.y

        self.offset.x += (target_x - self.offset.x) * self.lerp_speed * dt
        self.offset.y += (target_y - self.offset.y) * self.lerp_speed * dt

        # Screen shake
        if self._shake_timer > 0:
            self._shake_timer -= dt
            sx = random.uniform(-self._shake_amplitude, self._shake_amplitude)
            sy = random.uniform(-self._shake_amplitude, self._shake_amplitude)
            self.offset.x += sx
            self.offset.y += sy

    def set_parallax_factor(self, layer_name: str, factor: float) -> None:
        """Set the parallax factor for a named layer (0.0 = static, 1.0 = full follow)."""
        self._parallax_factors[layer_name] = factor

    def layer_offset(self, layer_name: str) -> pygame.Vector2:
        """Return the camera offset adjusted for a layer's parallax factor."""
        factor = self._parallax_factors.get(layer_name, 1.0)
        return pygame.Vector2(
            self.offset.x * factor,
            self.offset.y * factor,
        )

    def world_to_screen(self, pos: pygame.Vector2) -> pygame.Vector2:
        """Convert world-space coordinates to screen-space."""
        return pos - self.offset

    def screen_to_world(self, pos: pygame.Vector2) -> pygame.Vector2:
        """Convert screen-space coordinates to world-space."""
        return pos + self.offset
