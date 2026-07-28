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

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_DIVIDER,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_MEDIUM,
    FONT_SMALL,
    draw_bottom_bar,
    draw_top_bar,
    save_png,
)
from src.engine.scenes.demo_layout import (
    AUTHORED_H,
    AUTHORED_W,
    Lienzo,
    area_de_contenido,
)
from src.engine.utils.asset_loader import AssetLoader
from src.engine.utils.math_utils import (
    ease_in_cubic,
    ease_in_out_quad,
    ease_in_quad,
    ease_in_sine,
    ease_out_bounce,
    ease_out_cubic,
    ease_out_elastic,
    ease_out_quad,
    ease_out_sine,
    lerp,
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
    """Laboratorio de interpolación: lerp, curvas de suavizado y claves.

    AUD-094 — los tres modos dibujaban en la esquina
    ------------------------------------------------
    Los extremos del lerp estaban en (40, 140) y (280, 140), la gráfica de
    suavizado medía 260x120 en (40, 40) y los fotogramas clave iban de x=50 a
    x=270: coordenadas de una pantalla de 320x224. Medido sobre 800x600, el
    contenido cabía en x[8,322] —el 39 % del ancho— y tres de las nueve
    celdas de la rejilla, ninguna de ellas la central.
    """

    # -- geometría de autoría (320x224) ----------------------------
    #: Extremos del segmento del modo LERP.
    _LERP_A = (40, 150)
    _LERP_B = (280, 150)
    #: Los tres fotogramas clave del tercer modo.
    _KEYFRAMES = ((50, 170), (160, 60), (270, 170))
    #: Alto reservado arriba para el rótulo y la fórmula.
    _ALTO_CABECERA = 78
    #: Alto reservado abajo para la línea de lectura y los controles.
    _ALTO_PIE = 96

    def _lienzo(self) -> Lienzo:
        """El lienzo de autoría sobre la franja central del área útil."""
        return Lienzo(AUTHORED_W, AUTHORED_H, area=self._franja())

    def _franja(self) -> pygame.Rect:
        area = area_de_contenido()
        alto = max(120, area.h - self._ALTO_CABECERA - self._ALTO_PIE)
        return pygame.Rect(area.x, area.y + self._ALTO_CABECERA, area.w, alto)

    def _rect_grafica(self) -> pygame.Rect:
        """Rectángulo de la gráfica f(t), centrado en la franja."""
        franja = self._franja()
        ancho = int(franja.w * 0.78)
        return pygame.Rect(
            franja.centerx - ancho // 2, franja.y, ancho, franja.h,
        )

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

    def rect_principal(self) -> pygame.Rect:
        """Dónde vive el elemento que el estudiante mira y manipula.

        Lo consume `tests/test_demo_centering.py`, que exige que esté
        centrado horizontalmente en el área útil. Es la forma de dejar
        escrito, y comprobado en cada ejecución de la suite, el defecto
        AUD-094: el elemento vivía en la esquina superior izquierda porque
        estas escenas se escribieron para una pantalla de 320x224.
        """
        return self._franja()

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
        surface.blit(ct, (4, BOTTOM_BAR_Y - 28))

        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, BOTTOM_BAR_Y - 16))

        draw_bottom_bar(surface, f"MODE: {MODE_NAMES[self._mode]}")

    def _draw_lerp(self, surface: pygame.Surface) -> None:
        lienzo = self._lienzo()
        area = area_de_contenido()
        label = self._font_medium.render("LERP: Linear Interpolation", True, COLOR_HIGHLIGHT)
        surface.blit(label, (area.x + 8, area.y + 6))

        # Los dos extremos, en unidades de autoría
        ax, ay = self._LERP_A
        bx, by = self._LERP_B
        start_a = lienzo.p(ax, ay)
        end_b = lienzo.p(bx, by)
        radio = lienzo.l(6)
        pygame.draw.circle(surface, COLOR_TEXT, start_a, radio)
        pygame.draw.circle(surface, COLOR_TEXT, end_b, radio)
        pygame.draw.line(surface, COLOR_DIVIDER, start_a, end_b, max(1, lienzo.l(1)))

        # El punto interpolado. La interpolación se hace en unidades de
        # autoría —los mismos números que salen en la fórmula de abajo— y sólo
        # después se lleva a pantalla.
        eased = self._t
        px = lerp(float(ax), float(bx), eased)
        py = lerp(float(ay), float(by), eased)
        punto = lienzo.p(px, py)
        lerp_color = (255, 200, 80)
        radio_punto = lienzo.l(8)
        pygame.draw.circle(surface, lerp_color, punto, radio_punto)
        pygame.draw.circle(surface, (255, 255, 255), punto, radio_punto, 1)

        la = self._font_small.render("A (start)", True, COLOR_TEXT)
        surface.blit(la, (start_a[0] - la.get_width() // 2, start_a[1] + radio + 6))
        lb = self._font_small.render("B (end)", True, COLOR_TEXT)
        surface.blit(lb, (end_b[0] - lb.get_width() // 2, end_b[1] + radio + 6))
        lt = self._font_small.render(f"t = {self._t:.3f}", True, lerp_color)
        surface.blit(lt, (punto[0] - lt.get_width() // 2, punto[1] - radio_punto - 20))

        formula = self._font_small.render(
            "lerp(A, B, t) = A + (B - A) * t", True, COLOR_ACCENT)
        surface.blit(formula, (area.x + 8, area.y + 12 + label.get_height()))

        computed_x = ax + (bx - ax) * self._t
        result = self._font_small.render(
            f"= ({ax} + ({bx} - {ax}) * {self._t:.3f})  =>  x = {computed_x:.1f}",
            True, COLOR_TEXT)
        surface.blit(result, (area.x + 8,
                              area.y + 16 + label.get_height() + formula.get_height()))

    def _draw_easing_curves(self, surface: pygame.Surface) -> None:
        name, func = EASING_FUNCS[self._easing_idx]
        label = self._font_medium.render(f"EASING: {name}", True, COLOR_HIGHLIGHT)
        surface.blit(label, (area_de_contenido().x + 8, area_de_contenido().y + 6))

        # La gráfica ocupa el área útil menos la cabecera, no un rectángulo
        # de 260x120 escrito para una pantalla de 320 (AUD-094).
        area = area_de_contenido()
        g = self._rect_grafica()
        gx, gy, gw, gh = g.x, g.y, g.w, g.h
        pygame.draw.rect(surface, (10, 10, 25), g, 1)

        xl = self._font_small.render("t ->", True, COLOR_ACCENT)
        surface.blit(xl, (g.right - xl.get_width() - 4, g.bottom + 4))
        yl = self._font_small.render("f(t)", True, COLOR_ACCENT)
        surface.blit(yl, (g.left + 4, g.top + 4))

        # La curva se muestrea en t ∈ [0, 1] y se lleva a la gráfica. El paso
        # es de un píxel de pantalla, así que la resolución del trazo crece
        # con la gráfica en vez de quedarse en los 260 puntos de antes.
        pts = [
            (gx + i, gy + gh - int(func(i / gw) * gh))
            for i in range(gw + 1)
        ]
        if len(pts) > 1:
            pygame.draw.lines(surface, (80, 200, 255), False, pts, 3)

        # Marca de la t actual
        mx = gx + int(self._t * gw)
        mv = func(self._t)
        my = gy + gh - int(mv * gh)
        pygame.draw.line(surface, (255, 220, 80), (mx, gy), (mx, gy + gh), 1)
        pygame.draw.circle(surface, (255, 220, 80), (mx, my), 7)

        # Diagonal de referencia: f(t) = t
        pygame.draw.line(surface, (60, 60, 90), (gx, gy + gh), (gx + gw, gy), 1)

        info = self._font_small.render(
            f"f({self._t:.2f}) = {mv:.3f}  |  "
            f"[UP/DOWN: cycle easing]  |  [SPACE: animate]", True, COLOR_TEXT)
        surface.blit(info, (area.x + 8, g.bottom + 8 + xl.get_height()))

    def _draw_keyframe(self, surface: pygame.Surface) -> None:
        area = area_de_contenido()
        label = self._font_medium.render("KEYFRAME ANIMATION", True, COLOR_HIGHLIGHT)
        surface.blit(label, (area.x + 8, area.y + 6))

        # Fotogramas clave, en unidades de autoría
        lienzo = self._lienzo()
        kfs = [lienzo.p(*k) for k in self._KEYFRAMES]
        radio_kf = lienzo.l(5)
        for kf in kfs:
            pygame.draw.circle(surface, (80, 200, 255), kf, radio_kf)

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
            radio_animado = lienzo.l(8)
            pygame.draw.circle(surface, (255, 200, 80), (lx, ly), radio_animado)
            pygame.draw.circle(surface, (255, 255, 255), (lx, ly), radio_animado, 1)

            info = self._font_small.render(
                f"  Segment {idx}: t={local_t:.2f} (eased={eased_t:.2f})  |  "
                f"[LEFT/RIGHT: t]  |  [SPACE: animate]", True, COLOR_TEXT)
            surface.blit(info, (area_de_contenido().x + 8, self._rect_grafica().bottom + 8))

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

