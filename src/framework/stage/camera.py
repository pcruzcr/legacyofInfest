"""
Module: camera
System: framework.stage
Academic Unit: Unit II (Vectors, Transformations)
Description: Viewport camera that follows a target entity (the player).
Converts world-space coordinates to screen-space coordinates via
offset. Supports map boundary clamping.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings


class Camera:
    """Viewport camera that follows a target entity with smooth LERP."""

    def __init__(self) -> None:
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)
        self._target: pygame.Vector2 | None = None
        self._map_width: int = 0
        self._map_height: int = 0

    def follow(self, target) -> None:
        """Set the entity the camera follows."""
        self._target = target

    def set_map_size(self, width_px: int, height_px: int) -> None:
        """Set the total map dimensions in pixels for boundary clamping."""
        self._map_width = width_px
        self._map_height = height_px

    def update(self, dt: float) -> None:
        """Smoothly move the camera toward the target, clamped to map bounds."""
        if self._target is None:
            return

        target_x = self._target.rect.centerx - settings.INTERNAL_WIDTH / 2
        target_y = self._target.rect.centery - settings.INTERNAL_HEIGHT / 2

        if self._map_width > 0:
            target_x = max(0, min(target_x, self._map_width - settings.INTERNAL_WIDTH))
        if self._map_height > 0:
            target_y = max(0, min(target_y, self._map_height - settings.INTERNAL_HEIGHT))

        self.offset.x += (target_x - self.offset.x) * 8.0 * dt
        self.offset.y += (target_y - self.offset.y) * 8.0 * dt

    def world_to_screen(self, pos: pygame.Vector2) -> pygame.Vector2:
        """Convert world-space coordinates to screen-space."""
        return pos - self.offset

    def screen_to_world(self, pos: pygame.Vector2) -> pygame.Vector2:
        """Convert screen-space coordinates to world-space."""
        return pos + self.offset
