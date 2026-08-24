from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import numpy as np
import pygame

from src.engine.core import settings
from src.engine.core.i18n import _
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import (
    BOTTOM_BAR_H,
    BOTTOM_BAR_Y,
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_ERROR,
    COLOR_GOLD,
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    COLOR_TOP_BAR_BG,
    FONT_LARGE,
    FONT_MEDIUM,
    FONT_SMALL,
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
    draw_panel_border,
    draw_save_notification,
    draw_top_bar,
    save_png,
)
from src.engine.ui.theme import font
from src.framework.processing.vision_tools import ComponentResult, RegionInfo, VisionTools

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext
    from src.engine.input.input_manager import InputManager


MODE_NAMES = [
    _("THRESHOLD"),
    _("OTSU"),
    _("ERODE"),
    _("DILATE"),
    _("OPEN"),
    _("CLOSE"),
    _("COMPONENTS"),
    _("REGIONS"),
    _("WATERSHED"),
    _("FEATURES"),
]

FEATURE_METHODS: list[Literal["hog", "lbp", "color_hist", "combined"]] = ["hog", "lbp", "color_hist", "combined"]


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
        self._cached_left_scaled: pygame.Surface | None = None
        self._cached_left_src: pygame.Surface | None = None
        self._cached_right_scaled: pygame.Surface | None = None
        self._cached_right_src: pygame.Surface | None = None
        self._cached_thumb: pygame.Surface | None = None
        self._cached_thumb_src: pygame.Surface | None = None
        self._cached_regions: list[RegionInfo] | None = None
        self._cached_comp_result: ComponentResult | None = None
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

        # Intermediate overlay state
        self._show_intermediate: bool = False
        self._inter_mask: pygame.Surface | None = None
        self._inter_histogram: list[int] = []
        self._inter_threshold: int = 128
        self._inter_pipeline_label: str = ""
        self._inter_pipeline_desc: str = ""
        self._inter_overlay: pygame.Surface | None = None

        self._font_small = font(FONT_SMALL)
        self._font_medium = font(FONT_MEDIUM)
        self._font_large = font(FONT_LARGE)
        self._font_overlay_small = font(11)
        self._font_overlay_med = font(13)

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

        if im.is_raw_key_pressed(pygame.K_i):
            self._show_intermediate = not self._show_intermediate

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        self._handle_mode_input(im)

        if self._param_changed or self._cached_result is None:
            self._compute_result()

    def _handle_mode_input(self, im: InputManager) -> None:
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
        try:
            gray = np.mean(arr, axis=2).astype(np.uint8).flatten()
        finally:
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
            result, regions, comp_info, ws, mask, hist = self._apply_mode(src)
            self._cached_result = result
            self._cached_regions = regions
            self._cached_comp_result = comp_info
            self._cached_watershed = ws
            self._inter_mask = mask
            self._inter_histogram = hist
            self._inter_threshold = self._threshold
            self._update_intermediate_label()
            self._error_msg = ""
        except (pygame.error, ValueError, ZeroDivisionError, np.linalg.LinAlgError) as e:
            logger.warning("vision_demo: compute error: %s", e)
            self._error_msg = f"Error: {e}"[:60]
            self._error_timer = 2.0

    def _update_intermediate_label(self) -> None:
        mode = self._mode
        labels = {
            0: ("Threshold", "Binary: pixels > T are white"),
            1: ("Otsu", "Auto-threshold via variance"),
            2: ("Erode", "Erode(Threshold(src))"),
            3: ("Dilate", "Dilate(Threshold(src))"),
            4: ("Open", "Erode(Dilate(Threshold(src)))"),
            5: ("Close", "Dilate(Erode(Threshold(src)))"),
            6: ("Components", "Label(Threshold(src))"),
            7: ("Regions", "Analyze(Label(Threshold(src)))"),
            8: ("Watershed", "Segment(Gradient(src))"),
            9: ("Features", "Extract(" + FEATURE_METHODS[self._feat_method_idx] + ")"),
        }
        if mode in labels:
            self._inter_pipeline_label, self._inter_pipeline_desc = labels[mode]

    def _compute_histogram(self, src: pygame.Surface) -> list[int]:
        """Compute luminance histogram (256 bins) for intermediate self._inter_overlay."""
        gray = _to_grayscale(src)
        arr = pygame.surfarray.pixels3d(gray)
        try:
            lum = np.mean(arr[:, :, 0], axis=1).astype(np.uint8)
        finally:
            del arr
        hist = np.bincount(lum, minlength=256).tolist()
        return hist

    def _apply_mode(
        self, src: pygame.Surface
    ) -> tuple[pygame.Surface | None, list[RegionInfo] | None, ComponentResult | None, pygame.Surface | None, pygame.Surface | None, list[int]]:
        """Apply the current vision mode. Returns (result, regions, comp, watershed, intermediate_mask, histogram)."""
        mode = self._mode
        src_gray = _to_grayscale(src)
        hist = self._compute_histogram(src)
        inter_mask: pygame.Surface | None = None

        if mode == 0:  # THRESHOLD
            inter_mask = src_gray
            mask = VisionTools.threshold_binary(src_gray, self._threshold)
            return mask, None, None, None, inter_mask, hist

        elif mode == 1:  # OTSU
            inter_mask = src_gray
            mask, otsu_val = VisionTools.threshold_otsu(src_gray)
            self._otsu_value = int(otsu_val)
            self._otsu_curve, self._otsu_histogram = self._compute_otsu_curve(src_gray)
            return mask, None, None, None, inter_mask, hist

        elif mode in (2, 3, 4, 5):  # ERODE, DILATE, OPEN, CLOSE
            mask = VisionTools.threshold_binary(src_gray, self._threshold)
            inter_mask = mask
            if mode == 2:
                result = VisionTools.morphological_erode(mask, self._kernel_size)
            elif mode == 3:
                result = VisionTools.morphological_dilate(mask, self._kernel_size)
            elif mode == 4:
                result = VisionTools.morphological_open(mask, self._kernel_size)
            else:
                result = VisionTools.morphological_close(mask, self._kernel_size)
            return result, None, None, None, inter_mask, hist

        elif mode in (6, 7):  # COMPONENTS, REGIONS
            mask = VisionTools.threshold_binary(src_gray, self._threshold)
            inter_mask = mask
            comp = VisionTools.connected_components(mask)
            if mode == 6:
                return comp.label_surface, None, comp, None, inter_mask, hist
            else:
                regions = VisionTools.analyze_regions(mask)
                result = comp.label_surface.copy()
                for ri in regions[:3]:
                    bbox = ri.bounding_rect
                    pygame.draw.rect(result, (255, 255, 255), bbox, 1)
                    cx, cy = int(ri.centroid[0]), int(ri.centroid[1])
                    pygame.draw.line(result, (255, 255, 255), (cx - 2, cy), (cx + 2, cy))
                    pygame.draw.line(result, (255, 255, 255), (cx, cy - 2), (cx, cy + 2))
                return result, regions, comp, None, inter_mask, hist

        elif mode == 8:  # WATERSHED
            if self._cached_watershed is not None:
                return self._cached_watershed, None, None, self._cached_watershed, src_gray, hist
            ws_surf, _ = VisionTools.watershed_segment(src)
            return ws_surf, None, None, ws_surf, src_gray, hist

        elif mode == 9:  # FEATURES
            method = FEATURE_METHODS[self._feat_method_idx]
            feat = VisionTools.extract_features(src, method=method)
            inter_mask = src_gray
            return _render_feature_vis(feat, method), None, None, None, inter_mask, hist

        return pygame.Surface(PANEL_SIZE), None, None, None, None, hist

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "VISION DEMO", "UNIT VIII")

        mode_label = self._font_medium.render(
            f"  Mode: {MODE_NAMES[self._mode]}  ", True, COLOR_HIGHLIGHT,
        )
        surface.blit(mode_label, (4, TOP_BAR_Y + TOP_BAR_H - 14))

        # Education overlay
        _edu = {
            0: ("Threshold", "Binary segmentation: pixels above/below threshold → white/black."),
            1: ("Otsu", "Automatic threshold by maximizing inter-class variance."),
            2: ("Erode", "Morphological erosion: removes small white noise; shrinks foreground."),
            3: ("Dilate", "Morphological dilation: expands foreground; fills small holes."),
            4: ("Open", "Erode then dilate: removes noise without shrinking objects much."),
            5: ("Close", "Dilate then erode: fills gaps/holes inside objects."),
            6: ("Components", "Connected-component labeling: unique IDs for contiguous regions."),
            7: ("Regions", "Region properties: area, centroid, bounding box per component."),
            8: ("Watershed", "Segmentation treating gradient as topography; basins = segments."),
            9: ("Features", "Feature visualization for HOG/LBP/color_hist/combined descriptors."),
        }
        if self._mode in _edu:
            edu_title, edu_desc = _edu[self._mode]
            t1 = self._font_small.render(f"  {edu_title}", True, COLOR_HIGHLIGHT)
            t2 = self._font_small.render(f"  {edu_desc}", True, COLOR_TEXT)
            surface.blit(t1, (RIGHT_PANEL_X, TOP_BAR_Y + 2))
            surface.blit(t2, (RIGHT_PANEL_X, TOP_BAR_Y + 14))

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
            if self._cached_left_src is not src:
                self._cached_left_scaled = pygame.transform.scale(src, PANEL_SIZE)
                self._cached_left_src = src
            surface.blit(self._cached_left_scaled, (0, TOP_BAR_H))
        draw_panel_border(surface, pygame.Rect(0, TOP_BAR_H, PANEL_SIZE[0], PANEL_H))

        if self._sources.is_frozen:
            ft = self._font_small.render("FROZEN", True, COLOR_HIGHLIGHT)
            surface.blit(ft, (4, TOP_BAR_H + 2))

    def _draw_right_panel(self, surface: pygame.Surface) -> None:
        rect = pygame.Rect(RIGHT_PANEL_X, TOP_BAR_H, PANEL_SIZE[0], PANEL_H)
        if self._cached_result is not None:
            if self._cached_right_src is not self._cached_result:
                self._cached_right_scaled = pygame.transform.scale(self._cached_result, PANEL_SIZE)
                self._cached_right_src = self._cached_result
            surface.blit(self._cached_right_scaled, (RIGHT_PANEL_X, TOP_BAR_H))
        draw_panel_border(surface, rect)

        # Region info text overlay (modes 7)
        if self._mode == 7 and self._cached_regions:
            regions = self._cached_regions
            lines = [f"Regions found: {len(regions)}"]
            for i, ri in enumerate(regions[:3]):
                lines.append(f"#{i + 1}  A={ri.area}  C=({int(ri.centroid[0])},{int(ri.centroid[1])})  "
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

        # Intermediate overlay (if toggled)
        if self._show_intermediate:
            self._draw_intermediate_overlay(surface)

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

    def _draw_intermediate_overlay(self, surface: pygame.Surface) -> None:
        """Draw a semi-transparent overlay showing intermediate steps (histogram, mask, pipeline)."""
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        if self._inter_overlay is None or self._inter_overlay.get_size() != (w, h):
            self._inter_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        self._inter_overlay.fill((0, 0, 0, 190))

        box_w = 300
        box_h = 180
        bx = (w - box_w) // 2
        by = (h - box_h) // 2 - 10

        pygame.draw.rect(self._inter_overlay, (15, 15, 45), (bx, by, box_w, box_h))
        pygame.draw.rect(self._inter_overlay, COLOR_HIGHLIGHT, (bx, by, box_w, box_h), 1)

        # Pipeline label
        pipe_label = self._font_overlay_med.render(f"Pipeline: {self._inter_pipeline_label}", True, COLOR_HIGHLIGHT)
        self._inter_overlay.blit(pipe_label, (bx + 6, by + 4))
        pipe_desc = self._font_overlay_small.render(self._inter_pipeline_desc, True, COLOR_ACCENT)
        self._inter_overlay.blit(pipe_desc, (bx + 6, by + 18))

        # Histogram (if available)
        if self._inter_histogram:
            hist = self._inter_histogram
            max_hist = max(hist) if max(hist) > 0 else 1
            hist_w = box_w - 100
            hist_h = 50
            hx = bx + 50
            hy = by + 34
            pygame.draw.rect(self._inter_overlay, (10, 10, 30), (hx, hy, hist_w, hist_h))
            for t in range(256):
                bar_h = int(hist[t] / max_hist * hist_h)
                px = hx + int(t / 255 * hist_w)
                pygame.draw.line(self._inter_overlay, (80, 140, 200), (px, hy + hist_h), (px, hy + hist_h - bar_h), 1)
            # Threshold marker
            if self._mode in (0, 2, 3, 4, 5, 6, 7):
                tx = hx + int(self._inter_threshold / 255 * hist_w)
                pygame.draw.line(self._inter_overlay, COLOR_GOLD, (tx, hy), (tx, hy + hist_h), 2)
                tlabel = self._font_overlay_small.render(f"T={self._inter_threshold}", True, COLOR_GOLD)
                self._inter_overlay.blit(tlabel, (tx - 14, hy + hist_h + 2))
            # Otsu marker
            if self._mode == 1:
                tx = hx + int(self._otsu_value / 255 * hist_w)
                pygame.draw.line(self._inter_overlay, (80, 200, 80), (tx, hy), (tx, hy + hist_h), 2)
                tlabel = self._font_overlay_small.render(f"Otsu T={self._otsu_value}", True, (80, 200, 80))
                self._inter_overlay.blit(tlabel, (tx - 18, hy + hist_h + 2))
            h_label = self._font_overlay_small.render("Histogram", True, COLOR_TEXT)
            self._inter_overlay.blit(h_label, (bx + 6, hy + 2))

        # Binary mask thumbnail (if available)
        if self._inter_mask is not None and self._mode not in (8, 9):
            thumb_size = 60
            tx = bx + 6
            ty = by + box_h - thumb_size - 6
            if self._cached_thumb_src is not self._inter_mask:
                self._cached_thumb = pygame.transform.scale(self._inter_mask, (thumb_size, thumb_size))
                self._cached_thumb_src = self._inter_mask
            self._inter_overlay.blit(self._cached_thumb, (tx, ty))
            pygame.draw.rect(self._inter_overlay, COLOR_ACCENT, (tx, ty, thumb_size, thumb_size), 1)
            ml = self._font_overlay_small.render("Mask", True, COLOR_TEXT)
            self._inter_overlay.blit(ml, (tx, ty - 10))

        # White/black pixel stats for threshold modes
        if self._inter_mask is not None and self._mode in (0, 1, 2, 3, 4, 5):
            try:
                arr = pygame.surfarray.pixels3d(self._inter_mask)
                try:
                    total = arr.shape[0] * arr.shape[1]
                    white = int(np.sum(arr[:, :, 0] > 127))
                    black = total - white
                finally:
                    del arr
                stats_y = by + box_h - 16
                stats = self._font_overlay_small.render(f"White: {white}px ({white*100//total}%)  Black: {black}px ({black*100//total}%)", True, COLOR_TEXT)
                self._inter_overlay.blit(stats, (bx + 6, stats_y))
            except (pygame.error, ValueError, RuntimeError) as e:
                logger.warning("vision_demo: pixel stats failed: %s", e)

        # Kernel overlay for morph modes
        if self._mode in (2, 3, 4, 5):
            k_label = self._font_overlay_small.render(f"Kernel: {self._kernel_size}x{self._kernel_size}", True, COLOR_HIGHLIGHT)
            self._inter_overlay.blit(k_label, (bx + box_w - 90, by + 4))
            # Draw kernel grid
            kx = bx + box_w - 80
            ky = by + 18
            cell = 4
            kernel_w = self._kernel_size * cell
            for row in range(self._kernel_size):
                for col in range(self._kernel_size):
                    pygame.draw.rect(self._inter_overlay, (200, 200, 100), (kx + col * cell, ky + row * cell, cell, cell))
            pygame.draw.rect(self._inter_overlay, COLOR_ACCENT, (kx, ky, kernel_w, kernel_w), 1)

        # Component sizes for COMPONENTS mode
        if self._mode == 6 and self._cached_comp_result is not None:
            comp = self._cached_comp_result
            sizes = sorted(comp.component_sizes.values(), reverse=True)[:8]
            max_sz = max(sizes) if sizes else 1
            bar_x = bx + box_w - 80
            bar_y = by + 80
            for i, sz in enumerate(sizes):
                bw = int(sz / max_sz * 30)
                pygame.draw.rect(self._inter_overlay, (80 + i * 20, 160, 200 - i * 15), (bar_x, bar_y + i * 6, bw, 4))
            sz_label = self._font_overlay_small.render(f"Top {len(sizes)} comps", True, COLOR_TEXT)
            self._inter_overlay.blit(sz_label, (bar_x, bar_y - 10))

        # Feature method info
        if self._mode == 9:
            method = FEATURE_METHODS[self._feat_method_idx]
            feat_label = self._font_overlay_small.render(f"Descriptor: {method.upper()}", True, COLOR_HIGHLIGHT)
            self._inter_overlay.blit(feat_label, (bx + 6, by + box_h - 30))

        hint = self._font_overlay_small.render(_("Press I to close intermediate view"), True, (100, 100, 140))
        self._inter_overlay.blit(hint, (bx + 6, by + box_h - 12))

        surface.blit(self._inter_overlay, (0, 0))

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
        base_hint = " [I] intermediate view"
        if mode == 0:
            return (f"  Threshold: {self._threshold}  |  "
                    f"[LEFT/RIGHT: adjust]{base_hint}  |  [TAB] mode")
        elif mode == 1:
            return (f"  Otsu threshold: {self._otsu_value}  |  "
                    f"[TAB]{base_hint}")
        elif mode in (2, 3, 4, 5):
            return (f"  Pre-threshold: 128  |  Kernel: {self._kernel_size}x{self._kernel_size}  |  "
                    f"[LEFT/RIGHT: adjust]{base_hint}  |  [TAB] mode")
        elif mode == 6:
            return (f"  Threshold: {self._threshold}  |  "
                    f"[LEFT/RIGHT: adjust]{base_hint}  |  [TAB] mode")
        elif mode == 7:
            n = len(self._cached_regions) if self._cached_regions else 0
            return f"  Regions: {n}{base_hint}  |  [TAB] mode"
        elif mode == 8:
            return f"  Watershed{base_hint}  |  [TAB] mode"
        elif mode == 9:
            method = FEATURE_METHODS[self._feat_method_idx]
            return f"  Method: {method}{base_hint}  |  [UP/DOWN: cycle]  |  [TAB] mode"
        return ""


def _to_grayscale(surface: pygame.Surface) -> pygame.Surface:
    arr = pygame.surfarray.pixels3d(surface)
    try:
        gray = np.mean(arr, axis=2).astype(np.uint8)
    finally:
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
