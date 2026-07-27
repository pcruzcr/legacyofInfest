from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot
from src.framework.entities.states.helpers import _start_attack

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class HurtState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.HURT)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if inp.dash_pressed and player._knockback_timer > 0:
            from src.framework.entities.states import DashingState
            player.velocity.x = float(player.facing_direction) * settings.PLAYER_DASH_SPEED
            player.velocity.y = 0.0
            player._knockback_timer = 0.0
            player._dash_cooldown = 0.3
            player._invincibility_timer = max(player._invincibility_timer, 0.3)
            player._change_state_instance(DashingState())
            return

        if inp.short_attack and player._knockback_timer > 0:
            player.velocity.x = 0.0
            player.velocity.y = 0.0
            player._knockback_timer = 0.0
            _start_attack(player, player.SHORT_ATTACK)
            return

        if player._knockback_timer <= 0:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())


class DyingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.DYING)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        pass
