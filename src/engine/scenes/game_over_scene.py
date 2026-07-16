from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.title_scene import TitleScene
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class GameOverScene(BaseScene):
    """Game Over screen shown on player death. Offers Continue and Quit."""

    def __init__(self, context: GameContext, stage_scene: BaseScene) -> None:
        super().__init__(context)
        self._stage_scene = stage_scene
        self._stage_scene_respawn = stage_scene.respawn if hasattr(stage_scene, "respawn") else None
        self._selected: int = 0
        self._options: list[str] = ["CONTINUE", "QUIT"]
        self._title_font = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 28)
        self._option_font = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 18)
        self._elapsed: float = 0.0

    def on_enter(self) -> None:
        self._selected = 0
        self._elapsed = 0.0

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self._elapsed += dt
        im = self.input
        if im is None:
            return

        if self._elapsed > 0.5:
            if im.is_action_just_pressed(Action.MOVE_DOWN):
                self._selected = min(self._selected + 1, len(self._options) - 1)
            if im.is_action_just_pressed(Action.MOVE_UP):
                self._selected = max(self._selected - 1, 0)

            if im.is_action_just_pressed(Action.CONFIRM):
                if self._selected == 0:
                    self.context.scene_manager.pop()
                    try:
                        if self._stage_scene_respawn:
                            self._stage_scene_respawn()
                    except (RuntimeError, AttributeError, TypeError) as e:
                        logging.warning("game_over: respawn failed: %s", e)
                        import traceback
                        traceback.print_exc()
                        self.context.scene_manager.replace(TitleScene(self.context))
                elif self._selected == 1:
                    self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 5, 20))

        # GAME OVER title
        title = self._title_font.render("GAME OVER", True, (255, 80, 80))
        tx = (settings.INTERNAL_WIDTH - title.get_width()) // 2
        surface.blit(title, (tx, 60))

        # Options
        for i, opt in enumerate(self._options):
            color = (255, 215, 0) if i == self._selected else (150, 150, 150)
            prefix = "> " if i == self._selected else "  "
            text = self._option_font.render(f"{prefix}{opt}", True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = 100 + i * 22
            surface.blit(text, (ox, oy))
