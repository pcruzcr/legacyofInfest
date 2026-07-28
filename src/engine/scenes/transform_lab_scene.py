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

import math
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
from src.engine.scenes.demo_layout import (
    AUTHORED_H,
    AUTHORED_W,
    Lienzo,
    area_con_columna,
)
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = ["TRANSLATE", "ROTATE", "SCALE", "SHEAR", "COMPOSITE"]
SHAPE_PTS = [(0, -30), (20, 10), (0, 30), (-20, 10)]


class TransformLabScene(BaseScene):
    #: Origen del sistema de coordenadas, en unidades de autoría. El centro
    #: del lienzo, para que la figura sin transformar aparezca centrada.
    _ORIGEN_X: float = AUTHORED_W / 2.0
    _ORIGEN_Y: float = AUTHORED_H / 2.0
    #: Ancho de la columna donde van la matriz y las lecturas numéricas.
    _ANCHO_COLUMNA: int = 260

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._tx: float = self._ORIGEN_X
        self._ty: float = self._ORIGEN_Y
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
        self._tx, self._ty = self._ORIGEN_X, self._ORIGEN_Y
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

    def rect_principal(self) -> pygame.Rect:
        """Dónde vive el elemento que el estudiante mira y manipula.

        Lo consume `tests/test_demo_centering.py`, que exige que esté
        centrado horizontalmente en el área útil. Es la forma de dejar
        escrito, y comprobado en cada ejecución de la suite, el defecto
        AUD-094: el elemento vivía en la esquina superior izquierda porque
        estas escenas se escribieron para una pantalla de 320x224.
        """
        _, escenario = area_con_columna(self._ANCHO_COLUMNA)
        return Lienzo(AUTHORED_W, AUTHORED_H, area=escenario).rect()

    def draw(self, surface: pygame.Surface) -> None:
        """Dibuja la figura centrada y las lecturas en su propia columna.

        AUD-094 — la figura vivía en la esquina
        ---------------------------------------
        Todo esto estaba escrito para una pantalla de 320x224: el origen en
        `(160, 100)`, la rejilla cada 32 px, el texto en `x = 4`. Sobre los
        800x600 reales el contenido medía x[4,247] y[33,199] —el cuadrante
        superior izquierdo— y las tres cuartas partes de la pantalla estaban
        vacías.

        La aritmética de la transformación **no cambia**: sigue operando en
        coordenadas de autoría, que son las que aparecen en la pizarra. Sólo
        cambia el último paso, la traducción a píxeles, que ahora pasa por el
        lienzo.
        """
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "TRANSFORM LAB", "UNIT II/III")

        columna, escenario = area_con_columna(self._ANCHO_COLUMNA)
        lienzo = Lienzo(AUTHORED_W, AUTHORED_H, area=escenario)

        # Rejilla: se dibuja en el escenario, no sobre la columna de texto,
        # con el paso de autoría (32 px) escalado.
        paso = lienzo.l(32)
        for x in range(escenario.left, escenario.right, paso):
            pygame.draw.line(surface, (20, 20, 40), (x, escenario.top), (x, escenario.bottom), 1)
        for y in range(escenario.top, escenario.bottom, paso):
            pygame.draw.line(surface, (20, 20, 40), (escenario.left, y), (escenario.right, y), 1)

        # Ejes en el origen de autoría
        center = lienzo.p(self._ORIGEN_X, self._ORIGEN_Y)
        pygame.draw.line(surface, (60, 60, 100), center, (center[0] + lienzo.l(40), center[1]), 1)
        pygame.draw.line(surface, (60, 60, 100), center, (center[0], center[1] + lienzo.l(40)), 1)

        # Figura original (fantasma)
        orig_pts = [lienzo.p(self._ORIGEN_X + x, self._ORIGEN_Y + y) for x, y in SHAPE_PTS]
        pygame.draw.polygon(surface, (40, 40, 60), orig_pts, 1)

        # Figura transformada
        tpts = [lienzo.p(*self._transform_point(p)) for p in SHAPE_PTS]
        pygame.draw.polygon(surface, (80, 200, 255), tpts, max(2, lienzo.l(1)))

        # Columna de lecturas
        x_txt = columna.x + 8
        label = self._font_medium.render(f"Mode: {MODE_NAMES[self._mode]}", True, COLOR_HIGHLIGHT)
        surface.blit(label, (x_txt, columna.y + 8))

        salto = self._font_small.get_height() + 2
        y_txt = columna.y + 12 + label.get_height() + salto

        if self._show_matrix:
            for line in self._build_matrix_lines():
                surface.blit(self._font_small.render(line, True, COLOR_ACCENT), (x_txt, y_txt))
                y_txt += salto
            y_txt += salto

        for line in self._build_value_lines():
            surface.blit(self._font_small.render(line, True, COLOR_TEXT), (x_txt, y_txt))
            y_txt += salto

        controls = self._build_controls_text()
        ct = self._font_small.render(controls, True, COLOR_TEXT)
        surface.blit(ct, (x_txt, min(y_txt + salto, BOTTOM_BAR_Y - ct.get_height() - 24)))

        # Status
        if self._status_msg:
            st = self._font_small.render(self._status_msg, True, COLOR_HIGHLIGHT)
            surface.blit(st, (4, BOTTOM_BAR_Y - 16))

        draw_bottom_bar(surface, f"MODE: {MODE_NAMES[self._mode]}")

    def _build_matrix_lines(self) -> list[str]:
        if self._mode == 0:
            return [
                f"[1  0  tx]      [1  0  {self._tx:.0f}]",
                f"[0  1  ty]  =   [0  1  {self._ty:.0f}]",
                "[0  0   1]      [0  0   1]",
            ]
        elif self._mode == 1:
            rad = math.radians(self._angle)
            c, s = math.cos(rad), math.sin(rad)
            return [
                f"[cos -sin  0]    [{c:.2f}  {-s:.2f}  0]",
                f"[sin  cos  0]  = [{s:.2f}  {c:.2f}  0]",
                "[ 0    0   1]    [ 0     0    1]",
            ]
        elif self._mode == 2:
            return [
                f"[sx  0   0]     [{self._sx:.2f}  0    0]",
                f"[ 0  sy  0]  =  [ 0   {self._sy:.2f}  0]",
                "[ 0   0   1]     [ 0    0    1]",
            ]
        elif self._mode == 3:
            return [
                f"[1  shx  0]     [1    {self._shx:.2f}  0]",
                f"[shy 1   0]  =  [{self._shy:.2f}   1    0]",
                "[ 0   0   1]     [ 0     0    1]",
            ]
        elif self._mode == 4:
            rad = math.radians(self._angle)
            c, s = math.cos(rad), math.sin(rad)
            return [
                "Rot then Translate:",
                f"  tx={self._tx:.0f}  ty={self._ty:.0f}",
                f"  cos={c:.2f}  sin={s:.2f}  angle={self._angle:.0f}deg",
                "  [Composite matrix not shown — see paper]",
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

