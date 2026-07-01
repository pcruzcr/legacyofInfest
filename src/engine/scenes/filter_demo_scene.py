from __future__ import annotations


import pygame
import numpy as np

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_TEXT,
    COLOR_HIGHLIGHT,
    COLOR_ACCENT,
    COLOR_TOP_BAR_BG,
    COLOR_ERROR,
    FONT_SMALL,
    FONT_MEDIUM,
    FONT_LARGE,
    LEFT_PANEL_W,
    RIGHT_PANEL_X,
    PANEL_H,
    PANEL_SIZE,
    TOP_BAR_Y,
    TOP_BAR_H,
    BOTTOM_BAR_Y,
    BOTTOM_BAR_H,
    draw_top_bar,
    draw_bottom_bar,
    draw_bottom_bar_error,
    draw_panel_border,
    draw_divider,
    draw_histogram_bars,
    draw_save_notification,
    save_png,
    build_default_sources,
    SourceSurfaceManager,
    FrameThrottle,
)
from src.engine.utils.asset_loader import AssetLoader
from src.framework.processing.filter_tools import FilterTools


MODE_NAMES = [
    "HISTOGRAM", "BRIGHTNESS", "CONTRAST", "STRETCH", "KERNEL",
    "GAUSSIAN", "SOBEL", "CANNY", "EQUALIZE",
]

STANDARD_KERNEL_NAMES = [
    "identity", "sharpen", "box_blur", "box_blur_5",
    "edge_laplacian", "emboss",
]


class FilterDemoScene(BaseScene):
    def __init__(self) -> None:
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
        self._param_changed: bool = True

        # Save notification
        self._save_msg: str = ""
        self._save_timer: float = 0.0

        # Error
        self._error_msg: str = ""
        self._error_timer: float = 0.0

        # Recent param flash
        self._param_flash_timer: float = 0.0

        self._font_small = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._font_large = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_LARGE)

    def _get_im(self) -> InputManager | None:
        from src.engine.core.app import App
        if App._instance is not None:
            return App._instance.input_manager
        return None

    def on_enter(self) -> None:
        self._mode = 0
        self._throttle.reset()
        self._param_changed = True

    def on_exit(self) -> None:
        pass

    def update(self, dt: float) -> None:
        im = self._get_im()
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

        # SPACE — cycle source
        if im.is_raw_key_pressed(pygame.K_SPACE):
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
        if im.is_action_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            from src.engine.core.app import App
            if App._instance is not None:
                App._instance.scene_manager.replace(DemoMenuScene())
            return

        # Mode-specific input
        self._handle_mode_input(im)

        # Recompute if needed
        if self._param_changed or self._cached_result is None:
            self._compute_result()

    def _handle_mode_input(self, im: InputManager) -> None:
        key_left = im.is_raw_key_pressed(pygame.K_LEFT)
        key_right = im.is_raw_key_pressed(pygame.K_RIGHT)
        key_up = im.is_raw_key_pressed(pygame.K_UP)
        key_down = im.is_raw_key_pressed(pygame.K_DOWN)

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
        except Exception as e:
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

        return surface.copy()

    def _reset_params(self) -> None:
        self._brightness_factor = 1.0
        self._contrast_factor = 1.0
        self._kernel_idx = 0
        self._sigma = 1.0
        self._canny_low = 50
        self._canny_high = 150
        self._hist_threshold = 128

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "FILTER DEMO", "UNIT VII")

        # Mode label
        mode_color = COLOR_HIGHLIGHT if self._param_flash_timer > 0 else COLOR_TEXT
        mode_label = self._font_medium.render(
            f"  Mode: {MODE_NAMES[self._mode]}  ",
            True, mode_color,
        )
        surface.blit(mode_label, (4, TOP_BAR_Y + TOP_BAR_H - 14))

        # Source + name label
        src = self._sources.current_source
        src_label = self._font_small.render(
            f"  Source: {self._sources.current_name}{' [FROZEN]' if self._sources.is_frozen else ''}  ",
            True, COLOR_ACCENT,
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
        rect = pygame.Rect(LEFT_PANEL_W - PANEL_SIZE[0], TOP_BAR_Y + 2, PANEL_SIZE[0], PANEL_H - 4)
        src = self._sources.current_source
        if src is not None:
            scaled = pygame.transform.scale(src, PANEL_SIZE)
            surface.blit(scaled, (0, TOP_BAR_H))
        draw_panel_border(surface, pygame.Rect(0, TOP_BAR_H, PANEL_SIZE[0], PANEL_H))

        if self._sources.is_frozen:
            freeze_text = self._font_small.render("FROZEN", True, COLOR_HIGHLIGHT)
            surface.blit(freeze_text, (4, TOP_BAR_H + 2))

    def _draw_right_panel(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(RIGHT_PANEL_X, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
        if self._cached_result is not None:
            scaled = pygame.transform.scale(self._cached_result, PANEL_SIZE)
            surface.blit(scaled, (RIGHT_PANEL_X, TOP_BAR_H))
        draw_panel_border(surface, rect)

        # Histogram bars for mode 0
        if self._mode == 0 and self._cached_result is not None:
            self._draw_histogram(surface, rect)

        # Error overlay
        if self._error_msg:
            err_text = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            surface.blit(err_text, (RIGHT_PANEL_X + 4, TOP_BAR_H + 4))

    def _draw_histogram(self, surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
        src = self._sources.current_source
        if src is None:
            return
        # Compute histograms for source (left) and result (right)
        arr = pygame.surfarray.pixels3d(src)
        h_r, _ = np.histogram(arr[:, :, 0], bins=80, range=(0, 256))
        h_g, _ = np.histogram(arr[:, :, 1], bins=80, range=(0, 256))
        h_b, _ = np.histogram(arr[:, :, 2], bins=80, range=(0, 256))
        del arr

        # Draw source histogram in left panel
        left_rect = pygame.Rect(0, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
        draw_histogram_bars(surface, left_rect,
                            h_r.tolist(), h_g.tolist(), h_b.tolist(), bar_w=2, max_h=40)

        # Draw result histogram in right panel
        if self._cached_result is not None:
            arr2 = pygame.surfarray.pixels3d(self._cached_result)
            h2_r, _ = np.histogram(arr2[:, :, 0], bins=80, range=(0, 256))
            h2_g, _ = np.histogram(arr2[:, :, 1], bins=80, range=(0, 256))
            h2_b, _ = np.histogram(arr2[:, :, 2], bins=80, range=(0, 256))
            del arr2

            right_rect = pygame.Rect(RIGHT_PANEL_X, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
            draw_histogram_bars(surface, right_rect,
                                h2_r.tolist(), h2_g.tolist(), h2_b.tolist(), bar_w=2, max_h=40)

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
            k_str = f"[[{kernel[0][0]:2d} {kernel[0][1]:2d} {kernel[0][2]:2d}]"
            k_str += f"[{kernel[1][0]:2d} {kernel[1][1]:2d} {kernel[1][2]:2d}]"
            k_str += f"[{kernel[2][0]:2d} {kernel[2][1]:2d} {kernel[2][2]:2d}]]"
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
        return ""
