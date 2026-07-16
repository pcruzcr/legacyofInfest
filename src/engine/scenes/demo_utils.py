"""
Module: demo_utils
Description: Shared utilities for academic demonstration scenes:
source manager, frame throttle, error display, save helpers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
import datetime
import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.engine.scenes.demo_layout import PANEL_SIZE, FONT_LARGE


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
        idx = self._current_index
        if idx >= len(self.source_names):
            return "unknown"
        return self.source_names[idx]

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
        except (pygame.error, FileNotFoundError, PermissionError):
            logging.warning("demo_utils: failed to load %s", path)
        return False

    if not _try_load(Path("assets") / "sprites" / "player" / "player_idle.png",
                     "Player Idle", size=(32, 32)):
        surf = pygame.Surface((32, 32))
        surf.fill((80, 160, 255))
        sources.append(surf)
        names.append("Player (fallback)")

    if not _try_load(Path("assets") / "backgrounds" / "bg_stage0_far.png",
                     "BG Stage0 Far", size=PANEL_SIZE):
        if not _try_load(Path("assets") / "backgrounds" / "stage0.png",
                         "Backgrounds", size=PANEL_SIZE):
            fallback = _make_fallback_surface("BG", (100, 140, 200))
            sources.append(fallback)
            names.append("BG (fallback)")

    if not _try_load(Path("assets") / "tilesets" / "tileset_stage0.png",
                     "Tileset Stage0", size=PANEL_SIZE):
        if not _try_load(Path("assets") / "tileset_stage0.png",
                         "Tileset", size=PANEL_SIZE):
            fallback = _make_fallback_surface("Tileset", (120, 90, 60))
            sources.append(fallback)
            names.append("Tileset (fallback)")

    surf = pygame.Surface(PANEL_SIZE)
    surf.fill((30, 30, 30))
    pygame.draw.rect(surf, (60, 60, 80), surf.get_rect(), 2)
    sources.append(surf)
    names.append("Live Capture (unavailable)")

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
        if interval <= 0:
            return True
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
        from src.engine.scenes.demo_layout import COLOR_ERROR
        if self._message:
            text = font.render(self._message, True, COLOR_ERROR)
            surface.blit(text, (x, y))
        else:
            self._draw_default(surface, font, x, y)

    def _draw_default(self, surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> None:
        pass


# ── Save helper ───────────────────────────────────────────────────
def save_png(scene_prefix: str, mode_name: str, surface: pygame.Surface | None) -> str:
    if surface is None:
        return ""
    out_dir = Path("tests") / "output" / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{scene_prefix}_{mode_name}_{ts}.png"
    path = out_dir / fname
    pygame.image.save(surface, str(path))
    return str(path)
