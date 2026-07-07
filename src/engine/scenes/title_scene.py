from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_menu_scene import DemoMenuScene
from src.engine.scenes.story_scene import StoryScene
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class TitleScene(BaseScene):
    """Main title screen with background, logo, music, and custom font."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        assets = settings.ASSETS_DIR / "title"

        self._background = AssetLoader.load_image(
            assets / "bck1.png",
            size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )

        raw_logo = AssetLoader.load_image(assets / "logo.png")
        max_logo_w = settings.INTERNAL_WIDTH - 40
        max_logo_h = 80
        lw, lh = raw_logo.get_size()
        scale = min(max_logo_w / lw, max_logo_h / lh, 1.0)
        self._logo = AssetLoader.load_image(
            assets / "logo.png",
            size=(int(lw * scale), int(lh * scale)),
        )

        self._music = assets / "title.wav"

        self._font_game = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 14)
        self._selected: int = 0
        self._options: list[str] = ["START", "ACADEMIC DEMOS", "QUIT"]

    def on_enter(self) -> None:
        self._selected = 0
        audio = self.audio
        if audio is not None:
            audio.play_music(self._music)

    def on_exit(self) -> None:
        audio = self.audio
        if audio is not None:
            audio.stop_music()

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + 1) % len(self._options)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - 1) % len(self._options)

        if im.is_action_pressed(Action.CONFIRM):
            if self._selected == 0:
                self.context.scene_manager.replace(StoryScene(self.context, 1))
            elif self._selected == 1:
                self.context.scene_manager.replace(DemoMenuScene(self.context))
            elif self._selected == 2:
                self.context.quit()

        if im.is_action_pressed(Action.CANCEL):
            self.context.quit()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        logo_rect = self._logo.get_rect(
            center=(settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 3),
        )
        surface.blit(self._logo, logo_rect)

        for i, opt in enumerate(self._options):
            color = (255, 255, 100) if i == self._selected else (150, 150, 150)
            prefix = "> " if i == self._selected else "  "
            text = self._font_game.render(f"{prefix}{opt}", False, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = logo_rect.bottom + 30 + i * 22
            surface.blit(text, (ox, oy))
