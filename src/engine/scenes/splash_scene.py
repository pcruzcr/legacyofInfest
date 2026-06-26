"""
Module: splash_scene
System: engine
Academic Unit: Framework scaffold
Description: Minimal splash scene that fills the screen with a
visible color. Auto-advances after 2 seconds to demonstrate
scene system.
"""

from __future__ import annotations

import pygame

from src.engine.scene.base_scene import BaseScene
from src.engine.core.settings import INTERNAL_WIDTH, INTERNAL_HEIGHT
from src.engine.core.event_bus import EventBus


class SplashScene(BaseScene):
    """Splash screen — solid color fill, auto-advances after 2 seconds."""

    def __init__(self, duration: float = 2.0) -> None:
        """Initialise the splash scene.

        Args:
            duration: Time in seconds before auto-advance.
        """
        self._fill_color: tuple[int, int, int] = (15, 15, 40)  # dark navy
        self._duration: float = duration
        self._elapsed: float = 0.0

    def on_enter(self) -> None:
        """Called when this scene becomes active."""
        self._elapsed = 0.0

    def on_exit(self) -> None:
        """Called when this scene is removed."""

    def update(self, dt: float) -> None:
        """Advance timer and auto-advance after duration."""
        self._elapsed += dt
        if self._elapsed >= self._duration:
            # In a real implementation, this would push TitleScene
            # For Phase 3, we just demonstrate the scene system works
            pass

    def draw(self, surface: pygame.Surface) -> None:
        """Fill the screen with a visible color (not black)."""
        surface.fill(self._fill_color)