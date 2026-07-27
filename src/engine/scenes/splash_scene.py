from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y
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
        self._fading_out: bool = False
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
        self._logo_shadow = self._logo.copy()
        self._logo_shadow.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)

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
        if self._fading_out:
            if self.context.scene_manager.transition.finished:
                self.context.scene_manager.replace(TitleScene(self.context))
            return
        self._timer += dt
        if self._timer >= self.SPLASH_TIME:
            self.context.scene_manager.transition.start_fade_out(0.5)
            self._fading_out = True

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        logo_rect = self._logo.get_rect(
            center=(settings.INTERNAL_WIDTH // 2, settings.INTERNAL_HEIGHT // 2 - 35),
        )

        surface.blit(self._logo_shadow, (logo_rect.x + 3, logo_rect.y + 3))
        surface.blit(self._logo, logo_rect)

        loading = self._font_game.render("Cargando...", True, (255, 255, 255))
        lr = loading.get_rect(center=(settings.INTERNAL_WIDTH // 2, BOTTOM_BAR_Y - 36))
        loading.set_alpha(int(min(self._timer / self.SPLASH_TIME, 1.0) * 255))
        surface.blit(loading, lr)

        progress = min(self._timer / self.SPLASH_TIME, 1.0)
        BAR_W, BAR_H = 170, 6
        bar_rect = pygame.Rect(
            (settings.INTERNAL_WIDTH - BAR_W) // 2, BOTTOM_BAR_Y - 18,
            BAR_W, BAR_H,
        )
        pygame.draw.rect(surface, (45, 45, 45), bar_rect, border_radius=3)
        pygame.draw.rect(
            surface, (255, 210, 0),
            (bar_rect.x, bar_rect.y, int(progress * BAR_W), BAR_H),
            border_radius=3,
        )

        version = self._font_small.render("Prototype v0.1", True, (180, 180, 180))
        surface.blit(version, (6, BOTTOM_BAR_Y - 8))

        self.context.scene_manager.transition.draw(surface)

        cr = self._font_small.render("© 2026 Legacy of InFest", True, (180, 180, 180))
        surface.blit(cr, (settings.INTERNAL_WIDTH - cr.get_width() - 6, BOTTOM_BAR_Y - 8))

