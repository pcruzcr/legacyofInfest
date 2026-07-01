from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene


class GameOverScene(BaseScene):
    """Game Over screen shown on player death. Offers Continue and Quit."""

    def __init__(self, stage_scene: BaseScene) -> None:
        self._stage_scene = stage_scene
        self._selected: int = 0
        self._options: list[str] = ["CONTINUE", "QUIT"]
        self._font = pygame.font.Font(None, 16)
        self._elapsed: float = 0.0

    def on_enter(self) -> None:
        self._selected = 0
        self._elapsed = 0.0

    def on_exit(self) -> None:
        pass

    def _get_input(self):
        from src.engine.core.app import App
        return App._input_manager if App._instance is not None else None

    def update(self, dt: float) -> None:
        self._elapsed += dt
        im = self._get_input()
        if im is None:
            return

        if self._elapsed > 0.5:
            if im.is_raw_key_pressed(pygame.K_DOWN):
                self._selected = (self._selected + 1) % len(self._options)
            if im.is_raw_key_pressed(pygame.K_UP):
                self._selected = (self._selected - 1) % len(self._options)

            if im.is_action_pressed(Action.CONFIRM):
                if self._selected == 0:
                    from src.engine.core.app import App
                    if App._instance is not None:
                        App._instance.scene_manager.pop()
                        self._stage_scene._respawn()
                elif self._selected == 1:
                    from src.engine.core.app import App
                    from src.engine.scenes.title_scene import TitleScene
                    if App._instance is not None:
                        App._instance.scene_manager.replace(TitleScene())

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 5, 20))

        # GAME OVER title
        title = self._font.render("GAME OVER", True, (255, 80, 80))
        tx = (settings.INTERNAL_WIDTH - title.get_width()) // 2
        surface.blit(title, (tx, 60))

        # Options
        for i, opt in enumerate(self._options):
            color = (255, 215, 0) if i == self._selected else (150, 150, 150)
            prefix = "> " if i == self._selected else "  "
            text = self._font.render(f"{prefix}{opt}", True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = 100 + i * 22
            surface.blit(text, (ox, oy))
