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


ITEM_H = 24
VISIBLE_Y_START = 30
VISIBLE_Y_END = 194
VISIBLE_ITEMS = (VISIBLE_Y_END - VISIBLE_Y_START) // ITEM_H


class DemoMenuScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
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
            ("Combo System", "State Machine & Damage Scaling", "combo"),
        ]
        self._selected: int = 0
        self._scroll_offset: int = 0
        self._error_msg: str = ""
        self._error_timer: float = 0.0
        self._font_large = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_LARGE
        )
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM
        )
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL
        )

    def on_enter(self) -> None:
        self._selected = 0
        self._scroll_offset = 0
        self._error_msg = ""
        self._error_timer = 0.0

    def on_exit(self) -> None:
        pass

    def _max_scroll(self) -> int:
        return max(0, len(self._options) - VISIBLE_ITEMS)

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._error_timer > 0:
            self._error_timer -= dt
            if self._error_timer <= 0:
                self._error_msg = ""

        prev_selected = self._selected
        if im.is_raw_key_pressed(pygame.K_DOWN):
            if self._selected < len(self._options) - 1:
                self._selected += 1
                if self._selected - self._scroll_offset >= VISIBLE_ITEMS:
                    self._scroll_offset = min(self._scroll_offset + 1, self._max_scroll())

        if im.is_raw_key_pressed(pygame.K_UP):
            if self._selected > 0:
                self._selected -= 1
                if self._selected < self._scroll_offset:
                    self._scroll_offset = max(self._scroll_offset - 1, 0)
        if self._selected != prev_selected:
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_HOVER)

        if im.is_action_just_pressed(Action.CONFIRM):
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_CONFIRM)
            key = self._options[self._selected][2]
            registry = get_registry()
            scene = registry.build(key, self.context)
            if scene is not None:
                self.context.scene_manager.push(scene)
            else:
                self._error_msg = "Failed to load demo scene — missing assets?"
                self._error_timer = 3.0

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_CANCEL)
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "ACADEMIC DEMONSTRATIONS", "MENU")

        for i in range(self._scroll_offset, min(self._scroll_offset + VISIBLE_ITEMS, len(self._options))):
            unit, desc, _ = self._options[i]
            idx = i - self._scroll_offset
            cy = VISIBLE_Y_START + idx * ITEM_H
            selected = i == self._selected

            # Background highlight for selected item
            if selected:
                highlight_rect = pygame.Rect(8, cy - 2, settings.INTERNAL_WIDTH - 16, ITEM_H + 2)
                pygame.draw.rect(surface, (40, 40, 80), highlight_rect, border_radius=3)

            color = COLOR_HIGHLIGHT if selected else COLOR_TEXT
            unit_text = self._font_medium.render(f" {unit}", True, color)
            surface.blit(unit_text, (20, cy))

            desc_color = (180, 180, 200) if selected else (130, 130, 130)
            desc_text = self._font_small.render(f"  {desc}", True, desc_color)
            surface.blit(desc_text, (20, cy + 12))

        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            ex = (settings.INTERNAL_WIDTH - err.get_width()) // 2
            surface.blit(err, (ex, 170))

        draw_bottom_bar(surface, "  UP/DOWN: Navigate  |  ENTER: Select  |  ESC: Back to Title")
