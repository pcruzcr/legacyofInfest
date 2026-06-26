"""
Module: transitions
System: engine
Academic Unit: N/A
Description: Scene transition effects — fade and wipe transitions.
Used for smooth scene changes (e.g., level transitions, game over).
"""

from __future__ import annotations

import pygame

from src.engine.utils.math_utils import ease_out_quad, ease_in_quad


class FadeTransition:
    """Fade transition — fades to/from a solid color."""

    def __init__(
        self, duration: float, color: tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        """Create a fade transition.

        Args:
            duration: Total duration in seconds for the full fade (in + out).
            color: RGB color to fade to/from.
        """
        self._duration: float = duration
        self._color: tuple[int, int, int] = color
        self._elapsed: float = 0.0
        self._fading_in: bool = True  # True = fading to color, False = fading from color

    def update(self, dt: float) -> None:
        """Advance the transition by dt seconds."""
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._elapsed = self._duration

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the fade overlay onto surface."""
        if self._fading_in:
            # Fading in: alpha goes from 0 to 255
            progress = self._elapsed / (self._duration / 2)
            progress = min(progress, 1.0)
            alpha = int(ease_out_quad(progress) * 255)
        else:
            # Fading out: alpha goes from 255 to 0
            progress = (self._elapsed - self._duration / 2) / (self._duration / 2)
            progress = min(progress, 1.0)
            alpha = int((1.0 - ease_in_quad(progress)) * 255)

        overlay = pygame.Surface(surface.get_size())
        overlay.fill(self._color)
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))

    @property
    def is_complete(self) -> bool:
        """True when the full transition (in + out) is done."""
        return self._elapsed >= self._duration


class WipeTransition:
    """Wipe transition — slides a color across the screen."""

    def __init__(
        self, duration: float, direction: str = "left_to_right"
    ) -> None:
        """Create a wipe transition.

        Args:
            duration: Total duration in seconds.
            direction: One of "left_to_right", "right_to_left", "top_to_bottom", "bottom_to_top".
        """
        self._duration: float = duration
        self._direction: str = direction
        self._elapsed: float = 0.0

    def update(self, dt: float) -> None:
        """Advance the transition by dt seconds."""
        self._elapsed += dt
        if self._elapsed > self._duration:
            self._elapsed = self._duration

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the wipe overlay onto surface."""
        progress = self._elapsed / self._duration
        progress = min(progress, 1.0)
        eased = ease_out_quad(progress)

        w, h = surface.get_size()

        if self._direction == "left_to_right":
            rect_w = int(w * eased)
            rect = pygame.Rect(0, 0, rect_w, h)
        elif self._direction == "right_to_left":
            rect_w = int(w * eased)
            rect = pygame.Rect(w - rect_w, 0, rect_w, h)
        elif self._direction == "top_to_bottom":
            rect_h = int(h * eased)
            rect = pygame.Rect(0, 0, w, rect_h)
        elif self._direction == "bottom_to_top":
            rect_h = int(h * eased)
            rect = pygame.Rect(0, h - rect_h, w, rect_h)
        else:
            return

        overlay = pygame.Surface((rect_w, rect_h) if self._direction in ("left_to_right", "right_to_left") else (w, rect_h))
        overlay.fill((0, 0, 0))
        surface.blit(overlay, rect.topleft)

    @property
    def is_complete(self) -> bool:
        """True when the wipe is done."""
        return self._elapsed >= self._duration