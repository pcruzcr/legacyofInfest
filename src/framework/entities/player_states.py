"""
Module: player_states
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit IV (Sprite Animation)
Description: State Pattern implementation for Player entity.
9 concrete states extracted from Player's monolithic _run_state_machine.

STATE PATTERN: Each state encapsulates the behavior, input handling, and
transitions for one phase of the player's gameplay loop. The Player
delegates its per-frame update to the current state instance.

See also: player.py, 04_PLAYER_SPEC.md §8.1
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.engine.input.action_map import Action

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.engine.input.input_manager import InputManager


# ── Abstract base ─────────────────────────────────────────────────


class PlayerStateBase(ABC):
    """
    Abstract state in the Player State Pattern.
    Each concrete state owns one value of the PlayerState enum and
    handles update logic, input processing, and transitions.
    """

    def __init__(self, state_enum: object) -> None:
        """Store the PlayerState enum value this state represents."""
        self.state_enum = state_enum

    def enter(self, player: Player) -> None:
        """Called when entering this state. Resets animation by default."""
        player._animation_timer = 0.0
        player._animation_frame = 0

    @abstractmethod
    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        """Called every frame while this state is active."""
        ...

    def exit(self, player: Player) -> None:
        """Called when leaving this state. Override to clean up."""
        return


# ── Input helper ──────────────────────────────────────────────────


class _InputSnapshot:
    """
    Captures all relevant input actions for the current frame.
    States read from this snapshot rather than querying InputManager directly.
    """
    __slots__ = (
        "move_x", "jump_pressed", "jump_held",
        "crouch_held", "short_attack", "long_attack",
        "dash_pressed",
    )

    def __init__(self, im: InputManager | None) -> None:
        move_x = 0
        jump_pressed = False
        jump_held = False
        crouch_held = False
        short_attack = False
        long_attack = False
        dash_pressed = False

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

        self.move_x = move_x
        self.jump_pressed = jump_pressed
        self.jump_held = jump_held
        self.crouch_held = crouch_held
        self.short_attack = short_attack
        self.long_attack = long_attack
        self.dash_pressed = dash_pressed


# ── Grounded states (IDLE, WALKING, CROUCHING) ───────────────────
# Shared helpers that avoid code duplication across grounded states.


def _handle_grounded_attack_input(
    player: Player, inp: _InputSnapshot,
) -> bool:
    """If an attack input is active, start the attack and return True."""
    if inp.short_attack:
        _start_attack(player, player.SHORT_ATTACK)
        return True
    if inp.long_attack:
        _start_attack(player, player.LONG_ATTACK)
        return True
    return False


def _handle_grounded_jump_input(
    player: Player, inp: _InputSnapshot,
) -> bool:
    """If jump is pressed and the player can jump, execute and return True."""
    if inp.jump_pressed and _can_jump(player):
        _do_jump(player)
        return True
    return False


def _can_jump(player: Player) -> bool:
    return (
        player.is_grounded
        or player._coyote_counter < settings.PLAYER_COYOTE_FRAMES
    )


def _do_jump(player: Player) -> None:
    player.velocity.y = settings.PLAYER_JUMP_FORCE
    player.is_grounded = False
    player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
    player._jump_cut_applied = False
    from src.framework.entities.player_states import JumpingState
    player._change_state_instance(JumpingState())
    emit(Events.SFX_PLAYER_JUMP)


def _start_attack(player: Player, attack_type: object) -> None:
    """Create and transition to the appropriate attack state."""
    import src.engine.core.settings as settings
    atk_name = "SHORT_ATTACK" if attack_type == player.SHORT_ATTACK else "LONG_ATTACK"

    # Combo logic: window + type match
    if (player.combo_active
            and player.combo_timer > 0
            and player.last_attack_type == atk_name
            and player.combo_count < settings.COMBO_MAX):
        player.combo_count += 1
    else:
        player.combo_count = 1
    player.combo_timer = settings.COMBO_WINDOW
    player.last_attack_type = atk_name
    player.combo_active = True

    player.velocity.x = 0.0
    from src.framework.entities.player_states import (
        ShortAttackState,
        LongAttackState,
    )
    if attack_type == player.SHORT_ATTACK:
        player._change_state_instance(ShortAttackState())
        emit(Events.SFX_PLAYER_SHORT_ATTACK)
    else:
        player._change_state_instance(LongAttackState())
        emit(Events.SFX_PLAYER_LONG_ATTACK)


# ── Concrete states ───────────────────────────────────────────────


class IdleState(PlayerStateBase):
    """Player standing still on ground. Listens for movement, jump, crouch, attack."""

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

        # Attack input has priority
        if _handle_grounded_attack_input(player, inp):
            return

        # Dash
        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.player_states import DashingState
            player._change_state_instance(DashingState())
            return

        # Crouch
        if inp.crouch_held and player.is_grounded:
            from src.framework.entities.player_states import CrouchingState
            player._change_state_instance(CrouchingState())
            player.velocity.x = 0.0
            return

        # Jump
        if _handle_grounded_jump_input(player, inp):
            return

        # Horizontal movement
        if inp.move_x != 0 and player.is_grounded:
            player.facing_direction = inp.move_x
            from src.framework.entities.player_states import WalkingState
            player._change_state_instance(WalkingState())
            player.velocity.x = float(inp.move_x) * settings.PLAYER_WALK_SPEED
        else:
            player.velocity.x = 0.0

        # Airborne state tracking
        if not player.is_grounded:
            if player.velocity.y < 0:
                from src.framework.entities.player_states import JumpingState
                player._change_state_instance(JumpingState())
            else:
                from src.framework.entities.player_states import FallingState
                player._change_state_instance(FallingState())

class WalkingState(PlayerStateBase):
    """Player walking on ground. Same inputs as idle but maintains velocity."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.WALKING)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        if _handle_grounded_attack_input(player, inp):
            return

        # Dash
        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.player_states import DashingState
            player._change_state_instance(DashingState())
            return

        if inp.crouch_held and player.is_grounded:
            from src.framework.entities.player_states import CrouchingState
            player._change_state_instance(CrouchingState())
            player.velocity.x = 0.0
            return

        if _handle_grounded_jump_input(player, inp):
            return

        if inp.move_x != 0 and player.is_grounded:
            player.facing_direction = inp.move_x
            player.velocity.x = float(inp.move_x) * settings.PLAYER_WALK_SPEED
        elif inp.move_x == 0 and player.is_grounded:
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())
            player.velocity.x = 0.0

        if not player.is_grounded:
            if player.velocity.y < 0:
                from src.framework.entities.player_states import JumpingState
                player._change_state_instance(JumpingState())
            else:
                from src.framework.entities.player_states import FallingState
                player._change_state_instance(FallingState())


class CrouchingState(PlayerStateBase):
    """Player crouching. Reduced height, no horizontal movement."""

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

        if _handle_grounded_attack_input(player, inp):
            return

        # Dash from crouch
        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.player_states import DashingState
            player._change_state_instance(DashingState())
            return

        # Release crouch
        if not inp.crouch_held or not player.is_grounded:
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())
            player.velocity.x = 0.0
            return

        player.velocity.x = 0.0

    def exit(self, player: Player) -> None:
        player._update_rect_size()


# ── Airborne states ──────────────────────────────────────────────


class AirborneState(PlayerStateBase):
    """
    Base for JumpingState and FallingState.
    Handles horizontal air control and the transition to grounded.
    """

    def _airborne_update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        # Air dash
        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.player_states import DashingState
            player._change_state_instance(DashingState())
            return

        # Attack in air
        if _handle_grounded_attack_input(player, inp):
            return

        # Buffer jump: if jump pressed while airborne, save it for when we land
        # Timer (~8 frames) prevents bouncing off platforms when the player
        # pressed jump far above the ground while still giving coyote time.
        import src.engine.core.settings as settings
        if inp.jump_pressed:
            player._pending_jump = True
            player._pending_jump_timer = 8.0 / 60.0

        # Air control (reduced)
        if inp.move_x != 0:
            player.facing_direction = inp.move_x
            player.velocity.x = float(inp.move_x) * settings.PLAYER_WALK_SPEED * 0.5

        # Landed
        if player.is_grounded:
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())
            return

        # Fall-through: update air state type if vertical direction changed
        from src.framework.entities.player_states import JumpingState, FallingState
        if isinstance(self, JumpingState) and player.velocity.y >= 0:
            player._change_state_instance(FallingState())
            return

        if isinstance(self, FallingState) and player.velocity.y < 0:
            player._change_state_instance(JumpingState())
            return

        # Jump cut
        if not inp.jump_held and player.velocity.y < 0 and not player._jump_cut_applied:
            player.velocity.y *= 0.5
            player._jump_cut_applied = True


class JumpingState(AirborneState):
    """Player moving upward (velocity.y < 0)."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.JUMPING)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._airborne_update(player, dt, input_manager)


class FallingState(AirborneState):
    """Player falling downward (velocity.y >= 0)."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.FALLING)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._airborne_update(player, dt, input_manager)


# ── Dash state ──────────────────────────────────────────────────


def _can_dash(player: Player, inp: _InputSnapshot) -> bool:
    """Check if the player can dash (ground or air)."""
    if player._dash_cooldown > 0:
        return False
    if player.is_grounded:
        return True
    return player._air_dash_count < settings.PLAYER_AIR_DASH_LIMIT


_DASH_DURATION = 0.15


class DashingState(PlayerStateBase):
    """Player dashing — horizontal burst, invincible, no attacks."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.DASHING)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._dash_timer = _DASH_DURATION
        if not player.is_grounded:
            player._air_dash_count += 1
        player.velocity.y = 0.0
        player._invincibility_timer = max(player._invincibility_timer, _DASH_DURATION)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        player._dash_timer -= dt

        # Maintain dash velocity
        player.velocity.x = float(player.facing_direction) * settings.PLAYER_DASH_SPEED

        # Dash complete
        if player._dash_timer <= 0:
            player._dash_cooldown = 0.1
            if player.is_grounded:
                from src.framework.entities.player_states import IdleState
                player._change_state_instance(IdleState())
            else:
                from src.framework.entities.player_states import FallingState
                player._change_state_instance(FallingState())
            return


# ── Attack states ────────────────────────────────────────────────


class _AttackState(PlayerStateBase):
    """
    Base for ShortAttackState and LongAttackState.
    Handles animation-driven hitbox timing.
    Override FRAME_DATA in subclasses to configure attack-specific params.
    """

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
        player.velocity.x = 0.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        player._attack_timer += dt
        frame_duration = 1.0 / self.FPS

        if player._attack_timer >= frame_duration:
            player._attack_timer -= frame_duration
            player._attack_current_frame += 1
            player._animation_frame = player._attack_current_frame

        current_frame = player._attack_current_frame + 1  # 1-indexed

        if current_frame in self.ACTIVE_FRAMES and not player._hitbox_consumed:
            player._active_hitbox = _build_attack_hitbox(player, current_frame)
        else:
            player._active_hitbox = None

        # Animation complete
        if player._attack_current_frame >= self.TOTAL_FRAMES:
            player._active_hitbox = None
            if self.COOLDOWN > 0:
                player._cooldown_timer = self.COOLDOWN
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


class ShortAttackState(_AttackState):
    """Quick attack — 6 frames, frames 2-4 active, short cooldown."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SHORT_ATTACK)
        self.TOTAL_FRAMES = 6
        self.FPS = 18.0
        self.ACTIVE_FRAMES = [2, 3, 4]
        self.COOLDOWN = settings.PLAYER_COOLDOWN_SHORT


class LongAttackState(_AttackState):
    """Heavy attack — 10 frames, frames 4-7 active, long cooldown."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.LONG_ATTACK)
        self.TOTAL_FRAMES = 10
        self.FPS = 16.0
        self.ACTIVE_FRAMES = [4, 5, 6, 7]
        self.COOLDOWN = settings.PLAYER_COOLDOWN_LONG


def _reset_combo(player: Player) -> None:
    player.combo_count = 0
    player.combo_timer = 0.0
    player.combo_active = False


def _build_attack_hitbox(player: Player, frame: int) -> pygame.Rect:
    """Build the attack hitbox rect for the given 1-indexed frame."""
    attack_state = player._state_instance
    is_short = isinstance(attack_state, ShortAttackState)
    is_long = isinstance(attack_state, LongAttackState)
    is_crouching = isinstance(player._prev_state_instance, CrouchingState)

    cx = player.rect.centerx
    cy = player.rect.centery

    if is_short:
        offset_x = 8
        offset_y = -4 if not is_crouching else 8
        w, h = 36, 20
        if not is_crouching:
            h = 20
    elif is_long:
        frame_offsets = {
            4: (12, -10, 36, 20),
            5: (18, -4, 36, 20),
            6: (18, 0, 36, 20),
            7: (12, 6, 36, 20),
        }
        if frame in frame_offsets:
            offset_x, offset_y, w, h = frame_offsets[frame]
        else:
            return pygame.Rect(0, 0, 0, 0)
        if is_crouching:
            offset_y += 12
            h = 12
    else:
        return pygame.Rect(0, 0, 0, 0)

    hx = cx + (offset_x * player.facing_direction) - (w // 2)
    hy = cy + offset_y - (h // 2)
    return pygame.Rect(hx, hy, w, h)


# ── Damage states ────────────────────────────────────────────────


class HurtState(PlayerStateBase):
    """Player taking knockback. Waits for knockback timer then returns to idle."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.HURT)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        if player._knockback_timer <= 0:
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())


class DyingState(PlayerStateBase):
    """Player death animation. Terminal — no transitions to other states."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.DYING)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        pass  # Terminal state — no update logic needed
