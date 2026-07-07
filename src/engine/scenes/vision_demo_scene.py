from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
import numpy as np

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    COLOR_BG,
    COLOR_HIGHLIGHT,
    COLOR_ACCENT,
    COLOR_TOP_BAR_BG,
    COLOR_ERROR,
    COLOR_GOLD,
    FONT_SMALL,
    FONT_MEDIUM,
    FONT_LARGE,
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
    draw_save_notification,
    save_png,
    build_default_sources,
    SourceSurfaceManager,
    FrameThrottle,
)
from src.engine.utils.asset_loader import AssetLoader
from src.framework.processing.vision_tools import VisionTools

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


MODE_NAMES = [
    "THRESHOLD", "OTSU", "ERODE", "DILATE", "OPEN",
    "CLOSE", "COMPONENTS", "REGIONS", "WATERSHED", "FEATURES",
]

FEATURE_METHODS = ["hog", "lbp", "color_hist", "combined"]


class VisionDemoScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._mode: int = 0
        self._sources: SourceSurfaceManager = build_default_sources()
        self._throttle = FrameThrottle()

        # Parameters
        self._threshold: int = 128
        self._kernel_size: int = 3
        self._feat_method_idx: int = 0

        # Cached results
        self._cached_result: pygame.Surface | None = None
        self._cached_regions: list | None = None
        self._cached_comp_result: object | None = None  # ComponentResult
        self._cached_watershed: pygame.Surface | None = None
        self._otsu_value: int = 128
        self._otsu_curve: list[float] = []
        self._otsu_histogram: list[int] = []
        self._param_changed: bool = True

        # Save notification
        self._save_msg: str = ""
        self._save_timer: float = 0.0

        # Error
        self._error_msg: str = ""
        self._error_timer: float = 0.0

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

        if im.is_raw_key_pressed(pygame.K_TAB):
            self._mode = (self._mode + 1) % len(MODE_NAMES)
            self._cached_result = None
            self._cached_watershed = None
            self._param_changed = True
            self._throttle.reset()

        if im.is_raw_key_pressed(pygame.K_SPACE):
            self._sources.cycle()
            self._cached_result = None
            self._cached_watershed = None
            self._param_changed = True

        if im.is_raw_key_pressed(pygame.K_f):
            if self._sources.is_frozen:
                self._sources.unfreeze()
            else:
                self._sources.freeze()
            self._cached_result = None
            self._cached_watershed = None
            self._param_changed = True

        if im.is_raw_key_pressed(pygame.K_s):
            if self._cached_result is not None:
                path = save_png("vision", MODE_NAMES[self._mode].lower(), self._cached_result)
                self._save_msg = f"Saved: {path}"
                self._save_timer = 2.0

        if im.is_raw_key_pressed(pygame.K_r):
            self._threshold = 128
            self._kernel_size = 3
            self._feat_method_idx = 0
            self._cached_result = None
            self._param_changed = True

        if im.is_action_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        self._handle_mode_input(im)

        if self._param_changed or self._cached_result is None:
            self._compute_result()

    def _handle_mode_input(self, im):
        key_left = im.is_raw_key_pressed(pygame.K_LEFT)
        key_right = im.is_raw_key_pressed(pygame.K_RIGHT)

        if self._mode == 0:  # THRESHOLD
            if key_left:
                self._threshold = max(0, self._threshold - 5)
                self._param_changed = True
            if key_right:
                self._threshold = min(255, self._threshold + 5)
                self._param_changed = True

        elif self._mode in (2, 3, 4, 5):  # ERODE, DILATE, OPEN, CLOSE
            if key_left:
                self._kernel_size = max(1, self._kernel_size - 2)
                self._param_changed = True
            if key_right:
                self._kernel_size = min(15, self._kernel_size + 2)
                self._param_changed = True

        elif self._mode in (6, 7):  # COMPONENTS, REGIONS
            if key_left:
                self._threshold = max(0, self._threshold - 5)
                self._param_changed = True
            if key_right:
                self._threshold = min(255, self._threshold + 5)
                self._param_changed = True

        elif self._mode == 9:  # FEATURES
            if im.is_raw_key_pressed(pygame.K_UP):
                self._feat_method_idx = (self._feat_method_idx + 1) % len(FEATURE_METHODS)
                self._param_changed = True
            if im.is_raw_key_pressed(pygame.K_DOWN):
                self._feat_method_idx = (self._feat_method_idx - 1) % len(FEATURE_METHODS)
                self._param_changed = True

    def _compute_otsu_curve(self, gray_surface: pygame.Surface) -> tuple[list[float], list[int]]:
        arr = pygame.surfarray.pixels3d(gray_surface)
        gray = np.mean(arr, axis=2).astype(np.uint8).flatten()
        del arr
        total = len(gray)
        hist = np.bincount(gray, minlength=256).tolist()
        total_sum = sum(t * hist[t] for t in range(256))
        curve = []
        cum_sum = 0.0
        w0 = 0
        for t in range(256):
            w0 += hist[t]
            cum_sum += t * hist[t]
            if w0 == 0 or w0 == total:
                curve.append(0.0)
                continue
            w1 = total - w0
            mu0 = cum_sum / w0
            mu1 = (total_sum - cum_sum) / w1
            var_between = w0 * w1 * (mu0 - mu1) ** 2
            curve.append(var_between)
        norm = max(curve) if max(curve) > 0 else 1.0
        curve = [v / norm for v in curve]
        return curve, hist

    def _compute_result(self) -> None:
        src = self._sources.current_source
        if src is None:
            self._cached_result = pygame.Surface(PANEL_SIZE)
            self._cached_result.fill((0, 0, 0))
            return

        try:
            result, regions, comp_info, ws = self._apply_mode(src)
            self._cached_result = result
            self._cached_regions = regions
            self._cached_comp_result = comp_info
            self._cached_watershed = ws
            self._error_msg = ""
        except Exception as e:
            self._error_msg = f"Error: {e}"[:60]
            self._error_timer = 2.0

    def _apply_mode(self, src: pygame.Surface) -> tuple:
        mode = self._mode
        src_gray = _to_grayscale(src)

        if mode == 0:  # THRESHOLD
            mask = VisionTools.threshold_binary(src_gray, self._threshold)
            return mask, None, None, None

        elif mode == 1:  # OTSU
            mask, otsu_val = VisionTools.threshold_otsu(src_gray)
            self._otsu_value = int(otsu_val)
            # Compute full variance curve for visualization
            self._otsu_curve, self._otsu_histogram = self._compute_otsu_curve(src_gray)
            return mask, None, None, None

        elif mode == 2:  # ERODE
            mask = VisionTools.threshold_binary(src_gray, 128)
            return VisionTools.morphological_erode(mask, self._kernel_size), None, None, None

        elif mode == 3:  # DILATE
            mask = VisionTools.threshold_binary(src_gray, 128)
            return VisionTools.morphological_dilate(mask, self._kernel_size), None, None, None

        elif mode == 4:  # OPEN
            mask = VisionTools.threshold_binary(src_gray, 128)
            return VisionTools.morphological_open(mask, self._kernel_size), None, None, None

        elif mode == 5:  # CLOSE
            mask = VisionTools.threshold_binary(src_gray, 128)
            return VisionTools.morphological_close(mask, self._kernel_size), None, None, None

        elif mode == 6:  # COMPONENTS
            mask = VisionTools.threshold_binary(src_gray, self._threshold)
            comp = VisionTools.connected_components(mask)
            return comp.label_surface, None, comp, None

        elif mode == 7:  # REGIONS
            mask = VisionTools.threshold_binary(src_gray, self._threshold)
            regions = VisionTools.analyze_regions(mask)
            comp = VisionTools.connected_components(mask)
            # Draw bounding rects on label surface
            result = comp.label_surface.copy()
            for ri in regions[:3]:
                bbox = ri.bounding_rect
                pygame.draw.rect(result, (255, 255, 255), bbox, 1)
                cx, cy = int(ri.centroid[0]), int(ri.centroid[1])
                pygame.draw.line(result, (255, 255, 255), (cx - 2, cy), (cx + 2, cy))
                pygame.draw.line(result, (255, 255, 255), (cx, cy - 2), (cx, cy + 2))
            return result, regions, comp, None

        elif mode == 8:  # WATERSHED
            if self._cached_watershed is not None:
                return self._cached_watershed, None, None, self._cached_watershed
            ws_surf, _ = VisionTools.watershed_segment(src)
            return ws_surf, None, None, ws_surf

        elif mode == 9:  # FEATURES
            method = FEATURE_METHODS[self._feat_method_idx]
            feat = VisionTools.extract_features(src, method=method)
            return _render_feature_vis(feat, method), None, None, None

        return pygame.Surface(PANEL_SIZE), None, None, None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "VISION DEMO", "UNIT VIII")

        mode_label = self._font_medium.render(
            f"  Mode: {MODE_NAMES[self._mode]}  ", True, COLOR_HIGHLIGHT,
        )
        surface.blit(mode_label, (4, TOP_BAR_Y + TOP_BAR_H - 14))

        src_label = self._font_small.render(
            f"  Source: {self._sources.current_name}"
            f"{' [FROZEN]' if self._sources.is_frozen else ''}  ", True, COLOR_ACCENT,
        )
        surface.blit(src_label, (90, TOP_BAR_Y + TOP_BAR_H - 14))

        self._draw_left_panel(surface)
        self._draw_right_panel(surface)
        draw_divider(surface)
        self._draw_bottom_bar(surface)

        if self._save_msg:
            pygame.draw.rect(surface, COLOR_TOP_BAR_BG,
                             (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
            draw_save_notification(surface, self._save_msg, self._font_small)

    def _draw_left_panel(self, surface: pygame.Surface) -> None:
        src = self._sources.current_source
        if src is not None:
            scaled = pygame.transform.scale(src, PANEL_SIZE)
            surface.blit(scaled, (0, TOP_BAR_H))
        draw_panel_border(surface, pygame.Rect(0, TOP_BAR_H, PANEL_SIZE[0], PANEL_H))

        if self._sources.is_frozen:
            ft = self._font_small.render("FROZEN", True, COLOR_HIGHLIGHT)
            surface.blit(ft, (4, TOP_BAR_H + 2))

    def _draw_right_panel(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(RIGHT_PANEL_X, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
        if self._cached_result is not None:
            scaled = pygame.transform.scale(self._cached_result, PANEL_SIZE)
            surface.blit(scaled, (RIGHT_PANEL_X, TOP_BAR_H))
        draw_panel_border(surface, rect)

        # Region info text overlay (modes 7)
        if self._mode == 7 and self._cached_regions:
            regions = self._cached_regions
            lines = [f"Regions found: {len(regions)}"]
            for i, ri in enumerate(regions[:3]):
                lines.append(f"#{i+1}  A={ri.area}  C=({int(ri.centroid[0])},{int(ri.centroid[1])})  "
                             f"Rect={ri.bounding_rect.width}x{ri.bounding_rect.height}")
            for li, line in enumerate(lines):
                rt = self._font_small.render(line, True, COLOR_GOLD)
                surface.blit(rt, (RIGHT_PANEL_X + 4, TOP_BAR_H + 4 + li * 10))

        # Otsu curve overlay (mode 1)
        if self._mode == 1 and self._otsu_curve:
            self._draw_otsu_curve(surface, rect)

        # Component count (mode 6)
        if self._mode == 6 and self._cached_comp_result is not None:
            comp = self._cached_comp_result
            ct = self._font_small.render(f"Components: {comp.num_components}", True, COLOR_HIGHLIGHT)
            surface.blit(ct, (RIGHT_PANEL_X + 4, TOP_BAR_H + 4))

        # Error overlay
        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, COLOR_ERROR)
            surface.blit(err, (RIGHT_PANEL_X + 4, TOP_BAR_H + 4))

    def _draw_otsu_curve(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        curve = self._otsu_curve
        hist = self._otsu_histogram
        if not curve:
            return
        w, h = rect.width, rect.height
        ox, oy = rect.x, rect.y
        margin = 10
        plot_w = w - 2 * margin
        plot_h = h - 2 * margin - 24
        # Histogram bars (thin, dim)
        max_hist = max(hist) if max(hist) > 0 else 1
        for t in range(256):
            if t >= len(hist):
                break
            bar_h = int(hist[t] / max_hist * plot_h * 0.4)
            x = ox + margin + int(t / 255 * plot_w)
            pygame.draw.line(surface, (40, 40, 60), (x, oy + h - margin - bar_h), (x, oy + h - margin), 1)
        # Variance curve
        pts = []
        for t, v in enumerate(curve):
            x = ox + margin + int(t / 255 * plot_w)
            y = oy + h - margin - int(v * plot_h)
            pts.append((x, y))
        if len(pts) > 1:
            pygame.draw.lines(surface, (80, 200, 255), False, pts, 1)
        # Otsu threshold marker
        ot = self._otsu_value
        mx = ox + margin + int(ot / 255 * plot_w)
        pygame.draw.line(surface, COLOR_GOLD, (mx, oy + margin), (mx, oy + h - margin), 2)
        label = self._font_small.render(f"Otsu t={ot}", True, COLOR_GOLD)
        surface.blit(label, (mx - 20, oy + margin))
        # Axis labels
        xlabel = self._font_small.render("Threshold  t  ->", True, COLOR_ACCENT)
        surface.blit(xlabel, (ox + margin, oy + h - 10))
        ylabel = self._font_small.render("sigma^2_B", True, COLOR_ACCENT)
        surface.blit(ylabel, (ox + 2, oy + margin))

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
            return (f"  Threshold: {self._threshold}  |  White pixels: ?  |  Black pixels: ?  |  "
                    f"[TAB: mode]")
        elif mode == 1:
            return (f"  Otsu threshold: {self._otsu_value}  |  "
                    f"Inter-class variance maximized at this value  |  [TAB: mode]")
        elif mode in (2, 3, 4, 5):
            return (f"  Pre-applied threshold: 128  |  Kernel: {self._kernel_size}x{self._kernel_size}  |  "
                    f"[TAB: mode]")
        elif mode == 6:
            return (f"  Components: ?  |  Threshold: {self._threshold}  |  "
                    f"[Color key: each color = distinct region]  |  [TAB: mode]")
        elif mode == 7:
            n = len(self._cached_regions) if self._cached_regions else 0
            return f"  Regions: {n}  |  Threshold: {self._threshold}  |  [TAB: mode]"
        elif mode == 8:
            return "  Watershed: pre-computed  |  Press S to save overlay  |  [TAB: mode]"
        elif mode == 9:
            method = FEATURE_METHODS[self._feat_method_idx]
            return f"  Method: {method}  |  Vector: ?  |  [UP/DOWN: cycle method]  |  [TAB: mode]"
        return ""


def _to_grayscale(surface: pygame.Surface) -> pygame.Surface:
    arr = pygame.surfarray.pixels3d(surface)
    gray = np.mean(arr, axis=2).astype(np.uint8)
    del arr
    gray3 = np.stack([gray, gray, gray], axis=-1)
    return pygame.surfarray.make_surface(gray3.transpose(1, 0, 2))


def _render_feature_vis(features: np.ndarray, method: str) -> pygame.Surface:
    surf = pygame.Surface(PANEL_SIZE)
    surf.fill((5, 5, 15))
    max_val = max(abs(features).max(), 1e-6)
    n = min(len(features), 512)
    bar_w = max(PANEL_SIZE[0] // n, 1)
    for i in range(n):
        h = int((features[i] / max_val) * (PANEL_H - 20) / 2)
        cy = PANEL_H // 2
        color = _method_color(method)
        if h >= 0:
            pygame.draw.rect(surf, color, (i * bar_w, cy - h, bar_w, h))
        else:
            pygame.draw.rect(surf, color, (i * bar_w, cy, bar_w, -h))
    return surf


def _method_color(method: str) -> tuple[int, int, int]:
    return {
        "hog": (80, 160, 255),
        "lbp": (60, 200, 60),
        "color_hist": (200, 60, 60),
        "combined": (255, 200, 80),
    }.get(method, (200, 200, 200))
