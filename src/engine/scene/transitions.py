"""
Module: transitions
System: engine
Academic Unit: Framework scaffold
Description: Reusable transition effects that can be rendered between
scenes.  ``FadeTransition`` fades to/from a solid colour; ``WipeTransition``
slides a clipping edge across the display.  Both report completion via
the ``is_complete`` property and update using the same ``dt``-based
interface as other engine subsystems.
"""

from __future__ import annotations

import pygame


class FadeTransition:
    """Fade to / from a solid colour over *duration* seconds.

    The transition starts fully opaque (alpha = 255) and reduces alpha
    to 0 over *duration* seconds, revealing the scene below.
    """

    def __init__(
        self, duration: float, color: tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        """Initialise a fade transition.

        Args:
            duration: Total duration in seconds.
            color: The RGB colour to fade through.
        """
        self._duration: float = duration
        self._elapsed: float = 0.0
        self._color: tuple[int, int, int] = color
        self._surface: pygame.Surface = pygame.Surface(
            (320, 224)
        )
        self._surface.fill(color)

    def update(self, dt: float) -> None:
        """Advance the transition timer by *dt* seconds."""
        self._elapsed += dt

    def draw(self, surface: pygame.Surface) -> None:
        """Blit the fade overlay onto *surface*."""
        progress = min(1.0, max(0.0, self._elapsed / self._duration))
        alpha = int((1.0 - progress) * 255)
        if alpha <= 0:
            return
        self._surface.set_alpha(alpha)
        surface.blit(self._surface, (0, 0))

    @property
    def is_complete(self) -> bool:
        """``True`` once the fade duration has elapsed."""
        return self._elapsed >= self._duration


class WipeTransition:
    """Wipe from one side of the screen to the other.

    *Direction* controls which edge the wipe originates from:
    ``"left_to_right"``, ``"right_to_left"``, ``"top_to_bottom"``,
    or ``"bottom_to_top"``.
    """

    def __init__(
        self, duration: float, direction: str = "left_to_right"
    ) -> None:
        """Initialise a wipe transition.

        Args:
            duration: Total duration in seconds.
            direction: Edge of origin for the wipe.
        """
        self._duration: float = duration
        self._elapsed: float = 0.0
        self._direction: str = direction
        self._surface: pygame.Surface = pygame.Surface(
            (320, 224)
        )
        self._surface.fill((0, 0, 0))

    def update(self, dt: float) -> None:
        """Advance the transition timer by *dt* seconds."""
        self._elapsed += dt

    def draw(self, surface: pygame.Surface) -> None:
        """Blit the wipe overlay, revealing *surface* progressively."""
        progress = min(1.0, max(0.0, self._elapsed / self._duration))
        w, h = 320, 224
        self._surface.fill((0, 0, 0))

        clip_rect: pygame.Rect
        if self._direction == "left_to_right":
            clip_width = int(w * progress)
            clip_rect = pygame.Rect(0, 0, clip_width, h)
        elif self._direction == "right_to_left":
            clip_width = int(w * progress)
            clip_rect = pygame.Rect(w - clip_width, 0, clip_width, h)
        elif self._direction == "top_to_bottom":
            clip_height = int(h * progress)
            clip_rect = pygame.Rect(0, 0, w, clip_height)
        elif self._direction == "bottom_to_top":
            clip_height = int(h * progress)
            clip_rect = pygame.Rect(0, h - clip_height, w, clip_height)
        else:
            clip_rect = pygame.Rect(0, 0, 0, 0)

        # Blit the revealed portion of the source onto the overlay
        subsurface = surface.subsurface(clip_rect).copy()
        self._surface.blit(subsurface, clip_rect.topleft)
        surface.blit(self._surface, (0, 0))

    @property
    def is_complete(self) -> bool:
        """``True`` once the wipe duration has elapsed."""
        return self._elapsed >= self._duration
