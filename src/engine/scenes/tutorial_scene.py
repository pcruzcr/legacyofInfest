from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class _TutorialStep(TypedDict):
    title: str
    lines: list[str]


_TUTORIAL_STEPS: list[_TutorialStep] = [
    {
        "title": "MOVEMENT",
        "lines": [
            "LEFT/RIGHT or A/D to move",
            "UP or W or SPACE to jump",
            "DOWN or S to crouch",
        ],
    },
    {
        "title": "COMBAT",
        "lines": [
            "Z or J for short attack",
            "X or K for long attack",
            "Hold X to charge attack",
            "SHIFT to dash",
        ],
    },
    {
        "title": "ADVANCED",
        "lines": [
            "CROUCH + Z to parry",
            "CROUCH + X or G to grab",
            "Z+X with full meter = ULTIMATE",
            "Attack in air for aerial combo",
        ],
    },
    {
        "title": "HINTS",
        "lines": [
            "Red enemies = aggressive",
            "Purple telegraphs = incoming",
            "Gold checkpoints save progress",
            "Collect items for permanent upgrades",
        ],
    },
]


class TutorialScene(BaseScene):
    """Step-by-step tutorial overlay shown on first play."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._step_index: int = 0
        self._fade_alpha: int = 255
        self._fade_dir: int = -1
        self._ready: bool = False
        self._exit_requested: bool = False

    def on_enter(self) -> None:
        self._fade_alpha = 255
        self._fade_dir = -1
        self._ready = False
        self._exit_requested = False

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if self._exit_requested:
            self._fade_alpha = min(255, int(self._fade_alpha + 500 * dt))
            if self._fade_alpha >= 255:
                from src.engine.scenes.title_scene import TitleScene
                self.context.scene_manager.replace(TitleScene(self.context))
            return
        if not self._ready:
            self._fade_alpha = max(0, int(self._fade_alpha - 300 * dt))
            if self._fade_alpha <= 0:
                self._ready = True
            return
        if im.is_action_just_pressed(Action.CONFIRM) or \
                im.is_action_just_pressed(Action.SHORT_ATTACK) or \
                im.is_action_just_pressed(Action.JUMP):
            if self._step_index < len(_TUTORIAL_STEPS) - 1:
                self._step_index += 1
            else:
                self._exit_requested = True
        if im.is_action_just_pressed(Action.CANCEL):
            self._exit_requested = True

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 20))
        if not _TUTORIAL_STEPS:
            return
        step = _TUTORIAL_STEPS[self._step_index]
        font_large = pygame.font.Font(None, 26)
        font_small = pygame.font.Font(None, 18)
        title = font_large.render(step["title"], True, (255, 200, 80))
        surface.blit(title, ((settings.INTERNAL_WIDTH - title.get_width()) // 2, 40))
        y = 90
        for line in step["lines"]:
            text = font_small.render(line, True, (200, 200, 220))
            surface.blit(text, ((settings.INTERNAL_WIDTH - text.get_width()) // 2, y))
            y += 28
        page_text = font_small.render(
            f"{self._step_index + 1} / {len(_TUTORIAL_STEPS)}",
            True, (120, 120, 140),
        )
        surface.blit(page_text, ((settings.INTERNAL_WIDTH - page_text.get_width()) // 2, settings.INTERNAL_HEIGHT - 60))
        hint = font_small.render("[ENTER/Z/SPACE] Next  [ESC] Skip", True, (140, 140, 160))
        surface.blit(hint, ((settings.INTERNAL_WIDTH - hint.get_width()) // 2, settings.INTERNAL_HEIGHT - 30))
        if self._fade_alpha > 0:
            overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            overlay.set_alpha(self._fade_alpha)
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))
