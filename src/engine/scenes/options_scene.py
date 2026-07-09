from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

CONFIG_PATH = Path(os.environ.get("APPDATA", "~/.config")) / "legacyofinfest" / "config.json"


class OptionsScene(BaseScene):
    """Options menu with volume sliders and display scale."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._options = [
            {"name": "MUSIC VOLUME", "min": 0.0, "max": 1.0, "step": 0.1},
            {"name": "SFX VOLUME", "min": 0.0, "max": 1.0, "step": 0.1},
            {"name": "DISPLAY SCALE", "min": 1, "max": 4, "step": 1},
        ]
        self._selected = 0
        self._dirty = False

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_config(self) -> None:
        data = {
            "music_volume": self._options[0]["value"],
            "sfx_volume": self._options[1]["value"],
            "display_scale": int(self._options[2]["value"]),
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f)

    def on_enter(self) -> None:
        audio = self.audio
        cfg = self._load_config()
        self._options[0]["value"] = cfg.get("music_volume",
            float(audio.music_volume if audio else 0.7))
        self._options[1]["value"] = cfg.get("sfx_volume",
            float(audio.sfx_volume if audio else 1.0))
        self._options[2]["value"] = float(cfg.get("display_scale", settings.DISPLAY_SCALE))

    def on_exit(self) -> None:
        if self._dirty:
            self._save_config()
            scale = int(self._options[2]["value"])
            if scale != settings.DISPLAY_SCALE:
                settings.DISPLAY_SCALE = max(1, min(scale, 4))

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._selected = (self._selected + 1) % len(self._options)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._selected = (self._selected - 1) % len(self._options)
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))
            return
        opt = self._options[self._selected]
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            opt["value"] = min(opt["max"], opt["value"] + opt["step"])
            self._apply(opt)
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            opt["value"] = max(opt["min"], opt["value"] - opt["step"])
            self._apply(opt)

    def _apply(self, opt: dict) -> None:
        self._dirty = True
        audio = self.audio
        if opt["name"] == "MUSIC VOLUME" and audio is not None:
            audio.music_volume = opt["value"]
        if opt["name"] == "SFX VOLUME" and audio is not None:
            audio.sfx_volume = opt["value"]

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
            val = opt.get("value", (opt["min"] + opt["max"]) / 2)
            val_s = f"{val:.2f}" if isinstance(val, float) else f"{int(val)}"
            val_surf = pygame.font.Font(None, 18).render(val_s, True, color)
            surface.blit(val_surf, (settings.INTERNAL_WIDTH - 90, y))
            y += 28
