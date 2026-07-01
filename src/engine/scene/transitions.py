"""
Module: transitions
System: engine.scene
Academic Unit: N/A
Description: Visual transitions between scenes: FadeTransition and WipeTransition.
"""
from __future__ import annotations
import pygame


class FadeTransition:
    """Fade to/from a color over a given duration."""

    def __init__(self, duration: float = 0.5, fade_in: bool = True,
                 color: tuple[int, int, int] = (0, 0, 0)) -> None:
        self.duration: float = duration
        self.fade_in: bool = fade_in
        self._color: tuple[int, int, int] = color
        self.elapsed: float = 0.0
        self.active: bool = False

    def start(self) -> None:
        self.elapsed = 0.0
        self.active = True

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            self.elapsed = self.duration

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        progress = self.elapsed / self.duration
        if self.fade_in:
            alpha = int((1.0 - progress) * 255)
        else:
            alpha = int(progress * 255)
        alpha = max(0, min(255, alpha))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self._color, alpha))
        surface.blit(overlay, (0, 0))

    @property
    def is_complete(self) -> bool:
        return not self.active

    @property
    def is_done(self) -> bool:
        return self.is_complete


class WipeTransition:
    """Horizontal wipe transition between scenes."""

    def __init__(self, duration: float = 0.5,
                 direction: str = "left_to_right") -> None:
        self.duration: float = duration
        dir_map = {"left_to_right": "left", "right_to_left": "right"}
        self.direction: str = dir_map.get(direction, "left")
        self.elapsed: float = 0.0
        self.active: bool = False
        self._old_surface: pygame.Surface | None = None

    def start(self, old_surface: pygame.Surface) -> None:
        self.elapsed = 0.0
        self.active = True
        self._old_surface = old_surface.copy()

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            self.elapsed = self.duration

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active or self._old_surface is None:
            return
        progress = self.elapsed / self.duration
        width = int(surface.get_width() * (1.0 - progress))
        if self.direction == "left":
            surface.blit(self._old_surface, (0, 0), (0, 0, width, surface.get_height()))
        else:
            offset = surface.get_width() - width
            surface.blit(self._old_surface, (offset, 0),
                         (offset, 0, width, surface.get_height()))

    @property
    def is_complete(self) -> bool:
        return not self.active

    @property
    def is_done(self) -> bool:
        return self.is_complete
