from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.title_scene import TitleScene
from src.engine.ui.theme import Theme
from src.engine.ui.widgets import (
    MenuItem,
    MenuList,
    draw_key_hints,
    draw_screen,
    handle_menu_navigation,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class GameOverScene(BaseScene):
    """Game Over screen shown on player death. Offers Continue and Quit."""

    # Input is ignored for this long after death so a player mashing attack
    # cannot dismiss the screen before they have read it.
    INPUT_GRACE = 0.5

    def __init__(self, context: GameContext, stage_scene: BaseScene) -> None:
        super().__init__(context)
        self._stage_scene = stage_scene
        self._stage_scene_respawn = stage_scene.respawn if hasattr(stage_scene, "respawn") else None
        # AUD-045: navigation and focus now come from the shared MenuList, so
        # this screen behaves exactly like every other menu in the game.
        self._menu = MenuList(items=[
            MenuItem("CONTINUE", value="continue",
                     hint="Respawn at your last checkpoint"),
            MenuItem("QUIT", value="quit",
                     hint="Abandon the run and return to the title screen"),
        ])
        self._elapsed: float = 0.0

    def on_enter(self) -> None:
        self._menu.index = 0
        self._elapsed = 0.0

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self._elapsed += dt
        self._menu.update(dt)
        if self._elapsed <= self.INPUT_GRACE:
            return

        handle_menu_navigation(
            self._menu, self.input,
            on_confirm=self._activate,
            # CANCEL is deliberately not wired to anything here. There is no
            # "back" from death, and silently quitting on Escape would be a
            # destructive action triggered by the universal cancel key.
        )

    def _activate(self, item: MenuItem) -> None:
        if item.value == "continue":
            self.context.scene_manager.pop()
            try:
                if self._stage_scene_respawn:
                    self._stage_scene_respawn()
            except (RuntimeError, AttributeError, TypeError):
                logger.exception("game_over: respawn failed; returning to title")
                self.context.scene_manager.replace(TitleScene(self.context))
        else:
            self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        y = draw_screen(surface, "GAME OVER", "The infestation claims another")

        width = 280
        x = (settings.INTERNAL_WIDTH - width) // 2
        end_y = self._menu.draw(surface, x, y + Theme.SPACE_L, width)
        self._menu.draw_hint(surface, end_y + Theme.SPACE_M)

        draw_key_hints(surface, [
            ("↑↓", "Move"),
            ("Enter", "Select"),
        ])
