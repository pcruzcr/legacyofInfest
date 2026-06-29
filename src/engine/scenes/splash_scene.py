"""
Module: splash_scene
System: engine.scenes
Academic Unit: N/A
Description: Splash screen shown at startup. Displays 'LEGACY OF INFEST'
and auto-advances to TitleScene after ~3 seconds.
"""
from __future__ import annotations
import pygame
from src.engine.scene.base_scene import BaseScene
from src.engine.core import settings
from src.engine.core.app import _get_scene_manager


class SplashScene(BaseScene):
    """Opening splash screen with title text."""

    def __init__(self) -> None:
        self._timer: float = 0.0
        self._duration: float = 3.0
        self._font_large = pygame.font.Font(None, 24)
        self._font_small = pygame.font.Font(None, 12)

    def on_enter(self) -> None:
        self._timer = 0.0

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self._timer += dt
        if self._timer >= self._duration:
            from src.engine.scenes.title_scene import TitleScene
            sm = _get_scene_manager()
            if sm is not None:
                sm.replace(TitleScene())

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 60))

        title = self._font_large.render("LEGACY OF INFEST", True, (200, 200, 255))
        tx = (settings.INTERNAL_WIDTH - title.get_width()) // 2
        ty = settings.INTERNAL_HEIGHT // 2 - 20
        surface.blit(title, (tx, ty))

        sub = self._font_small.render("Cargando...", True, (150, 150, 200))
        sx = (settings.INTERNAL_WIDTH - sub.get_width()) // 2
        sy = ty + 30
        surface.blit(sub, (sx, sy))

        progress = min(self._timer / self._duration, 1.0)
        bar_width = 100
        bar_height = 4
        bar_x = (settings.INTERNAL_WIDTH - bar_width) // 2
        bar_y = sy + 20
        pygame.draw.rect(surface, (100, 100, 150), (bar_x, bar_y, bar_width, bar_height))
        fill_w = int(bar_width * progress)
        pygame.draw.rect(surface, (150, 150, 255), (bar_x, bar_y, fill_w, bar_height))
