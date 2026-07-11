from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pygame

from src.engine.core import settings
from src.engine.core.difficulty import Difficulty, set_difficulty
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

CONFIG_PATH = Path(os.environ.get("APPDATA", "~/.config")) / "legacyofinfest" / "config.json"


class OptionsScene(BaseScene):
    """Options menu with volume sliders and display scale."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._options: list[dict[str, Any]] = [
            {"name": "MUSIC VOLUME", "min": 0.0, "max": 1.0, "step": 0.1},
            {"name": "SFX VOLUME", "min": 0.0, "max": 1.0, "step": 0.1},
            {"name": "DISPLAY SCALE", "min": 1, "max": 4, "step": 1},
            {"name": "FULLSCREEN", "options": ["off", "on"]},
            {"name": "VSYNC", "options": ["off", "on"]},
            {"name": "RESOLUTION", "options": ["320x224", "640x448", "960x672", "1280x896"]},
            {"name": "DIFFICULTY", "options": ["easy", "normal", "hard"]},
            {"name": "KEY BINDINGS", "action": True},
            {"name": "COLORBLIND MODE", "options": ["off", "protanopia", "deuteranopia", "tritanopia"]},
            {"name": "SUBTITLES", "options": ["off", "on"]},
        ]
        self._selected = 0
        self._dirty = False

    def _load_config(self) -> dict[str, Any]:
        try:
            with open(CONFIG_PATH) as f:
                return cast(dict[str, Any], json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_config(self) -> None:
        data = {
            "music_volume": self._options[0]["value"],
            "sfx_volume": self._options[1]["value"],
            "display_scale": int(self._options[2]["value"]),
            "fullscreen": self._options[3].get("value", "off"),
            "vsync": self._options[4].get("value", "off"),
            "difficulty": self._options[6].get("value", "normal"),
            "colorblind_mode": self._options[8].get("value", "off"),
            "subtitles": self._options[9].get("value", "off"),
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f)

    def on_enter(self) -> None:
        audio = self.audio
        cfg = self._load_config()
        self._options[0]["value"] = cfg.get("music_volume", float(audio.music_volume if audio else 0.7))
        self._options[1]["value"] = cfg.get("sfx_volume", float(audio.sfx_volume if audio else 1.0))
        self._options[2]["value"] = float(cfg.get("display_scale", settings.DISPLAY_SCALE))
        self._options[3]["value"] = cfg.get("fullscreen", "off")
        self._options[4]["value"] = cfg.get("vsync", "off")
        self._options[6]["value"] = cfg.get("difficulty", "normal")
        self._options[8]["value"] = cfg.get("colorblind_mode", "off")
        self._options[9]["value"] = cfg.get("subtitles", "off")

    def on_exit(self) -> None:
        if self._dirty:
            self._save_config()
            scale = int(self._options[2]["value"])
            if scale != settings.DISPLAY_SCALE:
                settings.DISPLAY_SCALE = max(1, min(scale, 4))
            fullscreen = self._options[3].get("value", "off") == "on"
            vsync = self._options[4].get("value", "off") == "on"
            res_str = self._options[5].get("value", "320x224")
            res_parts = res_str.split("x")
            res_w = int(res_parts[0]) if len(res_parts) == 2 else settings.INTERNAL_WIDTH * scale
            res_h = int(res_parts[1]) if len(res_parts) == 2 else settings.INTERNAL_HEIGHT * scale
            flags = pygame.FULLSCREEN if fullscreen else 0
            if vsync:
                flags |= pygame.SCALED
            pygame.display.set_mode((res_w, res_h), flags)
            diff_val = self._options[6].get("value", "normal")
            for d in Difficulty:
                if d.value == diff_val:
                    set_difficulty(d)
                    break
            settings.COLORBLIND_MODE = self._options[8].get("value", "off")
            settings.SUBTITLES_ENABLED = self._options[9].get("value", "on") == "on"

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        prev_selected = self._selected
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + 1) % len(self._options)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - 1) % len(self._options)
        if self._selected != prev_selected:
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_HOVER)
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.core.event_bus import emit
            from src.engine.core.events import Events
            emit(Events.SFX_MENU_CANCEL)
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))
            return
        opt = self._options[self._selected]
        if opt.get("action"):
            if im.is_action_just_pressed(Action.CONFIRM) or im.is_action_just_pressed(Action.MOVE_RIGHT):
                from src.engine.scenes.keybinding_scene import KeybindingScene
                self.context.scene_manager.replace(KeybindingScene(self.context))
            return
        if "options" in opt:
            if im.is_action_just_pressed(Action.MOVE_RIGHT) or im.is_action_just_pressed(Action.MOVE_LEFT):
                from src.engine.core.event_bus import emit
                from src.engine.core.events import Events
                emit(Events.SFX_MENU_CONFIRM)
                idx = opt["options"].index(opt.get("value", opt["options"][0]))
                direction = 1 if im.is_action_just_pressed(Action.MOVE_RIGHT) else -1
                idx = (idx + direction) % len(opt["options"])
                opt["value"] = opt["options"][idx]
                self._apply(opt)
            return
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            opt["value"] = min(opt["max"], opt["value"] + opt["step"])
            self._apply(opt)
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            opt["value"] = max(opt["min"], opt["value"] - opt["step"])
            self._apply(opt)

    def _apply(self, opt: dict[str, Any]) -> None:
        self._dirty = True
        audio = self.audio
        if opt["name"] == "MUSIC VOLUME" and audio is not None:
            audio.music_volume = opt["value"]
        if opt["name"] == "SFX VOLUME" and audio is not None:
            audio.sfx_volume = opt["value"]
        if opt["name"] == "COLORBLIND MODE":
            settings.COLORBLIND_MODE = opt.get("value", "off")
        if opt["name"] == "SUBTITLES":
            settings.SUBTITLES_ENABLED = opt.get("value", "off") == "on"
        if opt["name"] in ("FULLSCREEN", "VSYNC", "RESOLUTION", "DIFFICULTY"):
            self._dirty = True

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 30))
        font = pygame.font.Font(None, 24)
        title = font.render("OPTIONS", True, (255, 255, 240))
        surface.blit(title, ((settings.INTERNAL_WIDTH - title.get_width()) // 2, 20))
        hint = pygame.font.Font(None, 16).render("[ESC] Back  [LEFT/RIGHT] Change", True, (160, 160, 170))
        surface.blit(hint, ((settings.INTERNAL_WIDTH - hint.get_width()) // 2, settings.INTERNAL_HEIGHT - 26))
        y = 70
        for i, opt in enumerate(self._options):
            color = (255, 255, 100) if i == self._selected else (200, 200, 200)
            label = pygame.font.Font(None, 18).render(opt["name"], True, color)
            surface.blit(label, (40, y))
            if opt.get("action"):
                arrow = pygame.font.Font(None, 18).render(">", True, color)
                surface.blit(arrow, (settings.INTERNAL_WIDTH - 30, y))
            elif "options" in opt:
                val = opt.get("value", opt["options"][0])
                val_surf = pygame.font.Font(None, 18).render(str(val).upper(), True, color)
                surface.blit(val_surf, (settings.INTERNAL_WIDTH - 90, y))
            else:
                val = opt.get("value", (opt["min"] + opt["max"]) / 2)
                val_s = f"{val:.2f}" if isinstance(val, float) else f"{int(val)}"
                val_surf = pygame.font.Font(None, 18).render(val_s, True, color)
                surface.blit(val_surf, (settings.INTERNAL_WIDTH - 90, y))
            y += 28
