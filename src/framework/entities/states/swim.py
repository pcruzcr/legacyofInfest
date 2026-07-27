from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class SwimmingState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SWIMMING)
        self._swim_timer: float = 0.0
        self._bubble_timer: float = 0.0
        self._surface_y: float = 0.0
        self._swim_boosts_used: int = 0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.y = 0.0
        player.velocity.x *= 0.5
        self._swim_timer = 0.0
        self._bubble_timer = 0.0
        self._surface_y = player.position.y - 16.0
        player._swim_boosts = 0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)
        self._swim_timer += dt
        self._bubble_timer += dt

        player.velocity.y += settings.GRAVITY * 0.3 * dt
        player.velocity.y = max(-60.0, min(120.0, player.velocity.y))

        if inp.move_x != 0:
            player.velocity.x += inp.move_x * 60.0 * dt
            player.velocity.x = max(-120.0, min(120.0, player.velocity.x))
            player.facing_direction = inp.move_x
        else:
            player.velocity.x *= 0.9 ** (dt * 60.0)

        if inp.jump_pressed and player._swim_boosts < 1:
            player.velocity.y = -120.0
            player._swim_boosts += 1
            player._event_bus.emit(Events.SFX_PLAYER_JUMP)

        if inp.crouch_held:
            player.velocity.y += 200.0 * dt

        if self._bubble_timer >= 0.3:
            self._bubble_timer = 0.0
            player._event_bus.emit(Events.VFX_BUBBLE, pos=(player.position.x, player.position.y))

        if player.position.y < self._surface_y - 8.0:
            player.velocity.y = -200.0
            from src.framework.entities.states import JumpingState
            player._change_state_instance(JumpingState())
            return

        if player.is_grounded:
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())
            return
