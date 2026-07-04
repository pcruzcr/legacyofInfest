"""
Module: player
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit IV (Sprite Animation)
Description: Player entity with full state machine (9 states), physics
(gravity, coyote time, jump cut), damage system (invincibility, knockback),
attack hitboxes (short/long), and hurtbox (standard/crouching).

STATE PATTERN (Fase 2): Per-frame behavior is delegated to a
PlayerStateBase instance (see player_states.py). The Player class
owns shared infrastructure (physics, collision, animation, sprites)
while each state encapsulates its own update logic and transitions.
"""
from __future__ import annotations

from enum import Enum

import pygame

from typing import TYPE_CHECKING
from src.engine.core import settings
from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.engine.input.input_manager import InputManager
    from src.framework.entities.player_states import PlayerStateBase


SPRITE_W = 32
SPRITE_H = 32

# State -> (filename, frame_count)
_PLAYER_SPRITE_MAP: dict[str, tuple[str, int]] = {
    "IDLE": ("player_idle.png", 4),
    "WALKING": ("player_walk.png", 8),
    "JUMPING": ("player_jump.png", 3),
    "FALLING": ("player_fall.png", 2),
    "CROUCHING": ("player_crouch.png", 2),
    "SHORT_ATTACK": ("player_short_attack.png", 6),
    "LONG_ATTACK": ("player_long_attack.png", 10),
    "HURT": ("player_hurt.png", 4),
    "DYING": ("player_die.png", 8),
    "DASHING": ("player_walk.png", 4),
}

# Per-state animation playback rate (frames per second)
_PLAYER_ANIM_FPS: dict[str, float] = {
    "IDLE": 8.0,
    "WALKING": 12.0,
    "JUMPING": 12.0,
    "FALLING": 8.0,
    "CROUCHING": 8.0,
    "SHORT_ATTACK": 18.0,
    "LONG_ATTACK": 16.0,
    "HURT": 12.0,
    "DYING": 10.0,
    "DASHING": 12.0,
}


class PlayerState(str, Enum):
    """All possible player states as defined in 04_PLAYER_SPEC.md §8.1."""
    IDLE = "IDLE"
    WALKING = "WALKING"
    JUMPING = "JUMPING"
    FALLING = "FALLING"
    CROUCHING = "CROUCHING"
    SHORT_ATTACK = "SHORT_ATTACK"
    LONG_ATTACK = "LONG_ATTACK"
    HURT = "HURT"
    DYING = "DYING"
    DASHING = "DASHING"


class Player(BaseEntity):
    """
    Player entity with physics, state machine, damage, combat, and sprite rendering.
    Inherits from BaseEntity.

    STATE PATTERN: self._state_instance holds the current PlayerStateBase
    subclass. Every frame, update() calls _state_instance.update() which
    handles state-specific logic and transitions. Shared infrastructure
    (physics, collision, animation frame advancement) remains in Player.
    """

    SHORT_ATTACK = PlayerState.SHORT_ATTACK
    LONG_ATTACK = PlayerState.LONG_ATTACK

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        """Initialize the player at the given spawn position."""
        super().__init__(spawn_position)

        # --- Physics state ---
        self.velocity: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self.is_grounded: bool = False
        self._coyote_counter: int = 0
        self._jump_cut_applied: bool = False

        # --- State pattern ---
        self._state_instance: PlayerStateBase
        self._prev_state_instance: PlayerStateBase | None = None
        self._init_state()

        # --- Attack state ---
        self._attack_timer: float = 0.0
        self._attack_active_frames: list[int] = []
        self._attack_current_frame: int = 0
        self._active_hitbox: pygame.Rect | None = None
        self._hitbox_consumed: bool = False
        self._cooldown_timer: float = 0.0

        # --- Dash state ---
        self._air_dash_count: int = 0
        self._dash_timer: float = 0.0
        self._dash_cooldown: float = 0.0

        # --- Damage state ---
        self._health: float = settings.PLAYER_MAX_HEALTH
        self._invincibility_timer: float = 0.0
        self._knockback_timer: float = 0.0
        self._flash_timer: float = 0.0
        self._flash_visible: bool = True

        # --- Direction ---
        self.facing_direction: int = 1  # -1 left, 1 right

        # --- Rect setup ---
        self.rect = pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            20,
            32,
        )

        # --- Sprite frames ---
        self._sprite_frames: dict[str, list[pygame.Surface]] = {}
        self._load_sprites()

        # --- Animation state ---
        self._animation_timer: float = 0.0
        self._animation_frame: int = 0

    def _init_state(self) -> None:
        """Create the initial idle state instance."""
        from src.framework.entities.player_states import IdleState
        self._state_instance = IdleState()
        self._state_instance.enter(self)

    def _load_sprites(self) -> None:
        """Load all player sprite sheets into frame lists."""
        sprite_dir = settings.ASSETS_DIR / "sprites" / "player"
        for state_name, (filename, _) in _PLAYER_SPRITE_MAP.items():
            path = sprite_dir / filename
            frames = AssetLoader.load_sprite_sheet(path, SPRITE_W, SPRITE_H)
            self._sprite_frames[state_name] = frames

    # ── Properties ──────────────────────────────────────────────

    @property
    def current_health(self) -> float:
        """Read-only health value."""
        return self._health

    @property
    def hurtbox(self) -> pygame.Rect:
        """
        Damage-receiving hitbox. Smaller than the collision rect so that
        enemy sprites can overlap visually without dealing contact damage.
          Standing:  20×28, offsetY=4  (top = rect.y + 4, bottom = rect.y + 32)
          Crouching: 20×18, offsetY=14 (top = rect.y + 14, bottom = rect.y + 32)
        """
        if self._state_instance.state_enum == PlayerState.CROUCHING:
            off_y = 14
            h = 18
        else:
            off_y = 4
            h = 28
        return pygame.Rect(self.rect.x, self.rect.y + off_y, self.rect.width, h)

    @property
    def state(self) -> PlayerState:
        """Read-only current state enum value."""
        return PlayerState(self._state_instance.state_enum.value)

    @property
    def active_hitbox(self) -> pygame.Rect | None:
        """
        Returns the current active hitbox if in an attack frame
        that deals damage, otherwise None.
        """
        if self._hitbox_consumed:
            return None
        return self._active_hitbox

    @property
    def current_attack_damage(self) -> float:
        """
        Damage value for the current attack state.
        0.50 during SHORT_ATTACK active frames,
        1.00 during LONG_ATTACK active frames,
        0.0 otherwise.
        """
        if (self._state_instance.state_enum == PlayerState.SHORT_ATTACK
                and self._active_hitbox is not None):
            return 0.5
        if (self._state_instance.state_enum == PlayerState.LONG_ATTACK
                and self._active_hitbox is not None):
            return 1.0
        return 0.0

    # ── Public methods ──────────────────────────────────────────

    def set_spawn(self, position: pygame.Vector2) -> None:
        """The ONLY sanctioned way to reposition the player."""
        self.position = pygame.Vector2(position)
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
        self.velocity = pygame.Vector2(0.0, 0.0)

    def heal(self, amount: float) -> None:
        self._health = min(settings.PLAYER_MAX_HEALTH, self._health + amount)

    def consume_hitbox(self) -> None:
        """
        Called by the stage collision system after an attack hitbox connects,
        to prevent multi-hit on the same frame.
        """
        self._hitbox_consumed = True
        self._active_hitbox = None

    def apply_damage(
        self,
        amount: float,
        source_position: tuple[float, float],
        knockback_force: float = 150.0,
    ) -> None:
        """
        Apply damage to the player. No-op if invincibility is active.
        Emits PLAYER_DAMAGED and potentially PLAYER_DIED.
        """
        if self._invincibility_timer > 0:
            return
        if self._state_instance.state_enum == PlayerState.DYING:
            return

        self._health = max(0.0, self._health - amount)
        self._invincibility_timer = settings.PLAYER_INVINCIBILITY_DURATION
        self._flash_timer = 0.0

        # Knockback away from source
        dx = self.position.x - source_position[0]
        self.velocity.x = knockback_force * (1 if dx >= 0 else -1)
        self.velocity.y = -200.0
        self._knockback_timer = 0.3

        emit(
            Events.PLAYER_DAMAGED,
            amount=amount,
            source=source_position,
        )

        if self._health <= 0.0:
            from src.framework.entities.player_states import DyingState
            self._change_state_instance(DyingState())
            emit(Events.PLAYER_DIED)
            emit(Events.SFX_PLAYER_DIE)
        else:
            from src.framework.entities.player_states import HurtState
            self._change_state_instance(HurtState())
            emit(Events.SFX_PLAYER_HURT)

    def _change_state_instance(self, new_state: PlayerStateBase) -> None:
        """
        Transition to a new state instance.
        Calls exit() on the current state, then enter() on the new state.
        """
        if self._state_instance.state_enum == new_state.state_enum:
            return
        self._prev_state_instance = self._state_instance
        self._state_instance.exit(self)
        self._state_instance = new_state
        self._state_instance.enter(self)

    # ──────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────

    def update(
        self,
        dt: float,
        collision_rects: list[pygame.Rect] | None = None,
        input_manager: InputManager | None = None,
        one_way_rects: list[pygame.Rect] | None = None,
    ) -> None:
        """
        Main update loop. Called every frame.
        If collision_rects is provided, performs AABB collision resolution.
        input_manager is injected by the stage — never accessed via App singleton.
        one_way_rects are platforms passable from below.
        """
        if collision_rects is None:
            collision_rects = []
        if one_way_rects is None:
            one_way_rects = []

        # Tick timers (includes animation_timer)
        self._tick_timers(dt)

        # State machine — delegate to current state
        self._state_instance.update(self, dt, input_manager)

        # Advance animation frame (attack states handle their own animation)
        if self._state_instance.state_enum not in (
            PlayerState.SHORT_ATTACK,
            PlayerState.LONG_ATTACK,
        ):
            self._advance_animation(dt)

        # Physics (gravity + movement)
        self._apply_physics(dt)

        # Collision resolution (axis-separated) — solid first
        self._resolve_collision(dt, collision_rects)

        # One-way platforms (only resolve Y when falling)
        self._resolve_one_way_collision(dt, one_way_rects)

        # Update rect position
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

        # Update hurtbox size based on state
        self._update_rect_size()

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """
        Draw the player sprite to the surface.
        camera_offset is subtracted from world position.
        """
        if not self.is_visible:
            return

        # Invincibility flash: skip draw every 6 frames when flashing
        if self._invincibility_timer > 0:
            self._flash_timer += 1.0 / 60.0
            if self._flash_timer >= 6.0 / 60.0:
                self._flash_timer = 0.0
                self._flash_visible = not self._flash_visible
            if not self._flash_visible:
                return

        frames = self._sprite_frames.get(self._state_instance.state_enum.value)
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            frame = frames[frame_idx]

            if self.facing_direction < 0:
                frame = pygame.transform.flip(frame, True, False)

            # Center the 32-wide sprite on the 20-wide collision rect
            offset_x = (self.rect.width - SPRITE_W) // 2
            offset_y = self.rect.height - SPRITE_H

            surface.blit(frame, (screen_x + offset_x, screen_y + offset_y))
            return

        # Fallback: colored rectangle when sprites are unavailable
        w = 20
        h = 20 if self._state_instance.state_enum == PlayerState.CROUCHING else 32
        color = (0, 120, 255)
        if self._state_instance.state_enum == PlayerState.HURT:
            color = (255, 100, 100)
        elif self._state_instance.state_enum == PlayerState.DYING:
            color = (100, 100, 100)
        pygame.draw.rect(surface, color, (screen_x, screen_y, w, h))
        pygame.draw.rect(surface, (255, 255, 255), (screen_x, screen_y, w, h), 1)

    # ──────────────────────────────────────────────
    # Timer ticking
    # ──────────────────────────────────────────────

    def _tick_timers(self, dt: float) -> None:
        """Tick all cooldown and duration timers."""
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt
        if self._knockback_timer > 0:
            self._knockback_timer -= dt
        if self._cooldown_timer > 0:
            self._cooldown_timer -= dt
        if self._dash_cooldown > 0:
            self._dash_cooldown -= dt
        self._animation_timer += dt

    def _advance_animation(self, dt: float) -> None:
        """Advance the sprite animation frame based on per-state FPS."""
        fps = _PLAYER_ANIM_FPS.get(self._state_instance.state_enum.value, 10.0)
        frame_duration = 1.0 / fps
        total_frames = _PLAYER_SPRITE_MAP.get(
            self._state_instance.state_enum.value, (None, 1),
        )[1]
        if self._animation_timer >= frame_duration:
            self._animation_timer -= frame_duration
            self._animation_frame = (self._animation_frame + 1) % total_frames

    # ──────────────────────────────────────────────
    # State machine (delegated to player_states.py)
    # ──────────────────────────────────────────────

    # All state-specific logic moved to PlayerStateBase subclasses
    # in player_states.py. The Player class handles shared infrastructure.

    def _do_jump(self) -> None:
        """Execute a jump (forwarder to module-level helper)."""
        from src.framework.entities.player_states import _do_jump as _do_jump_fn
        _do_jump_fn(self)

    def _can_jump(self) -> bool:
        """Check if the player can jump (forwarder to module-level helper)."""
        from src.framework.entities.player_states import _can_jump as _can_jump_fn
        return _can_jump_fn(self)

    # ──────────────────────────────────────────────
    # Physics
    # ──────────────────────────────────────────────

    def _apply_physics(self, dt: float) -> None:
        """Apply gravity and movement velocity."""
        # Gravity (only if not grounded and not in knockback)
        if not self.is_grounded and self._knockback_timer <= 0:
            self.velocity.y += settings.GRAVITY * dt
            self.velocity.y = min(
                self.velocity.y,
                settings.PLAYER_MAX_FALL_SPEED,
            )

        # Apply velocity to position
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt

        # Coyote time
        if self.is_grounded:
            self._coyote_counter = 0
        else:
            self._coyote_counter += 1

    # ──────────────────────────────────────────────
    # Collision resolution (AABB, axis-separated)
    # ──────────────────────────────────────────────

    def _resolve_collision(self, dt: float, collision_rects: list[pygame.Rect]) -> None:
        """
        Axis-separated AABB collision resolution.
        1. Resolve Y axis (vertical landing/push-out first)
        2. Resolve X axis (horizontal push-out second)
        3. Update grounded state

        Y-before-X order prevents floor tiles from being treated as
        walls when the player rect overlaps them vertically.
        """
        if not collision_rects:
            return

        # Build player rect at new position
        player_rect = pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            self.rect.width,
            self.rect.height,
        )

        # --- Y axis ---
        # Use an inflated rect so touching edges (bottom == floor top)
        # are detected as collisions.
        collision_check_rect = player_rect.inflate(0, 2)
        was_grounded = self.is_grounded
        self.is_grounded = False
        collided_y = False
        for tile in collision_rects:
            if collision_check_rect.colliderect(tile):
                collided_y = True
                if self.velocity.y >= 0:
                    # Falling or stationary: land on top
                    if not was_grounded and self.velocity.y > 0:
                        emit(Events.SFX_PLAYER_LAND)
                    player_rect.bottom = tile.top
                    self.velocity.y = 0.0
                    self.is_grounded = True
                    self._air_dash_count = 0
                elif self.velocity.y < 0:
                    # Moving up: push down
                    player_rect.top = tile.bottom
                    self.velocity.y = 0.0

        if collided_y:
            self.position.y = float(player_rect.y)
            player_rect.y = int(self.position.y)

        # --- X axis ---
        collided_x = False
        for tile in collision_rects:
            if player_rect.colliderect(tile):
                # Skip floor tiles: after Y resolution, the player's feet
                # sit on the floor, so these are clearly floors, not walls.
                if tile.top >= player_rect.centery:
                    continue
                collided_x = True
                # Push in the direction of smallest overlap
                overlap_left = player_rect.right - tile.left
                overlap_right = tile.right - player_rect.left
                if overlap_left < overlap_right:
                    player_rect.right = tile.left
                else:
                    player_rect.left = tile.right
                self.velocity.x = 0.0

        if collided_x:
            self.position.x = float(player_rect.x)

    def _resolve_one_way_collision(self, dt: float, one_way_rects: list[pygame.Rect]) -> None:
        """Resolve Y-axis collision for one-way platforms (passable from below).
        Only resolves when the player is falling (velocity.y >= 0)."""
        if not one_way_rects:
            return
        if self.velocity.y < 0:
            return  # Jumping up through — no collision

        player_rect = pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            self.rect.width,
            self.rect.height,
        )
        prev_bottom = player_rect.bottom - self.velocity.y * dt
        collision_check_rect = player_rect.inflate(0, 2)
        for plat in one_way_rects:
            if collision_check_rect.colliderect(plat) and prev_bottom <= plat.top:
                player_rect.bottom = plat.top
                self.velocity.y = 0.0
                self.is_grounded = True
                self._air_dash_count = 0
                self.position.y = float(player_rect.y)
                break

    # ──────────────────────────────────────────────
    # Rect / Hurtbox sizing
    # ──────────────────────────────────────────────

    def _update_rect_size(self) -> None:
        """Update rect size based on current state (crouching vs standing).
        Shifts position.y so the rect bottom (feet) stays at the same height."""
        old_bottom = self.position.y + self.rect.height
        if self._state_instance.state_enum == PlayerState.CROUCHING:
            self.rect.width = 20
            self.rect.height = 20
        else:
            self.rect.width = 20
            self.rect.height = 32
        self.position.y += old_bottom - (self.position.y + self.rect.height)
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
