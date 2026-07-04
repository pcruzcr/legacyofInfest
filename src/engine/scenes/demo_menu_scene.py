from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    COLOR_ERROR,
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_SMALL,
    draw_top_bar,
    draw_bottom_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


def _try_scene(name: str) -> Callable[[GameContext], BaseScene | None]:
    """Return a factory that tries to build the demo scene.
    Returns None if import or construction fails."""
    def factory(ctx: GameContext) -> BaseScene | None:
        try:
            if name == "filter":
                from src.engine.scenes.filter_demo_scene import FilterDemoScene
                return FilterDemoScene(ctx)
            elif name == "vision":
                from src.engine.scenes.vision_demo_scene import VisionDemoScene
                return VisionDemoScene(ctx)
            else:
                from src.engine.scenes.pattern_demo_scene import PatternDemoScene
                return PatternDemoScene(ctx)
        except Exception as exc:
            return None
    return factory


class DemoMenuScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._options: list[tuple[str, str, Callable[[GameContext], BaseScene | None]]] = [
            ("Unit VII", "Digital Image Processing", _try_scene("filter")),
            ("Unit VIII", "Segmentation & Analysis", _try_scene("vision")),
            ("Unit IX", "Pattern Recognition", _try_scene("pattern")),
        ]
        self._selected: int = 0
        self._error_msg: str = ""
        self._error_timer: float = 0.0
        self._font_large = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_LARGE)
        self._font_medium = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._font_small = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)

    def on_enter(self) -> None:
        self._selected = 0
        self._error_msg = ""
        self._error_timer = 0.0

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._error_timer > 0:
            self._error_timer -= dt
            if self._error_timer <= 0:
                self._error_msg = ""

        if im.is_raw_key_pressed(pygame.K_DOWN):
            self._selected = (self._selected + 1) % len(self._options)
        if im.is_raw_key_pressed(pygame.K_UP):
            self._selected = (self._selected - 1) % len(self._options)

        if im.is_action_pressed(Action.CONFIRM):
            factory = self._options[self._selected][2]
            scene = factory(self.context)
            if scene is not None:
                self.context.scene_manager.push(scene)
            else:
                self._error_msg = "Failed to load demo scene — missing assets?"
                self._error_timer = 3.0

        if im.is_action_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

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

        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            ex = (settings.INTERNAL_WIDTH - err.get_width()) // 2
            surface.blit(err, (ex, 170))

        draw_bottom_bar(surface, "  UP/DOWN: Navigate  |  ENTER: Select  |  ESC: Back to Title")
