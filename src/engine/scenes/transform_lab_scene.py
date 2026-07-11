"""
TransformLabScene — Interactive 2D Transformation Laboratory

Teaches Unit II/III concepts:
  - Translation, rotation, scaling, shearing matrices
  - Transformation order (non-commutativity)
  - Matrix visualization with live preview

Controls:
  arrows          — translate shape
  LEFT/RIGHT      — rotate / scale / shear (depends on mode)
  R               — reset transform
  TAB             — cycle transform type
  N               — toggle matrix display
  ESC             — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import math
import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT,
    FONT_SMALL, FONT_MEDIUM,
    draw_top_bar, draw_bottom_bar,
    save_png,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["TRANSLATE", "ROTATE", "SCALE", "SHEAR", "COMPOSITE"]
SHAPE_PTS = [(0, -30), (20, 10), (0, 30), (-20, 10)]


class TransformLabScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._tx: float = 160.0
        self._ty: float = 100.0
        self._angle: float = 0.0
        self._sx: float = 1.0
        self._sy: float = 1.0
        self._shx: float = 0.0
        self._shy: float = 0.0
        self._param_acc: float = 0.0
        self._show_matrix: bool = True
        self._reset()

        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

        self._status_msg: str = ""
        self._status_timer: float = 0.0

    def _reset(self) -> None:
        self._tx, self._ty = 160.0, 100.0
        self._angle = 0.0
        self._sx, self._sy = 1.0, 1.0
        self._shx, self._shy = 0.0, 0.0

    def on_enter(self) -> None:
        self._mode = 0
        self._status_msg = ""

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._status_timer > 0:
            self._status_timer -= dt
            if self._status_timer <= 0:
                self._status_msg = ""

        # TAB — cycle modes
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._status_msg = f"Mode: {MODE_NAMES[self._mode]}"
            self._status_timer = 1.5

        # N — toggle matrix
        if im.is_raw_key_pressed(pygame.K_n):
            self._show_matrix = not self._show_matrix

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._reset()
            self._status_msg = "Transform reset"
            self._status_timer = 1.0

        # S — save screenshot
        if im.is_raw_key_pressed(pygame.K_s):
            self._screenshot = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            self.draw(self._screenshot)
            path = save_png("transform", MODE_NAMES[self._mode].lower(), self._screenshot)
            self._status_msg = f"Saved: {path.split('/')[-1].split(chr(92))[-1]}"
            self._status_timer = 2.0

        # ESC — back
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # Mode-specific controls
        speed = 60.0 * dt
        if self._mode == 0:  # TRANSLATE
            if im.is_raw_key_pressed(pygame.K_LEFT):
                self._tx -= speed
            if im.is_raw_key_pressed(pygame.K_RIGHT):
                self._tx += speed
            if im.is_raw_key_pressed(pygame.K_UP):
                self._ty -= speed
            if im.is_raw_key_pressed(pygame.K_DOWN):
                self._ty += speed
            self._tx = max(20, min(300, self._tx))
            self._ty = max(20, min(180, self._ty))
        elif self._mode == 1:  # ROTATE
            if im.is_raw_key_pressed(pygame.K_LEFT):
                self._angle -= 90.0 * dt
            if im.is_raw_key_pressed(pygame.K_RIGHT):
                self._angle += 90.0 * dt
            self._angle %= 360.0
        elif self._mode == 2:  # SCALE
            if im.is_raw_key_pressed(pygame.K_LEFT):
                self._sx = max(0.1, self._sx - 1.0 * dt)
                self._sy = max(0.1, self._sy - 1.0 * dt)
            if im.is_raw_key_pressed(pygame.K_RIGHT):
                self._sx = min(5.0, self._sx + 1.0 * dt)
                self._sy = min(5.0, self._sy + 1.0 * dt)
        elif self._mode == 3:  # SHEAR
            if im.is_raw_key_pressed(pygame.K_LEFT):
                self._shx -= 1.0 * dt
            if im.is_raw_key_pressed(pygame.K_RIGHT):
                self._shx += 1.0 * dt
            if im.is_raw_key_pressed(pygame.K_UP):
                self._shy -= 1.0 * dt
            if im.is_raw_key_pressed(pygame.K_DOWN):
                self._shy += 1.0 * dt
            self._shx = max(-2.0, min(2.0, self._shx))
            self._shy = max(-2.0, min(2.0, self._shy))
        elif self._mode == 4:  # COMPOSITE — translate then rotate
            held = pygame.key.get_pressed()
            if held[pygame.K_LEFT]:
                self._tx -= speed
            if held[pygame.K_RIGHT]:
                self._tx += speed
            if im.is_raw_key_pressed(pygame.K_UP):
                self._angle += 90.0 * dt
            if im.is_raw_key_pressed(pygame.K_DOWN):
                self._angle -= 90.0 * dt
            self._tx = max(20, min(300, self._tx))
            self._angle %= 360.0

    def _transform_point(self, pt: tuple[float, float]) -> tuple[float, float]:
        x, y = pt
        if self._mode == 0:
            return (x + self._tx, y + self._ty)
        elif self._mode == 1:
            rad = math.radians(self._angle)
            c, s = math.cos(rad), math.sin(rad)
            return (x * c - y * s + self._tx, x * s + y * c + self._ty)
        elif self._mode == 2:
            return (x * self._sx + self._tx, y * self._sy + self._ty)
        elif self._mode == 3:
            return (x + self._shx * y + self._tx, y + self._shy * x + self._ty)
        elif self._mode == 4:
            rad = math.radians(self._angle)
            c, s = math.cos(rad), math.sin(rad)
            rx = x * c - y * s
            ry = x * s + y * c
            return (rx + self._tx, ry + self._ty)
        return (x, y)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "TRANSFORM LAB", "UNIT II/III")

        # Grid
        for x in range(0, settings.INTERNAL_WIDTH, 32):
            pygame.draw.line(surface, (20, 20, 40), (x, 0), (x, settings.INTERNAL_HEIGHT), 1)
        for y in range(0, settings.INTERNAL_HEIGHT, 32):
            pygame.draw.line(surface, (20, 20, 40), (0, y), (settings.INTERNAL_WIDTH, y), 1)

        # Axis indicator
        center = (160, 100)
        pygame.draw.line(surface, (60, 60, 100), center, (center[0] + 40, center[1]), 1)
        pygame.draw.line(surface, (60, 60, 100), center, (center[0], center[1] + 40), 1)

        # Original shape (ghost)
        orig_pts = [(160 + x, 100 + y) for x, y in SHAPE_PTS]
        pygame.draw.polygon(surface, (40, 40, 60), orig_pts, 1)

        # Transformed shape
        tpts = [self._transform_point(p) for p in SHAPE_PTS]
        pygame.draw.polygon(surface, (80, 200, 255), tpts, 2)
        # Fill with alpha-like effect
        pygame.draw.polygon(surface, (80, 200, 255, 60), tpts, 1)

        # Label
        label = self._font_medium.render(f"  Mode: {MODE_NAMES[self._mode]}  ", True, COLOR_HIGHLIGHT)
        surface.blit(label, (4, 24))

        # Matrix info
        if self._show_matrix:
            matrix_lines = self._build_matrix_lines()
            for i, line in enumerate(matrix_lines):
                txt = self._font_small.render(line, True, COLOR_ACCENT)
                surface.blit(txt, (4, 44 + i * 14))

        # Current values
        val_lines = self._build_value_lines()
        for i, line in enumerate(val_lines):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (4, 110 + i * 14))

        # Controls
        controls = self._build_controls_text()
        ct = self._font_small.render(controls, True, COLOR_TEXT)
        surface.blit(ct, (4, 190))

        # Status
        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, settings.INTERNAL_HEIGHT - 20))

        draw_bottom_bar(surface, f"MODE: {MODE_NAMES[self._mode]}")

    def _build_matrix_lines(self) -> list[str]:
        if self._mode == 0:
            return [
                "[1  0  tx]      [1  0  {:.0f}]".format(self._tx),
                "[0  1  ty]  =   [0  1  {:.0f}]".format(self._ty),
                "[0  0   1]      [0  0   1]",
            ]
        elif self._mode == 1:
            rad = math.radians(self._angle)
            c, s = math.cos(rad), math.sin(rad)
            return [
                "[cos -sin  0]    [{:.2f}  {:.2f}  0]".format(c, -s),
                "[sin  cos  0]  = [{:.2f}  {:.2f}  0]".format(s, c),
                "[ 0    0   1]    [ 0     0    1]",
            ]
        elif self._mode == 2:
            return [
                "[sx  0   0]     [{:.2f}  0    0]".format(self._sx),
                "[ 0  sy  0]  =  [ 0   {:.2f}  0]".format(self._sy),
                "[ 0   0   1]     [ 0    0    1]",
            ]
        elif self._mode == 3:
            return [
                "[1  shx  0]     [1    {:.2f}  0]".format(self._shx),
                "[shy 1   0]  =  [{:.2f}   1    0]".format(self._shy),
                "[ 0   0   1]     [ 0     0    1]",
            ]
        elif self._mode == 4:
            rad = math.radians(self._angle)
            c, s = math.cos(rad), math.sin(rad)
            return [
                f"Rot then Translate:",
                f"  tx={self._tx:.0f}  ty={self._ty:.0f}",
                f"  cos={c:.2f}  sin={s:.2f}  angle={self._angle:.0f}deg",
                f"  [Composite matrix not shown — see paper]",
            ]
        return []

    def _build_value_lines(self) -> list[str]:
        if self._mode == 0:
            return [f"Position: ({self._tx:.0f}, {self._ty:.0f})"]
        elif self._mode == 1:
            return [f"Angle: {self._angle:.1f}deg", f"Radians: {math.radians(self._angle):.3f}"]
        elif self._mode == 2:
            return [f"Scale X: {self._sx:.2f}", f"Scale Y: {self._sy:.2f}"]
        elif self._mode == 3:
            return [f"Shear X: {self._shx:.2f}", f"Shear Y: {self._shy:.2f}"]
        elif self._mode == 4:
            return [f"Translation: ({self._tx:.0f}, {self._ty:.0f})",
                    f"Rotation: {self._angle:.1f}deg"]
        return []

    def _build_controls_text(self) -> str:
        if self._mode == 0:
            return "  Arrows: translate  |  TAB: mode  |  N: matrix  |  R: reset"
        elif self._mode == 1:
            return "  LEFT/RIGHT: rotate  |  TAB: mode  |  N: matrix  |  R: reset"
        elif self._mode == 2:
            return "  LEFT/RIGHT: scale  |  TAB: mode  |  N: matrix  |  R: reset"
        elif self._mode == 3:
            return "  LEFT/RIGHT: shear X  |  UP/DOWN: shear Y  |  TAB: mode  |  N: matrix  |  R: reset"
        elif self._mode == 4:
            return "  LEFT/RIGHT: translate X  |  UP/DOWN: rotate  |  TAB: mode  |  N: matrix  |  R: reset"
        return ""
