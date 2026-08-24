from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.ui.theme import Theme, font

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager


# Module-level hardcoded tips. Future: externalize to JSON / YAML (ARC-033).
TUTORIAL_TIPS: dict[str, list[str]] = {
    "move": ["Move: LEFT/RIGHT or A/D", "Jump: SPACE or UP/W", "Crouch: DOWN/S"],
    "attack": ["Short attack: Z or J", "Long attack: X or K (hold to charge)", "Dash: SHIFT or ALT"],
    "combat": [
        "Parry: Attack + Crouch together",
        "Aerial attack: Press attack in air",
        "Dash attack: Attack during dash",
    ],
    "advanced": [
        "Wall jump: Jump while sliding on wall",
        "Air combo: Launch enemy + follow up in air",
        "Ultimate: Both attacks with full SP meter",
    ],
    "checkpoint": ["Checkpoint reached! Progress saved."],
    "boss": ["BOSS FIGHT! Use all your skills.", "Watch for telegraphs before attacks."],
}


class TutorialOverlay:
    """Contextual tutorial tips that appear on screen and auto-dismiss."""

    def __init__(self) -> None:
        self._active: bool = False
        self._lines: list[str] = []
        self._timer: float = 0.0
        self._duration: float = 5.0
        # AUD-451 — por el tema, para que la escala de accesibilidad llegue a
        # los avisos del tutorial, que son texto que se lee jugando.
        self._font = font(Theme.FONT_SMALL)
        self._title_font = font(Theme.FONT_BODY)
        self._box_surf = None

    def show(self, tip_key: str, duration: float = 5.0) -> None:
        lines = TUTORIAL_TIPS.get(tip_key)
        if lines:
            self._lines = lines
            self._duration = duration
            self._timer = duration
            self._active = True

    def update(self, dt: float, input_manager: InputManager | None) -> None:
        if not self._active:
            return
        self._timer -= dt
        if input_manager is not None and input_manager.is_action_just_pressed(Action.CONFIRM):
            self._active = False
        if self._timer <= 0:
            self._active = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self._active:
            return
        alpha = min(255, int(255 * (self._timer / 0.5))) if self._timer < 0.5 else 255
        box_w = 220
        line_h = 16
        title_h = 22
        pad = 8
        total_h = title_h + len(self._lines) * line_h + pad * 2
        if self._box_surf is None or self._box_surf.get_size() != (box_w, total_h):
            self._box_surf = pygame.Surface((box_w, total_h), pygame.SRCALPHA)
        box_surf = self._box_surf
        box_surf.fill((0, 0, 0, 180))
        bx = (settings.INTERNAL_WIDTH - box_w) // 2
        by = settings.INTERNAL_HEIGHT // 2 - total_h // 2

        title = self._title_font.render("TIP", True, (255, 220, 100))
        title.set_alpha(alpha)
        box_surf.blit(title, (pad, pad))

        for i, line in enumerate(self._lines):
            txt = self._font.render(line, True, (220, 220, 220))
            txt.set_alpha(alpha)
            box_surf.blit(txt, (pad, pad + title_h + i * line_h))

        surface.blit(box_surf, (bx, by))
