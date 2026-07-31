from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.engine.input.action_map import Action

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player, PlayerState


class PlayerStateBase(ABC):
    def __init__(self, state_enum: PlayerState) -> None:
        self.state_enum: PlayerState = state_enum

    def enter(self, player: Player) -> None:
        player._animation_timer = 0.0
        player._animation_frame = 0

    @abstractmethod
    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        ...

    def exit(self, player: Player) -> None:
        return


class _InputSnapshot:
    __slots__ = (
        "crouch_held",
        "dash_pressed",
        "grab_pressed",
        "jump_held",
        "jump_pressed",
        "long_attack",
        "move_x",
        "move_y_up",
        "short_attack",
    )

    def __init__(self, im: InputManager | None) -> None:
        move_x = 0
        jump_pressed = False
        jump_held = False
        crouch_held = False
        short_attack = False
        long_attack = False
        dash_pressed = False
        grab_pressed = False
        # F5.14 — subir. Hasta las lianas no hacía falta: MOVE_UP existía en
        # `Action` y no lo leía nadie, así que pulsar arriba no hacía nada.
        move_y_up = False

        if im is not None:
            if im.is_action_held(Action.MOVE_LEFT):
                move_x -= 1
            if im.is_action_held(Action.MOVE_RIGHT):
                move_x += 1
            jump_pressed = im.is_action_pressed(Action.JUMP)
            jump_held = im.is_action_held(Action.JUMP)
            crouch_held = im.is_action_held(Action.CROUCH)
            short_attack = im.is_action_pressed(Action.SHORT_ATTACK)
            long_attack = im.is_action_pressed(Action.LONG_ATTACK)
            dash_pressed = im.is_action_pressed(Action.DASH)
            grab_pressed = im.is_action_pressed(Action.GRAB)
            move_y_up = im.is_action_held(Action.MOVE_UP)

        self.move_x = move_x
        self.move_y_up = move_y_up
        self.jump_pressed = jump_pressed
        self.jump_held = jump_held
        self.crouch_held = crouch_held
        self.short_attack = short_attack
        self.long_attack = long_attack
        self.dash_pressed = dash_pressed
        self.grab_pressed = grab_pressed
