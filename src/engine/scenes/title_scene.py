from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene
from src.engine.scenes.demo_menu_scene import DemoMenuScene
from src.engine.scenes.options_scene import OptionsScene
from src.engine.scenes.story_scene import StoryScene
from src.engine.scenes.tutorial_scene import TutorialScene
from src.engine.utils.asset_loader import AssetLoader
from src.framework.vfx.particle_system import ParticleSystem
from src.framework.vfx.hit_effects import HitEffects

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


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

        self._music = assets / "title.wav"

        self._font_game = AssetLoader.load_font(settings.ASSETS_DIR / "fonts" / "game.ttf", 14)
        self._selected: int = 0
        self._options: list[str] = ["START", "TUTORIAL", "WORLD MAP", "INVENTORY", "ACHIEVEMENTS", "ACADEMIC DEMOS", "OPTIONS", "QUIT"]

        self._particle_system = ParticleSystem()
        self._particle_timer: float = 0.0

    def on_enter(self) -> None:
        self._selected = 0
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
        self._logo_y_offset = 2.0 * (1.0 + 0.5 * (1.0 + __import__('math').cos(self._logo_timer * 1.5)))

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
        # Mouse hover detection
        import pygame
        if pygame.mouse.get_focused():
            mx, my = pygame.mouse.get_pos()
            mx = int(mx * settings.INTERNAL_WIDTH / self.context.display.get_width()) if hasattr(self.context, 'display') else mx
            my = int(my * settings.INTERNAL_HEIGHT / self.context.display.get_height()) if hasattr(self.context, 'display') else my
            logo_rect_bottom = settings.INTERNAL_HEIGHT // 3
            for i, opt in enumerate(self._options):
                ox = (settings.INTERNAL_WIDTH - len(opt) * 12) // 2
                oy = logo_rect_bottom + 30 + i * 22
                if ox <= mx <= ox + len(opt) * 12 and oy - 10 <= my <= oy + 10:
                    self._selected = i
                    if pygame.mouse.get_pressed()[0]:
                        from src.engine.core.event_bus import emit
                        from src.engine.core.events import Events
                        emit(Events.SFX_MENU_CONFIRM)
                        self._activate_option(opt)
                        return

        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + 1) % len(self._options)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - 1) % len(self._options)
        if self._selected != prev_selected:
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_HOVER)

        if im.is_action_just_pressed(Action.CONFIRM):
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_CONFIRM)
            self._activate_option(self._options[self._selected])

        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_CANCEL)
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
        from pathlib import Path
        import json, os
        flag_path = Path(os.environ.get("APPDATA", "~/.config")) / "legacyofinfest" / "tutorial_seen.json"
        try:
            with open(flag_path) as f:
                data = json.load(f)
                return data.get("seen", False)
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def _mark_tutorial_seen(self) -> None:
        from pathlib import Path
        import json, os
        flag_path = Path(os.environ.get("APPDATA", "~/.config")) / "legacyofinfest" / "tutorial_seen.json"
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        with open(flag_path, "w") as f:
            json.dump({"seen": True}, f)

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

        for i, opt in enumerate(self._options):
            color = (255, 255, 100) if i == self._selected else (150, 150, 150)
            prefix = "> " if i == self._selected else "  "
            text = self._font_game.render(f"{prefix}{opt}", True, color)
            ox = (settings.INTERNAL_WIDTH - text.get_width()) // 2
            oy = logo_rect.bottom + 30 + i * 22
            surface.blit(text, (ox, oy))
