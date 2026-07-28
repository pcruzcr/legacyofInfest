from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_H,
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_ERROR,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    COLOR_TOP_BAR_BG,
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_SMALL,
    LEFT_PANEL_W,
    PANEL_H,
    PANEL_SIZE,
    RIGHT_PANEL_X,
    TOP_BAR_H,
    TOP_BAR_Y,
    FrameThrottle,
    SourceSurfaceManager,
    build_default_sources,
    draw_bottom_bar,
    draw_bottom_bar_error,
    draw_divider,
    draw_histogram_bars,
    draw_panel_border,
    draw_save_notification,
    draw_top_bar,
    save_png,
)
from src.engine.utils.asset_loader import AssetLoader
from src.framework.processing.filter_tools import FilterTools

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.input.input_manager import InputManager


MODE_NAMES = [
    "HISTOGRAM", "BRIGHTNESS", "CONTRAST", "STRETCH", "KERNEL",
    "GAUSSIAN", "SOBEL", "CANNY", "EQUALIZE", "CONV_STEP",
]

#: Número de barras del histograma. El mismo de siempre.
_BARRAS_HIST = 80
#: Índices donde empieza cada barra, en niveles de 0 a 255.
#:
#: `np.histogram(..., bins=80, range=(0, 256))` reparte los 256 niveles en
#: tramos de 3,2 y mete el nivel v en la barra ⌊v/3,2⌋; el primer nivel de la
#: barra i es por tanto ⌈3,2·i⌉. Se calcula con división entera negada para
#: no depender de la coma flotante, y así el resultado es **idéntico** al de
#: `np.histogram`: se cambió el coste, no la lección (AUD-097).
_CORTES_HIST = np.array(
    [-((-256 * i) // _BARRAS_HIST) for i in range(_BARRAS_HIST)], dtype=np.intp,
)

STANDARD_KERNEL_NAMES = [
    "identity", "sharpen", "box_blur", "box_blur_5",
    "edge_laplacian", "emboss",
]


class FilterDemoScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._sources: SourceSurfaceManager = build_default_sources()
        self._throttle = FrameThrottle()

        # Parameters
        self._brightness_factor: float = 1.0
        self._contrast_factor: float = 1.0
        self._kernel_idx: int = 0
        self._sigma: float = 1.0
        self._canny_low: int = 50
        self._canny_high: int = 150
        self._hist_threshold: int = 128

        # Cached result
        self._cached_result: pygame.Surface | None = None
        self._cached_left_scaled: pygame.Surface | None = None
        self._cached_left_src: pygame.Surface | None = None
        self._cached_right_scaled: pygame.Surface | None = None
        # AUD-097: histogramas cacheados. `_hist_firma` identifica de qué
        # imágenes son; mientras no cambie, no se recalculan.
        self._hist_firma: tuple = ()
        self._hist_src: list[list[int]] | None = None
        self._hist_res: list[list[int]] | None = None
        self._cached_right_src: pygame.Surface | None = None
        self._param_changed: bool = True

        # Save notification
        self._save_msg: str = ""
        self._save_timer: float = 0.0

        # Error
        self._error_msg: str = ""
        self._error_timer: float = 0.0

        # Recent param flash
        self._param_flash_timer: float = 0.0

        # CONV_STEP state
        self._conv_x: int = 1
        self._conv_y: int = 1
        self._conv_paused: bool = True
        self._conv_speed: float = 16.0  # px per second
        self._conv_step_acc: float = 0.0
        self._conv_show_formula: bool = True

        self._font_small = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._font_large = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_LARGE)

    def on_enter(self) -> None:
        self._mode = 0
        self._throttle.reset()
        self._param_changed = True

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        self._throttle.tick()
        self._param_changed = False

        # Timers
        if self._save_timer > 0:
            self._save_timer -= dt
        if self._save_timer <= 0:
            self._save_msg = ""
        if self._error_timer > 0:
            self._error_timer -= dt
        if self._error_timer <= 0:
            self._error_msg = ""
        if self._param_flash_timer > 0:
            self._param_flash_timer -= dt

        # TAB — cycle modes
        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._cached_result = None
            self._throttle.reset()

        # SPACE — cycle source (except in CONV_STEP mode where it pauses)
        if im.is_raw_key_pressed(pygame.K_SPACE) and self._mode != 9:
            self._sources.cycle()
            self._cached_result = None
            self._param_changed = True

        # F — freeze
        if im.is_raw_key_pressed(pygame.K_f):
            if self._sources.is_frozen:
                self._sources.unfreeze()
            else:
                self._sources.freeze()
            self._cached_result = None
            self._param_changed = True

        # S — save
        if im.is_raw_key_pressed(pygame.K_s):
            if self._cached_result is not None:
                path = save_png("filter", MODE_NAMES[self._mode].lower(), self._cached_result)
                self._save_msg = f"Saved: {path}"
                self._save_timer = 2.0

        # R — reset
        if im.is_raw_key_pressed(pygame.K_r):
            self._reset_params()
            self._cached_result = None
            self._param_changed = True

        # ESC — back to menu
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        # Mode-specific input
        self._handle_mode_input(im)

        # CONV_STEP animation
        if self._mode == 9 and not self._conv_paused:
            src = self._sources.current_source
            if src is not None:
                w, h = src.get_size()
                self._conv_step_acc += self._conv_speed * dt
                while self._conv_step_acc >= 1.0:
                    self._conv_step_acc -= 1.0
                    self._conv_x += 1
                    if self._conv_x >= w - 2:
                        self._conv_x = 1
                        self._conv_y += 1
                    if self._conv_y >= h - 2:
                        self._conv_x, self._conv_y = 1, 1
                self._param_changed = True

        # Recompute if needed
        if self._param_changed or self._cached_result is None:
            self._compute_result()

    def _handle_mode_input(self, im: InputManager) -> None:
        key_left = im.is_raw_key_pressed(pygame.K_LEFT)
        key_right = im.is_raw_key_pressed(pygame.K_RIGHT)
        key_up = im.is_raw_key_pressed(pygame.K_UP)
        key_down = im.is_raw_key_pressed(pygame.K_DOWN)
        key_space = im.is_raw_key_pressed(pygame.K_SPACE)

        if self._mode == 0:  # HISTOGRAM
            if key_left:
                self._hist_threshold = max(0, self._hist_threshold - 5)
                self._param_changed = True
            if key_right:
                self._hist_threshold = min(255, self._hist_threshold + 5)
                self._param_changed = True

        elif self._mode == 1:  # BRIGHTNESS
            if key_left:
                self._brightness_factor = max(0.0, self._brightness_factor - 0.05)
                self._param_changed = True
                self._param_flash_timer = 0.3
            if key_right:
                self._brightness_factor = min(4.0, self._brightness_factor + 0.05)
                self._param_changed = True
                self._param_flash_timer = 0.3

        elif self._mode == 2:  # CONTRAST
            if key_left:
                self._contrast_factor = max(0.0, self._contrast_factor - 0.05)
                self._param_changed = True
                self._param_flash_timer = 0.3
            if key_right:
                self._contrast_factor = min(4.0, self._contrast_factor + 0.05)
                self._param_changed = True
                self._param_flash_timer = 0.3

        elif self._mode == 4:  # KERNEL
            if key_up:
                self._kernel_idx = (self._kernel_idx + 1) % len(STANDARD_KERNEL_NAMES)
                self._param_changed = True
            if key_down:
                self._kernel_idx = (self._kernel_idx - 1) % len(STANDARD_KERNEL_NAMES)
                self._param_changed = True

        elif self._mode == 5:  # GAUSSIAN
            if key_left:
                self._sigma = max(0.1, round(self._sigma - 0.1, 1))
                self._param_changed = True
                self._param_flash_timer = 0.3
            if key_right:
                self._sigma = min(5.0, round(self._sigma + 0.1, 1))
                self._param_changed = True
                self._param_flash_timer = 0.3

        elif self._mode == 7:  # CANNY
            if key_right:
                self._canny_low = min(255, self._canny_low + 5)
                self._param_changed = True
            if key_left:
                self._canny_low = max(0, self._canny_low - 5)
                self._param_changed = True
            if key_up:
                self._canny_high = min(255, self._canny_high + 5)
                self._param_changed = True
            if key_down:
                self._canny_high = max(0, self._canny_high - 5)
                self._param_changed = True

        elif self._mode == 9:  # CONV_STEP
            if key_space:
                self._conv_paused = not self._conv_paused
                self._param_changed = True
            if key_left:
                self._conv_speed = max(2.0, self._conv_speed - 4.0)
            if key_right:
                self._conv_speed = min(64.0, self._conv_speed + 4.0)
            if key_up:
                self._kernel_idx = (self._kernel_idx + 1) % len(STANDARD_KERNEL_NAMES)
                self._conv_x, self._conv_y = 1, 1
                self._param_changed = True
            if key_down:
                self._kernel_idx = (self._kernel_idx - 1) % len(STANDARD_KERNEL_NAMES)
                self._conv_x, self._conv_y = 1, 1
                self._param_changed = True

    def _compute_result(self) -> None:
        src = self._sources.current_source
        if src is None:
            self._cached_result = pygame.Surface(PANEL_SIZE)
            self._cached_result.fill((0, 0, 0))
            return

        try:
            result = self._apply_mode(src)
            result = pygame.transform.scale(result, PANEL_SIZE)
            self._cached_result = result
            self._error_msg = ""
        except (pygame.error, ValueError, ZeroDivisionError) as e:
            logger.warning("filter_demo: compute error: %s", e)
            self._error_msg = f"Error: {e}"[:60]
            self._error_timer = 2.0

    def _apply_mode(self, surface: pygame.Surface) -> pygame.Surface:
        if self._mode == 0:  # HISTOGRAM — just copy
            return surface.copy()

        elif self._mode == 1:  # BRIGHTNESS
            return FilterTools.adjust_brightness(surface, self._brightness_factor)

        elif self._mode == 2:  # CONTRAST
            return FilterTools.adjust_contrast(surface, self._contrast_factor)

        elif self._mode == 3:  # STRETCH
            return FilterTools.stretch_contrast(surface)

        elif self._mode == 4:  # KERNEL
            kernel = FilterTools.get_standard_kernel(STANDARD_KERNEL_NAMES[self._kernel_idx])
            return FilterTools.apply_kernel(surface, kernel)

        elif self._mode == 5:  # GAUSSIAN
            return FilterTools.gaussian_blur(surface, self._sigma)

        elif self._mode == 6:  # SOBEL
            return FilterTools.sobel_edge(surface)

        elif self._mode == 7:  # CANNY
            return FilterTools.canny_edge(surface, self._canny_low, self._canny_high)

        elif self._mode == 8:  # EQUALIZE
            return FilterTools.histogram_equalize(surface)

        elif self._mode == 9:  # CONV_STEP — full result for right panel
            return surface.copy()

        return surface.copy()

    def _reset_params(self) -> None:
        self._brightness_factor = 1.0
        self._contrast_factor = 1.0
        self._kernel_idx = 0
        self._sigma = 1.0
        self._canny_low = 50
        self._canny_high = 150
        self._hist_threshold = 128
        self._conv_x, self._conv_y = 1, 1
        self._conv_paused = True
        self._conv_speed = 16.0
        self._conv_step_acc = 0.0

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "FILTER DEMO", "UNIT VII")

        # Mode label
        mode_color = COLOR_HIGHLIGHT if self._param_flash_timer > 0 else COLOR_TEXT
        mode_label = self._font_medium.render(
            f"  Mode: {MODE_NAMES[self._mode]}  ", True, mode_color,
        )
        surface.blit(mode_label, (4, TOP_BAR_Y + TOP_BAR_H - 14))

        # Education overlay
        _edu = {
            0: ("Histogram", "Shows per-channel intensity distribution (R/G/B)."),
            1: ("Brightness", "Formula: out = in + beta"),
            2: ("Contrast", "Formula: out = (in - 128) x alpha + 128"),
            3: ("Stretch", "Linear remap [min, max] → [0, 255] to improve contrast."),
            4: ("Kernel", "3x3 convolution: weighted sum of neighborhood pixels."),
            5: ("Gaussian", "Smoothing kernel reduces noise via local averaging."),
            6: ("Sobel", "Gradient magnitude filter for edge detection."),
            7: ("Canny", "Multi-stage edge detector: blur → Sobel → NMS → hysteresis."),
            8: ("Equalize", "Histogram equalization redistributes intensities."),
            9: ("Conv Step", "Visualizes kernel sliding across the image."),
        }
        if self._mode in _edu:
            edu_title, edu_desc = _edu[self._mode]
            t1 = self._font_small.render(f"  {edu_title}", True, COLOR_HIGHLIGHT)
            t2 = self._font_small.render(f"  {edu_desc}", True, COLOR_TEXT)
            surface.blit(t1, (RIGHT_PANEL_X, TOP_BAR_Y + 2))
            surface.blit(t2, (RIGHT_PANEL_X, TOP_BAR_Y + 14))

        # Source + name label
        src_label = self._font_small.render(
            f"  Source: {self._sources.current_name}"
            f"{' [FROZEN]' if self._sources.is_frozen else ''}  ", True, COLOR_ACCENT,
        )
        surface.blit(src_label, (90, TOP_BAR_Y + TOP_BAR_H - 14))

        # Panels
        self._draw_left_panel(surface)
        self._draw_right_panel(surface)
        draw_divider(surface)

        # Bottom bar
        self._draw_bottom_bar(surface)

        # Save notification
        if self._save_msg:
            pygame.draw.rect(surface, COLOR_TOP_BAR_BG,
                             (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
            draw_save_notification(surface, self._save_msg, self._font_small)

    def _draw_left_panel(self, surface: pygame.Surface) -> None:
        pygame.Rect(LEFT_PANEL_W - PANEL_SIZE[0], TOP_BAR_Y + 2, PANEL_SIZE[0], PANEL_H - 4)
        src = self._sources.current_source
        if src is not None:
            if self._cached_left_src is not src:
                self._cached_left_scaled = pygame.transform.scale(src, PANEL_SIZE)
                self._cached_left_src = src
            surface.blit(self._cached_left_scaled, (0, TOP_BAR_H))
        draw_panel_border(surface, pygame.Rect(0, TOP_BAR_H, PANEL_SIZE[0], PANEL_H))

        if self._sources.is_frozen:
            freeze_text = self._font_small.render("FROZEN", True, COLOR_HIGHLIGHT)
            surface.blit(freeze_text, (4, TOP_BAR_H + 2))

    def _draw_right_panel(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(RIGHT_PANEL_X, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
        if self._cached_result is not None:
            if self._cached_right_src is not self._cached_result:
                self._cached_right_scaled = pygame.transform.scale(self._cached_result, PANEL_SIZE)
                self._cached_right_src = self._cached_result
            surface.blit(self._cached_right_scaled, (RIGHT_PANEL_X, TOP_BAR_H))
        draw_panel_border(surface, rect)

        # Histogram bars for mode 0
        if self._mode == 0 and self._cached_result is not None:
            self._draw_histogram(surface, rect)

        # CONV_STEP overlay
        if self._mode == 9:
            self._draw_conv_step(surface, rect)

        # Error overlay
        if self._error_msg:
            err_text = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            surface.blit(err_text, (RIGHT_PANEL_X + 4, TOP_BAR_H + 4))

    @staticmethod
    def _histograma(superficie: pygame.Surface) -> tuple[list[int], list[int], list[int]]:
        """Los tres histogramas de canal de una superficie.

        AUD-097 — por qué esto está en una función aparte y con caché
        -------------------------------------------------------------
        Esto se llamaba **seis veces por fotograma** —tres canales por dos
        paneles— desde `draw`, recalculando el histograma de imágenes que no
        habían cambiado. Medido con cProfile sobre 180 fotogramas:
        `np.histogram` se llevaba 3,95 s de los 4,41 s que costaba dibujar la
        escena entera, el 90 %.

        Es el mismo defecto que AUD-073 en el laboratorio de ruido: trabajo
        caro y determinista repetido en cada fotograma porque nadie se
        preguntó cuándo cambia de verdad su entrada. La respuesta aquí es:
        cuando el estudiante cambia de imagen o de filtro, no sesenta veces
        por segundo.

        Se usa `np.bincount` y no `np.histogram` porque los datos ya son
        enteros de 0 a 255: no hace falta buscar el hueco de cada valor con
        `searchsorted`, basta con contarlos. Sale unas cuatro veces más
        barato aun sin la caché.
        """
        try:
            arr = pygame.surfarray.pixels3d(superficie)
            canales = [
                np.bincount(arr[:, :, c].ravel(), minlength=256)[:256]
                for c in range(3)
            ]
        finally:
            del arr
        return [np.add.reduceat(c, _CORTES_HIST).tolist() for c in canales]

    def _histogramas_al_dia(self) -> None:
        """Recalcula los histogramas sólo si cambió lo que representan."""
        src = self._sources.current_source
        firma = (
            id(src),
            id(self._cached_result),
            self._sources.index if hasattr(self._sources, "index") else 0,
        )
        if firma == self._hist_firma:
            return
        self._hist_firma = firma
        self._hist_src = self._histograma(src) if src is not None else None
        self._hist_res = (
            self._histograma(self._cached_result)
            if self._cached_result is not None else None
        )

    def _draw_histogram(self, surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
        if self._sources.current_source is None:
            return
        self._histogramas_al_dia()

        if self._hist_src is not None:
            left_rect = pygame.Rect(0, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
            draw_histogram_bars(surface, left_rect, *self._hist_src, bar_w=2, max_h=40)

        if self._hist_res is not None:
            right_rect = pygame.Rect(RIGHT_PANEL_X, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
            draw_histogram_bars(surface, right_rect, *self._hist_res, bar_w=2, max_h=40)

    def _draw_conv_step(self, surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
        src = self._sources.current_source
        if src is None:
            return
        sw, sh = src.get_size()
        kx, ky = self._conv_x, self._conv_y
        kname = STANDARD_KERNEL_NAMES[self._kernel_idx]
        kernel = FilterTools.get_standard_kernel(kname)
        k_size = len(kernel)
        half = k_size // 2

        # Clamp
        kx = max(half, min(sw - half - 1, kx))
        ky = max(half, min(sh - half - 1, ky))

        # Overlay on left panel (scaled)
        sx = int(kx / sw * LEFT_PANEL_W)
        sy = int(ky / sh * PANEL_H)
        cell_w = max(2, LEFT_PANEL_W // sw)
        cell_h = max(2, PANEL_H // sh)
        kw = k_size * cell_w
        kh = k_size * cell_h

        # Highlight kernel window
        k_rect = pygame.Rect(sx - half * cell_w, sy - half * cell_h, kw, kh)
        pygame.draw.rect(surface, (255, 220, 80), k_rect, 2)

        # Draw kernel grid overlay
        for ki in range(k_size):
            for kj in range(k_size):
                cx = k_rect.x + kj * cell_w
                cy = k_rect.y + ki * cell_h
                val = kernel[ki][kj]
                color = (100, 200, 100) if val > 0 else (200, 100, 100) if val < 0 else (100, 100, 100)
                pygame.draw.rect(surface, color, (cx, cy, cell_w, cell_h), 1)

        # Result pixel highlight on right panel
        rx = int(kx / sw * PANEL_SIZE[0])
        ry = int(ky / sh * PANEL_H)
        pygame.draw.circle(surface, (255, 220, 80), (RIGHT_PANEL_X + rx, TOP_BAR_H + ry), 4)
        pygame.draw.circle(surface, (255, 255, 255), (RIGHT_PANEL_X + rx, TOP_BAR_H + ry), 4, 1)

        # Formula text
        k_str = f"{kname}"
        formula = self._font_small.render(
            f"  Kernel: {k_str}  |  Pos: ({kx},{ky})  |  Speed: {self._conv_speed:.0f} px/s",
            True, COLOR_HIGHLIGHT)
        surface.blit(formula, (4, TOP_BAR_H + PANEL_H - 18))

        pause_label = self._font_small.render(
            "  [SPACE] pause/resume  [UP/DOWN] kernel  [LEFT/RIGHT] speed", True, COLOR_ACCENT)
        surface.blit(pause_label, (RIGHT_PANEL_X, TOP_BAR_H + 2))

    def _draw_bottom_bar(self, surface: pygame.Surface) -> None:
        if self._error_msg:
            draw_bottom_bar_error(surface, self._error_msg)
            return

        if self._save_msg:
            return

        text = self._bottom_bar_text()
        draw_bottom_bar(surface, text)

    def _bottom_bar_text(self) -> str:
        mode = self._mode
        if mode == 0:
            return f"  Threshold: {self._hist_threshold}  |  [TAB: mode]  |  [SPACE: source]"
        elif mode == 1:
            return (f"  factor = {self._brightness_factor:.2f}  |  Range: [0.0, 4.0]  |  "
                    f"Formula: out = in x factor  |  [TAB: mode]")
        elif mode == 2:
            return (f"  factor = {self._contrast_factor:.2f}  |  Range: [0.0, 4.0]  |  "
                    f"Formula: out = (in - 128) x factor + 128  |  [TAB: mode]")
        elif mode == 3:
            return "  No parameters  |  [TAB: mode]  |  [SPACE: source]"
        elif mode == 4:
            kname = STANDARD_KERNEL_NAMES[self._kernel_idx]
            kernel = FilterTools.get_standard_kernel(kname)
            k_str = f"[[{kernel[0][0]:6.2f} {kernel[0][1]:6.2f} {kernel[0][2]:6.2f}]"
            k_str += f"[{kernel[1][0]:6.2f} {kernel[1][1]:6.2f} {kernel[1][2]:6.2f}]"
            k_str += f"[{kernel[2][0]:6.2f} {kernel[2][1]:6.2f} {kernel[2][2]:6.2f}]]"
            return f"  Kernel: {kname}  |  Size: 3x3  |  {k_str}  |  [TAB: mode]"
        elif mode == 5:
            return f"  sigma = {self._sigma:.1f}  |  Range: [0.1, 5.0]  |  [TAB: mode]"
        elif mode == 6:
            return "  No parameters  |  [TAB: mode]  |  [SPACE: source]"
        elif mode == 7:
            ratio = self._canny_high / max(self._canny_low, 1)
            return (f"  low={self._canny_low}  |  high={self._canny_high}  |  "
                    f"ratio={ratio:.1f}  |  Pipeline: blur->Sobel->NMS->threshold->hysteresis  |  "
                    f"[TAB: mode]")
        elif mode == 8:
            return "  No parameters  |  [TAB: mode]  |  [SPACE: source]"
        elif mode == 9:
            kname = STANDARD_KERNEL_NAMES[self._kernel_idx]
            paused = "PAUSED" if self._conv_paused else "RUNNING"
            return (f"  {kname}  |  ({self._conv_x},{self._conv_y})  |  "
                    f"{paused}  |  [SPACE] toggle  |  [TAB: mode]")
        return ""
