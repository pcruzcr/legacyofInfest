from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action, DEFAULT_KEY_BINDINGS
from src.engine.scene.base_scene import BaseScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

CONFIG_PATH = Path(os.environ.get("APPDATA", "~/.config")) / "legacyofinfest" / "keybindings.json"

_KEY_NAMES: dict[int, str] = {
    pygame.K_a: "A", pygame.K_b: "B", pygame.K_c: "C", pygame.K_d: "D",
    pygame.K_e: "E", pygame.K_f: "F", pygame.K_g: "G", pygame.K_h: "H",
    pygame.K_i: "I", pygame.K_j: "J", pygame.K_k: "K", pygame.K_l: "L",
    pygame.K_m: "M", pygame.K_n: "N", pygame.K_o: "O", pygame.K_p: "P",
    pygame.K_q: "Q", pygame.K_r: "R", pygame.K_s: "S", pygame.K_t: "T",
    pygame.K_u: "U", pygame.K_v: "V", pygame.K_w: "W", pygame.K_x: "X",
    pygame.K_y: "Y", pygame.K_z: "Z",
    pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3",
    pygame.K_4: "4", pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7",
    pygame.K_8: "8", pygame.K_9: "9",
    pygame.K_SPACE: "SPACE", pygame.K_RETURN: "ENTER", pygame.K_ESCAPE: "ESC",
    pygame.K_TAB: "TAB", pygame.K_LSHIFT: "L-SHIFT", pygame.K_RSHIFT: "R-SHIFT",
    pygame.K_LCTRL: "L-CTRL", pygame.K_RCTRL: "R-CTRL",
    pygame.K_LALT: "L-ALT", pygame.K_RALT: "R-ALT",
    pygame.K_LEFT: "LEFT", pygame.K_RIGHT: "RIGHT", pygame.K_UP: "UP", pygame.K_DOWN: "DOWN",
    pygame.K_F1: "F1", pygame.K_F2: "F2", pygame.K_F3: "F3", pygame.K_F4: "F4",
    pygame.K_F5: "F5", pygame.K_F6: "F6", pygame.K_F7: "F7", pygame.K_F8: "F8",
    pygame.K_F9: "F9", pygame.K_F10: "F10", pygame.K_F11: "F11", pygame.K_F12: "F12",
}


def _key_name(key: int) -> str:
    return _KEY_NAMES.get(key, f"K{key}")


_ACTION_LABELS: dict[Action, str] = {
    Action.MOVE_LEFT: "Move Left",
    Action.MOVE_RIGHT: "Move Right",
    Action.MOVE_UP: "Move Up",
    Action.MOVE_DOWN: "Move Down",
    Action.JUMP: "Jump",
    Action.CROUCH: "Crouch",
    Action.SHORT_ATTACK: "Attack (Short)",
    Action.LONG_ATTACK: "Attack (Long)",
    Action.DASH: "Dash",
    Action.GRAB: "Grab",
    Action.CONFIRM: "Confirm",
    Action.CANCEL: "Cancel",
    Action.PAUSE: "Pause",
}


class KeybindingScene(BaseScene):
    """Key rebinding screen. Select an action, press a key to rebind."""

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._actions: list[Action] = list(_ACTION_LABELS.keys())
        self._selected: int = 0
        self._waiting_for_key: bool = False
        self._num_cols: int = 2
        self._dirty: bool = False

    def _load_bindings(self) -> dict[str, list[int]]:
        try:
            with open(CONFIG_PATH) as f:
                raw = json.load(f)
                return {str(k): v for k, v in raw.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_bindings(self) -> None:
        data: dict[str, list[int]] = {}
        for action in self._actions:
            im = self.input
            if im is not None:
                keys = im._bindings.get(action, DEFAULT_KEY_BINDINGS.get(action, []))
                data[action.name] = list(keys)
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def on_enter(self) -> None:
        saved = self._load_bindings()
        im = self.input
        if im is not None:
            for action in self._actions:
                key = action.name
                if key in saved:
                    im.rebind(action, saved[key])

    def on_exit(self) -> None:
        if self._dirty:
            self._save_bindings()

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._waiting_for_key:
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self._waiting_for_key = False
                        break
                    action = self._actions[self._selected]
                    im.rebind(action, [e.key])
                    self._dirty = True
                    self._waiting_for_key = False
                    break
            return

        if im.is_action_just_pressed(Action.MOVE_DOWN):
            if self._selected < len(self._actions) - self._num_cols:
                self._selected += self._num_cols
            else:
                self._selected = self._selected % self._num_cols
        if im.is_action_just_pressed(Action.MOVE_UP):
            if self._selected >= self._num_cols:
                self._selected -= self._num_cols
            else:
                row_count = (len(self._actions) + self._num_cols - 1) // self._num_cols
                last_row = len(self._actions) - self._num_cols * (row_count - 1)
                col = self._selected % self._num_cols
                self._selected = (row_count - 1) * self._num_cols + min(col, last_row - 1)
        if im.is_action_just_pressed(Action.MOVE_RIGHT):
            col = self._selected % self._num_cols
            if col < self._num_cols - 1 and self._selected + 1 < len(self._actions):
                self._selected += 1
        if im.is_action_just_pressed(Action.MOVE_LEFT):
            col = self._selected % self._num_cols
            if col > 0:
                self._selected -= 1
        if im.is_action_just_pressed(Action.CONFIRM):
            self._waiting_for_key = True
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 35))
        font = pygame.font.Font(None, 24)
        small = pygame.font.Font(None, 16)
        mid = pygame.font.Font(None, 18)

        title = font.render("KEY BINDINGS", True, (255, 255, 240))
        surface.blit(title, ((settings.INTERNAL_WIDTH - title.get_width()) // 2, 14))

        cols = self._num_cols
        col_w = settings.INTERNAL_WIDTH // cols
        start_y = 50
        row_h = 40

        for i, action in enumerate(self._actions):
            col = i % cols
            row = i // cols
            x = col * col_w + 16
            y = start_y + row * row_h
            active = i == self._selected and not self._waiting_for_key
            label_color = (255, 255, 100) if active else (200, 200, 200)
            label = mid.render(_ACTION_LABELS[action], True, label_color)
            surface.blit(label, (x, y))

            im = self.input
            if im is not None:
                keys = im._bindings.get(action, DEFAULT_KEY_BINDINGS.get(action, []))
                key_str = " / ".join(_key_name(k) for k in keys)
            else:
                key_str = "..."
            key_color = (180, 180, 220) if not active else (255, 200, 100)
            if self._waiting_for_key and i == self._selected:
                key_str = "--- PRESS KEY ---" if int(pygame.time.get_ticks() / 500) % 2 == 0 else ""
            key_display = small.render(key_str, True, key_color)
            surface.blit(key_display, (x, y + 18))

        hint_y = settings.INTERNAL_HEIGHT - 26
        if self._waiting_for_key:
            hint = small.render("Press any key to bind | ESC to cancel", True, (255, 200, 100))
        else:
            hint = small.render("[ARROWS] Navigate  [ENTER] Rebind  [ESC] Back", True, (160, 160, 170))
        surface.blit(hint, ((settings.INTERNAL_WIDTH - hint.get_width()) // 2, hint_y))
