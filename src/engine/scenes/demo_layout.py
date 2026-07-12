"""
Module: demo_layout
Description: Resolution-responsive layout constants and drawing helpers
shared by all academic demonstration scenes.

All constants are computed from settings.INTERNAL_WIDTH and
settings.INTERNAL_HEIGHT so the UI adapts to any resolution.
Minimum tested: 800x600.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader


# ── Computed Layout Constants ──────────────────────────────────────
# These scale with INTERNAL_WIDTH and INTERNAL_HEIGHT.
# Override via env vars: LOI_TOP_BAR_H=40 LOI_PANEL_W=300 etc.

def _env_int(key: str, default: int) -> int:
    import os
    val = os.environ.get(key)
    return int(val) if val and val.lstrip("-").isdigit() else default

# Top bar: 5% of height, min 28px, max 48px
TOP_BAR_H: int = max(28, min(48, int(settings.INTERNAL_HEIGHT * 0.055)))
# Bottom bar: 4% of height, min 20px, max 32px
BOTTOM_BAR_H: int = max(20, min(32, int(settings.INTERNAL_HEIGHT * 0.04)))
# Panel width: 32% of total width each, min 200px
PANEL_W: int = max(200, int(settings.INTERNAL_WIDTH * 0.32))
LEFT_PANEL_W: int = PANEL_W
RIGHT_PANEL_W: int = PANEL_W
# Panel height: fill space between top bar and bottom bar minus reserves
_RESERVE_Y: int = max(60, int(settings.INTERNAL_HEIGHT * 0.10))
PANEL_H: int = max(180, settings.INTERNAL_HEIGHT - TOP_BAR_H - BOTTOM_BAR_H - _RESERVE_Y)

TOP_BAR_Y: int = 0
LEFT_PANEL_X: int = 0
LEFT_PANEL_Y: int = TOP_BAR_H
RIGHT_PANEL_X: int = settings.INTERNAL_WIDTH - RIGHT_PANEL_W
RIGHT_PANEL_Y: int = TOP_BAR_H
BOTTOM_BAR_Y: int = settings.INTERNAL_HEIGHT - BOTTOM_BAR_H

PANEL_SIZE: tuple[int, int] = (PANEL_W, PANEL_H)

# Center area (between panels) for controls/info
CENTER_X: int = LEFT_PANEL_W + 8
CENTER_W: int = max(100, RIGHT_PANEL_X - LEFT_PANEL_W - 16)

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

# Font sizes — scale with resolution
FONT_SMALL: int = max(12, settings.INTERNAL_WIDTH // 55)
FONT_MEDIUM: int = max(15, settings.INTERNAL_WIDTH // 42)
FONT_LARGE: int = max(18, settings.INTERNAL_WIDTH // 35)

# Shared font cache
_FONT_CACHE: dict[int, pygame.font.Font] = {}

# ── Public: re-export everything that demo_common exposes ──────────
__all__ = [
    "TOP_BAR_H", "LEFT_PANEL_W", "RIGHT_PANEL_W", "PANEL_H", "BOTTOM_BAR_H",
    "TOP_BAR_Y", "LEFT_PANEL_X", "LEFT_PANEL_Y", "RIGHT_PANEL_X", "RIGHT_PANEL_Y",
    "BOTTOM_BAR_Y", "PANEL_W", "PANEL_SIZE", "CENTER_X", "CENTER_W",
    "COLOR_BG", "COLOR_TOP_BAR_BG", "COLOR_BOTTOM_BAR_BG", "COLOR_DIVIDER",
    "COLOR_TEXT", "COLOR_HIGHLIGHT", "COLOR_ACCENT", "COLOR_ERROR", "COLOR_GOLD",
    "FONT_SMALL", "FONT_MEDIUM", "FONT_LARGE",
    "draw_top_bar", "draw_bottom_bar", "draw_bottom_bar_error",
    "draw_panel_border", "draw_divider", "draw_save_notification", "draw_histogram_bars",
]


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
    surface.blit(ts, (8, TOP_BAR_Y + (TOP_BAR_H - ts.get_height()) // 2))
    ts2 = fnt.render(f"{unit}  ", True, COLOR_ACCENT)
    tw = ts2.get_width()
    surface.blit(ts2, (settings.INTERNAL_WIDTH - tw - 8, TOP_BAR_Y + (TOP_BAR_H - ts2.get_height()) // 2))


def draw_bottom_bar(surface: pygame.Surface, text: str) -> None:
    pygame.draw.rect(surface, COLOR_BOTTOM_BAR_BG,
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = _get_demo_font(FONT_SMALL)
    ts = fnt.render(text, True, COLOR_TEXT)
    surface.blit(ts, (8, BOTTOM_BAR_Y + (BOTTOM_BAR_H - ts.get_height()) // 2))


def draw_bottom_bar_error(surface: pygame.Surface, error: str) -> None:
    pygame.draw.rect(surface, (40, 10, 10),
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = _get_demo_font(FONT_SMALL)
    ts = fnt.render(error, True, COLOR_ERROR)
    surface.blit(ts, (8, BOTTOM_BAR_Y + (BOTTOM_BAR_H - ts.get_height()) // 2))


def draw_panel_border(surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, COLOR_DIVIDER, panel_rect, 1)


def draw_divider(surface: pygame.Surface) -> None:
    pygame.draw.line(surface, COLOR_DIVIDER, (LEFT_PANEL_W, TOP_BAR_Y), (LEFT_PANEL_W, TOP_BAR_Y + PANEL_H), 1)
    pygame.draw.line(surface, COLOR_DIVIDER,
                     (RIGHT_PANEL_X, TOP_BAR_Y), (RIGHT_PANEL_X, TOP_BAR_Y + PANEL_H), 1)


def draw_save_notification(surface: pygame.Surface, saved_path: str, font: pygame.font.Font) -> None:
    ts = font.render(f"Saved: {saved_path}", True, COLOR_GOLD)
    surface.blit(ts, (8, BOTTOM_BAR_Y + 2))


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
    if n == 0 or not hist_g or not hist_b:
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
