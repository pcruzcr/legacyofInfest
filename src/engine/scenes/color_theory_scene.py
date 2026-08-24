"""
ColorTheoryScene — Interactive Color Spaces & Alpha Blending Laboratory

Teaches Unit V concepts:
  - RGB, HSV, HSL, CMYK color spaces and conversions
  - Step-by-step algorithm visualization (RGB->HSV, etc.)
  - Alpha blending formula: out = src*alpha + dst*(1-alpha)
  - Tinting and color manipulation

Modes:
  0: RGB explorer — adjust R/G/B sliders, see live preview + hex
  1: HSV explorer — adjust H/S/V, see step-by-step conversion
  2: HSL explorer — adjust H/S/L, compare with HSV
  3: CMYK explorer — adjust C/M/Y/K, see relationship to RGB
  4: Alpha Blend — two layers with alpha slider, formula visible
  5: Challenge — "Achieve the target color" exercise

Controls:
  LEFT/RIGHT    — adjust primary parameter (value depends on mode)
  UP/DOWN       — adjust secondary parameter
  TAB           — cycle modes
  R             — reset / new challenge
  ESC           — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.i18n import _
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    draw_bottom_bar,
    draw_top_bar,
)
from src.engine.scenes.demo_layout import TOP_BAR_H
from src.engine.ui.theme import font
from src.framework.processing.color_tools import ColorTools

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = [
    _("RGB EXPLORER"),
    _("HSV EXPLORER"),
    _("HSL EXPLORER"),
    _("CMYK EXPLORER"),
    _("ALPHA BLEND"),
    _("CHALLENGE"),
]

CHANNEL_COLORS = [(255, 60, 60), (60, 200, 60), (60, 60, 255), (200, 200, 60)]
SLIDER_H = 10
SLIDER_GAP = 4

# ── Escala de autoría → pantalla (AUD-094) ─────────────────────────
#
# Los catorce deslizadores de esta escena están escritos con `x = 10` y
# `w = 300`: el ancho completo de una pantalla de 320 px. Sobre los 800x600
# reales ocupaban el 38 % del ancho, pegados al borde izquierdo, y el
# contenido entero cabía en x[4,315] y[33,163] —dos de nueve celdas—.
#
# En vez de tocar los catorce sitios se escala aquí, que es por donde pasan
# todos. `_ESCALA_X` es la razón entre el ancho real y el de autoría.
_ESCALA_X: float = settings.INTERNAL_WIDTH / 320.0
#: Alto de un deslizador ya escalado, y separación entre filas.
SLIDER_H_REAL: int = max(SLIDER_H, int(SLIDER_H * _ESCALA_X * 0.7))
#: Salto vertical entre filas de deslizadores, en píxeles de pantalla.
FILA: int = SLIDER_H_REAL + 16
#: Alto del tarjetón de color. Es el «elemento» de esta escena: lo que el
#: estudiante cambia y mira. Antes medía 44 px de alto sobre 600.
_ALTO_TARJETON: int = 96


def _ex(valor: float) -> int:
    """Una coordenada o longitud horizontal de autoría, en pantalla."""
    return int(valor * _ESCALA_X)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _draw_slider(surf: pygame.Surface, x: int, y: int, w: int,
                 val: float, color: tuple[int, int, int],
                 label: str) -> None:
    """Dibuja un deslizador. `x` y `w` van en unidades de autoría (320)."""
    x = _ex(x)
    w = _ex(w)
    alto = SLIDER_H_REAL
    pygame.draw.rect(surf, (40, 40, 60), (x, y, w, alto))
    fill_w = int(w * val)
    if fill_w > 0:
        pygame.draw.rect(surf, color, (x, y, fill_w, alto))
    pygame.draw.rect(surf, (100, 100, 140), (x, y, w, alto), 1)
    dot_x = x + fill_w
    pygame.draw.circle(surf, (255, 255, 255), (dot_x, y + alto // 2), max(4, alto // 2))


def _draw_gradient_bar(surf: pygame.Surface, x: int, y: int, w: int, h: int,
                       colors: list[tuple[int, int, int]]) -> None:
    steps = len(colors)
    if steps < 2:
        return
    bw = max(1, w // (steps - 1))
    for i in range(steps - 1):
        c0 = colors[i]
        c1 = colors[i + 1]
        for j in range(bw):
            t = j / bw
            r = int(c0[0] + (c1[0] - c0[0]) * t)
            g = int(c0[1] + (c1[1] - c0[1]) * t)
            b = int(c0[2] + (c1[2] - c0[2]) * t)
            px = x + i * bw + j
            if px < x + w:
                pygame.draw.line(surf, (r, g, b), (px, y), (px, y + h - 1))


class ColorTheoryScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._r: int = 128
        self._g: int = 64
        self._b: int = 200
        self._h: float = 240.0
        self._s: float = 0.7
        self._v: float = 0.8
        self._lightness: float = 0.5
        self._c: float = 0.3
        self._m: float = 0.6
        self._y: float = 0.1
        self._k: float = 0.2
        self._alpha: float = 0.5
        self._checker_surf: pygame.Surface | None = None
        self._blended_surf: pygame.Surface | None = None
        self._top_surf: pygame.Surface | None = None
        self._step_index: int = 0
        self._challenge_target: tuple[int, int, int] = (0, 0, 0)
        self._challenge_attempts: int = 0
        self._show_steps: bool = False
        self._status_msg: str = ""
        self._status_timer: float = 0.0

        self._font_small = font(FONT_SMALL)
        self._font_medium = font(FONT_MEDIUM)

        self._init_challenge()

    def _init_challenge(self) -> None:
        import random
        self._challenge_target = (
            random.randint(20, 235),
            random.randint(20, 235),
            random.randint(20, 235),
        )
        self._r = 128
        self._g = 128
        self._b = 128
        self._challenge_attempts = 0

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _sync_rgb_from_hsv(self) -> None:
        self._r, self._g, self._b = ColorTools.hsv_to_rgb(self._h, self._s, self._v)

    def _sync_rgb_from_hsl(self) -> None:
        self._r, self._g, self._b = ColorTools.hsl_to_rgb(self._h, self._s, self._lightness)

    def _sync_rgb_from_cmyk(self) -> None:
        self._r, self._g, self._b = ColorTools.cmyk_to_rgb(self._c, self._m, self._y, self._k)

    def _sync_hsv_from_rgb(self) -> None:
        self._h, self._s, self._v = ColorTools.rgb_to_hsv(self._r, self._g, self._b)

    def _sync_hsl_from_rgb(self) -> None:
        self._h, self._s, self._lightness = ColorTools.rgb_to_hsl(self._r, self._g, self._b)

    def _sync_cmyk_from_rgb(self) -> None:
        self._c, self._m, self._y, self._k = ColorTools.rgb_to_cmyk(self._r, self._g, self._b)

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._status_timer > 0:
            self._status_timer -= dt
            if self._status_timer <= 0:
                self._status_msg = ""

        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._status_msg = f"Mode: {MODE_NAMES[self._mode]}"
            self._status_timer = 1.5
            self._show_steps = False

        if im.is_raw_key_pressed(pygame.K_r):
            if self._mode == 5:
                self._init_challenge()
                self._status_msg = "New challenge!"
                self._status_timer = 2.0
            else:
                self._r, self._g, self._b = 128, 128, 128
                self._h, self._s, self._v = 0.0, 0.0, 0.5
                self._lightness = 0.5
                self._c, self._m, self._y, self._k = 0.0, 0.0, 0.0, 0.0
                self._alpha = 0.5
                self._step_index = 0

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        step = 0.05 if not im.is_action_held(Action.DASH) else 1.0
        int_step = 5 if not im.is_action_held(Action.DASH) else 15

        if self._mode == 0:
            if im.is_action_held(Action.MOVE_RIGHT):
                self._r = min(255, self._r + int_step)
            if im.is_action_held(Action.MOVE_LEFT):
                self._r = max(0, self._r - int_step)
            if im.is_action_held(Action.JUMP):
                self._g = min(255, self._g + int_step)
            if im.is_action_held(Action.CROUCH):
                self._g = max(0, self._g - int_step)
            if im.is_raw_key_pressed(pygame.K_e):
                self._b = min(255, self._b + int_step)
            if im.is_raw_key_pressed(pygame.K_q):
                self._b = max(0, self._b - int_step)
            self._sync_hsv_from_rgb()
            self._sync_hsl_from_rgb()
            self._sync_cmyk_from_rgb()

        elif self._mode == 1:
            if im.is_action_held(Action.MOVE_RIGHT):
                self._h = (self._h + 3) % 360
            if im.is_action_held(Action.MOVE_LEFT):
                self._h = (self._h - 3) % 360
            if im.is_action_held(Action.JUMP):
                self._s = min(1.0, self._s + step)
            if im.is_action_held(Action.CROUCH):
                self._s = max(0.0, self._s - step)
            if im.is_raw_key_pressed(pygame.K_e):
                self._v = min(1.0, self._v + step)
            if im.is_raw_key_pressed(pygame.K_q):
                self._v = max(0.0, self._v - step)
            if im.is_action_just_pressed(Action.DASH):
                self._show_steps = not self._show_steps
            self._sync_rgb_from_hsv()
            self._sync_hsl_from_rgb()
            self._sync_cmyk_from_rgb()

        elif self._mode == 2:
            if im.is_action_held(Action.MOVE_RIGHT):
                self._h = (self._h + 3) % 360
            if im.is_action_held(Action.MOVE_LEFT):
                self._h = (self._h - 3) % 360
            if im.is_action_held(Action.JUMP):
                self._s = min(1.0, self._s + step)
            if im.is_action_held(Action.CROUCH):
                self._s = max(0.0, self._s - step)
            if im.is_raw_key_pressed(pygame.K_e):
                self._lightness = min(1.0, self._lightness + step)
            if im.is_raw_key_pressed(pygame.K_q):
                self._lightness = max(0.0, self._lightness - step)
            if im.is_action_just_pressed(Action.DASH):
                self._show_steps = not self._show_steps
            self._sync_rgb_from_hsl()
            self._sync_hsv_from_rgb()
            self._sync_cmyk_from_rgb()

        elif self._mode == 3:
            if im.is_action_held(Action.MOVE_RIGHT):
                self._c = min(1.0, self._c + step)
            if im.is_action_held(Action.MOVE_LEFT):
                self._c = max(0.0, self._c - step)
            if im.is_action_held(Action.JUMP):
                self._m = min(1.0, self._m + step)
            if im.is_action_held(Action.CROUCH):
                self._m = max(0.0, self._m - step)
            if im.is_raw_key_pressed(pygame.K_e):
                self._y = min(1.0, self._y + step)
            if im.is_raw_key_pressed(pygame.K_q):
                self._y = max(0.0, self._y - step)
            if im.is_raw_key_pressed(pygame.K_w):
                self._k = min(1.0, self._k + step)
            if im.is_raw_key_pressed(pygame.K_s):
                self._k = max(0.0, self._k - step)
            self._sync_rgb_from_cmyk()
            self._sync_hsv_from_rgb()
            self._sync_hsl_from_rgb()

        elif self._mode == 4:
            if im.is_action_held(Action.MOVE_RIGHT):
                self._alpha = min(1.0, self._alpha + step)
            if im.is_action_held(Action.MOVE_LEFT):
                self._alpha = max(0.0, self._alpha - step)
            if im.is_action_held(Action.JUMP):
                self._r = min(255, self._r + int_step)
            if im.is_action_held(Action.CROUCH):
                self._r = max(0, self._r - int_step)

        elif self._mode == 5:
            if im.is_action_held(Action.MOVE_RIGHT):
                self._r = min(255, self._r + int_step)
            if im.is_action_held(Action.MOVE_LEFT):
                self._r = max(0, self._r - int_step)
            if im.is_action_held(Action.JUMP):
                self._g = min(255, self._g + int_step)
            if im.is_action_held(Action.CROUCH):
                self._g = max(0, self._g - int_step)
            if im.is_raw_key_pressed(pygame.K_e):
                self._b = min(255, self._b + int_step)
            if im.is_raw_key_pressed(pygame.K_q):
                self._b = max(0, self._b - int_step)
            if im.is_action_just_pressed(Action.DASH):
                diff = abs(self._r - self._challenge_target[0])
                diff += abs(self._g - self._challenge_target[1])
                diff += abs(self._b - self._challenge_target[2])
                self._challenge_attempts += 1
                if diff < 25:
                    self._status_msg = f"CORRECT! ({self._challenge_attempts} tries)"
                    self._status_timer = 3.0
                    self._init_challenge()
                else:
                    self._status_msg = f"Keep trying — diff={diff:.0f} (target < 25)"
                    self._status_timer = 2.0

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, f"COLOR THEORY — {MODE_NAMES[self._mode]}", "UNIT V")

        cr, cg, cb = self._r, self._g, self._b
        hex_str = _rgb_to_hex(cr, cg, cb)

        # Color swatch (compact)
        swatch_rect = pygame.Rect(_ex(4), TOP_BAR_H + 6, _ex(312), _ALTO_TARJETON)
        pygame.draw.rect(surface, (cr, cg, cb), swatch_rect)
        pygame.draw.rect(surface, (150, 150, 150), swatch_rect, 1)

        hex_label = self._font_medium.render(f"  RGB: ({cr:3d}, {cg:3d}, {cb:3d})  {hex_str}", True, COLOR_HIGHLIGHT)
        surface.blit(hex_label, (_ex(8), swatch_rect.bottom + 6))

        info_y = swatch_rect.bottom + 12 + hex_label.get_height()

        if self._mode == 0:
            self._draw_rgb_ui(surface, info_y)
            self._draw_all_space_readouts(surface, info_y + FILA * 3)

        elif self._mode == 1:
            self._draw_hsv_ui(surface, info_y)
            if self._show_steps:
                self._draw_hsv_conversion_steps(surface, info_y + FILA * 3)
            else:
                self._draw_all_space_readouts(surface, info_y + FILA * 3)

        elif self._mode == 2:
            self._draw_hsl_ui(surface, info_y)
            if self._show_steps:
                self._draw_hsl_conversion_steps(surface, info_y + FILA * 3)
            else:
                self._draw_all_space_readouts(surface, info_y + FILA * 3)

        elif self._mode == 3:
            self._draw_cmyk_ui(surface, info_y)
            self._draw_all_space_readouts(surface, info_y + FILA * 4)

        elif self._mode == 4:
            self._draw_alpha_blend_ui(surface, info_y)
            self._draw_alpha_formula(surface, info_y + FILA * 4)

        elif self._mode == 5:
            self._draw_challenge_ui(surface, info_y)

        # Status
        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, BOTTOM_BAR_Y - 16))

        draw_bottom_bar(surface, (
            "  [LEFT/RIGHT] adj  [UP/DOWN] adj2  [E/Q] adj3  "
            "[TAB] mode  [SHIFT] step view  [R] reset  [ESC] exit"
        ))

    def _draw_rgb_ui(self, surface: pygame.Surface, y: int) -> None:
        _draw_slider(surface, 10, y, 300, self._r / 255, CHANNEL_COLORS[0], "R")
        _draw_slider(surface, 10, y + FILA * 1, 300, self._g / 255, CHANNEL_COLORS[1], "G")
        _draw_slider(surface, 10, y + FILA * 2, 300, self._b / 255, CHANNEL_COLORS[2], "B")

    def _draw_hsv_ui(self, surface: pygame.Surface, y: int) -> None:
        _draw_slider(surface, 10, y, 300, self._h / 360, (255, 200, 100), "H")
        _draw_slider(surface, 10, y + FILA * 1, 300, self._s, (200, 100, 200), "S")
        _draw_slider(surface, 10, y + FILA * 2, 300, self._v, (100, 200, 255), "V")
        hint = self._font_small.render(_("SHIFT to toggle step-by-step algorithm"), True, COLOR_ACCENT)
        surface.blit(hint, (10, y + 38))
        surface.blit(hint, (10, y + 38))

    def _draw_hsl_ui(self, surface: pygame.Surface, y: int) -> None:
        _draw_slider(surface, 10, y, 300, self._h / 360, (255, 200, 100), "H")
        _draw_slider(surface, 10, y + FILA * 1, 300, self._s, (200, 100, 200), "S")
        _draw_slider(surface, 10, y + FILA * 2, 300, self._lightness, (100, 200, 200), "L")
        hint = self._font_small.render(_("SHIFT to toggle step-by-step algorithm"), True, COLOR_ACCENT)
        surface.blit(hint, (10, y + 38))
        surface.blit(hint, (10, y + 38))

    def _draw_cmyk_ui(self, surface: pygame.Surface, y: int) -> None:
        _draw_slider(surface, 10, y, 300, self._c, CHANNEL_COLORS[3], "C")
        _draw_slider(surface, 10, y + FILA * 1, 300, self._m, (200, 80, 200), "M")
        _draw_slider(surface, 10, y + FILA * 2, 300, self._y, (200, 200, 80), "Y")
        _draw_slider(surface, 10, y + FILA * 3, 300, self._k, (80, 80, 80), "K")

    def _draw_all_space_readouts(self, surface: pygame.Surface, y: int) -> None:
        lines = [
            f"HSV: H={self._h:.0f}° S={self._s:.3f} V={self._v:.3f}",
            f"HSL: H={self._h:.0f}° S={self._s:.3f} L={self._lightness:.3f}",
            f"CMYK: C={self._c:.3f} M={self._m:.3f} Y={self._y:.3f} K={self._k:.3f}",
        ]
        for i, line in enumerate(lines):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (10, y + i * 11))

    def _draw_hsv_conversion_steps(self, surface: pygame.Surface, y: int) -> None:
        rn, gn, bn = self._r / 255, self._g / 255, self._b / 255
        mx = max(rn, gn, bn)
        mn = min(rn, gn, bn)
        diff = mx - mn
        steps = [
            f"Step 1:  R'={rn:.3f}  G'={gn:.3f}  B'={bn:.3f}  (/{255})",
            f"Step 2:  max={mx:.3f}  min={mn:.3f}  delta={diff:.3f}",
        ]
        if diff > 0.001:
            if mx == rn:
                h_calc = 60 * (((gn - bn) / diff) % 6)
            elif mx == gn:
                h_calc = 60 * (((bn - rn) / diff) + 2)
            else:
                h_calc = 60 * (((rn - gn) / diff) + 4)
            s_calc = diff / mx if mx > 0.001 else 0
            steps.append(f"Step 3:  H={h_calc:.1f}° = hue angle from dominant channel")
            steps.append(f"Step 4:  S={s_calc:.3f} = delta / max  ({diff:.3f}/{mx:.3f})")
            steps.append(f"Step 5:  V={mx:.3f} = max(R', G', B')  (value = intensity)")
        else:
            steps.append("Step 3:  delta≈0  =>  H=0°, S=0%  (achromatic)")
            steps.append(f"Step 4:  V={mx:.3f} (only value carries info)")
        for i, line in enumerate(steps):
            txt = self._font_small.render(line, True, COLOR_ACCENT if i < 2 else COLOR_TEXT)
            surface.blit(txt, (10, y + i * 11))

    def _draw_hsl_conversion_steps(self, surface: pygame.Surface, y: int) -> None:
        rn, gn, bn = self._r / 255, self._g / 255, self._b / 255
        mx = max(rn, gn, bn)
        mn = min(rn, gn, bn)
        diff = mx - mn
        L_val = (mx + mn) / 2
        steps = [
            f"Step 1:  R'={rn:.3f}  G'={gn:.3f}  B'={bn:.3f}",
            f"Step 2:  max={mx:.3f}  min={mn:.3f}  delta={diff:.3f}",
            f"Step 3:  L={L_val:.3f} = (max+min)/2  (lightness)",
        ]
        if diff > 0.001:
            s_calc = diff / (1 - abs(2 * L_val - 1))
            steps.append(f"Step 4:  S={s_calc:.3f} = delta/(1-|2L-1|)")
            steps.append("Step 5:  S!=0 => H calculated from dominant channel (same as HSV)")
        else:
            steps.append("Step 4:  delta≈0  =>  S=0%  (achromatic)")
        for i, line in enumerate(steps):
            txt = self._font_small.render(line, True, COLOR_ACCENT if i < 3 else COLOR_TEXT)
            surface.blit(txt, (10, y + i * 11))

    def _draw_alpha_blend_ui(self, surface: pygame.Surface, y: int) -> None:
        # Top layer color
        lr, lg, lb = self._r, self._g, self._b
        # Bottom layer: fixed checkerboard
        bw, bh = 16, 16
        if self._checker_surf is None or self._checker_surf.get_size() != (160, 40):
            self._checker_surf = pygame.Surface((160, 40))
            for cx in range(0, 160, bw):
                for cy in range(0, 40, bh):
                    c = (200, 200, 200) if ((cx // bw) + (cy // bh)) % 2 == 0 else (100, 100, 100)
                    pygame.draw.rect(self._checker_surf, c, (cx, cy, bw, bh))
        surface.blit(self._checker_surf, (80, y))

        if self._blended_surf is None or self._blended_surf.get_size() != (160, 40):
            self._blended_surf = pygame.Surface((160, 40), pygame.SRCALPHA)
        if self._top_surf is None or self._top_surf.get_size() != (160, 40):
            self._top_surf = pygame.Surface((160, 40))
        self._blended_surf.blit(self._checker_surf, (0, 0))
        self._top_surf.fill((lr, lg, lb))
        self._top_surf.set_alpha(int(self._alpha * 255))
        self._blended_surf.blit(self._top_surf, (0, 0))
        surface.blit(self._blended_surf, (80, y + 45))

        # Labels
        labels = [
            "Layer A (checker): fixed background",
            f"Layer B (color):  RGB({lr},{lg},{lb})  alpha={self._alpha:.2f}",
        ]
        for i, line in enumerate(labels):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (10, y + 90 + i * 14))

        _draw_slider(surface, 80, y + FILA * 6, 160, self._alpha, (200, 200, 255), "Alpha")

    def _draw_alpha_formula(self, surface: pygame.Surface, y: int) -> None:
        formula = "out = src * alpha + dst * (1 - alpha)"
        txt = self._font_small.render(formula, True, COLOR_HIGHLIGHT)
        surface.blit(txt, (10, y))

        a = self._alpha
        r, g, b = self._r, self._g, self._b
        lines = [
            f"= ({r:3d},{g:3d},{b:3d}) * {a:.2f} + checker * {1 - a:.2f}",
        ]
        for i, line in enumerate(lines):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (10, y + 14 + i * 12))

    def _draw_challenge_ui(self, surface: pygame.Surface, y: int) -> None:
        t = self._challenge_target
        tw, th = 50, 34
        pygame.draw.rect(surface, t, (120, y, tw, th))
        pygame.draw.rect(surface, (255, 255, 255), (120, y, tw, th), 1)
        hex_t = _rgb_to_hex(*t)
        pygame.draw.rect(surface, (self._r, self._g, self._b), (190, y, tw, th))
        pygame.draw.rect(surface, (255, 255, 255), (190, y, tw, th), 1)

        labels = self._font_small.render("TARGET  YOURS", True, COLOR_HIGHLIGHT)
        surface.blit(labels, (118, y - 10))
        hex_lbl = self._font_small.render(f"{hex_t}  {_rgb_to_hex(self._r, self._g, self._b)}", True, COLOR_ACCENT)
        surface.blit(hex_lbl, (118, y + th + 2))

        self._draw_rgb_ui(surface, y + 46)
        diff = abs(self._r - t[0]) + abs(self._g - t[1]) + abs(self._b - t[2])
        info = self._font_small.render(
            f"Attempts: {self._challenge_attempts}  Diff: {diff:.0f}  [SPACE] submit", True, COLOR_TEXT)
        surface.blit(info, (10, y + 108))

