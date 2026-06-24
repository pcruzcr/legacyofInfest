"""
Module: clock
System: engine
Academic Unit: Framework scaffold
Description: DeltaClock provides frame-rate-independent delta time for
the game loop. Delta values are scaled by a mutable time_scale attribute
(for slow-motion/pause effects). The fps property reports the measured
frame rate averaged over recent frames.
"""

import pygame.time


class DeltaClock:
    """Frame-rate-independent clock for the main game loop.

    Usage:
        clock = DeltaClock()
        while running:
            dt = clock.tick()  # seconds since last frame
            # ... update game state with dt ...
    """

    def __init__(self) -> None:
        """Create a DeltaClock and initialise the underlying Pygame clock."""
        self._clock = pygame.time.Clock()
        self.time_scale: float = 1.0

    def tick(self) -> float:
        """Return delta time in seconds, scaled by ``self.time_scale``.

        The raw delta from Pygame's clock (milliseconds) is converted to
        seconds and multiplied by the current time scale.
        """
        raw_ms = self._clock.tick()  # milliseconds since last call
        dt_seconds = raw_ms / 1000.0
        return dt_seconds * self.time_scale

    @property
    def fps(self) -> float:
        """The measured frame rate of the most recent tick (frames/second)."""
        return self._clock.get_fps()
