from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class BestiaryScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._font_title = pygame.font.Font(None, 24)
        self._font_entry = pygame.font.Font(None, 16)
        self._font_stats = pygame.font.Font(None, 14)
        self._font_hint = pygame.font.Font(None, 14)
        self._scroll_offset: int = 0
        self._selected: int = 0

    def on_enter(self) -> None:
        self._scroll_offset = 0
        self._selected = 0
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def _get_entries(self) -> list:
        from src.framework.entities.bestiary import Bestiary
        bestiary = Bestiary.get_instance()
        return [e for e in bestiary.get_all_entries() if e.encountered]

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        entries = self._get_entries()
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = min(self._selected + 1, max(len(entries) - 1, 0))
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = max(self._selected - 1, 0)
        if im.is_action_just_pressed(Action.CANCEL):
            self.context.scene_manager.pop()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 20))
        title = self._font_title.render("BESTIARY", True, (255, 215, 0))
        surface.blit(title, ((settings.INTERNAL_WIDTH - title.get_width()) // 2, 12))

        entries = self._get_entries()
        y = 40
        entry_h = 48

        if not entries:
            empty = self._font_entry.render("No enemies encountered yet.", True, (120, 120, 130))
            surface.blit(empty, ((settings.INTERNAL_WIDTH - empty.get_width()) // 2, 80))
        else:
            for idx, entry in enumerate(entries):
                if idx < self._scroll_offset:
                    continue
                ey = y + (idx - self._scroll_offset) * entry_h
                if ey > settings.INTERNAL_HEIGHT - 20:
                    break

                bg_color = (30, 30, 45) if idx == self._selected else (18, 18, 32)
                pygame.draw.rect(surface, bg_color, (8, ey, settings.INTERNAL_WIDTH - 16, entry_h - 2))
                if idx == self._selected:
                    pygame.draw.rect(surface, (255, 215, 0), (8, ey, settings.INTERNAL_WIDTH - 16, entry_h - 2), 1)

                name_color = (255, 255, 240) if entry.encountered else (100, 100, 100)
                name = self._font_entry.render(entry.name, True, name_color)
                surface.blit(name, (16, ey + 2))

                desc = self._font_stats.render(entry.description, True, (180, 180, 180))
                surface.blit(desc, (16, ey + 20))

                kills_text = self._font_stats.render(f"Kills: {entry.kills}", True, (200, 180, 100))
                surface.blit(kills_text, (settings.INTERNAL_WIDTH - 80, ey + 2))

                hp_text = self._font_stats.render(f"HP: {entry.hp}", True, (180, 100, 100))
                surface.blit(hp_text, (settings.INTERNAL_WIDTH - 80, ey + 18))

        hint = self._font_hint.render("[ESC] Back  [UP/DOWN] Navigate", True, (100, 100, 110))
        surface.blit(hint, ((settings.INTERNAL_WIDTH - hint.get_width()) // 2, BOTTOM_BAR_Y - 12))

