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
    from src.framework.entities.player import Player, PlayerState
    from src.engine.input.input_manager import InputManager


# ── Abstract base ─────────────────────────────────────────────────


class PlayerStateBase(ABC):
    """
    Abstract state in the Player State Pattern.
    Each concrete state owns one value of the PlayerState enum and
    handles update logic, input processing, and transitions.
    """

    def __init__(self, state_enum: PlayerState) -> None:
        """Store the PlayerState enum value this state represents."""
        self.state_enum: PlayerState = state_enum

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
        "dash_pressed", "grab_pressed",
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

        grab_pressed = False
        if im is not None:
            if im.is_action_pressed(Action.GRAB):
                grab_pressed = True

        self.move_x = move_x
        self.jump_pressed = jump_pressed
        self.jump_held = jump_held
        self.crouch_held = crouch_held
        self.short_attack = short_attack
        self.long_attack = long_attack
        self.dash_pressed = dash_pressed
        self.grab_pressed = grab_pressed


def _handle_parry_input(player: Player, inp: _InputSnapshot) -> bool:
    """Check if player should enter parry state. Press attack + CROUCH simultaneously."""
    if inp.short_attack and inp.crouch_held and player._parry_window <= 0:
        from src.framework.entities.player_states import ParryState
        player._change_state_instance(ParryState())
        return True
    return False


def _handle_charge_input(player: Player, inp: _InputSnapshot) -> bool:
    """Start charging on long attack press if not in cooldown."""
    from src.framework.entities.player import PlayerState
    if inp.long_attack and player._cooldown_timer <= 0:
        from src.framework.entities.player_states import ChargingState
        if player._state_instance.state_enum not in (PlayerState.CHARGE_ATTACK,):
            player._change_state_instance(ChargingState())
            return True
    return False


def _handle_wall_jump(player: Player, inp: _InputSnapshot) -> bool:
    """Wall jump off the detected wall side."""
    if player._can_wall_jump and inp.jump_pressed:
        wall_dir = player._wall_side
        player._air_jumps_used = 0
        player.velocity.y = settings.PLAYER_JUMP_FORCE * 0.85
        player.is_grounded = False
        player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
        player._jump_cut_applied = False
        player._wall_side = 0
        player._can_wall_jump = False
        player.facing_direction = -wall_dir
        from src.framework.entities.player_states import JumpingState
        player._change_state_instance(JumpingState())
        emit(Events.SFX_PLAYER_JUMP)
        return True
    return False


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


def _handle_aerial_attack_input(
    player: Player, inp: _InputSnapshot,
) -> bool:
    """Aerial attack — downward strike with different hitbox."""
    if inp.short_attack:
        from src.framework.entities.player_states import AerialAttackState
        player._change_state_instance(AerialAttackState(short=True))
        emit(Events.SFX_PLAYER_SHORT_ATTACK)
        return True
    if inp.long_attack:
        from src.framework.entities.player_states import AerialAttackState
        player._change_state_instance(AerialAttackState(short=False))
        emit(Events.SFX_PLAYER_LONG_ATTACK)
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
        or player._air_jumps_used < settings.PLAYER_AIR_JUMPS
    )


def _do_jump(player: Player) -> None:
    was_grounded = player.is_grounded
    player.velocity.y = settings.PLAYER_JUMP_FORCE
    player.is_grounded = False
    player._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1
    player._jump_cut_applied = False
    if not was_grounded and player._air_jumps_used < settings.PLAYER_AIR_JUMPS:
        player._air_jumps_used += 1
    from src.framework.entities.player_states import JumpingState
    player._change_state_instance(JumpingState())


def _reset_air_jumps(player: Player) -> None:
    player._air_jumps_used = 0
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

        # Ultimate input (both attacks + full meter)
        if _handle_ultimate_input(player, inp):
            return

        # Grab input (long attack + crouch, no short attack)
        if _handle_grab_input(player, inp):
            return

        # Parry input (attack + crouch)
        if _handle_parry_input(player, inp):
            return

        # Charge long attack
        if _handle_charge_input(player, inp):
            return

        # Attack input
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
            emit(Events.SFX_PLAYER_FOOTSTEP)
        inp = _InputSnapshot(input_manager)
        # Ultimate input (both attacks + full meter)
        if _handle_ultimate_input(player, inp):
            return

        # Grab input (long attack + crouch, no short attack)
        if _handle_grab_input(player, inp):
            return

        # Parry input (attack + crouch)
        if _handle_parry_input(player, inp):
            return

        # Charge long attack
        if _handle_charge_input(player, inp):
            return

        if _handle_grounded_attack_input(player, inp):
            return

        # Dash
        if inp.dash_pressed and _can_dash(player, inp):

            from src.framework.entities.player_states import DashingState
            player._change_state_instance(DashingState())
            return

        if inp.crouch_held and player.is_grounded and abs(player.velocity.x) > 30.0:
            from src.framework.entities.player_states import SlideState
            player._change_state_instance(SlideState())
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

        # Ultimate input (both attacks + full meter)
        if _handle_ultimate_input(player, inp):
            return

        # Parry input (attack + crouch) has highest priority
        if _handle_parry_input(player, inp):
            return

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


class SlideState(PlayerStateBase):
    """Player ground slide. Maintain momentum, reduced hitbox."""

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
        # Lower hurtbox while sliding
        orig_h = player.rect.h
        player.rect.h = int(orig_h * 0.6)
        player.rect.y = player.rect.bottom - player.rect.h

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
            player.velocity.x *= 0.3
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())
            return

        if not player.is_grounded:
            from src.framework.entities.player_states import FallingState
            player._change_state_instance(FallingState())
            return

    def exit(self, player: Player) -> None:
        player._update_rect_size()
        player.velocity.x = 0.0


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

        # Ultimate input (both attacks + full meter) works in air too
        if _handle_ultimate_input(player, inp):
            return

        # Air dash
        if inp.dash_pressed and _can_dash(player, inp):
            from src.framework.entities.player_states import DashingState
            player._change_state_instance(DashingState())
            return

        # Aerial attack (downward strike)
        if _handle_aerial_attack_input(player, inp):
            return

        # Wall jump
        if _handle_wall_jump(player, inp):
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

        # Wall slide detection
        if player._wall_side != 0 and player.velocity.y > 0 and inp.move_x == player._wall_side:
            from src.framework.entities.player_states import WallSlideState
            player._change_state_instance(WallSlideState())
            return

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

        # Dash attack
        inp = _InputSnapshot(input_manager)
        if inp.short_attack:
            from src.framework.entities.player_states import DashAttackState
            player._change_state_instance(DashAttackState())
            return
        if inp.long_attack:
            from src.framework.entities.player_states import DashAttackState
            player._change_state_instance(DashAttackState())
            return

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
        inp = _InputSnapshot(input_manager)

        # Cancel opportunities — only after active frames
        if current_frame > max(self.ACTIVE_FRAMES):
            if inp.dash_pressed and _can_dash(player, inp):
                from src.framework.entities.player_states import DashingState
                player._change_state_instance(DashingState())
                return
            if _handle_grounded_jump_input(player, inp):
                return

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


# ── Ultimate / Special state ─────────────────────────────────────


class UltimateState(PlayerStateBase):
    """Ultimate attack — full-screen AOE, spends all special meter."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.LONG_ATTACK)
        self._timer: float = 0.0
        self._duration: float = 0.6
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.x = 0.0
        player.velocity.y = 0.0
        player.special_meter = 0.0
        from src.engine.core.event_bus import emit
        from src.engine.core.events import Events
        emit(Events.VFX_ULTIMATE, pos=(player.position.x, player.position.y))

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt

        # Full-screen hitbox during active frames (0.1 to 0.4)
        if 0.1 <= self._timer < 0.4 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 96, 64  # Big AOE
            hx = cx - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
            player._damage_mult = 3.0  # Triple damage
        else:
            player._active_hitbox = None
            player._damage_mult = 1.0

        if self._timer >= self._duration:
            player._active_hitbox = None
            player._damage_mult = 1.0
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None
        player._damage_mult = 1.0


# ── Grab / Throw state ──────────────────────────────────────────


class GrabState(PlayerStateBase):
    """Grab an enemy — brief window to throw for big damage."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SHORT_ATTACK)
        self._timer: float = 0.0
        self._has_grabbed: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = float(player.facing_direction) * 30.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        inp = _InputSnapshot(input_manager)

        # Grab hitbox during first 0.15s
        if self._timer < 0.15 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 20, 16
            hx = cx + (8 * player.facing_direction) - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        if player._hitbox_consumed and not self._has_grabbed:
            self._has_grabbed = True
            player._active_hitbox = None
            # Throw forward
            if inp.short_attack or inp.long_attack:
                from src.framework.entities.player_states import ThrowState
                player._change_state_instance(ThrowState())
                return

        if self._timer >= 0.3:
            player._active_hitbox = None
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


class ThrowState(PlayerStateBase):
    """Throw a grabbed enemy forward for big damage + knockback."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SHORT_ATTACK)
        self._timer: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = float(player.facing_direction) * 50.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt

        if self._timer < 0.08 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 36, 20
            hx = cx + (14 * player.facing_direction) - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        if player._hitbox_consumed:
            player._active_hitbox = None

        if self._timer >= 0.2:
            player._active_hitbox = None
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


def _handle_grab_input(player: Player, inp: _InputSnapshot) -> bool:
    """Grab: CROUCH + LONG_ATTACK or dedicated GRAB button."""
    if inp.grab_pressed or (inp.long_attack and inp.crouch_held and not inp.short_attack):
        from src.framework.entities.player_states import GrabState
        player._change_state_instance(GrabState())
        return True
    return False


def _handle_ultimate_input(player: Player, inp: _InputSnapshot) -> bool:
    """Trigger ultimate when both attacks pressed simultaneously with full meter."""
    if inp.short_attack and inp.long_attack and player.special_meter >= player.special_meter_max:
        from src.framework.entities.player_states import UltimateState
        player._change_state_instance(UltimateState())
        return True
    return False


# ── Parry state ──────────────────────────────────────────────────

_PARRY_DURATION = 0.2


class ParryState(PlayerStateBase):
    """Parry state — brief window where incoming attacks are deflected."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.PARRY)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._parry_window = _PARRY_DURATION
        player._parry_active = True
        player._parry_success = False
        player.velocity.x = 0.0
        player.velocity.y = 0.0
        from src.engine.core.events import Events
        from src.engine.core.event_bus import emit
        emit(Events.VFX_PARRY, pos=(player.position.x, player.position.y))

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        player._parry_window -= dt
        if player._parry_window <= 0:
            player._parry_active = False
            player._parry_window = 0.0
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._parry_active = False
        player._parry_window = 0.0


# ── Charging state ──────────────────────────────────────────────

_CHARGE_MAX_TIME = 1.0
_CHARGE_LEVELS = [(0.5, 1.0), (1.0, 1.5), (1.5, 2.0)]  # (min_time, dmg_mult)


class ChargingState(PlayerStateBase):
    """Hold attack to charge — release for powered-up strike."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.CHARGE_ATTACK)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._charging = True
        player._charge_timer = 0.0
        player._charge_level = 0
        player.velocity.x = 0.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        player._charge_timer += dt
        if player._charge_timer >= _CHARGE_MAX_TIME:
            player._charge_level = 2
        elif player._charge_timer >= _CHARGE_LEVELS[0][0]:
            player._charge_level = 1

        # Emit charge glow particles periodically
        from src.engine.core.events import Events
        from src.engine.core.event_bus import emit
        emit(Events.VFX_CHARGE, pos=(player.position.x, player.position.y), level=player._charge_level)

        # Check for release (long attack released)
        inp = _InputSnapshot(input_manager)
        if not inp.long_attack and player._charge_timer > 0.1:
            self._release_charge(player)
            return

        # Can still parry during charge
        if inp.short_attack and inp.crouch_held:
            from src.framework.entities.player_states import ParryState
            player._change_state_instance(ParryState())
            return

    def _release_charge(self, player: Player) -> None:
        level = min(player._charge_level, len(_CHARGE_LEVELS) - 1)
        dmg_mult = _CHARGE_LEVELS[level][1]
        player._charge_level = 0
        player._charging = False
        from src.framework.entities.player_states import ChargeReleaseState
        player._change_state_instance(ChargeReleaseState(dmg_mult))

    def exit(self, player: Player) -> None:
        player._charging = False


class ChargeReleaseState(PlayerStateBase):
    """The actual charged attack animation — hits hard with big hitbox."""

    def __init__(self, damage_mult: float = 1.0) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SHORT_ATTACK)
        self._dmg_mult = damage_mult
        self._timer: float = 0.0
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = float(player.facing_direction) * settings.PLAYER_WALK_SPEED * 1.5

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        inp = _InputSnapshot(input_manager)

        # Active hitbox for the first 0.15s
        if self._timer < 0.15 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 48, 40
            hx = cx + (16 * player.facing_direction) - (w // 2)
            hy = cy - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        player._damage_mult = self._dmg_mult

        # Cancel opportunities in recovery
        if self._timer >= 0.15:
            if inp.dash_pressed and _can_dash(player, inp):
                from src.framework.entities.player_states import DashingState
                player._change_state_instance(DashingState())
                return
            if _handle_grounded_jump_input(player, inp):
                return

        if self._timer >= 0.3:
            player._damage_mult = 1.0
            player._active_hitbox = None
            player._cooldown_timer = 0.15
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None
        player._damage_mult = 1.0


# ── Aerial attack state ─────────────────────────────────────────


class AerialAttackState(PlayerStateBase):
    """Attack performed while airborne — downward strike with knockback."""

    def __init__(self, short: bool = True) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SHORT_ATTACK if short else PlayerState.LONG_ATTACK)
        self._short = short
        self._timer: float = 0.0
        self._frames: int = 6 if short else 10
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        if player.velocity.y < 50:
            player.velocity.y = 80.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt
        frame_duration = 1.0 / 18.0
        current_frame = int(self._timer / frame_duration) + 1

        active = [2, 3, 4] if self._short else [4, 5, 6, 7]
        if current_frame in active and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = (36, 24) if self._short else (40, 28)
            offset_x = 6 if self._short else 10
            hx = cx + (offset_x * player.facing_direction) - (w // 2)
            hy = cy + 4 - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        if player._hitbox_consumed and not self._has_hit:
            self._has_hit = True
            if not player.is_grounded:
                player._combo_air_hits += 1
                if player._combo_air_hits >= 2:
                    from src.framework.entities.player_states import AerialSlamState
                    player._change_state_instance(AerialSlamState())
                    return

        if player.is_grounded and self._timer > 0.05:
            player._active_hitbox = None
            if self._timer > 0.2:
                from src.framework.entities.player_states import IdleState
                player._change_state_instance(IdleState())

        if current_frame >= self._frames:
            player._active_hitbox = None
            from src.framework.entities.player_states import IdleState, FallingState
            target = IdleState if player.is_grounded else FallingState
            player._change_state_instance(target())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


# ── Air chase state (follow-up after launch) ────────────────────


class AirChaseState(PlayerStateBase):
    """Player chases a launched enemy in the air for continued combo."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.JUMPING)

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.x = float(player.facing_direction) * 120.0
        player.velocity.y = -200.0
        player._combo_air_hits = getattr(player, "_combo_air_hits", 0) + 1

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)

        # Follow-up attack in air
        if inp.short_attack or inp.long_attack:
            from src.framework.entities.player_states import AerialSlamState, AerialAttackState
            target = AerialSlamState if player._combo_air_hits >= 2 else AerialAttackState
            player._change_state_instance(target())
            return

        # Landed
        if player.is_grounded:
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())
            return

        # Air control
        if inp.move_x != 0:
            player.facing_direction = inp.move_x
            player.velocity.x = float(inp.move_x) * 100.0

        if player.velocity.y >= 0:
            from src.framework.entities.player_states import FallingState
            player._change_state_instance(FallingState())


class AerialSlamState(PlayerStateBase):
    """Slam attack — drives enemy downward with force."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SHORT_ATTACK)
        self._timer: float = 0.0
        self._has_hit: bool = False

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = 0.0
        player.velocity.y = 300.0  # Fast downward

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt

        if self._timer < 0.12 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 44, 32
            hx = cx + (8 * player.facing_direction) - (w // 2)
            hy = cy + 6 - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        player.velocity.y = 300.0

        # Grounded → slam complete
        if player.is_grounded:
            player._active_hitbox = None
            player._combo_air_hits = 0
            from src.engine.core.events import Events
            from src.engine.core.event_bus import emit
            emit(Events.VFX_SLAM, pos=(player.position.x, player.position.y))
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())
            return

        if self._timer >= 0.3:
            player._active_hitbox = None
            from src.framework.entities.player_states import FallingState
            player._change_state_instance(FallingState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


# ── Dash attack state ────────────────────────────────────────────


class DashAttackState(PlayerStateBase):
    """Attack performed during dash — sliding strike with forward momentum."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.DASH_ATTACK)
        self._timer: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player._attack_timer = 0.0
        player._active_hitbox = None
        player._hitbox_consumed = False
        player.velocity.x = float(player.facing_direction) * settings.PLAYER_DASH_SPEED * 0.7
        player.velocity.y = 0.0
        player._invincibility_timer = max(player._invincibility_timer, 0.1)

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        self._timer += dt

        # Active hitbox during first half
        if self._timer < 0.1 and not player._hitbox_consumed:
            cx = player.rect.centerx
            cy = player.rect.centery
            w, h = 40, 20
            hx = cx + (10 * player.facing_direction) - (w // 2)
            hy = cy - 4 - (h // 2)
            player._active_hitbox = pygame.Rect(hx, hy, w, h)
        else:
            player._active_hitbox = None

        player.velocity.x *= 0.92  # Deceleration

        if self._timer >= 0.25:
            player._active_hitbox = None
            player._dash_cooldown = 0.1
            if player.is_grounded:
                from src.framework.entities.player_states import IdleState
                player._change_state_instance(IdleState())
            else:
                from src.framework.entities.player_states import FallingState
                player._change_state_instance(FallingState())

    def exit(self, player: Player) -> None:
        player._active_hitbox = None


# ── Wall slide state ────────────────────────────────────────────


class WallSlideState(PlayerStateBase):
    """Player sliding down a wall — enables wall jump."""

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

        # Wall jump
        if _handle_wall_jump(player, inp):
            return

        # Ledge grab — detect ledge above and transition
        if player._can_ledge_grab:
            from src.framework.entities.player_states import LedgeGrabState
            player._change_state_instance(LedgeGrabState())
            return

        # Attack while wall sliding
        if inp.short_attack:
            from src.framework.entities.player_states import AerialAttackState
            player._change_state_instance(AerialAttackState(short=True))
            return

        # Drop off wall when moving away
        if inp.move_x == -player._wall_side:
            player._wall_side = 0
            player._can_wall_jump = False
            from src.framework.entities.player_states import FallingState
            player._change_state_instance(FallingState())
            return

        # Fell off wall
        if player._wall_side == 0 or player.is_grounded:
            from src.framework.entities.player_states import IdleState, FallingState
            target = IdleState if player.is_grounded else FallingState
            player._change_state_instance(target())


# ── Ledge grab state ────────────────────────────────────────────


class LedgeGrabState(PlayerStateBase):
    """Ledge grab hang — player hangs from a wall edge.
    Press UP to climb, DOWN to drop, or wait to drop off.
    """

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.LEDGE_GRAB)
        self._timer: float = 0.0

    def enter(self, player: Player) -> None:
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

        # Climb up → pop to top of wall
        if inp.jump_pressed:
            from src.framework.entities.player_states import JumpingState
            player.velocity.y = -250.0
            player.velocity.x = float(player._wall_side) * 50.0
            player._wall_side = 0
            player._can_wall_jump = False
            player._change_state_instance(JumpingState())
            return

        # Drop down
        if inp.crouch_held or self._timer > 1.5:
            player._wall_side = 0
            player._can_wall_jump = False
            from src.framework.entities.player_states import FallingState
            player._change_state_instance(FallingState())
            return

        # Fall off wall
        if player.is_grounded or player._wall_side == 0:
            from src.framework.entities.player_states import IdleState, FallingState
            target = IdleState if player.is_grounded else FallingState
            player._change_state_instance(target())

        # Hold position
        player.velocity.x = 0.0
        player.velocity.y = 0.0

    def exit(self, player: Player) -> None:
        pass


# ── Combo and hitbox helpers ─────────────────────────────────────


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
    """Player taking knockback. Wake-up options: tech roll (dash) or get-up attack."""

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

        # Tech roll — cancel knockback into a forward roll
        if inp.dash_pressed and player._knockback_timer > 0:
            from src.framework.entities.player_states import DashingState
            player.velocity.x = float(player.facing_direction) * settings.PLAYER_DASH_SPEED
            player.velocity.y = 0.0
            player._knockback_timer = 0.0
            player._dash_cooldown = 0.3
            player._invincibility_timer = max(player._invincibility_timer, 0.3)
            player._change_state_instance(DashingState())
            return

        # Get-up attack — quick strike while recovering
        if inp.short_attack and player._knockback_timer > 0:
            player.velocity.x = 0.0
            player.velocity.y = 0.0
            player._knockback_timer = 0.0
            _start_attack(player, player.SHORT_ATTACK)
            return

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


class SwimmingState(PlayerStateBase):
    """Player swimming in water. Buoyancy, reduced gravity, bubbles."""

    def __init__(self) -> None:
        from src.framework.entities.player import PlayerState
        super().__init__(PlayerState.SWIMMING)
        self._swim_timer: float = 0.0
        self._bubble_timer: float = 0.0
        self._surface_y: float = 0.0

    def enter(self, player: Player) -> None:
        super().enter(player)
        player.velocity.y = 0.0
        player.velocity.x *= 0.5
        self._swim_timer = 0.0
        self._bubble_timer = 0.0
        self._surface_y = player.position.y - 16.0

    def update(
        self,
        player: Player,
        dt: float,
        input_manager: InputManager | None,
    ) -> None:
        inp = _InputSnapshot(input_manager)
        self._swim_timer += dt
        self._bubble_timer += dt

        # Buoyancy: float up slowly
        player.velocity.y += settings.GRAVITY * 0.3 * dt
        player.velocity.y = max(-80.0, min(80.0, player.velocity.y))

        # Horizontal movement (slower in water)
        if inp.move_x != 0:
            player.velocity.x += inp.move_x * 60.0 * dt
            player.velocity.x = max(-120.0, min(120.0, player.velocity.x))
            player.facing_direction = inp.move_x
        else:
            player.velocity.x *= 0.9

        # Swim upward (jump in water)
        if inp.jump_pressed and player._air_jumps_used < 1:
            player.velocity.y = -120.0
            player._air_jumps_used += 1
            emit(Events.SFX_PLAYER_JUMP)

        # Swim downward
        if inp.crouch_held:
            player.velocity.y += 200.0 * dt

        # Emit bubbles periodically
        if self._bubble_timer >= 0.3:
            self._bubble_timer = 0.0
            emit(Events.VFX_CHARGE, pos=(player.position.x, player.position.y))

        # Transition: leave water (jump above surface)
        if player.position.y < self._surface_y - 8.0:
            player.velocity.y = -200.0
            from src.framework.entities.player_states import JumpingState
            player._change_state_instance(JumpingState())
            return

        # Transition: land on ground
        if player.is_grounded:
            from src.framework.entities.player_states import IdleState
            player._change_state_instance(IdleState())
            return
