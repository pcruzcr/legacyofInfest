"""
Module: screen_banner
System: engine.ui
Academic Unit: N/A
Description: Stage title banner that slides in, holds, then slides out.
Uses ease_out_quad for entrance and ease_in_quad for exit.
"""
from __future__ import annotations
import pygame
from src.engine.core import settings
from src.engine.utils.math_utils import ease_out_quad, ease_in_quad


class ScreenBanner:
    """Animated stage title banner."""

    def __init__(self) -> None:
        self._stage_id: str = ""
        self._stage_name: str = ""
        self._state: str = "idle"  # idle | slide_in | hold | slide_out
        self._timer: float = 0.0
        self._slide_in_duration: float = 0.5
        self._hold_duration: float = 1.5
        self._slide_out_duration: float = 0.5
        self._font = pygame.font.Font(None, 18)
        self._banner_height: int = 30
        self._offset: float = float(settings.INTERNAL_WIDTH)

    def play(self, stage_id: str, stage_name: str) -> None:
        """Start the banner animation for a stage."""
        self._stage_id = stage_id
        self._stage_name = stage_name
        self._state = "slide_in"
        self._timer = 0.0
        self._offset = float(settings.INTERNAL_WIDTH)

    def update(self, dt: float) -> None:
        if self._state == "idle":
            return

        self._timer += dt

        if self._state == "slide_in":
            progress = min(self._timer / self._slide_in_duration, 1.0)
            t = ease_out_quad(progress)
            self._offset = settings.INTERNAL_WIDTH * (1.0 - t)
            if progress >= 1.0:
                self._state = "hold"
                self._timer = 0.0

        elif self._state == "hold":
            if self._timer >= self._hold_duration:
                self._state = "slide_out"
                self._timer = 0.0

        elif self._state == "slide_out":
            progress = min(self._timer / self._slide_out_duration, 1.0)
            t = ease_in_quad(progress)
            self._offset = settings.INTERNAL_WIDTH * t
            if progress >= 1.0:
                self._state = "idle"

    def draw(self, surface: pygame.Surface) -> None:
        if self._state == "idle":
            return

        banner_rect = pygame.Rect(int(self._offset - settings.INTERNAL_WIDTH),
                                  20, settings.INTERNAL_WIDTH, self._banner_height)

        # Draw banner background
        pygame.draw.rect(surface, (30, 30, 80), banner_rect)
        pygame.draw.rect(surface, (100, 100, 180), banner_rect, 1)

        # Draw stage name
        text = self._font.render(self._stage_name, True, (255, 255, 200))
        tx = banner_rect.x + (banner_rect.width - text.get_width()) // 2
        ty = banner_rect.y + (banner_rect.height - text.get_height()) // 2
        surface.blit(text, (tx, ty))

    @property
    def is_active(self) -> bool:
        return self._state != "idle"
