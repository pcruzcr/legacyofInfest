"""
Module: transitions
System: engine.scene
Academic Unit: N/A
Description: Visual transitions between scenes: FadeTransition, WipeTransition,
SlideTransition, and CircleTransition. All inherit from BaseTransition.
"""
from __future__ import annotations

import abc

import pygame


class BaseTransition(abc.ABC):
    """Abstract base for scene transitions. Subclasses implement start, update, draw."""

    def __init__(self, duration: float = 0.5) -> None:
        self.duration: float = duration
        self.elapsed: float = 0.0
        self.active: bool = False

    @abc.abstractmethod
    def start(self) -> None:
        ...

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            self.elapsed = self.duration

    @abc.abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        ...

    @property
    def is_complete(self) -> bool:
        return not self.active

    @property
    def is_done(self) -> bool:
        return self.is_complete


class FadeTransition(BaseTransition):
    """Fade to/from a color over a given duration."""

    def __init__(self, duration: float = 0.5, fade_in: bool = True,
                 color: tuple[int, int, int] = (0, 0, 0)) -> None:
        super().__init__(duration)
        self.fade_in: bool = fade_in
        self._color: tuple[int, int, int] = color
        self._overlay: pygame.Surface | None = None

    def start(self) -> None:
        self.elapsed = 0.0
        self.active = True

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        progress = self.elapsed / self.duration
        if self.fade_in:
            alpha = int((1.0 - progress) * 255)
        else:
            alpha = int(progress * 255)
        alpha = max(0, min(255, alpha))
        size = surface.get_size()
        if self._overlay is None or self._overlay.get_size() != size:
            self._overlay = pygame.Surface(size, pygame.SRCALPHA)
        self._overlay.fill((*self._color, alpha))
        surface.blit(self._overlay, (0, 0))


class WipeTransition(BaseTransition):
    """Horizontal wipe transition between scenes."""

    def __init__(self, duration: float = 0.5,
                 direction: str = "left_to_right") -> None:
        super().__init__(duration)
        dir_map = {"left_to_right": "left", "right_to_left": "right"}
        self.direction: str = dir_map.get(direction, "left")
        self._old_surface: pygame.Surface | None = None

    def start(self, old_surface: pygame.Surface) -> None:
        self.elapsed = 0.0
        self.active = True
        self._old_surface = old_surface.copy()

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


class SlideTransition(BaseTransition):
    """Slide transition between scenes."""

    def __init__(self, duration: float = 0.5,
                 direction: str = "left") -> None:
        super().__init__(duration)
        self.direction: str = direction
        self._old_surface: pygame.Surface | None = None

    def start(self, old_surface: pygame.Surface) -> None:
        self.elapsed = 0.0
        self.active = True
        self._old_surface = old_surface.copy()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active or self._old_surface is None:
            return
        progress = self.elapsed / self.duration
        w = surface.get_width()
        offset = int(w * progress)
        if self.direction == "left":
            surface.blit(self._old_surface, (-offset, 0))
        elif self.direction == "right":
            surface.blit(self._old_surface, (offset, 0))
        elif self.direction == "up":
            surface.blit(self._old_surface, (0, -offset))
        else:
            surface.blit(self._old_surface, (0, offset))


class CircleTransition(BaseTransition):
    """Circle wipe transition between scenes."""

    def __init__(self, duration: float = 0.5,
                 expanding: bool = True) -> None:
        super().__init__(duration)
        self.expanding: bool = expanding
        self._old_surface: pygame.Surface | None = None
        self._mask: pygame.Surface | None = None

    def start(self, old_surface: pygame.Surface) -> None:
        self.elapsed = 0.0
        self.active = True
        self._old_surface = old_surface.copy()

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active or self._old_surface is None:
            return
        progress = self.elapsed / self.duration
        w = surface.get_width()
        h = surface.get_height()
        cx = w // 2
        cy = h // 2
        max_r = int((w**2 + h**2) ** 0.5)
        if self.expanding:
            radius = int(max_r * progress)
        else:
            radius = max_r - int(max_r * progress)
        if self._mask is None or self._mask.get_size() != (w, h):
            self._mask = pygame.Surface((w, h), pygame.SRCALPHA)
        self._mask.fill((0, 0, 0, 0))
        pygame.draw.circle(self._mask, (0, 0, 0, 255), (cx, cy), radius)
        surface.blit(self._old_surface, (0, 0))
        surface.blit(self._mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
