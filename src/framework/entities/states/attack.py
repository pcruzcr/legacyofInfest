from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.entities.states.base import PlayerStateBase, _InputSnapshot
from src.framework.entities.states.helpers import (
    _build_attack_hitbox,
    _can_dash,
    _handle_grounded_jump_input,
)

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player import Player


class _AttackState(PlayerStateBase):
    TOTAL_FRAMES: int = 6
    FPS: float = 18.0
    ACTIVE_FRAMES: list[int] = [2, 3, 4]
    COOLDOWN: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._attack_current_frame = 0
        player._active_hitbox = None
        player._hitbox_consumed = False

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        player._attack_timer += dt
        frame_duration = 1.0 / self.FPS

        while player._attack_timer >= frame_duration and player._attack_current_frame < self.TOTAL_FRAMES:
            player._attack_timer -= frame_duration
            player._attack_current_frame += 1
            player._animation_frame = player._attack_current_frame

        current_frame = player._attack_current_frame + 1
        inp = _InputSnapshot(input_manager)

        if current_frame > max(self.ACTIVE_FRAMES):
            if inp.dash_pressed and _can_dash(player, inp):
                from src.framework.entities.states import DashingState
                player._change_state_instance(DashingState())
                return
            if _handle_grounded_jump_input(player, inp):
                return

        if current_frame in self.ACTIVE_FRAMES and not player._hitbox_consumed:
            player._active_hitbox = _build_attack_hitbox(player, current_frame)
        else:
            player._active_hitbox = None

        if player._attack_current_frame >= self.TOTAL_FRAMES:
            player._active_hitbox = None
            if self.COOLDOWN > 0:
                player._cooldown_timer = self.COOLDOWN
            from src.framework.entities.states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


class ShortAttackState(_AttackState):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SHORT_ATTACK)
        self.TOTAL_FRAMES = 6
        self.FPS = 18.0
        self.ACTIVE_FRAMES = [2, 3, 4]
        self.COOLDOWN = settings.PLAYER_COOLDOWN_SHORT


class LongAttackState(_AttackState):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.LONG_ATTACK)
        self.TOTAL_FRAMES = 10
        self.FPS = 16.0
        self.ACTIVE_FRAMES = [4, 5, 6, 7]
        self.COOLDOWN = settings.PLAYER_COOLDOWN_LONG


class DashAttackState(PlayerStateBase):
    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.DASH_ATTACK)
        self._timer: float = 0.0
        self._dir_x: float = 0.0
        self._dir_y: float = 0.0
        self._dir_init: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        # P0: 8-dir dash attack — dirección se resuelve en update con input; fallback a facing
        player.velocity.x = float(player.facing_direction) * settings.PLAYER_DASH_SPEED * 0.7
        player.velocity.y = 0.0
        self._dir_init = False
        player._invincibility_timer = max(player._invincibility_timer, 0.1)
        # P0: VFX_SLAM y estamina check
        if not player.hay_estamina_para_correr:
            pass
        try:
            from src.engine.core.events import Events as _Ev
            player._event_bus.emit(_Ev.VFX_SLAM, pos=(player.position.x, player.position.y))
        except Exception:
            pass

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        inp = _InputSnapshot(input_manager)
        # P0: 8-dir — inicializa dirección del dash-attack al primer fotograma
        if not self._dir_init:
            if inp.move_x != 0 or inp.move_y != 0:
                dx = float(inp.move_x)
                dy = float(inp.move_y)
            else:
                dx = float(player.facing_direction)
                dy = 0.0
            if dx != 0.0 and dy != 0.0:
                dx *= 0.70710678
                dy *= 0.70710678
            self._dir_x = dx
            self._dir_y = dy
            self._dir_init = True
            if self._dir_x > 0:
                player.facing_direction = 1
            elif self._dir_x < 0:
                player.facing_direction = -1
            # aplicar velocidad 8-dir al inicio del ataque
            player.velocity.x = self._dir_x * settings.PLAYER_DASH_SPEED * 0.7
            player.velocity.y = self._dir_y * settings.PLAYER_DASH_SPEED * 0.7

        if self._timer < 0.1 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 40, 20
            # P0: hitbox sigue la dirección 8-dir (usa _dir_x/_dir_y si inicializado)
            off_x = 10 * (self._dir_x if self._dir_init else float(player.facing_direction))
            off_y = -4 + (6 * self._dir_y if self._dir_init and self._dir_y != 0 else 0)
            hx = cx + int(off_x) - (w // 2)
            hy = cy + int(off_y) - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        # fricción en ambos ejes para 8-dir
        player.velocity.x *= 0.92 ** (dt * 60.0)
        player.velocity.y *= 0.92 ** (dt * 60.0)

        if self._timer >= 0.25:
            player._active_hitbox = None
            player._dash_cooldown = 0.1
            if player.is_grounded:
                from src.framework.entities.states import IdleState
                player._change_state_instance(IdleState())
            else:
                from src.framework.entities.states import FallingState
                player._change_state_instance(FallingState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None
