from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_LARGE,
    FONT_MEDIUM,
    draw_top_bar,
    draw_bottom_bar,
)
from src.engine.utils.asset_loader import AssetLoader


class DemoMenuScene(BaseScene):
    def __init__(self) -> None:
        self._options: list[tuple[str, str, type[BaseScene]]] = [
            ("Unit VII", "Digital Image Processing", self._scene_for("filter")),
            ("Unit VIII", "Segmentation & Analysis", self._scene_for("vision")),
            ("Unit IX", "Pattern Recognition", self._scene_for("pattern")),
        ]
        self._selected: int = 0
        self._font_large = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_LARGE)
        self._font_medium = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

    @staticmethod
    def _scene_for(name: str) -> type[BaseScene]:
        if name == "filter":
            from src.engine.scenes.filter_demo_scene import FilterDemoScene
            return FilterDemoScene
        elif name == "vision":
            from src.engine.scenes.vision_demo_scene import VisionDemoScene
            return VisionDemoScene
        else:
            from src.engine.scenes.pattern_demo_scene import PatternDemoScene
            return PatternDemoScene

    def on_enter(self) -> None:
        self._selected = 0

    def on_exit(self) -> None:
        pass

    def _get_im(self) -> InputManager | None:
        from src.engine.core.app import App
        if App._instance is not None:
            return App._instance.input_manager
        return None

    def update(self, dt: float) -> None:
        im = self._get_im()
        if im is None:
            return

        if im.is_raw_key_pressed(pygame.K_DOWN):
            self._selected = (self._selected + 1) % len(self._options)
        if im.is_raw_key_pressed(pygame.K_UP):
            self._selected = (self._selected - 1) % len(self._options)

        if im.is_action_pressed(Action.CONFIRM):
            scene_cls = self._options[self._selected][2]
            from src.engine.core.app import App
            if App._instance is not None:
                App._instance.scene_manager.push(scene_cls())

        if im.is_action_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            from src.engine.core.app import App
            if App._instance is not None:
                App._instance.scene_manager.replace(TitleScene())

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "ACADEMIC DEMONSTRATIONS", "MENU")

        cy = 55
        cx = 40
        for i, (unit, desc, _) in enumerate(self._options):
            selected = i == self._selected
            prefix = "\u25b6" if selected else " "
            color = COLOR_HIGHLIGHT if selected else COLOR_TEXT
            text = self._font_large.render(f"  {prefix}  {unit}", True, color)
            surface.blit(text, (cx, cy))
            desc_text = self._font_medium.render(f"        {desc}", True, (150, 150, 150))
            surface.blit(desc_text, (cx, cy + 14))
            cy += 40

        draw_bottom_bar(surface, "  UP/DOWN: Navigate  |  ENTER: Select  |  ESC: Back to Title")
