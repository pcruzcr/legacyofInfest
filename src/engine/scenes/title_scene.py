from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene
from src.engine.input.action_map import Action
from src.engine.utils.asset_loader import AssetLoader


class TitleScene(BaseScene):
    """Main title screen with background, logo, music, and custom font."""

    def __init__(self) -> None:
        assets = Path("assets") / "title"

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

        self._music = assets / "title.mp3"

        self._font_game = AssetLoader.load_font(Path("fonts") / "game.ttf", 14)
        self._selected: int = 0
        self._options: list[str] = ["START", "QUIT"]

    def on_enter(self) -> None:
        self._selected = 0
        AssetLoader.play_music(self._music, volume=0.50)

    def on_exit(self) -> None:
        AssetLoader.fadeout(300)

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
        surface.blit(self._background, (0, 0))

        logo_rect = self._logo.get_rect(
            center=(settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 3),
        )
        surface.blit(self._logo, logo_rect)

        for i, opt in enumerate(self._options):
            color = (255, 255, 100) if i == self._selected else (150, 150, 150)
            prefix = "> " if i == self._selected else "  "
            text = self._font_game.render(f"{prefix}{opt}", True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = logo_rect.bottom + 30 + i * 22
            surface.blit(text, (ox, oy))
