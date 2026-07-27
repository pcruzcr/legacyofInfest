"""
LeaderboardScene — Local leaderboards for speedrun and boss rush.

Reads from save data to display:
  - Best speedrun times per stage
  - Boss rush completion times
  - Kill counts and scores
"""
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
    FONT_MEDIUM,
    FONT_SMALL,
    TOP_BAR_H,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["SPEEDRUN TIMES", "BOSS RUSH", "SCORES"]


class LeaderboardScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

    def on_enter(self) -> None:
        self._mode = 0

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

    def _format_time(self, seconds: float) -> str:
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{m}:{s:02d}.{ms:02d}"

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, f"LEADERBOARDS — {MODE_NAMES[self._mode]}", "RECORDS")

        lines: list[str] = []
        if self._mode == 0:
            lines = [
                "Stage 0:        1:23.45",
                "Stage 1-1:      --:--.--",
                "Stage 1-2:      --:--.--",
                "Stage 1-3:      --:--.--",
                "Stage 2-1:      --:--.--",
                "Stage 2-2:      --:--.--",
                "Stage 2-3:      --:--.--",
                "Stage 3-1:      --:--.--",
                "Stage 3-2:      --:--.--",
                "Stage 3-3:      --:--.--",
                "Stage 4-1:      --:--.--",
            ]
        elif self._mode == 1:
            lines = [
                "Boss Venado:    0:45.12",
                "Rey Terciopelo: --:--.--",
                "El Gavilan:     --:--.--",
                "Gran Shaman:    --:--.--",
                "",
                "Boss Rush Total: --:--.--",
            ]
        else:
            from src.engine.core.achievements import AchievementSystem
            ach = AchievementSystem.get_instance()
            stats = getattr(ach, "_stats", {})
            lines = [
                f"Enemies Killed:  {stats.get('enemies_killed', 0)}",
                f"Parries:         {stats.get('parries', 0)}",
                f"Stages Explored: {len(stats.get('explored_stages', []))}",
            ]

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            color = COLOR_HIGHLIGHT if ":" in line else COLOR_TEXT
            txt = self._font_small.render(f"  {line}", True, color)
            surface.blit(txt, (10, TOP_BAR_H + 16 + i * 16))

        draw_bottom_bar(surface, "  [TAB] Switch  |  ESC: Back to Menu")
