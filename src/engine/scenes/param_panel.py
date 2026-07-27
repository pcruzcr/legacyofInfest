"""
Module: param_panel
Description: Reusable parameter widget for demo/lab scenes.
Provides labelled integer/float parameters with +/- controls
and automatic rendering.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.scenes.demo_layout import (
    COLOR_HIGHLIGHT,
    COLOR_TEXT,
    FONT_SMALL,
    _get_demo_font,
)

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager


class ParamPanel:
    """A panel of labelled, adjustable parameters.

    Each param has a name, current value, min/max range, step, and
    a callback invoked when the value changes.

    Usage:
        panel = ParamPanel()
        panel.add_int("Threshold", 128, 0, 255, on_change=...)
        panel.add_float("Scale", 1.0, 0.1, 5.0, 0.1)
        # In update():
        panel.handle_input(im, dt)
        # In draw():
        panel.draw(surface, x, y)
    """

    def __init__(self) -> None:
        self._params: list[_ParamDef] = []
        self._selected: int = 0

    def add_int(self, name: str, default: int, vmin: int, vmax: int,
                step: int = 1, on_change: Callable[[int], None] | None = None,
                fmt: str | None = None) -> None:
        self._params.append(_ParamDef(name, default, vmin, vmax, step, on_change, fmt, _int_get, _int_set))

    def add_float(self, name: str, default: float, vmin: float, vmax: float,
                  step: float = 0.1, on_change: Callable[[float], None] | None = None,
                  fmt: str | None = None) -> None:
        self._params.append(_ParamDef(name, default, vmin, vmax, step, on_change, fmt, _float_get, _float_set))

    @property
    def values(self) -> dict[str, Any]:
        return {p.name: p.get() for p in self._params}

    def __getitem__(self, name: str) -> Any:
        for p in self._params:
            if p.name == name:
                return p.get()
        raise KeyError(name)

    def __setitem__(self, name: str, value: Any) -> None:
        for p in self._params:
            if p.name == name:
                p.set(value)
                return
        raise KeyError(name)

    def reset_to_defaults(self) -> None:
        for p in self._params:
            p.reset()

    def select(self, name: str) -> None:
        for i, p in enumerate(self._params):
            if p.name == name:
                self._selected = i
                return

    def cycle_selected(self, direction: int = 1) -> None:
        if not self._params:
            return
        self._selected = (self._selected + direction) % len(self._params)

    def adjust_selected(self, direction: int) -> None:
        if not self._params:
            return
        p = self._params[self._selected]
        p.adjust(direction)

    def handle_input(self, im: InputManager, dt: float) -> None:
        # UP/DOWN — cycle param
        if im.is_raw_key_pressed(pygame.K_UP):
            self.cycle_selected(-1)
        if im.is_raw_key_pressed(pygame.K_DOWN):
            self.cycle_selected(1)
        # LEFT/RIGHT — adjust value
        if im.is_raw_key_pressed(pygame.K_LEFT):
            self.adjust_selected(-1)
        if im.is_raw_key_pressed(pygame.K_RIGHT):
            self.adjust_selected(1)

    def draw(self, surface: pygame.Surface, x: int, y: int) -> None:
        fnt = _get_demo_font(FONT_SMALL)
        for i, p in enumerate(self._params):
            selected = i == self._selected
            prefix = ">" if selected else " "
            color = COLOR_HIGHLIGHT if selected else COLOR_TEXT
            txt = fnt.render(f"  {prefix} {p.name}: {p.fmt()}", True, color)
            surface.blit(txt, (x, y + i * 14))


class _ParamDef:
    def __init__(self, name: str, default: Any, vmin: Any, vmax: Any,
                 step: Any, on_change: Callable[..., None] | None, fmt: str | None,
                 getter: Callable[..., Any], setter: Callable[..., None]) -> None:
        self.name = name
        self.default = default
        self.vmin = vmin
        self.vmax = vmax
        self.step = step
        self.on_change = on_change
        self._getter = getter
        self._setter = setter
        self.fmt: Callable[[], str] = lambda: str(default)
        self._value = default
        self._setup_fmt(fmt)

    def _setup_fmt(self, fmt: str | None) -> None:
        if fmt:
            self.fmt = lambda: fmt % self._value
        elif isinstance(self.default, float):
            self.fmt = lambda: f"{self._value:.2f}"
        else:
            self.fmt = lambda: str(self._value)

    def get(self) -> Any:
        return self._getter(self)

    def set(self, value: Any) -> None:
        clamped = max(self.vmin, min(self.vmax, value))
        if clamped != self._value:
            self._value = clamped
            if self.on_change:
                self.on_change(self._value)

    def adjust(self, direction: int) -> None:
        self.set(self._value + self.step * direction)

    def reset(self) -> None:
        self._value = self.default


def _int_get(p: _ParamDef) -> int:
    return int(p._value)


def _int_set(p: _ParamDef, v: Any) -> None:
    p._value = int(max(p.vmin, min(p.vmax, v)))


def _float_get(p: _ParamDef) -> float:
    return float(p._value)


def _float_set(p: _ParamDef, v: Any) -> None:
    p._value = float(max(p.vmin, min(p.vmax, v)))
