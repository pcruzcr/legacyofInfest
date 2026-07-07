from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.title_scene import TitleScene
from src.engine.utils.asset_loader import AssetLoader

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class SplashScene(BaseScene):
    """Game startup splash screen."""

    SPLASH_TIME = 3.0

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._timer = 0.0
        assets = settings.ASSETS_DIR / "splash"

        self._background = AssetLoader.load_image(
            assets / "bck1.png",
            size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )

        raw_logo = AssetLoader.load_image(assets / "logo.png")
        max_logo_w = settings.INTERNAL_WIDTH - 40
        max_logo_h = 90
        lw, lh = raw_logo.get_size()
        scale = min(max_logo_w / lw, max_logo_h / lh, 1.0)
        self._logo = AssetLoader.load_image(
            assets / "logo.png",
            size=(int(lw * scale), int(lh * scale)),
        )

        self._music = assets / "bck.wav"

        self._font_game = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", 14,
        )
        self._font_small = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf", 10,
        )

    def on_enter(self) -> None:
        self._timer = 0.0
        audio = self.audio
        if audio is not None:
            audio.play_music(self._music, loops=0)

    def on_exit(self) -> None:
        audio = self.audio
        if audio is not None:
            audio.stop_music()

    def update(self, dt: float) -> None:
        self._timer += dt
        if self._timer >= self.SPLASH_TIME:
            if self.context.scene_manager is not None:
                self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        fade = min(self._timer / 0.60, 1.0)
        alpha = int(fade * 255)

        logo = self._logo.copy()
        logo.set_alpha(alpha)
        logo_rect = logo.get_rect(
            center=(settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 2 - 35),
        )

        shadow = logo.copy()
        shadow.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow, (logo_rect.x + 3, logo_rect.y + 3))
        surface.blit(logo, logo_rect)

        loading = self._font_game.render("Cargando...", False, (255, 255, 255))
        loading.set_alpha(alpha)
        lr = loading.get_rect(center=(settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT - 40))
        surface.blit(loading, lr)

        progress = min(self._timer / self.SPLASH_TIME, 1.0)
        BAR_W, BAR_H = 170, 6
        bar_rect = pygame.Rect(
            (settings.INTERNAL_WIDTH - BAR_W) // 2, settings.INTERNAL_HEIGHT - 22,
            BAR_W, BAR_H,
        )
        pygame.draw.rect(surface, (45, 45, 45), bar_rect, border_radius=3)
        pygame.draw.rect(
            surface, (255, 210, 0),
            (bar_rect.x, bar_rect.y, int(progress * BAR_W), BAR_H),
            border_radius=3,
        )

        version = self._font_small.render("Prototype v0.1", False, (180, 180, 180))
        surface.blit(version, (6, settings.INTERNAL_HEIGHT - 12))

        cr = self._font_small.render("© 2026 Legacy of InFest", False, (180, 180, 180))
        surface.blit(cr, (settings.INTERNAL_WIDTH - cr.get_width() - 6, settings.INTERNAL_HEIGHT - 12))
