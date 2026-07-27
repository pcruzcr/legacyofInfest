from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame
import pygame_gui

from src.engine.core import settings, user_settings
from src.engine.core.difficulty import Difficulty, set_difficulty
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class OptionsScene(BaseScene):
    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._gui_manager = pygame_gui.UIManager(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )
        self._ui_elements: list[pygame_gui.core.UIElement] = []
        self._dirty = False
        self._btn_subtitles: Any = None
        self._subtitles_on: bool = False

    def on_enter(self) -> None:
        audio = self.audio
        cfg = self._load_config()
        self._gui_manager = pygame_gui.UIManager(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT),
        )
        self._ui_elements.clear()

        y = 20
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((250, y), (300, 36)),
            text="OPTIONS",
            manager=self._gui_manager,
        )
        y += 44

        self._slider_music = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((40, y), (300, 24)),
            start_value=cfg.get("music_volume", float(audio.music_volume if audio else 0.7)),
            value_range=(0.0, 1.0),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((350, y), (150, 24)),
            "MUSIC VOLUME", self._gui_manager,
        )
        y += 32

        self._slider_sfx = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((40, y), (300, 24)),
            start_value=cfg.get("sfx_volume", float(audio.sfx_volume if audio else 1.0)),
            value_range=(0.0, 1.0),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((350, y), (150, 24)),
            "SFX VOLUME", self._gui_manager,
        )
        y += 32

        self._dropdown_difficulty = pygame_gui.elements.UIDropDownMenu(
            options_list=["easy", "normal", "hard"],
            starting_option=cfg.get("difficulty", "normal"),
            relative_rect=pygame.Rect((40, y), (150, 28)),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (150, 28)),
            "DIFFICULTY", self._gui_manager,
        )
        y += 36

        self._dropdown_cb = pygame_gui.elements.UIDropDownMenu(
            options_list=["off", "protanopia", "deuteranopia", "tritanopia"],
            starting_option=cfg.get("colorblind_mode", "off"),
            relative_rect=pygame.Rect((40, y), (150, 28)),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (200, 28)),
            "COLORBLIND MODE", self._gui_manager,
        )
        y += 36

        # AUD-036: subtitles had no UI at all. Captions for non-speech audio are
        # implemented by engine.ui.subtitle_overlay; this is how a player turns
        # them on.
        self._subtitles_on = bool(cfg.get("subtitles_enabled", False))
        self._btn_subtitles = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (150, 28)),
            text=self._subtitles_label(),
            manager=self._gui_manager,
        )
        pygame_gui.elements.UILabel(
            pygame.Rect((200, y), (240, 28)),
            "SUBTITLES (audio captions)", self._gui_manager,
        )
        y += 36

        self._btn_keybindings = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (200, 32)),
            text="KEY BINDINGS",
            manager=self._gui_manager,
        )
        y += 40

        self._btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((40, y), (200, 32)),
            text="BACK",
            manager=self._gui_manager,
        )

        self.context.scene_manager.transition.start_fade_in(0.5)

    def _subtitles_label(self) -> str:
        return f"SUBTITLES: {'ON' if self._subtitles_on else 'OFF'}"

    def _load_config(self) -> dict[str, Any]:
        """Current preference values, for populating the widgets."""
        prefs = user_settings.get()
        return {
            "music_volume": prefs.music_volume,
            "sfx_volume": prefs.sfx_volume,
            "difficulty": prefs.difficulty,
            "colorblind_mode": prefs.colorblind_mode,
            "subtitles_enabled": prefs.subtitles_enabled,
        }

    def _save_config(self) -> None:
        """Apply the widget values to the live preferences and persist them.

        AUD-036: this used to write the values straight to a JSON file that
        nothing ever read back, so the colourblind dropdown persisted a choice
        that never reached the renderer. Writing through ``user_settings`` means
        the change takes effect on the very next frame *and* survives a restart.
        """
        prefs = user_settings.get()
        prefs.music_volume = self._slider_music.get_current_value()
        prefs.sfx_volume = self._slider_sfx.get_current_value()
        prefs.difficulty = self._dropdown_difficulty.selected_option[0]
        prefs.colorblind_mode = self._dropdown_cb.selected_option[0]
        if self._btn_subtitles is not None:
            prefs.subtitles_enabled = self._subtitles_on
        prefs.save()

    def on_exit(self) -> None:
        if self._dirty:
            self._save_config()
        audio = self.audio
        if audio is not None:
            audio.music_volume = self._slider_music.get_current_value()
            audio.sfx_volume = self._slider_sfx.get_current_value()
        diff_val = self._dropdown_difficulty.selected_option[0]
        for d in Difficulty:
            if d.value == diff_val:
                set_difficulty(d)
                break

    def process_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            self._gui_manager.process_events(event)
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    self._dirty = True
                    if (self._btn_subtitles is not None
                            and event.ui_element == self._btn_subtitles):
                        self._subtitles_on = not self._subtitles_on
                        self._btn_subtitles.set_text(self._subtitles_label())
                        # Apply immediately so the player can hear-test the
                        # change without leaving the menu.
                        prefs = user_settings.get()
                        prefs.subtitles_enabled = self._subtitles_on
                        return
                    if event.ui_element == self._btn_keybindings:
                        from src.engine.scenes.keybinding_scene import KeybindingScene
                        self.context.scene_manager.replace(KeybindingScene(self.context))
                        return
                    if event.ui_element == self._btn_back:
                        from src.engine.scenes.title_scene import TitleScene
                        self.context.scene_manager.replace(TitleScene(self.context))
                        return
                elif event.user_type in (
                    pygame_gui.UI_HORIZONTAL_SLIDER_MOVED,
                    pygame_gui.UI_DROP_DOWN_MENU_CHANGED,
                ):
                    self._dirty = True

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))
            return

        self._gui_manager.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 30))
        self._gui_manager.draw_ui(surface)
