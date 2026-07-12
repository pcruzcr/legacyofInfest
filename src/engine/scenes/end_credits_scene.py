from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.title_scene import TitleScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class EndCreditsScene(BaseScene):
    """End Credits screen shown after all stages are complete."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._font_title = pygame.font.Font(None, 18)
        self._font_text = pygame.font.Font(None, 14)
        self._font_hint = pygame.font.Font(None, 11)
        self._elapsed: float = 0.0
        self._scroll_y: float = settings.INTERNAL_HEIGHT
        self._done: bool = False

        self._lines = [
            ("", 0),
            ("LEGACY OF INFEST", 0),
            ("", 0),
            ("A Game by Professor & Students", 0),
            ("", 0),
            ("--- Professor ---", 0),
            ("Professor: Stage 0 Engine & Framework", 0),
            ("", 0),
            ("--- Students ---", 0),
            ("Student A: Stage 1-1", 0),
            ("Student B: Stage 1-2", 0),
            ("Student C: Stage 1-3", 0),
            ("Student D: Stage 1-4 (El Venado Sagrado)", 0),
            ("Student E: Stage 2-1", 0),
            ("Student F: Stage 2-2", 0),
            ("Student G: Stage 2-3", 0),
            ("Student H: Stage 2-4 (El Rey Terciopelo)", 0),
            ("Student I: Stage 3-1", 0),
            ("Student J: Stage 3-2", 0),
            ("Student K: Stage 3-3", 0),
            ("Student L: Stage 3-4 (El Gavilan)", 0),
            ("Student M: Stage 4-1", 0),
            ("Student N: Stage 4-2 (Gran Shaman Paburu)", 0),
            ("", 0),
            ("Thanks for playing!", 0),
        ]

    def on_enter(self) -> None:
        self._elapsed = 0.0
        self._scroll_y = settings.INTERNAL_HEIGHT
        self._done = False

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self._elapsed += dt
        im = self.input
        if im is None:
            return

        if self._done and im.is_action_just_pressed(Action.CONFIRM):
            self.context.scene_manager.replace(TitleScene(self.context))
            return

        if self._elapsed > 1.0 and im.is_action_just_pressed(Action.CONFIRM):
            self._done = True
            return

        self._scroll_y -= 24 * dt

        last_line_y = self._scroll_y + len(self._lines) * 22
        if last_line_y < -50:
            self._done = True

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(settings.BG_COLOR)

        y = int(self._scroll_y)
        for text, _ in self._lines:
            if y < -30 or y > settings.INTERNAL_HEIGHT + 10:
                y += 22
                continue
            if text.startswith("---"):
                surf = self._font_title.render(text, True, (200, 200, 100))
            elif text.startswith("LEGACY"):
                surf = self._font_title.render(text, True, (255, 215, 0))
            elif ":" in text:
                surf = self._font_text.render(text, True, (220, 220, 220))
            else:
                surf = self._font_text.render(text, True, (180, 180, 180))
            sx = (settings.INTERNAL_WIDTH - surf.get_width()) // 2
            surface.blit(surf, (sx, y))
            y += 22

        if self._done:
            hint = self._font_hint.render("Press CONFIRM to return to title", True, (150, 150, 150))
            hx = (settings.INTERNAL_WIDTH - hint.get_width()) // 2
            surface.blit(hint, (hx, BOTTOM_BAR_Y - 16))

