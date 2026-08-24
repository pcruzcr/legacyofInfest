"""
Module: test_input_manager
System: tests
Description: Tests for InputManager: pressed/held/released semantics and action mapping.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager


@pytest.fixture
def manager() -> InputManager:
    return InputManager()


def simulate_key(manager: InputManager, key: int, down: bool) -> None:
    etype = pygame.KEYDOWN if down else pygame.KEYUP
    event = pygame.event.Event(etype, {"key": key})
    manager.pump([event])


class TestInputManager:
    def test_is_action_just_pressed_true_on_keydown(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        assert manager.is_action_just_pressed(Action.MOVE_LEFT)

    def test_is_action_just_pressed_false_after_consume(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        manager.consume(Action.MOVE_LEFT)
        assert not manager.is_action_just_pressed(Action.MOVE_LEFT)

    def test_is_action_held_true_while_key_down(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_RIGHT, True)
        assert manager.is_action_held(Action.MOVE_RIGHT)
        manager.pump([])
        assert manager.is_action_held(Action.MOVE_RIGHT)

    def test_is_action_held_false_after_release(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_RIGHT, True)
        simulate_key(manager, pygame.K_RIGHT, False)
        assert not manager.is_action_held(Action.MOVE_RIGHT)

    def test_is_action_released_true_on_keyup(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_SPACE, True)
        simulate_key(manager, pygame.K_SPACE, False)
        assert manager.is_action_released(Action.JUMP)

    def test_is_action_just_pressed_false_for_unbound_action(self, manager: InputManager) -> None:
        manager.pump([])
        assert not manager.is_action_just_pressed(Action.PAUSE)

    def test_rebind_changes_key(self, manager: InputManager) -> None:
        manager.rebind(Action.JUMP, [pygame.K_q])
        simulate_key(manager, pygame.K_q, True)
        assert manager.is_action_just_pressed(Action.JUMP)
        simulate_key(manager, pygame.K_SPACE, True)
        assert not manager.is_action_just_pressed(Action.JUMP)

    def test_is_action_just_pressed_only_one_frame(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        assert manager.is_action_just_pressed(Action.MOVE_LEFT)
        manager.pump([])
        assert not manager.is_action_just_pressed(Action.MOVE_LEFT)

    def test_is_action_held_returns_true_after_multiple_frames(self, manager: InputManager) -> None:
        simulate_key(manager, pygame.K_LEFT, True)
        assert manager.is_action_held(Action.MOVE_LEFT)
        manager.pump([])
        assert manager.is_action_held(Action.MOVE_LEFT)
        manager.pump([])
        assert manager.is_action_held(Action.MOVE_LEFT)

    def test_default_bindings_exist_for_all_actions(self, manager: InputManager) -> None:
        for action in Action:
            assert action in manager._bindings
            assert len(manager._bindings[action]) > 0


class _FakeJoystick:
    """Un mando sin SDL: sólo responde a `get_axis`."""

    def __init__(self, axis_x: float = 0.0, axis_y: float = 0.0) -> None:
        self._x, self._y = axis_x, axis_y

    def get_axis(self, i: int) -> float:
        return self._x if i == 0 else self._y


class TestElMandoNavegaLosMenus:
    """AUD-320 — el mando no podía navegar los menús: los menús leen
    `is_raw_key_pressed(K_UP/K_DOWN)` y el `InputManager` nunca sintetizaba
    esas teclas desde el mando (ni el hat de la cruceta ni el eje Y)."""

    def test_el_hat_arriba_sintetiza_la_flecha_arriba(self, manager: InputManager) -> None:
        manager.pump([pygame.event.Event(pygame.JOYHATMOTION, {"hat": 0, "value": (0, 1)})])
        assert manager.is_raw_key_pressed(pygame.K_UP)

    def test_el_hat_abajo_sintetiza_la_flecha_abajo(self, manager: InputManager) -> None:
        manager.pump([pygame.event.Event(pygame.JOYHATMOTION, {"hat": 0, "value": (0, -1)})])
        assert manager.is_raw_key_pressed(pygame.K_DOWN)

    def test_el_hat_izquierda_sintetiza_la_flecha_izquierda(self, manager: InputManager) -> None:
        manager.pump([pygame.event.Event(pygame.JOYHATMOTION, {"hat": 0, "value": (-1, 0)})])
        assert manager.is_raw_key_pressed(pygame.K_LEFT)

    def test_el_hat_solo_pulsa_un_fotograma(self, manager: InputManager) -> None:
        manager.pump([pygame.event.Event(pygame.JOYHATMOTION, {"hat": 0, "value": (0, 1)})])
        assert manager.is_raw_key_pressed(pygame.K_UP)
        manager.pump([])
        assert not manager.is_raw_key_pressed(pygame.K_UP), (
            "la navegación del hat tiene que ser de un fotograma: si se repite, "
            "el menú recorre varias filas por pulsación"
        )

    def test_el_eje_vertical_sintetiza_la_flecha_arriba(self, manager: InputManager) -> None:
        manager._joystick = _FakeJoystick(axis_y=-0.9)
        manager.pump([pygame.event.Event(pygame.JOYAXISMOTION, {"axis": 0})])
        assert manager.is_raw_key_pressed(pygame.K_UP)

    def test_el_eje_en_la_banda_muerta_no_pulsa_nada(self, manager: InputManager) -> None:
        manager._joystick = _FakeJoystick(axis_y=0.2)
        manager.pump([pygame.event.Event(pygame.JOYAXISMOTION, {"axis": 0})])
        assert not manager.is_raw_key_pressed(pygame.K_UP)
        assert not manager.is_raw_key_pressed(pygame.K_DOWN)

    def test_el_hat_navega_el_menu_de_demos_de_verdad(self) -> None:
        """Extremo a extremo: hat abajo y la selección del menú baja."""
        from unittest.mock import MagicMock

        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.scenes.demo_menu_scene import DemoMenuScene

        pygame.init()
        pygame.font.init()
        im = InputManager()
        ctx = GameContext(
            input_manager=im,
            audio_manager=MagicMock(),
            scene_manager=MagicMock(),
            event_bus=EventBus(),
        )
        escena = DemoMenuScene(ctx)
        escena.on_enter()
        inicial = escena._selected

        im.pump([pygame.event.Event(pygame.JOYHATMOTION, {"hat": 0, "value": (0, -1)})])
        escena.update(0.016)

        assert escena._selected == inicial + 1, (
            "el hat no movió la selección del menú: el mando no navega"
        )
