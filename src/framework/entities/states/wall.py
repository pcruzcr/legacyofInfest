from __future__ import annotations

from typing import TYPE_CHECKING

from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot
from src.framework.entities.states.helpers import _handle_wall_jump

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class WallSlideState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.WALL_SLIDE)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if _handle_wall_jump(player, inp):
            return

        if player._can_ledge_grab:
            from src.framework.entities.states import LedgeGrabState
            player._change_state_instance(LedgeGrabState())
            return

        if inp.short_attack:
            from src.framework.entities.states import AerialAttackState
            player._change_state_instance(AerialAttackState(short=True))
            return

        if inp.move_x == -player._wall_side:
            player._wall_side = 0
            player._can_wall_jump = False
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())
            return

        if player._wall_side == 0 or player.is_grounded:
            from src.framework.entities.states import FallingState, IdleState
            target = IdleState if player.is_grounded else FallingState
            player._change_state_instance(target())


class LedgeGrabState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.LEDGE_GRAB)
        self._timer: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        self._timer = 0.0
        player._invincibility_timer = max(player._invincibility_timer, 0.5)
        player.velocity.x = 0.0
        player.velocity.y = 0.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        inp = _InputSnapshot(input_manager)

        if inp.jump_pressed:
            from src.framework.entities.states import JumpingState
            player.velocity.y = -250.0
            player.velocity.x = float(player._wall_side) * 50.0
            player._wall_side = 0
            player._can_wall_jump = False
            player._change_state_instance(JumpingState())
            return

        if inp.crouch_held or self._timer > 1.5:
            player._wall_side = 0
            player._can_wall_jump = False
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())
            return

        if player.is_grounded or player._wall_side == 0:
            from src.framework.entities.states import FallingState, IdleState
            target = IdleState if player.is_grounded else FallingState
            player._change_state_instance(target())

        player.velocity.x = 0.0
        player.velocity.y = 0.0

    def exit(self, player: Player) -> None:
        pass
