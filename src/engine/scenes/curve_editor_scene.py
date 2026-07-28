"""
CurveEditorScene — Interactive Curve & Spline Laboratory

Teaches Unit III concepts:
  - Bézier curves (quadratic, cubic, higher degree) via de Casteljau
  - Catmull-Rom splines (interpolating)
  - B-Spline (uniform cubic)
  - De Casteljau step-by-step animation
  - Control point manipulation

Modes:
  0: BEZIER_QUAD — Quadratic Bézier (3 control points)
  1: BEZIER_CUBIC — Cubic Bézier (4 control points)
  2: BEZIER_HIGH — Higher-degree Bézier (5+ points)
  3: CATMULL_ROM — Catmull-Rom spline (interpolating)
  4: BSPLINE — Uniform cubic B-Spline
  5: DE_CASTELJAU — Step-by-step de Casteljau animation

Controls:
  Click+drag  — move closest control point
  TAB         — cycle curve type
  1-5         — jump to mode
  R           — reset control points to default
  D           — toggle de Casteljau visualization (modes 0-2)
  +/-         — add/remove control point (modes 2, 4)
  ESC         — back to demo menu
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
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
    save_png,
)
from src.engine.scenes.demo_layout import area_de_contenido
from src.engine.utils.asset_loader import AssetLoader
from src.framework.processing.curve_tools import CurveTools

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = [
    "BEZIER_QUAD", "BEZIER_CUBIC", "BEZIER_HIGH",
    "CATMULL_ROM", "BSPLINE", "DE_CASTELJAU",
]

CTRL_PT_RADIUS = 6
CTRL_PT_COLOR = (255, 200, 80)
CTRL_PT_ACTIVE = (255, 255, 100)
CURVE_COLOR = (100, 180, 255)
CURVE_ACTIVE_COLOR = (255, 220, 80)
LERP_COLOR = (200, 100, 255)
ANNOTATION_COLOR = (150, 200, 150)
GRID_COLOR = (20, 20, 40)

N_SAMPLES = 100

# ── Área de la curva (AUD-094) ─────────────────────────────────────
#
# Esto era `pygame.Rect(4, 48, 312, 160)`: el ancho entero de una pantalla de
# 320 px. Sobre los 800x600 reales el lienzo de la curva ocupaba el 39 % del
# ancho y el 29 % del alto, arriba a la izquierda, y los puntos de control
# —que se arrastran con el ratón— quedaban tan juntos que costaba agarrarlos.
#
# Ahora el área se calcula desde el área útil. Los puntos por defecto se
# escalan con un factor **uniforme** para que la curva conserve su forma: una
# Bézier estirada en un eje ya no es la Bézier que se explicó en clase.
_MARGEN_CURVA = 20
_ALTO_CABECERA_CURVA = 44
_ALTO_INFO_CURVA = 150

_area_util = area_de_contenido()
CURVE_AREA = pygame.Rect(
    _area_util.x + _MARGEN_CURVA,
    _area_util.y + _ALTO_CABECERA_CURVA,
    _area_util.w - _MARGEN_CURVA * 2,
    max(120, _area_util.h - _ALTO_CABECERA_CURVA - _ALTO_INFO_CURVA),
)
#: Tamaño para el que se escribieron los puntos de control originales.
_AREA_AUTORIA = (312, 160)
#: Factor uniforme para llevar aquellos desplazamientos a este área.
_ESCALA_PUNTOS = min(
    CURVE_AREA.width / _AREA_AUTORIA[0], CURVE_AREA.height / _AREA_AUTORIA[1],
)


def _default_points(mode: int) -> list[tuple[float, float]]:
    """Puntos de control por defecto, centrados en el área de la curva."""
    cx, cy = CURVE_AREA.center
    k = _ESCALA_PUNTOS

    def p(dx: float, dy: float) -> tuple[float, float]:
        return (cx + dx * k, cy + dy * k)

    if mode == 0:
        return [p(-100, 50), p(0, -40), p(100, 50)]
    elif mode == 1:
        return [p(-110, 50), p(-50, -50), p(50, 40), p(110, -40)]
    elif mode in (2, 5):
        return [p(-120, 40), p(-80, -50), p(0, 20), p(60, -40), p(120, 30)]
    elif mode == 3:
        return [p(-120, 30), p(-80, -40), p(0, 10), p(80, -30), p(120, 40)]
    else:  # BSPLINE
        return [p(-130, 20), p(-80, -50), p(-20, 30),
                p(40, -40), p(100, 20), p(130, -20)]


def _lerp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _de_casteljau(
    pts: list[tuple[float, float]], t: float
) -> tuple[list[list[tuple[float, float]]], tuple[float, float]]:
    """Run full de Casteljau, return all levels and final point."""
    levels: list[list[tuple[float, float]]] = [list(pts)]
    current = list(pts)
    while len(current) > 1:
        nxt = []
        for i in range(len(current) - 1):
            nxt.append(_lerp(current[i], current[i + 1], t))
        levels.append(nxt)
        current = nxt
    return levels, current[0] if current else pts[0]


class CurveEditorScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._points: list[tuple[float, float]] = _default_points(0)
        self._drag_idx: int = -1
        self._show_casteljau: bool = False
        self._casteljau_t: float = 0.3
        self._status_msg: str = ""
        self._status_timer: float = 0.0
        self._n_samples: int = N_SAMPLES

        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)

    def _reset_to_mode(self, mode: int) -> None:
        self._mode = mode
        self._points = _default_points(mode)
        self._drag_idx = -1
        self._show_casteljau = False
        self._casteljau_t = 0.3

    def on_enter(self) -> None:
        pass

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

        # Mode switching
        if im.is_raw_key_pressed(pygame.K_TAB):
            nmi = (self._mode + 1) % len(MODE_NAMES)
            self._reset_to_mode(nmi)
            self._status_msg = f"Mode: {MODE_NAMES[nmi]}"
            self._status_timer = 1.5

        for key, mi in [(pygame.K_1, 0), (pygame.K_2, 1), (pygame.K_3, 2),
                        (pygame.K_4, 3), (pygame.K_5, 4)]:
            if im.is_raw_key_pressed(key):
                if mi < len(MODE_NAMES):
                    self._reset_to_mode(mi)
                    self._status_msg = f"Mode: {MODE_NAMES[mi]}"
                    self._status_timer = 1.5

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._reset_to_mode(self._mode)
            self._status_msg = "Reset control points"
            self._status_timer = 1.0

        # S — save screenshot
        if im.is_raw_key_pressed(pygame.K_s):
            ss = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
            self.draw(ss)
            path = save_png("curve", MODE_NAMES[self._mode].lower(), ss)
            self._status_msg = f"Saved: {path.split('/')[-1].split(chr(92))[-1]}"
            self._status_timer = 2.0

        # D — toggle de Casteljau (modes 0-2)
        if im.is_raw_key_pressed(pygame.K_d) and self._mode in (0, 1, 2):
            self._show_casteljau = not self._show_casteljau

        # +/- add/remove points
        if im.is_raw_key_pressed(pygame.K_EQUALS) or im.is_raw_key_pressed(pygame.K_PLUS):
            if self._mode in (2, 4, 5) and len(self._points) < 10:
                last = self._points[-1]
                self._points.append((last[0] + 30 * _ESCALA_PUNTOS,
                                     last[1] - 20 * _ESCALA_PUNTOS))
                self._status_msg = f"Added point ({len(self._points)} total)"
                self._status_timer = 1.0
        if im.is_raw_key_pressed(pygame.K_MINUS):
            if len(self._points) > 3:
                self._points.pop()
                self._status_msg = f"Removed point ({len(self._points)} total)"
                self._status_timer = 1.0

        # ESC
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # Mouse drag (via pygame.mouse since InputManager has no mouse property)
        buttons = pygame.mouse.get_pressed()
        mx, my = pygame.mouse.get_pos()
        scale = settings.DISPLAY_SCALE
        mx = mx // scale
        my = my // scale

        if buttons[0]:
            if self._drag_idx == -1:
                # Find closest point
                min_d = 20
                self._drag_idx = -1
                for i, (px, py) in enumerate(self._points):
                    d = (px - mx) ** 2 + (py - my) ** 2
                    if d ** 0.5 < min_d:
                        min_d = d ** 0.5
                        self._drag_idx = i
            if self._drag_idx >= 0:
                pts = list(self._points)
                px, py = pts[self._drag_idx]
                px = max(CURVE_AREA.left + 2, min(CURVE_AREA.right - 2, mx))
                py = max(CURVE_AREA.top + 2, min(CURVE_AREA.bottom - 2, my))
                pts[self._drag_idx] = (px, py)
                self._points = pts
        else:
            self._drag_idx = -1

        if self._mode == 5 and self._show_casteljau:
            # Use mouse X for t parameter
            t = (mx - CURVE_AREA.left) / max(1, CURVE_AREA.width)
            self._casteljau_t = max(0.0, min(1.0, t))

    def rect_principal(self) -> pygame.Rect:
        """Dónde vive el elemento que el estudiante mira y manipula.

        Lo consume `tests/test_demo_centering.py`, que exige que esté
        centrado horizontalmente en el área útil. Es la forma de dejar
        escrito, y comprobado en cada ejecución de la suite, el defecto
        AUD-094: el elemento vivía en la esquina superior izquierda porque
        estas escenas se escribieron para una pantalla de 320x224.
        """
        return CURVE_AREA

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, f"CURVE EDITOR — {MODE_NAMES[self._mode]}", "UNIT III")

        # Draw curve area background
        pygame.draw.rect(surface, (10, 10, 25), CURVE_AREA)
        pygame.draw.rect(surface, (40, 40, 60), CURVE_AREA, 1)

        # Draw grid
        paso_rejilla = max(8, int(20 * _ESCALA_PUNTOS))
        for gx in range(CURVE_AREA.left, CURVE_AREA.right, paso_rejilla):
            pygame.draw.line(surface, GRID_COLOR, (gx, CURVE_AREA.top),
                             (gx, CURVE_AREA.bottom), 1)
        for gy in range(CURVE_AREA.top, CURVE_AREA.bottom, paso_rejilla):
            pygame.draw.line(surface, GRID_COLOR, (CURVE_AREA.left, gy),
                             (CURVE_AREA.right, gy), 1)

        # Compute and draw curve
        pts = self._points

        if self._mode == 5 and self._show_casteljau:
            self._draw_de_casteljau(surface, pts)
        else:
            curve_pts = self._eval_curve(pts, self._mode)
            if curve_pts and len(curve_pts) > 1:
                pygame.draw.lines(surface, CURVE_COLOR, False,
                                  [(int(x), int(y)) for x, y in curve_pts], 2)

            # Draw control polygon
            if len(pts) > 1:
                pygame.draw.lines(surface, (80, 80, 100), False,
                                  [(int(x), int(y)) for x, y in pts], 1)

        # Draw control points
        for i, (px, py) in enumerate(pts):
            color = CTRL_PT_ACTIVE if i == self._drag_idx else CTRL_PT_COLOR
            pygame.draw.circle(surface, color, (int(px), int(py)), CTRL_PT_RADIUS)
            pygame.draw.circle(surface, (255, 255, 255), (int(px), int(py)), CTRL_PT_RADIUS, 1)
            label = self._font_small.render(f"P{i}", True, color)
            surface.blit(label, (int(px) + 8, int(py) - 8))

        # Info panel
        info_y = CURVE_AREA.bottom + 4
        degree = len(pts) - 1
        mode = self._mode
        if mode == 0:
            infos = ["Degree: 2 (quadratic)  |  Points: 3"]
        elif mode == 1:
            infos = ["Degree: 3 (cubic)  |  Points: 4"]
        elif mode == 2:
            infos = [f"Degree: {degree}  |  Points: {len(pts)}"]
        elif mode == 3:
            infos = [f"Interpolating spline  |  Points: {len(pts)}"]
        elif mode == 4:
            infos = [f"Uniform cubic B-Spline  |  Points: {len(pts)}  |  Degree: 3"]
        else:
            infos = [f"DE CASTELJAU t={self._casteljau_t:.2f}  |  Degree: {degree}  |  Points: {len(pts)}"]

        for mi, mname in enumerate(MODE_NAMES):
            hl = COLOR_HIGHLIGHT if mi == self._mode else (COLOR_TEXT if mi < 5 else COLOR_ACCENT)
            label = self._font_small.render(f"[{mi + 1}] {mname[:4]}", True, hl)
            surface.blit(label, (info_y + mi * 40, 26))

        for i, line in enumerate(infos):
            txt = self._font_small.render(line, True, COLOR_TEXT)
            surface.blit(txt, (4, info_y + i * 14))

        # Status
        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, BOTTOM_BAR_Y - 16))

        draw_bottom_bar(surface, (
            "  [Drag] point  [TAB] mode  [1-5] jump  [D] de Casteljau  "
            "[+/-] add/rem pt  [R] reset  [ESC] exit"
        ))

    def _eval_curve(self, pts: list[tuple[float, float]], mode: int) -> list[tuple[float, float]]:
        if len(pts) < 2:
            return pts
        try:
            if mode == 0 or mode == 1 or mode == 2 or mode == 5:
                return CurveTools.bezier(pts, self._n_samples)
            elif mode == 3:
                return CurveTools.catmull_rom(pts, self._n_samples)
            elif mode == 4:
                degree = min(3, len(pts) - 1)
                return CurveTools.b_spline(pts, degree, self._n_samples)
        except (ValueError, IndexError, ZeroDivisionError) as e:
            logger.warning("curve_editor: curve evaluation failed: %s", e)
            return pts
        return pts

    def _draw_de_casteljau(self, surface: pygame.Surface,
                           pts: list[tuple[float, float]]) -> None:
        t = self._casteljau_t
        levels, final = _de_casteljau(pts, t)

        # Draw each level
        colors = [
            (200, 200, 200), (180, 180, 100), (100, 180, 180),
            (180, 100, 180), (100, 200, 100), (200, 150, 100),
        ]

        for level_idx, level in enumerate(levels):
            col = colors[level_idx % len(colors)]
            if len(level) > 1:
                pygame.draw.lines(surface, col, False,
                                  [(int(x), int(y)) for x, y in level], 1)
            for px, py in level:
                r = max(2, CTRL_PT_RADIUS - level_idx)
                pygame.draw.circle(surface, col, (int(px), int(py)), r)

        # Draw final point
        fx, fy = int(final[0]), int(final[1])
        pygame.draw.circle(surface, CURVE_ACTIVE_COLOR, (fx, fy), 8)
        pygame.draw.circle(surface, (255, 255, 255), (fx, fy), 8, 2)

        # Draw the full Bézier curve behind
        curve_pts = self._eval_curve(pts, self._mode)
        if curve_pts and len(curve_pts) > 1:
            pygame.draw.lines(surface, (60, 120, 200), False,
                              [(int(x), int(y)) for x, y in curve_pts], 1)

        # Annotation
        label = self._font_small.render(
            f"t={t:.2f}  —  Move mouse X to change t", True, CURVE_ACTIVE_COLOR)
        surface.blit(label, (CURVE_AREA.left + 4, CURVE_AREA.top + 4))

        # Levels info
        info_lines = [f"Level {i}: {len(lv)} pts" for i, lv in enumerate(levels)]
        for i, line in enumerate(info_lines):
            txt = self._font_small.render(line, True, colors[i % len(colors)])
            surface.blit(txt, (CURVE_AREA.right - txt.get_width() - 8,
                               CURVE_AREA.top + 4 + i * (self._font_small.get_height() + 2)))

