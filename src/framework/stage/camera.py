"""
Module: camera
System: framework/stage
Academic Unit: Stage system
Description: Camera that follows a target entity with smooth lerp
interpolation. Provides world-to-screen coordinate conversion and
parallax offset computation for background layers.
Implements the contract from 22_API_CONTRACTS.md §11.1 and
06_TMX_SPEC.md §3.2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core.settings import INTERNAL_WIDTH, INTERNAL_HEIGHT
from src.engine.utils.math_utils import lerp, clamp

if TYPE_CHECKING:
    from src.framework.entities.base_entity import BaseEntity


# Parallax factors per 06_TMX_SPEC.md §3.2
PARALLAX_FACTORS: dict[str, tuple[float, float]] = {
    "BG_Far": (0.15, 0.05),
    "BG_Mid": (0.40, 0.15),
    "BG_Near": (0.70, 0.30),
    "Terrain": (1.00, 1.00),
}

# Default background layer name for entities without a specific layer
_DEFAULT_BG_LAYER = "Terrain"

# Smoothing factor for camera lerp (lower = smoother, higher = snappier)
_CAMERA_LERP_SPEED: float = 6.0


class Camera:
    """Smooth-follow camera with parallax support.

    Usage::

        camera = Camera()
        camera.follow(player)
        # Each frame:
        camera.update(dt)
        layer_offset = camera.get_parallax_offset("BG_Far")
        screen_pos = camera.world_to_screen(entity.position)
    """

    def __init__(self) -> None:
        """Create a camera centred on the origin."""
        self._offset: pygame.Vector2 = pygame.Vector2(0, 0)
        self._target: BaseEntity | None = None
        self._target_world_center: pygame.Vector2 = pygame.Vector2(0, 0)

    # ── Public API ────────────────────────────────────────────────

    def follow(self, target: BaseEntity) -> None:
        """Set the entity the camera should track.

        Args:
            target: The entity to follow.  Must have a ``position``
                    attribute.
        """
        self._target = target

    def update(self, dt: float) -> None:
        """Lerp the camera offset toward the target's screen centre.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        if self._target is None:
            return

        # Target world-space position (centre of the entity)
        target_pos: pygame.Vector2 = self._target.position

        # Desired camera offset = target world position - half screen
        # so the target appears centred on screen
        desired_offset_x: float = target_pos.x - (INTERNAL_WIDTH / 2.0)
        desired_offset_y: float = target_pos.y - (INTERNAL_HEIGHT / 2.0)

        # Smooth lerp toward the desired offset
        t: float = 1.0 - pow(2.0, -_CAMERA_LERP_SPEED * dt)
        self._offset.x = lerp(self._offset.x, desired_offset_x, t)
        self._offset.y = lerp(self._offset.y, desired_offset_y, t)

        # Clamp offset so we never show areas outside the map
        # (no clamping bounds without knowing map size — stage code or
        #  CameraLock zones may override this later)
        self._offset.x = clamp(self._offset.x, 0.0, float("inf"))
        self._offset.y = clamp(self._offset.y, 0.0, float("inf"))

    def world_to_screen(self, pos: pygame.Vector2) -> pygame.Vector2:
        """Convert a world-space position to screen-space.

        Args:
            pos: World-space position.

        Returns:
            Screen-space position (pixels from top-left of the
            internal surface).
        """
        return pygame.Vector2(
            pos.x - self._offset.x,
            pos.y - self._offset.y,
        )

    def screen_to_world(self, pos: pygame.Vector2) -> pygame.Vector2:
        """Convert a screen-space position to world-space.

        This is the inverse of :meth:`world_to_screen`.

        Args:
            pos: Screen-space position.

        Returns:
            World-space position.
        """
        return pygame.Vector2(
            pos.x + self._offset.x,
            pos.y + self._offset.y,
        )

    def get_parallax_offset(
        self, layer_name: str = _DEFAULT_BG_LAYER
    ) -> pygame.Vector2:
        """Return a per-layer offset for parallax scrolling.

        Background layers scroll at different speeds based on their
        parallax factor (see ``06_TMX_SPEC.md`` §3.2).

        Args:
            layer_name: One of ``"BG_Far"``, ``"BG_Mid"``,
                        ``"BG_Near"``, or ``"Terrain"``.
                        Defaults to ``"Terrain"``.

        Returns:
            The offset to apply when rendering this layer.
        """
        factor_x, factor_y = PARALLAX_FACTORS.get(
            layer_name, PARALLAX_FACTORS[_DEFAULT_BG_LAYER]
        )
        return pygame.Vector2(
            self._offset.x * factor_x,
            self._offset.y * factor_y,
        )

    # ── Properties ────────────────────────────────────────────────

    @property
    def offset(self) -> pygame.Vector2:
        """Current world-space camera offset (read-only)."""
        return pygame.Vector2(self._offset.x, self._offset.y)

    @property
    def target(self) -> BaseEntity | None:
        """The entity currently being followed, or ``None``."""
        return self._target
