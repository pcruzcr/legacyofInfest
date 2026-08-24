"""
QuizSystem — Interactive quiz overlay for academic lab scenes.

Each lab registers questions; pressing Q toggles quiz mode.
Questions are displayed as multiple-choice overlays.

To integrate into a lab:
  1. Import QuizManager
  2. Create questions list
  3. Pass to QuizManager at start
  4. Call update() and draw() during the lab's update/draw
"""
from __future__ import annotations

from typing import Any

import pygame

from src.engine.core import settings
from src.engine.scenes.demo_common import (
    COLOR_ACCENT,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
)
from src.engine.ui.theme import font


class QuizManager:
    def __init__(self, questions: list[dict[str, Any]]) -> None:
        self._questions = questions
        self._current: int = 0
        self._selected: int = 0
        self._answered: bool = False
        self._correct: bool = False
        self._show_result_timer: float = 0.0
        self._score: int = 0
        self._total_answered: int = 0
        self._results: list[bool] = []
        self._active: bool = False
        self._overlay: pygame.Surface | None = None
        self._font_question = font(13)
        self._font_answer = font(15)

    def toggle(self) -> None:
        self._active = not self._active
        if self._active:
            self._current = 0
            self._selected = 0
            self._answered = False

    @property
    def active(self) -> bool:
        return self._active

    def handle_input(self, im: Any) -> None:
        if not self._active:
            return
        if self._answered:
            if self._show_result_timer > 0:
                return
            self._current = (self._current + 1) % len(self._questions)
            self._selected = 0
            self._answered = False
            return

        if im.is_raw_key_pressed(pygame.K_UP):
            self._selected = (self._selected - 1) % len(self._current_question()["options"])
        if im.is_raw_key_pressed(pygame.K_DOWN):
            self._selected = (self._selected + 1) % len(self._current_question()["options"])
        if im.is_raw_key_pressed(pygame.K_SPACE) or im.is_raw_key_pressed(pygame.K_RETURN):
            self._answered = True
            self._total_answered += 1
            correct_idx = self._current_question().get("answer", 0)
            self._correct = (self._selected == correct_idx)
            self._results.append(self._correct)
            if self._correct:
                self._score += 1
            self._show_result_timer = 1.5

    def _current_question(self) -> dict[str, Any]:
        return self._questions[self._current] if self._questions else {
            "question": "No questions loaded",
            "options": ["OK"],
            "answer": 0,
        }

    def update(self, dt: float) -> None:
        if self._show_result_timer > 0:
            self._show_result_timer -= dt

    def draw(self, surface: pygame.Surface) -> None:
        if not self._active:
            return

        q = self._current_question()
        if self._overlay is None or self._overlay.get_size() != (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT):
            self._overlay = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay = self._overlay
        overlay.fill((0, 0, 0, 200))

        box_w = 320
        box_h = 160
        bx = (settings.INTERNAL_WIDTH - box_w) // 2
        by = (settings.INTERNAL_HEIGHT - box_h) // 2

        pygame.draw.rect(overlay, (20, 20, 40), (bx, by, box_w, box_h))
        pygame.draw.rect(overlay, COLOR_HIGHLIGHT, (bx, by, box_w, box_h), 1)

        title = self._font_answer.render("QUIZ", True, COLOR_HIGHLIGHT)
        overlay.blit(title, (bx + 8, by + 6))

        qtext = q.get("question", "")
        wrapped = []
        words = qtext.split(" ")
        line = ""
        for w in words:
            if self._font_question.size(line + " " + w)[0] > box_w - 24:
                wrapped.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            wrapped.append(line)

        for i, line in enumerate(wrapped):
            txt = self._font_question.render(line, True, COLOR_TEXT)
            overlay.blit(txt, (bx + 12, by + 24 + i * 12))

        options = q.get("options", [])
        for i, opt in enumerate(options):
            color = COLOR_HIGHLIGHT if i == self._selected else COLOR_TEXT
            marker = "▶" if i == self._selected else " "
            if self._answered:
                if i == q.get("answer", 0):
                    color = (80, 200, 80)
                    marker = "✓"
                elif i == self._selected and not self._correct:
                    color = (200, 80, 80)
                    marker = "✗"
            otxt = self._font_question.render(f"  {marker} {opt}", True, color)
            overlay.blit(otxt, (bx + 12, by + 24 + len(wrapped) * 12 + 4 + i * 14))

        if self._answered:
            result_color = (80, 200, 80) if self._correct else (200, 80, 80)
            result_text = "✓ Correct!" if self._correct else "✗ Incorrect"
            rt = self._font_answer.render(result_text, True, result_color)
            overlay.blit(rt, (bx + 12, by + box_h - 22))

        progress = self._font_question.render(
            f"  {self._current + 1}/{len(self._questions)}  |  Score: {self._score}/{self._total_answered}",
            True, COLOR_ACCENT)
        overlay.blit(progress, (bx + 12, by + box_h - 14))

        surface.blit(overlay, (0, 0))

    def close(self) -> None:
        self._active = False
