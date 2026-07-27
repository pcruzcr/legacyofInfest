"""
Module: clock
System: engine.core
Academic Unit: N/A
Description: Wrapper around pygame.time.Clock providing delta time
scaled by a time_scale factor.

Two deltas are exposed every frame:

``dt``        — scaled by ``time_scale``. Drives gameplay simulation, so
                slow-motion and hit-stop affect it.
``unscaled_dt`` — the real elapsed wall-clock time, unaffected by
                ``time_scale``. Drives anything that must keep running while
                the simulation is slowed or frozen: the hit-stop timer itself,
                UI animation, transitions and pause menus.

BUGFIX (AUD-001): systems that *end* a freeze must never be driven by the
scaled delta. Previously ``time_scale`` was set to 0.0 during hit-stop, which
made ``dt`` 0.0, which meant the hit-stop countdown decremented by 0.0 and
therefore never expired — the game locked up permanently on the first landed
hit. ``unscaled_dt`` exists so that class of self-deadlock is impossible.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings

# Longest simulation step we will ever report. Protects the fixed-ish
# integrators in the player/enemy state machines from tunnelling through
# geometry after a stall (breakpoint, window drag, GC pause, disk hitch).
MAX_FRAME_TIME: float = 0.05  # 20 FPS floor


class DeltaClock:
    """Provides delta time in seconds, scaled by time_scale."""

    def __init__(self) -> None:
        self._clock = pygame.time.Clock()
        self.time_scale: float = 1.0
        self._dt: float = 0.0
        self._unscaled_dt: float = 0.0

    def tick(self) -> float:
        """Advance the clock one frame and return the *scaled* delta time."""
        raw_dt = min(self._clock.tick(settings.TARGET_FPS) / 1000.0, MAX_FRAME_TIME)
        self._unscaled_dt = raw_dt
        self._dt = raw_dt * self.time_scale
        return self._dt

    @property
    def dt(self) -> float:
        """Scaled delta of the current frame (same value ``tick`` returned)."""
        return self._dt

    @property
    def unscaled_dt(self) -> float:
        """Real elapsed time of the current frame, ignoring ``time_scale``.

        Use this for timers whose job is to *restore* normal time flow.
        """
        return self._unscaled_dt

    @property
    def fps(self) -> float:
        """Returns the current frame rate."""
        return self._clock.get_fps()
