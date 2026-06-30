"""
Module: splash_scene
System: engine.scenes

Description:
Initial splash screen.

Responsibilities
----------------
- Display splash background
- Display game logo
- Play intro music
- Display loading progress
- Automatically transition to TitleScene
"""

from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.core.app import _get_scene_manager
from src.engine.scene.base_scene import BaseScene
from src.engine.utils.asset_loader import AssetLoader


class SplashScene(BaseScene):
    """Game startup splash screen."""

    SPLASH_TIME = 3.0

    def __init__(self) -> None:

        self._timer = 0.0

        assets = Path("assets") / "splash"

        # Background (scaled to internal resolution)
        self._background = AssetLoader.load_image(
            assets / "bck1.png",
            size=(
                settings.INTERNAL_WIDTH,
                settings.INTERNAL_HEIGHT,
            ),
        )

        # Logo (scaled only once)
        self._logo = AssetLoader.load_image(
            assets / "logo.png",
            scale=0.22,
        )

        self._music = assets / "bck.mp3"

        self._font = AssetLoader.load_font(
            None,
            14,
        )

        self._font_small = AssetLoader.load_font(
            None,
            10,
        )

    # ---------------------------------------------------------

    def on_enter(self) -> None:

        self._timer = 0.0

        AssetLoader.play_music(
            self._music,
            volume=0.60,
            loop=False,
        )

    # ---------------------------------------------------------

    def on_exit(self) -> None:

        AssetLoader.fadeout(500)

    # ---------------------------------------------------------

    def update(self, dt: float) -> None:

        self._timer += dt

        if self._timer >= self.SPLASH_TIME:

            from src.engine.scenes.title_scene import TitleScene

            manager = _get_scene_manager()

            if manager is not None:
                manager.replace(
                    TitleScene()
                )

    # ---------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:

        # =====================================================
        # Background
        # =====================================================

        surface.blit(
            self._background,
            (0, 0),
        )

        # =====================================================
        # Fade In
        # =====================================================

        fade = min(
            self._timer / 0.60,
            1.0,
        )

        alpha = int(fade * 255)

        # =====================================================
        # Logo
        # =====================================================

        logo = self._logo.copy()

        logo.set_alpha(alpha)

        logo_rect = logo.get_rect(
            center=(
                settings.INTERNAL_WIDTH // 2,
                settings.INTERNAL_HEIGHT // 2 - 35,
            )
        )

        shadow = logo.copy()

        shadow.fill(
            (0, 0, 0, 150),
            special_flags=pygame.BLEND_RGBA_MULT,
        )

        surface.blit(
            shadow,
            (
                logo_rect.x + 3,
                logo_rect.y + 3,
            ),
        )

        surface.blit(
            logo,
            logo_rect,
        )

        # =====================================================
        # Loading Text
        # =====================================================

        loading = self._font.render(
            "Cargando...",
            True,
            (255, 255, 255),
        )

        loading.set_alpha(alpha)

        loading_rect = loading.get_rect(
            center=(
                settings.INTERNAL_WIDTH // 2,
                settings.INTERNAL_HEIGHT - 40,
            )
        )

        surface.blit(
            loading,
            loading_rect,
        )

        # =====================================================
        # Progress Bar
        # =====================================================

        progress = min(
            self._timer / self.SPLASH_TIME,
            1.0,
        )

        BAR_WIDTH = 170
        BAR_HEIGHT = 6

        bar_rect = pygame.Rect(
            (
                settings.INTERNAL_WIDTH - BAR_WIDTH
            ) // 2,
            settings.INTERNAL_HEIGHT - 22,
            BAR_WIDTH,
            BAR_HEIGHT,
        )

        pygame.draw.rect(
            surface,
            (45, 45, 45),
            bar_rect,
            border_radius=3,
        )

        pygame.draw.rect(
            surface,
            (255, 210, 0),
            (
                bar_rect.x,
                bar_rect.y,
                int(progress * BAR_WIDTH),
                BAR_HEIGHT,
            ),
            border_radius=3,
        )

        # =====================================================
        # Version
        # =====================================================

        version = self._font_small.render(
            "Prototype v0.1",
            True,
            (180, 180, 180),
        )

        surface.blit(
            version,
            (
                6,
                settings.INTERNAL_HEIGHT - 12,
            ),
        )

        # =====================================================
        # Copyright
        # =====================================================

        copyright_text = self._font_small.render(
            "© 2026 Legacy of InFest",
            True,
            (180, 180, 180),
        )

        surface.blit(
            copyright_text,
            (
                settings.INTERNAL_WIDTH
                - copyright_text.get_width()
                - 6,
                settings.INTERNAL_HEIGHT - 12,
            ),
        )