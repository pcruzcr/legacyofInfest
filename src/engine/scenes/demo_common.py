"""
Module: demo_common
Description: Legacy re-exports from demo_layout and demo_utils.
New imports should use the sub-modules directly.
"""
from __future__ import annotations

__all__ = [
    "TOP_BAR_H", "LEFT_PANEL_W", "RIGHT_PANEL_W", "PANEL_H", "BOTTOM_BAR_H",
    "TOP_BAR_Y", "LEFT_PANEL_X", "LEFT_PANEL_Y", "RIGHT_PANEL_X", "RIGHT_PANEL_Y", "BOTTOM_BAR_Y",
    "PANEL_W", "PANEL_SIZE", "CENTER_X", "CENTER_W",
    "COLOR_BG", "COLOR_TOP_BAR_BG", "COLOR_BOTTOM_BAR_BG", "COLOR_DIVIDER",
    "COLOR_TEXT", "COLOR_HIGHLIGHT", "COLOR_ACCENT", "COLOR_ERROR", "COLOR_GOLD",
    "FONT_SMALL", "FONT_MEDIUM", "FONT_LARGE",
    "draw_top_bar", "draw_bottom_bar", "draw_bottom_bar_error",
    "draw_panel_border", "draw_divider", "draw_save_notification", "draw_histogram_bars",
    "SourceSurfaceManager", "build_default_sources",
    "FrameThrottle", "ErrorDisplay",
    "save_png",
]

from src.engine.scenes.demo_layout import (
    TOP_BAR_H, LEFT_PANEL_W, RIGHT_PANEL_W, PANEL_H, BOTTOM_BAR_H,
    TOP_BAR_Y, LEFT_PANEL_X, LEFT_PANEL_Y, RIGHT_PANEL_X, RIGHT_PANEL_Y, BOTTOM_BAR_Y,
    PANEL_W, PANEL_SIZE, CENTER_X, CENTER_W,
    COLOR_BG, COLOR_TOP_BAR_BG, COLOR_BOTTOM_BAR_BG, COLOR_DIVIDER,
    COLOR_TEXT, COLOR_HIGHLIGHT, COLOR_ACCENT, COLOR_ERROR, COLOR_GOLD,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE,
    draw_top_bar, draw_bottom_bar, draw_bottom_bar_error,
    draw_panel_border, draw_divider, draw_save_notification, draw_histogram_bars,
)

from src.engine.scenes.demo_utils import (
    SourceSurfaceManager, build_default_sources,
    FrameThrottle, ErrorDisplay,
    save_png,
)
