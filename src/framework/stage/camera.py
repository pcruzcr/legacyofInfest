"""
Module: camera
System: framework.stage
Academic Unit: Unit II (Vectors, Transformations)
Description: Viewport camera that follows a target entity (the player).
Converts world-space coordinates to screen-space coordinates via
offset. Supports map boundary clamping and per-layer parallax factors.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings

if TYPE_CHECKING:
    from src.framework.entities.base_entity import BaseEntity


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

        self.offset.x += (target_x - self.offset.x) * self.lerp_speed * dt
        self.offset.y += (target_y - self.offset.y) * self.lerp_speed * dt

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
