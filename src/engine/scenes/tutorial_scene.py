from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_key_hints, draw_screen

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class _TutorialStep(TypedDict):
    title: str
    lines: list[str]


_TUTORIAL_STEPS: list[_TutorialStep] = [
    {
        "title": "MOVEMENT",
        "lines": [
            "LEFT/RIGHT or A/D to move (flechas o WASD)",
            "UP or W or SPACE to jump",
            "DOWN or S to crouch",
            "Stick izq / ratón: alternativo",
        ],
    },
    {
        "title": "COMBAT",
        "lines": [
            "Z/J or MOUSE LEFT for short attack",
            "X/K or MOUSE RIGHT for long attack",
            "Hold X to charge attack",
            "SHIFT / MIDDLE-CLICK / LT to dash",
        ],
    },
    {
        "title": "ADVANCED",
        "lines": [
            "CROUCH + Z to parry (mando Y+B)",
            "CROUCH + X or G to grab (mando LB)",
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
    {
        "title": "INTERACTIVE",
        "lines": [
            "Pulsa T para tutorial GUIADO",
            "5 salas con práctica + moneda + XP",
            "Flechas/WASD/stick/ratón: todos sirven",
            "Enter = texto, T = jugable",
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
        # Where the fade-out should land. "story" = the player read the
        # tutorial through to the end and is starting the game; "title" = the
        # player backed out with CANCEL and expects to be where they came
        # from. Conflating the two (AUD-009) meant Escape did not cancel —
        # it force-started the campaign.
        self._exit_target: str = "story"
        self._overlay: pygame.Surface | None = None
        # AUD-069: escala tipográfica del tema y su caché de fuentes.
        self._font_text = font(Theme.FONT_SMALL)

    def on_enter(self) -> None:
        self._fade_alpha = 255
        self._fade_dir = -1
        self._ready = False
        self._exit_requested = False
        self._exit_target = "story"
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if self._exit_requested:
            self._fade_alpha = min(255, int(self._fade_alpha + 500 * dt))
            if self._fade_alpha >= 255:
                if self._exit_target == "title":
                    from src.engine.scenes.title_scene import TitleScene
                    self.context.scene_manager.replace(TitleScene(self.context))
                else:
                    from src.engine.scenes.story_scene import StoryScene
                    self.context.scene_manager.replace(StoryScene(self.context, 1))
            return
        if not self._ready:
            self._fade_alpha = max(0, int(self._fade_alpha - 300 * dt))
            if self._fade_alpha <= 0:
                self._ready = True
            return
        # CANCEL is checked first and returns: otherwise a frame carrying both
        # CONFIRM and CANCEL would advance the step *and* exit.
        if im.is_action_just_pressed(Action.CANCEL):
            self._exit_requested = True
            self._exit_target = "title"
            return
        # AUD-721 — T lanza el hub guiado desde cualquier paso
        if im.is_raw_key_pressed(pygame.K_t):
            try:
                from src.stages.tutorial_hub.tutorial_hub import TutorialHub
                self.context.scene_manager.transition.start_fade_out(0.3)
                self.context.scene_manager.push(TutorialHub(self.context))
                return
            except Exception:
                pass
        if im.is_action_just_pressed(Action.CONFIRM) or \
                im.is_action_just_pressed(Action.SHORT_ATTACK) or \
                im.is_action_just_pressed(Action.JUMP):
            if self._step_index < len(_TUTORIAL_STEPS) - 1:
                self._step_index += 1
            else:
                self._exit_requested = True
                self._exit_target = "story"

    def draw(self, surface: pygame.Surface) -> None:
        if not _TUTORIAL_STEPS:
            draw_screen(surface, "TUTORIAL")
            return

        step = _TUTORIAL_STEPS[self._step_index]
        # AUD-069: el título del paso pasa a ser el título de la pantalla, con
        # el contador de páginas como subtítulo. Antes esta pantalla tenía su
        # propio fondo `(10,10,20)` y cuatro colores inventados.
        y = draw_screen(
            surface, step["title"],
            f"{self._step_index + 1} de {len(_TUTORIAL_STEPS)}",
        )

        y += Theme.SPACE_L
        for line in step["lines"]:
            text = self._font_text.render(line, True, Theme.TEXT)
            surface.blit(
                text, ((settings.INTERNAL_WIDTH - text.get_width()) // 2, y),
            )
            y += 28

        draw_key_hints(surface, [
            ("Enter", "Siguiente"),
            ("Esc", "Saltar"),
        ])
        if self._fade_alpha > 0:
            if self._overlay is None or self._overlay.get_size() != (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT):
                self._overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            overlay = self._overlay
            overlay.set_alpha(self._fade_alpha)
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))

