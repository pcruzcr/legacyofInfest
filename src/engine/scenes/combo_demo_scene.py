"""
ComboDemoScene — Educational visualization of the Player combo state machine.

Shows:
  - Z → Z → X chain (light → light → heavy)
  - Combo window timer (0.5s)
  - Damage scaling: 1.0x → 1.5x → 2.0x
  - Reset on type change or timeout

Controls:
  Z   — light attack
  X   — heavy attack
  ESC — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE,
    draw_top_bar, draw_bottom_bar,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class ComboDemoScene(BaseScene):
    PANEL_W = 260
    PANEL_H = 160
    NODE_R = 14
    WINDOW_BAR_H = 8

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._combo_count: int = 0
        self._combo_timer: float = 0.0
        self._last_type: str = ""
        self._hit_log: list[str] = []
        self._font_large = pygame.font.Font(None, FONT_LARGE)
        self._font_medium = pygame.font.Font(None, FONT_MEDIUM)
        self._font_small = pygame.font.Font(None, FONT_SMALL)

    def on_enter(self) -> None:
        self._combo_count = 0
        self._combo_timer = 0.0
        self._last_type = ""
        self._hit_log = ["Press Z (light) or X (heavy)"]

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        # Decay combo timer
        if self._combo_timer > 0:
            self._combo_timer -= dt
            if self._combo_timer <= 0:
                self._reset_combo("timeout")

        # Inputs
        if im.is_action_pressed(Action.SHORT_ATTACK):
            self._register_hit("SHORT")
        if im.is_action_pressed(Action.LONG_ATTACK):
            self._register_hit("LONG")

        if im.is_action_pressed(Action.CANCEL):
            self.context.scene_manager.pop()

    def _register_hit(self, atk_type: str) -> None:
        import src.engine.core.settings as settings
        if (self._combo_count > 0
                and self._combo_timer > 0
                and self._last_type == atk_type
                and self._combo_count < settings.COMBO_MAX):
            self._combo_count += 1
        else:
            self._combo_count = 1
        self._combo_timer = settings.COMBO_WINDOW
        self._last_type = atk_type
        idx = min(self._combo_count - 1, len(settings.COMBO_DAMAGE_MULT) - 1)
        mult = settings.COMBO_DAMAGE_MULT[idx]
        label = "Light" if atk_type == "SHORT" else "Heavy"
        self._hit_log.append(f"{label} hit → COMBO x{self._combo_count} ({mult}x)")
        if len(self._hit_log) > 6:
            self._hit_log.pop(0)

    def _reset_combo(self, reason: str) -> None:
        self._combo_count = 0
        self._combo_timer = 0.0
        self._last_type = ""
        if reason:
            self._hit_log.append(f"[{reason}] — reset")

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "COMBO STATE MACHINE", "Demo")

        x = 20
        y = 40
        # Title
        title = self._font_medium.render("Chain: Z → Z → X", True, COLOR_HIGHLIGHT)
        surface.blit(title, (x, y))
        y += 30

        # Window bar
        if self._combo_timer > 0:
            ratio = max(0.0, min(1.0, self._combo_timer / settings.COMBO_WINDOW))
            bw = int(180 * ratio)
            pygame.draw.rect(surface, (60, 60, 80), (x, y, 180, self.WINDOW_BAR_H))
            pygame.draw.rect(surface, COLOR_ACCENT, (x, y, bw, self.WINDOW_BAR_H))
        else:
            pygame.draw.rect(surface, (60, 60, 80), (x, y, 180, self.WINDOW_BAR_H))
        label = self._font_small.render("Combo window", True, COLOR_TEXT)
        surface.blit(label, (x + 190, y - 2))
        y += 30

        # Nodes
        nodes = [
            ("Z", self._last_type == "SHORT"),
            ("X", self._last_type == "LONG"),
        ]
        for i, (sym, active) in enumerate(nodes):
            nx = x + 40 + i * 60
            ny = y + 20
            color = COLOR_HIGHLIGHT if active else (80, 80, 100)
            pygame.draw.circle(surface, color, (nx, ny), self.NODE_R)
            txt = self._font_medium.render(sym, True, (20, 20, 20))
            surface.blit(txt, (nx - txt.get_width() // 2, ny - txt.get_height() // 2))

        # Arrow between nodes
        if self._last_type:
            pygame.draw.line(surface, COLOR_ACCENT,
                             (x + 40 + 20, y + 20),
                             (x + 40 + 100 - 20, y + 20), 3)

        y += 70

        # Combo count and multiplier
        count_txt = self._font_large.render(
            f"Combo: x{self._combo_count}" if self._combo_count > 0 else "Combo: —",
            True, COLOR_HIGHLIGHT if self._combo_count > 0 else COLOR_TEXT,
        )
        surface.blit(count_txt, (x, y))
        y += 28
        idx = min(max(0, self._combo_count - 1), len(settings.COMBO_DAMAGE_MULT) - 1)
        mult = settings.COMBO_DAMAGE_MULT[idx] if self._combo_count > 0 else 1.0
        mult_txt = self._font_medium.render(
            f"Multiplier: {mult}x", True, COLOR_ACCENT,
        )
        surface.blit(mult_txt, (x, y))
        y += 30

        # Log
        for line in self._hit_log[-4:]:
            log_txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(log_txt, (x, y))
            y += 16

        draw_bottom_bar(surface, "Z: Light | X: Heavy | ESC: Back")