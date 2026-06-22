"""
Module: splash_scene
System: engine
Academic Unit: Framework scaffold
Description: Minimal placeholder splash scene that fills the screen
with a solid colour.  Replaced by a richer splash screen in later
phases.
"""

from __future__ import annotations

import pygame

from src.engine.scene.base_scene import BaseScene


class SplashScene(BaseScene):
    """Placeholder splash screen — solid colour fill, no assets."""

    def __init__(
        self, fill_color: tuple[int, int, int] = (32, 32, 64)
    ) -> None:
        """Initialise the splash scene.

        Args:
            fill_color: The RGB colour to clear the screen with.
        """
        self._fill_color: tuple[int, int, int] = fill_color

    def on_enter(self) -> None:
        """Called when this scene becomes active (no-op)."""

    def on_exit(self) -> None:
        """Called when this scene is removed (no-op)."""

    def update(self, dt: float) -> None:
        """No logic for the placeholder splash scene."""

    def draw(self, surface: pygame.Surface) -> None:
        """Fill the screen with a solid colour."""
        surface.fill(self._fill_color)
