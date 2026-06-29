"""
Module: title_scene
System: engine.scenes
Academic Unit: N/A
Description: Title screen with game title and START/QUIT options.
CONFIRM action advances to the first StoryScene.
"""
from __future__ import annotations
import pygame
from src.engine.scene.base_scene import BaseScene
from src.engine.core import settings
from src.engine.input.action_map import Action


class TitleScene(BaseScene):
    """Main title screen."""

    def __init__(self) -> None:
        self._font_title = pygame.font.Font(None, 30)
        self._font_option = pygame.font.Font(None, 18)
        self._selected: int = 0
        self._options: list[str] = ["START", "QUIT"]

    def on_enter(self) -> None:
        self._selected = 0

    def on_exit(self) -> None:
        pass

    def _get_input(self):
        from src.engine.core.app import App
        if App._instance is not None:
            return App._instance.input_manager
        return None

    def update(self, dt: float) -> None:
        im = self._get_input()
        if im is None:
            return

        if im.is_pressed(Action.CONFIRM):
            if self._selected == 0:
                from src.engine.scenes.story_scene import StoryScene
                from src.engine.core.app import App
                if App._instance is not None:
                    App._instance.scene_manager.replace(StoryScene(1))
            elif self._selected == 1:
                from src.engine.core.app import App
                if App._instance is not None:
                    App._instance._running = False

        if im.is_pressed(Action.CANCEL):
            from src.engine.core.app import App
            if App._instance is not None:
                App._instance._running = False

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 30))

        title = self._font_title.render("LEGACY OF INFEST", True, (200, 200, 255))
        tx = (settings.INTERNAL_WIDTH - title.get_width()) // 2
        ty = settings.INTERNAL_HEIGHT // 3
        surface.blit(title, (tx, ty))

        for i, opt in enumerate(self._options):
            color = (255, 255, 100) if i == self._selected else (150, 150, 150)
            prefix = "> " if i == self._selected else "  "
            text = self._font_option.render(f"{prefix}{opt}", True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = ty + 50 + i * 25
            surface.blit(text, (ox, oy))
