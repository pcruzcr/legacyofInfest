"""
TutorialOverlay — Step-by-step tutorial guide for lab scenes.

Shows highlighted control descriptions and explains each
slider/button/mode when the student presses T.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.scenes.demo_common import COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT


TUTORIAL_CONTENT: dict[str, list[dict[str, str]]] = {
    "vector_lab": [
        {"title": "Welcome to Vector Lab", "text": "Learn vector math through interactive visualization."},
        {"title": "Modes (TAB)", "text": "Cycle through 4 modes: Free Move, Chase, Orbit, Distance Check."},
        {"title": "Player (Arrows)", "text": "Move the green player dot with arrow keys."},
        {"title": "Enemy (WASD)", "text": "Move the red enemy dot with W/A/S/D keys."},
        {"title": "Normalized (N)", "text": "Press N to toggle the unit vector display (length=1)."},
        {"title": "Math Panel", "text": "The left panel shows vector length, dot product, and angle."},
        {"title": "Quiz (Q)", "text": "Press Q to test your knowledge with quiz questions."},
        {"title": "Code (C)", "text": "Press C to see the algorithm code running behind the scenes."},
        {"title": "Reset (R)", "text": "Press R to reset player and enemy positions."},
    ],
    "color_theory": [
        {"title": "Color Theory Lab", "text": "Explore RGB, HSV, HSL, CMYK color spaces."},
        {"title": "Modes (TAB)", "text": "Cycle through RGB, HSV, HSL, CMYK, Alpha Blend, Challenge."},
        {"title": "Sliders", "text": "Use LEFT/RIGHT arrows to adjust color channel values."},
        {"title": "Visual Feedback", "text": "The preview shows the resulting color in real-time."},
        {"title": "Challenge Mode", "text": "Match a target color by adjusting sliders."},
        {"title": "Quiz (Q)", "text": "Press Q to answer color theory questions."},
    ],
    "filter_lab": [
        {"title": "Filter Lab", "text": "Learn image convolution and filtering techniques."},
        {"title": "Modes (TAB)", "text": "Cycle through: Histogram, Brightness, Contrast, Kernels, etc."},
        {"title": "Parameters", "text": "Use LEFT/RIGHT to adjust filter parameters like strength."},
        {"title": "Kernel Mode", "text": "See how different convolution kernels affect the image."},
        {"title": "Presets (Pipeline)", "text": "Visit the Pipeline Builder for preset filter chains."},
        {"title": "Quiz (Q)", "text": "Press Q to test filter knowledge."},
    ],
}


class TutorialOverlay:
    """Step-by-step tutorial guide for lab scenes. Toggle with T key, navigate with LEFT/RIGHT."""

    def __init__(self, lab_key: str = "vector_lab") -> None:
        """Load tutorial steps for the given lab key."""
        self._active: bool = False
        self._lab_key: str = lab_key
        self._step: int = 0
        self._steps: list[dict[str, str]] = TUTORIAL_CONTENT.get(lab_key, [
            {"title": "No Tutorial", "text": "No tutorial content available for this lab."},
        ])

    @property
    def active(self) -> bool:
        """Whether the tutorial is currently displayed."""
        return self._active

    def toggle(self) -> None:
        """Show or hide the tutorial. Resets to step 0 when shown."""
        self._active = not self._active
        if self._active:
            self._step = 0

    def set_lab(self, lab_key: str) -> None:
        """Switch which lab's tutorial content to display."""
        self._lab_key = lab_key
        self._steps = TUTORIAL_CONTENT.get(lab_key, [
            {"title": "No Tutorial", "text": "No tutorial content available."},
        ])
        self._step = 0

    def next_step(self) -> None:
        """Advance to the next tutorial step."""
        if self._step < len(self._steps) - 1:
            self._step += 1

    def prev_step(self) -> None:
        """Go back to the previous tutorial step."""
        if self._step > 0:
            self._step -= 1

    def draw(self, surface: pygame.Surface) -> None:
        """Render the tutorial overlay box with current step content."""
        if not self._active or not self._steps:
            return

        step = self._steps[self._step]
        overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))

        box_w = 360
        box_h = 120
        bx = (settings.INTERNAL_WIDTH - box_w) // 2
        by = (settings.INTERNAL_HEIGHT - box_h) // 2

        pygame.draw.rect(overlay, (20, 20, 50), (bx, by, box_w, box_h))
        pygame.draw.rect(overlay, COLOR_HIGHLIGHT, (bx, by, box_w, box_h), 1)

        font_small = pygame.font.Font(None, 12)
        font_title = pygame.font.Font(None, 15)
        font_step = pygame.font.Font(None, 11)

        title = font_title.render(f"Tutorial: {step.get('title','')}", True, COLOR_HIGHLIGHT)
        overlay.blit(title, (bx + 8, by + 6))

        text = step.get("text", "")
        wrapped = []
        words = text.split(" ")
        line = ""
        for w in words:
            if font_small.size(line + " " + w)[0] > box_w - 24:
                wrapped.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            wrapped.append(line)

        for i, line in enumerate(wrapped):
            txt = font_small.render(line, True, COLOR_TEXT)
            overlay.blit(txt, (bx + 12, by + 28 + i * 14))

        step_info = font_step.render(
            f"  Step {self._step + 1}/{len(self._steps)}  |  LEFT/RIGHT to navigate  |  T to close",
            True, COLOR_ACCENT)
        overlay.blit(step_info, (bx + 8, by + box_h - 18))

        surface.blit(overlay, (0, 0))


_TUTORIAL: TutorialOverlay | None = None


def get_tutorial(lab_key: str = "vector_lab") -> TutorialOverlay:
    """Return the module-level singleton TutorialOverlay instance."""
    global _TUTORIAL
    if _TUTORIAL is None:
        _TUTORIAL = TutorialOverlay(lab_key)
    return _TUTORIAL
