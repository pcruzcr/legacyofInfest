from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.achievements import AchievementSystem
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class AchievementScene(BaseScene):
    """Achievement browse screen showing locked/unlocked achievements."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._font = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 14)
        self._title_font = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 18)
        self._selected: int = 0
        self._scroll_offset: int = 0
        self._bg: pygame.Surface | None = None
        try:
            bg_path = settings.ASSETS_DIR / "title" / "bck1.png"
            self._bg = AssetLoader.load_image(bg_path, size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        except (pygame.error, FileNotFoundError, PermissionError):
            logging.warning("achievement_scene: failed to load background %s", bg_path)

    def on_enter(self) -> None:
        self._selected = 0
        self._scroll_offset = 0
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(TitleScene(self.context))
            return

        ach_sys = AchievementSystem.get_instance()
        all_achs = ach_sys.get_all_achievements()
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = min(self._selected + 1, len(all_achs) - 1)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = max(self._selected - 1, 0)

        visible = (settings.INTERNAL_HEIGHT - 80) // 22
        if self._selected < self._scroll_offset:
            self._scroll_offset = self._selected
        if self._selected >= self._scroll_offset + visible:
            self._scroll_offset = self._selected - visible + 1

    def draw(self, surface: pygame.Surface) -> None:
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        if self._bg:
            surface.blit(self._bg, (0, 0))
        else:
            surface.fill((15, 15, 40))

        title = self._title_font.render("ACHIEVEMENTS", True, (220, 220, 200))
        surface.blit(title, ((w - title.get_width()) // 2, 12))

        ach_sys = AchievementSystem.get_instance()
        all_achs = ach_sys.get_all_achievements()
        unlocked_count = sum(1 for _, p in all_achs if p.unlocked)

        counter = self._font.render(f"{unlocked_count} / {len(all_achs)} unlocked", True, (180, 200, 220))
        surface.blit(counter, (20, 36))

        for i, (ach_def, prog) in enumerate(all_achs):
            if i < self._scroll_offset:
                continue
            y = 60 + (i - self._scroll_offset) * 22
            if y > h - 30:
                break

            if prog.unlocked:
                color = (255, 215, 0) if i == self._selected else (200, 200, 150)
                icon = "*"
                progress_str = ""
            else:
                color = (100, 100, 100) if i == self._selected else (70, 70, 70)
                icon = "?"
                progress_str = f" [{prog.current}/{ach_def.target}]"

            if i == self._selected:
                arrow = self._font.render(">", True, (255, 255, 100))
                surface.blit(arrow, (8, y))

            label = self._font.render(
                f"  {icon} {ach_def.name}{progress_str}",
                True, color,
            )
            surface.blit(label, (22, y))

            if i == self._selected:
                desc = self._font.render(ach_def.description, True, (150, 150, 170))
                surface.blit(desc, (40, y + 11))

        hint = self._font.render("CANCEL: Back", True, (120, 120, 140))
        surface.blit(hint, (8, h - 20))
        self.context.scene_manager.transition.draw(surface)

