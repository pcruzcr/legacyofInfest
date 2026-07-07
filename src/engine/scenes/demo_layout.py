"""
Module: demo_layout
Description: Layout constants and drawing helpers shared by all
academic demonstration scenes.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader


# ── Layout Constants ──────────────────────────────────────────────
TOP_BAR_H = 24
LEFT_PANEL_W = 160
RIGHT_PANEL_W = 160
PANEL_H = 176
BOTTOM_BAR_H = 24

TOP_BAR_Y = 0
LEFT_PANEL_X = 0
LEFT_PANEL_Y = TOP_BAR_H
RIGHT_PANEL_X = LEFT_PANEL_W
RIGHT_PANEL_Y = TOP_BAR_H
BOTTOM_BAR_Y = TOP_BAR_H + PANEL_H

PANEL_W = LEFT_PANEL_W
PANEL_SIZE = (PANEL_W, PANEL_H)

# Colors
COLOR_BG = (10, 10, 30)
COLOR_TOP_BAR_BG = (20, 20, 50)
COLOR_BOTTOM_BAR_BG = (20, 20, 50)
COLOR_DIVIDER = (60, 60, 100)
COLOR_TEXT = (200, 200, 200)
COLOR_HIGHLIGHT = (255, 220, 80)
COLOR_ACCENT = (100, 180, 255)
COLOR_ERROR = (255, 60, 60)
COLOR_GOLD = (255, 200, 50)

# Font sizes
FONT_SMALL = 7
FONT_MEDIUM = 9
FONT_LARGE = 11

# Shared font cache (per-size singleton fonts)
_FONT_CACHE: dict[int, pygame.font.Font] = {}


def _get_demo_font(size: int) -> pygame.font.Font:
    key = size
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", size)
    return _FONT_CACHE[key]


def draw_top_bar(surface: pygame.Surface, title: str, unit: str) -> None:
    pygame.draw.rect(surface, COLOR_TOP_BAR_BG,
                     (0, TOP_BAR_Y, settings.INTERNAL_WIDTH, TOP_BAR_H))
    fnt = _get_demo_font(FONT_MEDIUM)
    ts = fnt.render(f"  {title}", True, COLOR_HIGHLIGHT)
    surface.blit(ts, (4, TOP_BAR_Y + 2))
    ts2 = fnt.render(f"{unit}  ", True, COLOR_ACCENT)
    tw = ts2.get_width()
    surface.blit(ts2, (settings.INTERNAL_WIDTH - tw - 4, TOP_BAR_Y + 2))


def draw_bottom_bar(surface: pygame.Surface, text: str) -> None:
    pygame.draw.rect(surface, COLOR_BOTTOM_BAR_BG,
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = _get_demo_font(FONT_SMALL)
    ts = fnt.render(text, True, COLOR_TEXT)
    surface.blit(ts, (4, BOTTOM_BAR_Y + 2))


def draw_bottom_bar_error(surface: pygame.Surface, error: str) -> None:
    pygame.draw.rect(surface, (40, 10, 10),
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = _get_demo_font(FONT_SMALL)
    ts = fnt.render(error, True, COLOR_ERROR)
    surface.blit(ts, (4, BOTTOM_BAR_Y + 2))


def draw_panel_border(surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, COLOR_DIVIDER, panel_rect, 1)


def draw_divider(surface: pygame.Surface) -> None:
    x = LEFT_PANEL_W
    pygame.draw.line(surface, COLOR_DIVIDER, (x, TOP_BAR_Y), (x, TOP_BAR_Y + PANEL_H), 1)


def draw_save_notification(surface: pygame.Surface, saved_path: str, font: pygame.font.Font) -> None:
    ts = font.render(f"Saved: {saved_path}", True, COLOR_GOLD)
    surface.blit(ts, (4, BOTTOM_BAR_Y + 2))


def draw_histogram_bars(
    surface: pygame.Surface,
    rect: pygame.Rect,
    hist_r: list[int],
    hist_g: list[int],
    hist_b: list[int],
    bar_w: int = 2,
    max_h: int = 40,
) -> None:
    bar_area = pygame.Rect(rect.x, rect.y + rect.h - max_h - 2, rect.w, max_h + 2)
    pygame.draw.rect(surface, (5, 5, 15), bar_area)
    n = min(len(hist_r), bar_area.w // bar_w)
    if n == 0:
        return
    step = len(hist_r) // n
    max_val = max(max(hist_r), max(hist_g), max(hist_b)) + 1
    for i in range(n):
        idx = i * step
        for channel, hist, color in [(0, hist_r, (255, 60, 60)),
                                     (1, hist_g, (60, 200, 60)),
                                     (2, hist_b, (60, 60, 255))]:
            h_val = int((hist[idx] / max_val) * max_h)
            if h_val > 0:
                bx = bar_area.x + i * bar_w + 1
                by = bar_area.bottom - 2 - channel * (max_h // 3 + 2) - h_val
                bw = max(bar_w - 2, 1)
                pygame.draw.rect(surface, color, (bx, by, bw, h_val))
