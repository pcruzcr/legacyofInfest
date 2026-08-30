from __future__ import annotations

from typing import TYPE_CHECKING

import orjson
import pygame

from src.engine.core import settings
from src.engine.core.i18n import _
from src.engine.core.user_settings import user_data_dir
from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action
from src.engine.scene.base_scene import BaseScene
from src.engine.ui.theme import Theme, font
from src.engine.ui.widgets import draw_key_hints, draw_screen

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

CONFIG_PATH = user_data_dir() / "keybindings.json"

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
    Action.MOVE_LEFT: _("ui.move_left"),
    Action.MOVE_RIGHT: _("ui.move_right"),
    Action.MOVE_UP: _("ui.move_up"),
    Action.MOVE_DOWN: _("ui.move_down"),
    Action.JUMP: _("ui.jump"),
    Action.CROUCH: _("ui.crouch"),
    Action.SHORT_ATTACK: _("ui.attack_short"),
    Action.LONG_ATTACK: _("ui.attack_long"),
    Action.DASH: _("ui.dash"),
    Action.GRAB: _("ui.grab"),
    Action.RANGED_ATTACK: _("ui.ranged_attack"),
    Action.CONFIRM: _("ui.confirm"),
    Action.CANCEL: _("ui.cancel"),
    Action.PAUSE: _("ui.pause"),
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
        self._last_keys_state: tuple[bool, ...] = tuple()
        # AUD-069: escala del tema y caché de fuentes compartida.
        self._font_text = font(Theme.FONT_TINY)
        self._font_label = font(Theme.FONT_SMALL)

    def _load_bindings(self) -> dict[str, list[int]]:
        try:
            raw = orjson.loads(CONFIG_PATH.read_bytes())
            return {str(k): v for k, v in raw.items()}
        except (FileNotFoundError, orjson.JSONDecodeError):
            return {}

    def _save_bindings(self) -> None:
        data: dict[str, list[int]] = {}
        for action in self._actions:
            im = self.input
            if im is not None:
                keys = im._bindings.get(action, DEFAULT_KEY_BINDINGS.get(action, []))
                data[action.name] = list(keys)
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))

    def on_enter(self) -> None:
        saved = self._load_bindings()
        im = self.input
        if im is not None:
            for action in self._actions:
                key = action.name
                if key in saved:
                    im.rebind(action, saved[key])
        self.context.scene_manager.transition.start_fade_in(0.5)

    def on_exit(self) -> None:
        if self._dirty:
            self._save_bindings()

    @staticmethod
    def _snapshot_keys() -> tuple[bool, ...]:
        """Copy the current keyboard state into a plain tuple.

        AUD-041: the previous code called ``tuple(pygame.key.get_pressed())``
        and ``enumerate(keys)``. In pygame-ce 2.5 ``get_pressed()`` returns a
        ``ScancodeWrapper``, which supports ``len()`` and indexing but **not**
        iteration, so both raised::

            TypeError: Iterating over key states is not supported

        That made the entire key-rebinding screen unreachable — pressing Enter
        on any binding crashed the scene. Indexing explicitly works on every
        pygame version.
        """
        keys = pygame.key.get_pressed()
        return tuple(bool(keys[i]) for i in range(len(keys)))

    def update(self, dt: float) -> None:
        im = self.input
        if im is None:
            return

        if self._waiting_for_key:
            keys = self._snapshot_keys()
            for k, pressed in enumerate(keys):
                if pressed and (k >= len(self._last_keys_state) or not self._last_keys_state[k]):
                    if k == pygame.K_ESCAPE:
                        self._waiting_for_key = False
                        self._last_keys_state = keys
                        return
                    action = self._actions[self._selected]
                    im.rebind(action, [k])
                    self._dirty = True
                    self._waiting_for_key = False
                    self._last_keys_state = keys
                    return
            self._last_keys_state = keys
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
            self._last_keys_state = self._snapshot_keys()
        if im.is_action_just_pressed(Action.CANCEL):
            from src.engine.scenes.title_scene import TitleScene
            self.context.scene_manager.replace(TitleScene(self.context))

    def draw(self, surface: pygame.Surface) -> None:
        # AUD-069: rejilla de dos columnas, así que la navegación sigue siendo
        # propia; lo que se unifica es la paleta, la tipografía y los atajos.
        start_y = draw_screen(
            surface, "ui.controls", "ui.choose_action",
        ) + Theme.SPACE_S

        cols = self._num_cols
        col_w = settings.INTERNAL_WIDTH // cols
        row_h = 40

        for i, action in enumerate(self._actions):
            col = i % cols
            row = i // cols
            x = col * col_w + 16
            y = start_y + row * row_h
            focused = i == self._selected
            active = focused and not self._waiting_for_key
            if focused:
                # Fondo elevado bajo la fila enfocada: el color del texto por
                # sí solo no marca el foco cuando hay ocho filas en dos
                # columnas y la vista salta de una a otra.
                pygame.draw.rect(
                    surface, Theme.SURFACE_RAISED,
                    pygame.Rect(x - Theme.SPACE_S, y - 2,
                                col_w - Theme.SPACE_M, row_h - Theme.SPACE_XS),
                    border_radius=Theme.RADIUS,
                )
            label = self._font_label.render(
                _ACTION_LABELS[action], True,
                Theme.ACCENT if active else Theme.TEXT,
            )
            surface.blit(label, (x, y))

            im = self.input
            if im is not None:
                keys = im._bindings.get(action, DEFAULT_KEY_BINDINGS.get(action, []))
                key_str = " / ".join(_key_name(k) for k in keys)
            else:
                key_str = "..."
            key_colour = Theme.ACCENT if active else Theme.TEXT_MUTED
            if self._waiting_for_key and focused:
                blinking = int(pygame.time.get_ticks() / 500) % 2 == 0
                key_str = "— PULSA UNA TECLA —" if blinking else ""
                key_colour = Theme.WARNING
            key_display = self._font_text.render(key_str, True, key_colour)
            surface.blit(key_display, (x, y + 18))

        if self._waiting_for_key:
            draw_key_hints(surface, [
                ("Cualquier tecla", "ui.nav.assign"),
                ("Esc", "ui.cancel"),
            ])
        else:
            draw_key_hints(surface, [
                ("←→↑↓", "ui.nav.navigate"),
                ("Enter", "ui.change"),
                ("Esc", "ui.back"),
            ])

