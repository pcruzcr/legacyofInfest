"""
Module: transition_manager
System: engine.scenes
Description: Handles fade transitions between scenes.
SceneManager calls this before/after scene swaps so the user sees
a short fade instead of an abrupt cut.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings

FADE_DURATION = 0.35


class TransitionManager:
    """Fade overlay controller."""

    def __init__(self) -> None:
        self._fade_alpha: int = 0
        self._fade_duration: float = FADE_DURATION
        self._fade_timer: float = 0.0
        self._direction: int = 0  # -1 fade out, 1 fade in, 0 none
        self._active: bool = False
        self._has_been_active: bool = False

    def start_fade_out(self, duration: float = FADE_DURATION) -> None:
        self._fade_duration = duration
        self._fade_timer = duration
        self._direction = -1
        self._active = True
        self._has_been_active = True

    def start_fade_in(self, duration: float = FADE_DURATION) -> None:
        self._fade_duration = duration
        self._fade_timer = duration
        self._direction = 1
        self._active = True
        self._has_been_active = True

    def update(self, dt: float) -> None:
        if not self._active:
            return
        self._fade_timer -= dt
        if self._fade_timer <= 0:
            self._fade_timer = 0.0
            if self._direction == -1:
                self._fade_alpha = 255
            elif self._direction == 1:
                self._fade_alpha = 0
            self._active = False
            return
        ratio = self._fade_timer / self._fade_duration
        if self._direction == -1:
            self._fade_alpha = int(255 * (1.0 - ratio))
        elif self._direction == 1:
            self._fade_alpha = int(255 * ratio)

    def draw(self, surface: pygame.Surface) -> None:
        if self._fade_alpha > 0:
            overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self._fade_alpha)
            surface.blit(overlay, (0, 0))

    @property
    def active(self) -> bool:
        return self._active

    @property
    def finished(self) -> bool:
        return self._has_been_active and not self._active