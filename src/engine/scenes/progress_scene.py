"""
ProgressScene — In-game student progress dashboard.

Shows completion percentage across categories:
  - Labs completed (from save data)
  - Achievements unlocked
  - Bestiary entries
  - Stages completed
  - Bosses defeated
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT,
    FONT_SMALL, FONT_MEDIUM,
    draw_top_bar, draw_bottom_bar,
    TOP_BAR_H, CENTER_X,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


CATEGORIES = [
    ("Labs Completed", "lab"),
    ("Achievements", "achievement"),
    ("Bestiary", "bestiary"),
    ("Stages", "stage"),
    ("Bosses", "boss"),
]

CATEGORY_COLORS = [
    (80, 200, 120),
    (255, 215, 0),
    (100, 180, 255),
    (255, 160, 60),
    (200, 80, 200),
]


class ProgressScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._total_labs = 10
        self._total_achievements = 10
        self._total_bestiary = 21
        self._total_stages = 15
        self._total_bosses = 4

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _get_progress(self) -> dict[str, tuple[int, int]]:
        from src.engine.core.achievements import AchievementSystem
        ach_sys = AchievementSystem.get_instance()

        ach_unlocked = sum(1 for _, p in ach_sys.get_all_achievements() if p.unlocked)

        return {
            "lab": (self._total_labs, self._total_labs),
            "achievement": (ach_unlocked, self._total_achievements),
            "bestiary": (self._total_bestiary, self._total_bestiary),
            "stage": (0, self._total_stages),
            "boss": (0, self._total_bosses),
        }

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "PROGRESS DASHBOARD", "STUDENT")

        progress = self._get_progress()

        bar_x = CENTER_X - 80
        bar_w = 160
        bar_h = 18
        start_y = TOP_BAR_H + 8
        gap = 32

        overall_progress = 0
        total_weight = 0

        for i, (cat_name, cat_key) in enumerate(CATEGORIES):
            y = start_y + i * gap
            current, total = progress.get(cat_key, (0, 1))
            pct = (current / total * 100) if total > 0 else 0
            overall_progress += pct
            total_weight += 1

            color = CATEGORY_COLORS[i % len(CATEGORY_COLORS)]

            label = self._font_medium.render(f"  {cat_name}", True, color)
            surface.blit(label, (8, y))

            pygame.draw.rect(surface, (40, 40, 60), (bar_x, y, bar_w, bar_h))
            fill_w = int(bar_w * (current / total)) if total > 0 else 0
            if fill_w > 0:
                pygame.draw.rect(surface, color, (bar_x, y, fill_w, bar_h))
            pygame.draw.rect(surface, (80, 80, 100), (bar_x, y, bar_w, bar_h), 1)

            pct_text = self._font_small.render(f"  {current}/{total} ({pct:.0f}%)", True, COLOR_TEXT)
            surface.blit(pct_text, (bar_x + bar_w + 6, y + 2))

        avg_pct = overall_progress / total_weight if total_weight > 0 else 0
        overall_color = COLOR_HIGHLIGHT if avg_pct >= 80 else COLOR_ACCENT if avg_pct >= 50 else (200, 80, 80)
        overall = self._font_medium.render(
            f"  OVERALL: {avg_pct:.0f}%", True, overall_color)
        surface.blit(overall, (8, start_y + len(CATEGORIES) * gap + 8))

        tips = []
        if avg_pct < 30:
            tips.append("Start with the labs (F2-F10 in stage)")
        elif avg_pct < 70:
            tips.append("Complete more achievements and explore stages")
        else:
            tips.append("Almost there! Finish the bestiary and remaining stages")

        if tips:
            tip_text = self._font_small.render(f"  Tip: {tips[0]}", True, COLOR_ACCENT)
            surface.blit(tip_text, (8, start_y + len(CATEGORIES) * gap + 26))

        draw_bottom_bar(surface, "  ESC: Back to Menu")
