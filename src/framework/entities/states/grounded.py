from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core.events import Events
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot
from src.framework.entities.states.helpers import (
    _can_dash,
    _handle_charge_input,
    _handle_grab_input,
    _handle_grounded_attack_input,
    _handle_grounded_jump_input,
    _handle_parry_input,
    _handle_ultimate_input,
)

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class IdleState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.IDLE)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if _handle_ultimate_input(player, inp):
            return

        if _handle_grab_input(player, inp):
            return

        if _handle_parry_input(player, inp):
            return

        if _handle_charge_input(player, inp):
            return

        if inp.move_x != 0:
            player.facing_direction = inp.move_x

        if _handle_grounded_attack_input(player, inp):
            return

        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.states import DashingState
            player._change_state_instance(DashingState())
            return

        if inp.crouch_held and player.is_grounded:
            from src.framework.entities.states import CrouchingState
            player._change_state_instance(CrouchingState())
            player.velocity.x = 0.0
            return

        if _handle_grounded_jump_input(player, inp):
            return

        if inp.move_x != 0 and player.is_grounded:
            from src.framework.entities.states import WalkingState
            player._change_state_instance(WalkingState())
            player.velocity.x = float(inp.move_x) * player.walk_speed
        else:
            player.velocity.x = 0.0

        if not player.is_grounded:
            if player.velocity.y < 0:
                from src.framework.entities.states import JumpingState
                player._change_state_instance(JumpingState())
            else:
                from src.framework.entities.states import FallingState
                player._change_state_instance(FallingState())


class WalkingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.WALKING)
        self._footstep_timer: float = 0.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._footstep_timer += dt
        if self._footstep_timer >= 0.35:
            self._footstep_timer = 0.0
            player._event_bus.emit(Events.SFX_PLAYER_FOOTSTEP)
        inp = _InputSnapshot(input_manager)

        if _handle_ultimate_input(player, inp):
            return

        if _handle_grab_input(player, inp):
            return

        if _handle_parry_input(player, inp):
            return

        if _handle_charge_input(player, inp):
            return

        if inp.move_x != 0:
            player.facing_direction = inp.move_x

        if _handle_grounded_attack_input(player, inp):
            return

        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.states import DashingState
            player._change_state_instance(DashingState())
            return

        if inp.crouch_held and player.is_grounded and abs(player.velocity.x) > 30.0:
            from src.framework.entities.states import SlideState
            player._change_state_instance(SlideState())
            return

        if inp.crouch_held and player.is_grounded:
            from src.framework.entities.states import CrouchingState
            player._change_state_instance(CrouchingState())
            player.velocity.x = 0.0
            return

        if _handle_grounded_jump_input(player, inp):
            return

        if inp.move_x != 0 and player.is_grounded:
            player.velocity.x = float(inp.move_x) * player.walk_speed
        elif inp.move_x == 0 and player.is_grounded:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            player.velocity.x = 0.0

        if not player.is_grounded:
            if player.velocity.y < 0:
                from src.framework.entities.states import JumpingState
                player._change_state_instance(JumpingState())
            else:
                from src.framework.entities.states import FallingState
                player._change_state_instance(FallingState())


class CrouchingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.CROUCHING)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._update_rect_size()

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if _handle_ultimate_input(player, inp):
            return

        if _handle_parry_input(player, inp):
            return

        if _handle_grounded_attack_input(player, inp):
            return

        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.states import DashingState
            player._change_state_instance(DashingState())
            return

        if not inp.crouch_held or not player.is_grounded:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            player.velocity.x = 0.0
            return

        player.velocity.x = 0.0

    def exit(self, player: Player) -> None:
        player._update_rect_size()


class SlideState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SLIDE)
        self._timer: float = 0.0
        self._slide_dir: float = 1.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        self._timer = player._slide_duration
        self._slide_dir = 1.0 if abs(player.velocity.x) > 0 else float(player.facing_direction)
        player.velocity.x = self._slide_dir * player._slide_speed
        old_bottom = player.rect.bottom
        player.rect.h = 18
        player.rect.y = old_bottom - 18
        player.position.y = float(player.rect.y)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        self._timer -= dt
        player.velocity.x = self._slide_dir * player._slide_speed

        if self._timer <= 0.0 or (player.is_grounded and not inp.crouch_held):
            player.velocity.x *= 0.3 ** (dt * 60.0)
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return

        if not player.is_grounded:
            from src.framework.entities.states import FallingState
            player._change_state_instance(FallingState())
            return

    def exit(self, player: Player) -> None:
        player._update_rect_size()
        player.velocity.x = 0.0
