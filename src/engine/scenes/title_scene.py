from __future__ import annotations

import math
from typing import TYPE_CHECKING

import orjson
import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.core.user_settings import user_data_dir
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_common import BOTTOM_BAR_Y
from src.engine.scenes.demo_menu_scene import DemoMenuScene
from src.engine.scenes.options_scene import OptionsScene
from src.engine.scenes.story_scene import StoryScene
from src.engine.scenes.tutorial_scene import TutorialScene
from src.engine.utils.asset_loader import AssetLoader
from src.framework.vfx.hit_effects import HitEffects
from src.framework.vfx.particle_system import ParticleSystem

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

_tutorial_seen_cache: bool | None = None


class TitleScene(BaseScene):
    """Main title screen with background, logo, music, custom font, and particles."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        assets = settings.ASSETS_DIR / "title"

        self._background = AssetLoader.load_image(
            assets / "bck1.png",
            size=(settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )

        raw_logo = AssetLoader.load_image(assets / "logo.png")
        max_logo_w = settings.INTERNAL_WIDTH - 40
        max_logo_h = 80
        lw, lh = raw_logo.get_size()
        scale = min(max_logo_w / lw, max_logo_h / lh, 1.0)
        self._logo = AssetLoader.load_image(
            assets / "logo.png",
            size=(int(lw * scale), int(lh * scale)),
        )
        self._logo_y_offset: float = 0.0
        self._logo_timer: float = 0.0

        title_wav = assets / "title.wav"
        title_ogg = assets / "title.ogg"
        if title_wav.exists():
            self._music = title_wav
        else:
            self._music = title_ogg

        self._selected: int = 0
        self._scroll_offset: int = 0
        self._options: list[str] = [
            "START", "TUTORIAL", "WORLD MAP", "INVENTORY",
            "BESTIARY", "ACHIEVEMENTS", "ACADEMIC DEMOS", "OPTIONS", "QUIT",
        ]
        self._recalc_layout()

        self._bar_surf: pygame.Surface | None = None
        self._particle_system = ParticleSystem()
        self._particle_timer: float = 0.0

    def _recalc_layout(self) -> None:
        h = settings.INTERNAL_HEIGHT
        logo_bottom = h // 3 + 20
        available = h - logo_bottom - 16
        n = len(self._options)
        line_h = max(11, min(18, available // max(n, 1)))
        self._font_size = max(14, line_h - 2)
        self._font_game = AssetLoader.load_font(
            settings.ASSETS_DIR / "fonts" / "game.ttf",
            self._font_size,
        )
        self._option_spacing = line_h
        self._max_visible = max(1, available // line_h)

    def on_enter(self) -> None:
        self._selected = 0
        self._scroll_offset = 0
        self._recalc_layout()
        self._update_options()
        self.context.scene_manager.transition.start_fade_in(0.5)
        audio = self.audio
        if audio is not None:
            audio.play_music(self._music)

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        self._logo_timer += dt
        self._logo_y_offset = 2.0 * (1.0 + 0.5 * (1.0 + math.cos(self._logo_timer * 1.5)))

        self._particle_timer += dt
        if self._particle_timer >= 0.1:
            self._particle_timer = 0.0
            import random
            self._particle_system.get_emitter("title_spark").emit(
                random.uniform(0, settings.INTERNAL_WIDTH),
                random.uniform(60, settings.INTERNAL_HEIGHT),
                HitEffects.SPARK,
            )
        self._particle_system.update(dt)

        prev_selected = self._selected
        n = len(self._options)
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = min(self._selected + 1, n - 1)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = max(self._selected - 1, 0)
        if self._selected != prev_selected:
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
        if self._selected < self._scroll_offset:
            self._scroll_offset = self._selected
        elif self._selected >= self._scroll_offset + self._max_visible:
            self._scroll_offset = self._selected - self._max_visible + 1

        if im.is_action_just_pressed(Action.CONFIRM):
            self.context.event_bus.emit(Events.SFX_MENU_CONFIRM)
            self._activate_option(self._options[self._selected])

        if im.is_action_just_pressed(Action.CANCEL):
            self.context.event_bus.emit(Events.SFX_MENU_CANCEL)
            self.context.quit()

    def _activate_option(self, opt: str) -> None:
        if opt == "CONTINUE":
            from src.engine.scenes.load_game_scene import LoadGameScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(LoadGameScene(self.context))
        elif opt == "START":
            self.context.scene_manager.transition.start_fade_out(0.4)
            if not self._has_seen_tutorial():
                self._mark_tutorial_seen()
                self.context.scene_manager.replace(TutorialScene(self.context))
            else:
                self.context.scene_manager.replace(StoryScene(self.context, 1))
        elif opt == "TUTORIAL":
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(TutorialScene(self.context))
        elif opt == "WORLD MAP":
            from src.engine.scenes.world_map_scene import WorldMapScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(WorldMapScene(self.context))
        elif opt == "INVENTORY":
            from src.engine.scenes.inventory_scene import InventoryScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(InventoryScene(self.context))
        elif opt == "BESTIARY":
            from src.engine.scenes.bestiary_scene import BestiaryScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(BestiaryScene(self.context))
        elif opt == "ACHIEVEMENTS":
            from src.engine.scenes.achievement_scene import AchievementScene
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(AchievementScene(self.context))
        elif opt == "ACADEMIC DEMOS":
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(DemoMenuScene(self.context))
        elif opt == "OPTIONS":
            self.context.scene_manager.transition.start_fade_out(0.4)
            self.context.scene_manager.replace(OptionsScene(self.context))
        elif opt == "QUIT":
            self.context.quit()

    def _update_options(self) -> None:
        sm = self.context.save_manager
        if sm is not None and sm.has_saves():
            if "CONTINUE" not in self._options:
                self._options.insert(0, "CONTINUE")
        else:
            if "CONTINUE" in self._options:
                self._options.remove("CONTINUE")

    def _has_seen_tutorial(self) -> bool:
        global _tutorial_seen_cache
        if _tutorial_seen_cache is not None:
            return _tutorial_seen_cache
        flag_path = user_data_dir() / "tutorial_seen.json"
        try:
            data = orjson.loads(flag_path.read_bytes())
            _tutorial_seen_cache = bool(data.get("seen", False))
            return _tutorial_seen_cache
        except (FileNotFoundError, orjson.JSONDecodeError):
            _tutorial_seen_cache = False
            return False

    def _mark_tutorial_seen(self) -> None:
        global _tutorial_seen_cache
        _tutorial_seen_cache = True
        flag_path = user_data_dir() / "tutorial_seen.json"
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        flag_path.write_bytes(orjson.dumps({"seen": True}))

    def on_exit(self) -> None:
        audio = self.audio
        if audio is not None:
            audio.stop_music()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        logo_rect = self._logo.get_rect(
            center=(settings.INTERNAL_WIDTH // 2, int(settings.INTERNAL_HEIGHT // 3 + self._logo_y_offset)),
        )
        surface.blit(self._logo, logo_rect)

        self._particle_system.draw(surface, pygame.Vector2(0, 0))

        self.context.scene_manager.transition.draw(surface)

        start_y = logo_rect.bottom + 8
        visible = self._options[self._scroll_offset:self._scroll_offset + self._max_visible]
        for idx, opt in enumerate(visible):
            i = self._scroll_offset + idx
            color = (255, 255, 100) if i == self._selected else (150, 150, 150)
            text = self._font_game.render(opt, True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = start_y + idx * self._option_spacing
            if oy + self._font_size <= settings.INTERNAL_HEIGHT:
                if i == self._selected:
                    pad = 4
                    bw, bh = text.get_width() + pad * 2, text.get_height()
                    if self._bar_surf is None or self._bar_surf.get_size() != (bw, bh):
                        self._bar_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                    bar_surf = self._bar_surf
                    bar_surf.fill((255, 255, 255, 60))
                    surface.blit(bar_surf, (ox - pad, oy))
                surface.blit(text, (ox, oy))

        if self._scroll_offset > 0:
            pygame.draw.polygon(surface, (200, 200, 200), [
                (settings.INTERNAL_WIDTH // 2, start_y - 4),
                (settings.INTERNAL_WIDTH // 2 - 6, start_y - 10),
                (settings.INTERNAL_WIDTH // 2 + 6, start_y - 10),
            ])
        if self._scroll_offset + self._max_visible < len(self._options):
            bot = BOTTOM_BAR_Y - 2
            pygame.draw.polygon(surface, (200, 200, 200), [
                (settings.INTERNAL_WIDTH // 2, bot),
                (settings.INTERNAL_WIDTH // 2 - 6, bot + 6),
                (settings.INTERNAL_WIDTH // 2 + 6, bot + 6),
            ])

