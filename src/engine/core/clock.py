"""
Module: clock
System: engine.core
Academic Unit: N/A
Description: Wrapper around pygame.time.Clock providing delta time
scaled by a time_scale factor.
"""
from __future__ import annotations
import pygame


class DeltaClock:
    """Provides delta time in seconds, scaled by time_scale."""

    def __init__(self) -> None:
        self._clock = pygame.time.Clock()
        self.time_scale: float = 1.0
        self._dt: float = 0.0

    def tick(self) -> float:
        """Returns delta time in seconds, scaled by self.time_scale."""
        raw_dt = self._clock.tick(60) / 1000.0
        self._dt = raw_dt * self.time_scale
        return self._dt

    @property
    def fps(self) -> float:
        """Returns the current frame rate."""
        return self._clock.get_fps()
