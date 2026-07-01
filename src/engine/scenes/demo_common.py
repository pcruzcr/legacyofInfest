from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import datetime
import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader


# ── Layout Constants ──────────────────────────────────────────────
TOP_BAR_H = 22
LEFT_PANEL_W = 160
RIGHT_PANEL_W = 160
PANEL_H = 180
BOTTOM_BAR_H = 22

TOP_BAR_Y = 0
LEFT_PANEL_X = 0
LEFT_PANEL_Y = TOP_BAR_H
RIGHT_PANEL_X = LEFT_PANEL_W
RIGHT_PANEL_Y = TOP_BAR_H
BOTTOM_BAR_Y = TOP_BAR_H + PANEL_H

PANEL_W = LEFT_PANEL_W  # each panel is 160 wide
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

# Font sizes (bitmap, fixed-width)
FONT_SMALL = 5
FONT_MEDIUM = 6
FONT_LARGE = 7


# ── Source Surface Manager ────────────────────────────────────────
@dataclass
class SourceSurfaceManager:
    sources: list[pygame.Surface] = field(default_factory=list)
    source_names: list[str] = field(default_factory=list)
    _current_index: int = 0
    _frozen: bool = False
    _frozen_surface: pygame.Surface | None = None

    def cycle(self) -> None:
        if not self.sources:
            return
        self._current_index = (self._current_index + 1) % len(self.sources)
        self._frozen = False
        self._frozen_surface = None

    @property
    def current_source(self) -> pygame.Surface | None:
        if not self.sources:
            return None
        if self._frozen and self._frozen_surface is not None:
            return self._frozen_surface
        return self.sources[self._current_index]

    @property
    def current_name(self) -> str:
        if not self.source_names:
            return "none"
        return self.source_names[self._current_index]

    def freeze(self) -> None:
        src = self.current_source
        if src is not None:
            self._frozen_surface = src.copy()
            self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False
        self._frozen_surface = None

    @property
    def is_frozen(self) -> bool:
        return self._frozen


def build_default_sources() -> SourceSurfaceManager:
    sources: list[pygame.Surface] = []
    names: list[str] = []

    def _try_load(path: Path, name: str, size: tuple[int, int] | None = None) -> bool:
        try:
            if path.exists():
                surf = AssetLoader.load_image(path, size=size) if size else AssetLoader.load_image(path)
                sources.append(surf)
                names.append(name)
                return True
        except Exception:
            pass
        return False

    # Source 0: player idle frame 0
    if not _try_load(Path("assets") / "sprites" / "player" / "player_idle.png",
                      "Player Idle", size=(32, 32)):
        surf = pygame.Surface((32, 32))
        surf.fill((80, 160, 255))
        sources.append(surf)
        names.append("Player (fallback)")

    # Source 1: Stage 0 far background
    if not _try_load(Path("assets") / "backgrounds" / "bg_stage0_far.png",
                      "BG Stage0 Far", size=PANEL_SIZE):
        if not _try_load(Path("assets") / "backgrounds" / "stage0.png",
                          "Backgrounds", size=PANEL_SIZE):
            fallback = _make_fallback_surface("BG", (100, 140, 200))
            sources.append(fallback)
            names.append("BG (fallback)")

    # Source 2: tileset_stage0
    if not _try_load(Path("assets") / "tilesets" / "tileset_stage0.png",
                      "Tileset Stage0", size=PANEL_SIZE):
        if not _try_load(Path("assets") / "tileset_stage0.png",
                          "Tileset", size=PANEL_SIZE):
            fallback = _make_fallback_surface("Tileset", (120, 90, 60))
            sources.append(fallback)
            names.append("Tileset (fallback)")

    # Source 3: live capture from stage0 (placeholder)
    surf = pygame.Surface(PANEL_SIZE)
    surf.fill((30, 30, 30))
    pygame.draw.rect(surf, (60, 60, 80), surf.get_rect(), 2)
    sources.append(surf)
    names.append("Live Capture (unavailable)")

    # Source 4: enemy walker frame 0
    if not _try_load(Path("assets") / "sprites" / "enemies" / "enemy_walker_walk.png",
                      "Enemy Walker", size=(32, 32)):
        surf = pygame.Surface((32, 32))
        surf.fill((200, 80, 80))
        sources.append(surf)
        names.append("Enemy (fallback)")

    return SourceSurfaceManager(sources=sources, source_names=names)


def _make_fallback_surface(label: str, color: tuple[int, int, int]) -> pygame.Surface:
    surf = pygame.Surface(PANEL_SIZE)
    surf.fill(color)
    fnt = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_LARGE)
    ts = fnt.render(label, True, (255, 255, 255))
    surf.blit(ts, (4, 4))
    return surf


# ── Frame Throttle ────────────────────────────────────────────────
class FrameThrottle:
    def __init__(self) -> None:
        self._counter: int = 1

    def tick(self) -> int:
        self._counter += 1
        return self._counter

    def should_update(self, interval: int) -> bool:
        return self._counter > 0 and self._counter % interval == 0

    def reset(self) -> None:
        self._counter = 1


# ── Error Display ─────────────────────────────────────────────────
class ErrorDisplay:
    def __init__(self, duration: float = 2.0) -> None:
        self._message: str = ""
        self._timer: float = 0.0
        self._duration = duration

    def set_error(self, message: str) -> None:
        self._message = message[:60]
        self._timer = self._duration

    def update(self, dt: float) -> None:
        if self._timer > 0:
            self._timer -= dt
        if self._timer <= 0:
            self._message = ""

    @property
    def message(self) -> str:
        return self._message

    @property
    def active(self) -> bool:
        return self._timer > 0

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> None:
        if self._message:
            text = font.render(self._message, True, COLOR_ERROR)
            surface.blit(text, (x, y))
        else:
            self._draw_default(surface, font, x, y)

    def _draw_default(self, surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> None:
        pass  # override per scene


# ── Drawing Helpers ────────────────────────────────────────────────
def draw_top_bar(surface: pygame.Surface, title: str, unit: str) -> None:
    pygame.draw.rect(surface, COLOR_TOP_BAR_BG, (0, TOP_BAR_Y, settings.INTERNAL_WIDTH, TOP_BAR_H))
    fnt = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_MEDIUM)
    ts = fnt.render(f"  {title}", True, COLOR_HIGHLIGHT)
    surface.blit(ts, (4, TOP_BAR_Y + 2))
    ts2 = fnt.render(f"{unit}  ", True, COLOR_ACCENT)
    tw = ts2.get_width()
    surface.blit(ts2, (settings.INTERNAL_WIDTH - tw - 4, TOP_BAR_Y + 2))


def draw_bottom_bar(surface: pygame.Surface, text: str) -> None:
    pygame.draw.rect(surface, COLOR_BOTTOM_BAR_BG,
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
    ts = fnt.render(text, True, COLOR_TEXT)
    surface.blit(ts, (4, BOTTOM_BAR_Y + 2))


def draw_bottom_bar_error(surface: pygame.Surface, error: str) -> None:
    pygame.draw.rect(surface, (40, 10, 10),
                     (0, BOTTOM_BAR_Y, settings.INTERNAL_WIDTH, BOTTOM_BAR_H))
    fnt = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", FONT_SMALL)
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


def save_png(scene_prefix: str, mode_name: str, surface: pygame.Surface) -> str:
    out_dir = Path("tests") / "output" / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{scene_prefix}_{mode_name}_{ts}.png"
    path = out_dir / fname
    pygame.image.save(surface, str(path))
    return str(path)
