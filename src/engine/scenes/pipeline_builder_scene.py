"""
PipelineBuilderScene — Visual filter chain builder.

Students can build a processing pipeline by selecting filters
in sequence and seeing the result in real-time.
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
    COLOR_BG, COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT,
    FONT_SMALL, FONT_MEDIUM,
    draw_top_bar, draw_bottom_bar,
    build_default_sources, SourceSurfaceManager,
    PANEL_SIZE, PANEL_H, TOP_BAR_H,
    draw_panel_border, RIGHT_PANEL_X,
)
from src.engine.utils.asset_loader import AssetLoader
from src.framework.processing.filter_tools import FilterTools

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


AVAILABLE_FILTERS = [
    ("Brightness", lambda s: FilterTools.adjust_brightness(s, 1.5)),
    ("Contrast", lambda s: FilterTools.adjust_contrast(s, 1.5)),
    ("Stretch", lambda s: FilterTools.stretch_contrast(s)),
    ("Sharpen", lambda s: FilterTools.apply_kernel(s, FilterTools.get_standard_kernel("sharpen"))),
    ("Box Blur", lambda s: FilterTools.apply_kernel(s, FilterTools.get_standard_kernel("box_blur"))),
    ("Gaussian", lambda s: FilterTools.gaussian_blur(s, 2.0)),
    ("Sobel Edge", lambda s: FilterTools.sobel_edge(s)),
    ("Canny Edge", lambda s: FilterTools.canny_edge(s, 50, 150)),
    ("Equalize", lambda s: FilterTools.histogram_equalize(s)),
    ("Emboss", lambda s: FilterTools.apply_kernel(s, FilterTools.get_standard_kernel("emboss"))),
    ("Laplacian", lambda s: FilterTools.apply_kernel(s, FilterTools.get_standard_kernel("edge_laplacian"))),
]

# Pre-built filter chains. Each list references indices in AVAILABLE_FILTERS.
# Press P in the pipeline builder to cycle through presets.
PRESETS: dict[str, list[int]] = {
    "grabado": [10, 7, 1],  # Emboss -> Sobel -> Contrast
    "acuarela": [5, 9, 4],  # Gaussian -> Emboss -> Sharpen
    "boceto": [7, 1, 9],    # Sobel -> Contrast -> Emboss
    "retro": [4, 8, 0],     # Sharpen -> Equalize -> Brightness
    "neon": [0, 1, 7],      # Brightness -> Contrast -> Sobel
    "suave": [5, 10, 4],    # Gaussian -> Laplacian -> Sharpen
}


class PipelineBuilderScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._sources: SourceSurfaceManager = build_default_sources()
        self._pipeline: list[int] = []
        self._selected_filter: int = 0
        self._cursor: int = -1  # -1 = not inserting, >=0 = position
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
        self._font_medium = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
        self._cached_result: pygame.Surface | None = None
        self._cached_left_scaled: pygame.Surface | None = None
        self._cached_left_src: pygame.Surface | None = None
        self._cached_right_scaled: pygame.Surface | None = None
        self._cached_right_src: pygame.Surface | None = None
        self._save_msg: str = ""
        self._save_timer: float = 0.0
        self._error_msg: str = ""
        self._error_timer: float = 0.0
        self._preset_msg: str = ""
        self._preset_timer: float = 0.0
        self._preset_names: list[str] = list(PRESETS.keys())
        self._selected_preset: int = 0

    def on_enter(self) -> None:
        self._pipeline = []
        self._selected_filter = 0
        self._cursor = -1

    def on_exit(self) -> None:
        pass

    def _recompute(self) -> None:
        src = self._sources.current_source
        if src is None:
            self._cached_result = pygame.Surface(PANEL_SIZE)
            self._cached_result.fill((0, 0, 0))
            return
        try:
            result = src.copy()
            for idx in self._pipeline:
                if 0 <= idx < len(AVAILABLE_FILTERS):
                    _, func = AVAILABLE_FILTERS[idx]
                    result = func(result)
            result = pygame.transform.scale(result, PANEL_SIZE)
            self._cached_result = result
            self._error_msg = ""
        except (pygame.error, ValueError, ZeroDivisionError) as e:
            logging.warning("pipeline_builder: recompute error: %s", e)
            self._error_msg = f"Pipeline error: {e}"[:60]
            self._error_timer = 2.0

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._save_timer > 0:
            self._save_timer -= dt
            if self._save_timer <= 0:
                self._save_msg = ""
        if self._preset_timer > 0:
            self._preset_timer -= dt
            if self._preset_timer <= 0:
                self._preset_msg = ""

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.demo_menu_scene import DemoMenuScene
            self.context.scene_manager.replace(DemoMenuScene(self.context))
            return

        if im.is_raw_key_pressed(pygame.K_TAB):
            self._selected_filter = (self._selected_filter + 1) % len(AVAILABLE_FILTERS)

        if im.is_raw_key_pressed(pygame.K_SPACE):
            if self._cursor < 0:
                self._cursor = len(self._pipeline)
            self._pipeline.insert(self._cursor, self._selected_filter)
            self._cursor += 1
            self._recompute()

        if im.is_raw_key_pressed(pygame.K_BACKSPACE) or im.is_raw_key_pressed(pygame.K_DELETE):
            if self._pipeline:
                self._pipeline.pop()
                self._cursor = min(self._cursor, len(self._pipeline) - 1) if self._cursor >= 0 else -1
                self._recompute()

        if im.is_raw_key_pressed(pygame.K_r):
            self._pipeline.clear()
            self._cursor = -1
            self._cached_result = None

        if im.is_raw_key_pressed(pygame.K_p):
            self._selected_preset = (self._selected_preset + 1) % len(self._preset_names)
            pname = self._preset_names[self._selected_preset]
            self._pipeline = list(PRESETS[pname])
            self._cursor = len(self._pipeline) - 1 if self._pipeline else -1
            self._recompute()
            self._preset_msg = f"Preset: {pname}"
            self._preset_timer = 2.0

        if im.is_raw_key_pressed(pygame.K_s):
            if self._cached_result is not None:
                from src.engine.scenes.demo_utils import save_png as sp
                path = sp("pipeline", "built", self._cached_result)
                self._save_msg = f"Saved: {path}"
                self._save_timer = 2.0

        if im.is_raw_key_pressed(pygame.K_f):
            if self._sources.is_frozen:
                self._sources.unfreeze()
            else:
                self._sources.freeze()
            self._recompute()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)
        draw_top_bar(surface, "FILTER PIPELINE BUILDER", "UNIT VII/VIII")

        left_panel_y = TOP_BAR_H
        right_panel_x = RIGHT_PANEL_X

        # Left panel: source image
        src = self._sources.current_source
        if src is not None:
            if self._cached_left_src is not src:
                self._cached_left_scaled = pygame.transform.scale(src, PANEL_SIZE)
                self._cached_left_src = src
            surface.blit(self._cached_left_scaled, (0, left_panel_y))
        draw_panel_border(surface, pygame.Rect(0, left_panel_y, PANEL_SIZE[0], PANEL_H))

        src_label = self._font_small.render(
            f"  Source: {self._sources.current_name}", True, COLOR_ACCENT)
        surface.blit(src_label, (4, left_panel_y + 2))

        if self._sources.is_frozen:
            frozen_text = self._font_small.render("  FROZEN", True, COLOR_HIGHLIGHT)
            surface.blit(frozen_text, (4, left_panel_y + 14))

        # Right panel: result
        right_rect = pygame.Rect(right_panel_x, left_panel_y, PANEL_SIZE[0], PANEL_H)
        if self._cached_result is not None:
            if self._cached_right_src is not self._cached_result:
                self._cached_right_scaled = pygame.transform.scale(self._cached_result, PANEL_SIZE)
                self._cached_right_src = self._cached_result
            surface.blit(self._cached_right_scaled, (right_panel_x, left_panel_y))
        else:
            no_result = self._font_medium.render("  Press SPACE to add filters", True, COLOR_TEXT)
            surface.blit(no_result, (right_panel_x + 10, left_panel_y + 40))
        draw_panel_border(surface, right_rect)

        if self._error_msg:
            err = self._font_small.render(self._error_msg, True, (255, 80, 80))
            surface.blit(err, (right_panel_x + 4, left_panel_y + 4))

        # Pipeline display
        py = left_panel_y + PANEL_H + 4
        pipeline_header = self._font_small.render(
            "  Pipeline (SPACE to add, BACKSPACE to remove, R to reset):", True, COLOR_TEXT)
        surface.blit(pipeline_header, (4, py))
        py += 16

        if not self._pipeline:
            empty = self._font_small.render("  [empty pipeline]", True, COLOR_ACCENT)
            surface.blit(empty, (16, py))
        else:
            pipe_str = "  →  ".join(
                AVAILABLE_FILTERS[idx][0] for idx in self._pipeline
            )
            for i in range(0, len(pipe_str), 56):
                line = pipe_str[i:i + 56]
                txt = self._font_small.render(f"  {line}", True, COLOR_HIGHLIGHT)
                surface.blit(txt, (16, py))
                py += 12

        # Filter selection
        fy = py + 8
        sel_name = AVAILABLE_FILTERS[self._selected_filter][0]
        sel_text = self._font_medium.render(
            f"  Selected: {sel_name}  (TAB to change)", True, COLOR_HIGHLIGHT)
        surface.blit(sel_text, (4, fy))

        # Available filters list
        for i, (fname, _) in enumerate(AVAILABLE_FILTERS):
            color = COLOR_HIGHLIGHT if i == self._selected_filter else COLOR_TEXT
            marker = ">" if i == self._selected_filter else " "
            added_count = sum(1 for p in self._pipeline if p == i)
            count_str = f" (x{added_count})" if added_count > 0 else ""
            ftext = self._font_small.render(f"  {marker} {fname}{count_str}", True, color)
            surface.blit(ftext, (16, fy + 14 + i * 12))

        # Presets section
        preset_y = fy + 14 + len(AVAILABLE_FILTERS) * 12 + 8
        preset_header = self._font_small.render("  PRESETS (P to cycle):", True, COLOR_ACCENT)
        surface.blit(preset_header, (4, preset_y))
        for i, pname in enumerate(self._preset_names):
            color = COLOR_HIGHLIGHT if i == self._selected_preset else COLOR_TEXT
            marker = ">" if i == self._selected_preset else " "
            ptxt = self._font_small.render(f"  {marker} {pname}", True, color)
            surface.blit(ptxt, (16, preset_y + 12 + i * 12))

        # Preset notification
        if self._preset_msg and self._preset_timer > 0:
            pn = self._font_small.render(self._preset_msg, True, COLOR_HIGHLIGHT)
            surface.blit(pn, (4, BOTTOM_BAR_Y - 16))

        # Save notification
        if self._save_msg:
            sn = self._font_small.render(self._save_msg, True, COLOR_HIGHLIGHT)
            surface.blit(sn, (4, BOTTOM_BAR_Y - 30))

        draw_bottom_bar(surface, (
            "  [TAB] select filter  [SPACE] add  [BACKSPACE] remove  [P] preset  "
            "[F] freeze  [S] save  [R] reset  [ESC] exit"
        ))

