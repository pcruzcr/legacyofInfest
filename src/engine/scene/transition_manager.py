from __future__ import annotations
import pygame
from src.engine.scene.transitions import FadeTransition, WipeTransition


class TransitionManager:
    """Manages scene transitions (fade/wipe)."""

    def __init__(self) -> None:
        self._active_transition: FadeTransition | WipeTransition | None = None
        self._callback = None

    def fade_to_black(self, duration: float = 0.3, callback=None) -> None:
        self._active_transition = FadeTransition(duration=duration, fade_in=False)
        self._active_transition.start()
        self._callback = callback

    def fade_from_black(self, duration: float = 0.3, callback=None) -> None:
        self._active_transition = FadeTransition(duration=duration, fade_in=True)
        self._active_transition.start()
        self._callback = callback

    def wipe(self, direction: str = "left_to_right", duration: float = 0.4,
             old_surface: pygame.Surface | None = None, callback=None) -> None:
        t = WipeTransition(duration=duration, direction=direction)
        if old_surface is not None:
            t.start(old_surface)
        self._active_transition = t
        self._callback = callback

    def update(self, dt: float) -> None:
        if self._active_transition is None:
            return
        self._active_transition.update(dt)
        if self._active_transition.is_complete:
            cb = self._callback
            self._active_transition = None
            self._callback = None
            if cb:
                cb()

    def draw(self, surface: pygame.Surface) -> None:
        if self._active_transition is not None:
            self._active_transition.draw(surface)

    @property
    def is_transitioning(self) -> bool:
        return self._active_transition is not None

    def cancel(self) -> None:
        self._active_transition = None
        self._callback = None
