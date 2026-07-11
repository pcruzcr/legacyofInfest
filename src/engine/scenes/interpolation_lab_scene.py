"""
InterpolationLabScene — Interactive Interpolation Laboratory

Teaches Unit III/IV concepts:
  - Linear interpolation (lerp)
  - Easing functions (quad, cubic, bounce, elastic, sine)
  - Keyframe animation visualization
  - Overshoot / damping

Controls:
  LEFT/RIGHT  — change t value
  UP/DOWN     — cycle easing function
  SPACE       — animate t automatically
  TAB         — cycle display mode
  R           — reset
  ESC         — back to demo menu
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT,
    COLOR_DIVIDER, FONT_SMALL, FONT_MEDIUM,
    draw_top_bar, draw_bottom_bar,
    save_png,
)
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import (
    lerp, ease_in_quad, ease_out_quad, ease_in_out_quad,
    ease_in_cubic, ease_out_cubic, ease_out_bounce,
    ease_out_elastic, ease_in_sine, ease_out_sine,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["LERP (LINEAR)", "EASING CURVES", "KEYFRAME ANIM"]

EASING_FUNCS: list[tuple[str, Callable[[float], float]]] = [
    ("Linear", lambda t: t),
    ("In Quad", ease_in_quad),
    ("Out Quad", ease_out_quad),
    ("InOut Quad", ease_in_out_quad),
    ("In Cubic", ease_in_cubic),
    ("Out Cubic", ease_out_cubic),
    ("Out Bounce", ease_out_bounce),
    ("Out Elastic", ease_out_elastic),
    ("In Sine", ease_in_sine),
    ("Out Sine", ease_out_sine),
]


class InterpolationLabScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._t: float = 0.0
        self._easing_idx: int = 0
        self._auto_animate: bool = False
        self._anim_t: float = 0.0
        self._anim_dir: int = 1

        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

        self._status_msg: str = ""
        self._status_timer: float = 0.0

    def on_enter(self) -> None:
        self._mode = 0
        self._t = 0.0
        self._auto_animate = False

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

        # SPACE — toggle auto-animate
        if im.is_raw_key_pressed(pygame.K_SPACE):
            self._auto_animate = not self._auto_animate
            self._anim_t = self._t
            self._anim_dir = 1
            status = "Animate ON" if self._auto_animate else "Animate OFF"
            self._status_msg = status
            self._status_timer = 1.0

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._t = 0.0
            self._auto_animate = False
            self._status_msg = "Reset"
            self._status_timer = 1.0

        # S — save screenshot
        if im.is_raw_key_pressed(pygame.K_s):
            ss = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            self.draw(ss)
            path = save_png("interpolation", MODE_NAMES[self._mode].lower(), ss)
            self._status_msg = f"Saved: {path.split('/')[-1].split(chr(92))[-1]}"
            self._status_timer = 2.0

        # ESC — back
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # Mode-specific controls
        if self._auto_animate:
            self._anim_t += dt * 0.5 * self._anim_dir
            if self._anim_t >= 1.0:
                self._anim_t = 1.0
                self._anim_dir = -1
            elif self._anim_t <= 0.0:
                self._anim_t = 0.0
                self._anim_dir = 1
            self._t = self._anim_t
        else:
            if im.is_raw_key_pressed(pygame.K_LEFT):
                self._t = max(0.0, self._t - 0.02)
            if im.is_raw_key_pressed(pygame.K_RIGHT):
                self._t = min(1.0, self._t + 0.02)

        if self._mode == 1:
            if im.is_raw_key_pressed(pygame.K_UP):
                self._easing_idx = (self._easing_idx + 1) % len(EASING_FUNCS)
                self._status_msg = f"Easing: {EASING_FUNCS[self._easing_idx][0]}"
                self._status_timer = 1.5
            if im.is_raw_key_pressed(pygame.K_DOWN):
                self._easing_idx = (self._easing_idx - 1) % len(EASING_FUNCS)
                self._status_msg = f"Easing: {EASING_FUNCS[self._easing_idx][0]}"
                self._status_timer = 1.5

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "INTERPOLATION LAB", "UNIT III/IV")

        if self._mode == 0:
            self._draw_lerp(surface)
        elif self._mode == 1:
            self._draw_easing_curves(surface)
        elif self._mode == 2:
            self._draw_keyframe(surface)

        # Controls
        controls = self._build_controls_text()
        ct = self._font_small.render(controls, True, COLOR_TEXT)
        surface.blit(ct, (4, settings.INTERNAL_HEIGHT - 32))

        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, settings.INTERNAL_HEIGHT - 20))

        draw_bottom_bar(surface, f"MODE: {MODE_NAMES[self._mode]}")

    def _draw_lerp(self, surface: pygame.Surface) -> None:
        label = self._font_medium.render("  LERP: Linear Interpolation  ", True, COLOR_HIGHLIGHT)
        surface.blit(label, (4, 24))

        # Two points
        start_a = (40, 140)
        end_b = (280, 140)
        pygame.draw.circle(surface, COLOR_TEXT, start_a, 6)
        pygame.draw.circle(surface, COLOR_TEXT, end_b, 6)

        # Line
        pygame.draw.line(surface, COLOR_DIVIDER, start_a, end_b, 1)

        # Lerped point
        eased = self._t
        lx = int(lerp(float(start_a[0]), float(end_b[0]), eased))
        ly = int(lerp(float(start_a[1]), float(end_b[1]), eased))
        lerp_color = (255, 200, 80)
        pygame.draw.circle(surface, lerp_color, (lx, ly), 8)
        pygame.draw.circle(surface, (255, 255, 255), (lx, ly), 8, 1)

        # Labels
        la = self._font_small.render("A (start)", True, COLOR_TEXT)
        surface.blit(la, (start_a[0] + 10, start_a[1] - 6))
        lb = self._font_small.render("B (end)", True, COLOR_TEXT)
        surface.blit(lb, (end_b[0] + 10, end_b[1] - 6))
        lt = self._font_small.render(f"t = {self._t:.3f}", True, lerp_color)
        surface.blit(lt, (lx + 12, ly - 8))

        # Formula
        formula = self._font_small.render(
            "  lerp(A, B, t) = A + (B - A) * t", True, COLOR_ACCENT)
        surface.blit(formula, (4, 50))

        computed_x = 40.0 + (280.0 - 40.0) * self._t
        result = self._font_small.render(
            f"  = ({start_a[0]} + ({end_b[0]} - {start_a[0]}) * {self._t:.3f})"
            f"  =>  x = {computed_x:.1f}", True, COLOR_TEXT)
        surface.blit(result, (4, 66))

    def _draw_easing_curves(self, surface: pygame.Surface) -> None:
        name, func = EASING_FUNCS[self._easing_idx]
        label = self._font_medium.render(f"  EASING: {name}  ", True, COLOR_HIGHLIGHT)
        surface.blit(label, (4, 24))

        # Graph area
        gx, gy = 40, 40
        gw, gh = 260, 120
        pygame.draw.rect(surface, (10, 10, 25), (gx, gy, gw, gh), 1)

        # Axis labels
        xl = self._font_small.render("t ->", True, COLOR_ACCENT)
        surface.blit(xl, (gx + gw - 20, gy + gh - 2))
        yl = self._font_small.render("f(t)", True, COLOR_ACCENT)
        surface.blit(yl, (gx - 30, gy + 2))

        # Draw curve
        pts = []
        for i in range(gw + 1):
            t = i / gw
            v = func(t)
            px = gx + i
            py = gy + gh - int(v * gh)
            pts.append((px, py))

        if len(pts) > 1:
            pygame.draw.lines(surface, (80, 200, 255), False, pts, 2)

        # Current t marker
        mx = gx + int(self._t * gw)
        mv = func(self._t)
        my = gy + gh - int(mv * gh)
        pygame.draw.line(surface, (255, 220, 80), (mx, gy), (mx, gy + gh), 1)
        pygame.draw.circle(surface, (255, 220, 80), (mx, my), 5)

        # Diagonal reference
        pygame.draw.line(surface, (30, 30, 50), (gx, gy + gh), (gx + gw, gy), 1)

        info = self._font_small.render(
            f"  f({self._t:.2f}) = {mv:.3f}  |  "
            f"[UP/DOWN: cycle easing]  |  [SPACE: animate]", True, COLOR_TEXT)
        surface.blit(info, (4, gy + gh + 8))

    def _draw_keyframe(self, surface: pygame.Surface) -> None:
        label = self._font_medium.render("  KEYFRAME ANIMATION  ", True, COLOR_HIGHLIGHT)
        surface.blit(label, (4, 24))

        # Keyframes
        kfs = [(50, 160), (160, 60), (270, 160)]
        for kf in kfs:
            pygame.draw.circle(surface, (80, 200, 255), kf, 5)

        # Path
        if len(kfs) >= 2:
            idx, local_t = self._get_keyframe_segment(len(kfs))
            start_pt = kfs[idx]
            end_pt = kfs[(idx + 1) % len(kfs)] if idx + 1 < len(kfs) else kfs[-1]
            eased_t = self._get_eased_t(local_t)

            # Draw path lines
            for i in range(len(kfs) - 1):
                pygame.draw.line(surface, COLOR_DIVIDER, kfs[i], kfs[i + 1], 1)

            # Animated point
            lx = int(lerp(float(start_pt[0]), float(end_pt[0]), eased_t))
            ly = int(lerp(float(start_pt[1]), float(end_pt[1]), eased_t))
            pygame.draw.circle(surface, (255, 200, 80), (lx, ly), 8)
            pygame.draw.circle(surface, (255, 255, 255), (lx, ly), 8, 1)

            info = self._font_small.render(
                f"  Segment {idx}: t={local_t:.2f} (eased={eased_t:.2f})  |  "
                f"[LEFT/RIGHT: t]  |  [SPACE: animate]", True, COLOR_TEXT)
            surface.blit(info, (4, 200))

    def _get_keyframe_segment(self, n: int) -> tuple[int, float]:
        if n <= 1:
            return 0, self._t
        seg_t = self._t * (n - 1)
        idx = int(seg_t)
        local_t = seg_t - idx
        if idx >= n - 1:
            idx = n - 2
            local_t = 1.0
        return idx, local_t

    def _get_eased_t(self, t: float) -> float:
        _, func = EASING_FUNCS[self._easing_idx]
        return func(t)

    def _build_controls_text(self) -> str:
        base = "  [LEFT/RIGHT] t  |  [SPACE] animate  |  [TAB] mode  |  [R] reset"
        if self._mode == 1:
            base = "  [LEFT/RIGHT] t  |  [UP/DOWN] easing  |  [SPACE] animate  |  [TAB] mode  |  [R] reset"
        return base
