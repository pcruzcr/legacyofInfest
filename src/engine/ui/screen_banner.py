from __future__ import annotations
import pygame
from src.engine.core import settings
from src.engine.utils.math_utils import ease_out_quad, ease_in_quad
from src.engine.utils.asset_loader import AssetLoader


class ScreenBanner:
    """Animated stage title banner with two-tone background and bitmap fonts."""

    def __init__(self) -> None:
        self._stage_id: str = ""
        self._stage_name: str = ""
        self._state: str = "idle"
        self._timer: float = 0.0
        self._slide_in_duration: float = 0.5
        self._hold_duration: float = 2.0
        self._slide_out_duration: float = 0.4
        self._offset: float = float(settings.INTERNAL_WIDTH * 2)
        self._banner_height: int = 40

        self._banner_top: pygame.Surface | None = None
        self._banner_bottom: pygame.Surface | None = None
        try:
            self._banner_top = AssetLoader.load_image(
                settings.ASSETS_DIR / "ui" / "banner_top.png",
                size=(settings.INTERNAL_WIDTH, self._banner_height // 2),
            )
            self._banner_bottom = AssetLoader.load_image(
                settings.ASSETS_DIR / "ui" / "banner_bottom.png",
                size=(settings.INTERNAL_WIDTH, self._banner_height // 2),
            )
        except Exception:
            pass

        self._font_large: pygame.font.Font | None = None
        self._font_medium: pygame.font.Font | None = None
        try:
            self._font_large = pygame.font.Font(
                settings.ASSETS_DIR / "fonts" / "game.ttf", 16,
            )
        except Exception:
            self._font_large = None
        try:
            self._font_medium = pygame.font.Font(
                settings.ASSETS_DIR / "fonts" / "game.ttf", 14,
            )
        except Exception:
            self._font_medium = None

        self._fallback_font = pygame.font.Font(None, 18)

    def play(self, stage_id: str, stage_name: str) -> None:
        self._stage_id = stage_id
        self._stage_name = stage_name
        self._state = "slide_in"
        self._timer = 0.0
        self._offset = float(settings.INTERNAL_WIDTH * 2)

    def update(self, dt: float) -> None:
        if self._state == "idle":
            return

        self._timer += dt

        if self._state == "slide_in":
            progress = min(self._timer / self._slide_in_duration, 1.0)
            t = ease_out_quad(progress)
            self._offset = settings.INTERNAL_WIDTH * (2.0 - t)
            if progress >= 1.0:
                self._state = "hold"
                self._timer = 0.0

        elif self._state == "hold":
            if self._timer >= self._hold_duration:
                self._state = "slide_out"
                self._timer = 0.0

        elif self._state == "slide_out":
            progress = min(self._timer / self._slide_out_duration, 1.0)
            t = ease_in_quad(progress)
            self._offset = settings.INTERNAL_WIDTH * (1.0 + t)
            if progress >= 1.0:
                self._state = "idle"

    def draw(self, surface: pygame.Surface) -> None:
        if self._state == "idle":
            return

        bx = int(self._offset - settings.INTERNAL_WIDTH)
        by = 88
        bw = settings.INTERNAL_WIDTH

        # Draw two-tone banner background
        if self._banner_top and self._banner_bottom:
            surface.blit(self._banner_top, (bx, by))
            surface.blit(self._banner_bottom, (bx, by + self._banner_height // 2))
        else:
            top_half = pygame.Rect(bx, by, bw, self._banner_height // 2)
            bottom_half = pygame.Rect(bx, by + self._banner_height // 2,
                                       bw, self._banner_height // 2)
            pygame.draw.rect(surface, (40, 30, 60), top_half)
            pygame.draw.rect(surface, (60, 40, 80), bottom_half)
            pygame.draw.rect(surface, (100, 80, 140), (bx, by, bw, self._banner_height), 1)

        # Draw stage name with banner fonts
        name_surf: pygame.Surface | None = None
        if self._font_large:
            name_surf = self._font_large.render(self._stage_name, False, (255, 255, 200))
        if name_surf is None or name_surf.get_width() == 0:
            name_surf = self._fallback_font.render(self._stage_name, False, (255, 255, 200))

        nx = bx + (bw - name_surf.get_width()) // 2
        ny = by + (self._banner_height - name_surf.get_height()) // 2
        surface.blit(name_surf, (nx, ny))

    @property
    def is_active(self) -> bool:
        return self._state != "idle"
