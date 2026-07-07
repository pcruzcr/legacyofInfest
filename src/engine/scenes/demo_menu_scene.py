from __future__ import annotations

from typing import TYPE_CHECKING

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
from src.engine.scenes.scene_registry import get_registry
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class DemoMenuScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        registry = get_registry()
        self._options: list[tuple[str, str, str]] = [
            ("Unit II", "Vectors & Transformations", "vector"),
            ("Unit II/III", "2D Transformations", "transform"),
            ("Unit III", "Bézier Curves & Splines", "curve"),
            ("Unit III/IV", "Interpolation & Easing", "interpolate"),
            ("Unit V", "Color Spaces & Alpha Blending", "color"),
            ("Unit V/VIII", "Noise & Procedural Generation", "noise"),
            ("Unit VI", "AABB Collision Resolution", "collision"),
            ("Unit VII", "Digital Image Processing", "filter"),
            ("Unit VIII", "Segmentation & Analysis", "vision"),
            ("Unit IX", "Pattern Recognition", "pattern"),
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
            registry = get_registry()
            key = self._options[self._selected][2]
            scene = registry.build(key, self.context)
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

        cy = 28
        cx = 20
        for i, (unit, desc, _) in enumerate(self._options):
            selected = i == self._selected
            prefix = "\u25b6" if selected else " "
            color = COLOR_HIGHLIGHT if selected else COLOR_TEXT
            text = self._font_medium.render(f" {prefix} {unit}", True, color)
            surface.blit(text, (cx, cy))
            desc_text = self._font_small.render(f"  {desc}", True, (150, 150, 150))
            surface.blit(desc_text, (cx, cy + 11))
            cy += 24

        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            ex = (settings.INTERNAL_WIDTH - err.get_width()) // 2
            surface.blit(err, (ex, 170))

        draw_bottom_bar(surface, "  UP/DOWN: Navigate  |  ENTER: Select  |  ESC: Back to Title")
