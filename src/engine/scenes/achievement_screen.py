"""
Module: achievement_sene.py
System: engine.scenes
Academic Unit: N/A
Description: Achievement screen showing unlocked and locked achievements.
"""
from __future__ import annotations
import pygame
from typing import TYPE_CHECKING
from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.core.achievements import AchievementSystem

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class AchievementScene(BaseScene):
    """Achievement screen — displays all achievements with locked/unlocked states."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        mgr: AchievementSystem | None = getattr(context, "achievement_manager", None)
        self._achievements = mgr.achievements if mgr else []
        self._font_title = pygame.font.Font(None, 28)
        self._font_name = pygame.font.Font(None, 16)
        self._font_desc = pygame.font.Font(None, 12)
        self._scroll_y: int = 0
        self._max_scroll: int = 0
        self._font_hint = pygame.font.Font(None, 14)

    def on_enter(self) -> None:
        self._scroll_y = 0
        self._max_scroll = max(0, len(self._achievements) * 56 - (settings.INTERNAL_HEIGHT - 60))

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._scroll_y = min(self._scroll_y + 20, self._max_scroll)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._scroll_y = max(self._scroll_y - 20, 0)
        if im.is_action_just_pressed(Action.CANCEL) or im.is_action_just_pressed(Action.CONFIRM):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 30))
        title = self._font_title.render("ACHIEVEMENTS", True, (255, 255, 240))
        surface.blit(title, ((settings.INTERNAL_WIDTH - title.get_width()) // 2, 16))
        y = 56 - self._scroll_y
        for defn, prog in self._achievements:
            if y + 56 < 0 or y > settings.INTERNAL_HEIGHT:
                y += 56
                continue
            unlocked = prog.unlocked
            bg_color = (50, 60, 40) if unlocked else (35, 35, 45)
            pygame.draw.rect(surface, bg_color, (10, y, settings.INTERNAL_WIDTH - 20, 50), border_radius=4)
            icon_text = "✓" if unlocked else "?"
            icon_color = (100, 255, 100) if unlocked else (120, 120, 120)
            icon = self._font_name.render(icon_text, True, icon_color)
            surface.blit(icon, (20, y + 8))
            name = self._font_name.render(defn.name, True, (255, 255, 220) if unlocked else (160, 160, 160))
            surface.blit(name, (46, y + 8))
            desc = self._font_desc.render(defn.description, True, (180, 180, 170) if unlocked else (100, 100, 110))
            surface.blit(desc, (46, y + 28))
            if not unlocked:
                target = self._font_desc.render(f"Progress: {prog.current}/{defn.target}", True, (130, 130, 140))
                surface.blit(target, (46, y + 42))
            y += 56
        hint = self._font_hint.render("[ESC] Back  [UP/DOWN] Scroll", True, (120, 120, 130))
        surface.blit(hint, ((settings.INTERNAL_WIDTH - hint.get_width()) // 2, settings.INTERNAL_HEIGHT - 18))
