"""
Module: player
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit IV (Sprite Animation)
Description: Player entity with full state machine (9 states), physics
(gravity, coyote time, jump cut), damage system (invincibility, knockback),
attack hitboxes (short/long), and hurtbox (standard/crouching).
"""
from __future__ import annotations

from enum import Enum

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import EventBus
from src.framework.entities.base_entity import BaseEntity


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


class Player(BaseEntity):
    """
    Player entity with physics, state machine, damage, and combat systems.
    Inherits from BaseEntity.
    """

    def __init__(self, spawn_position: pygame.Vector2) -> None:
        """Initialize the player at the given spawn position."""
        super().__init__(spawn_position)

        # --- Physics state ---
        self.velocity: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self.is_grounded: bool = False
        self._coyote_counter: int = 0
        self._jump_cut_applied: bool = False

        # --- State machine ---
        self._state: PlayerState = PlayerState.IDLE
        self._animation_timer: float = 0.0
        self._animation_frame: int = 0

        # --- Attack state ---
        self._attack_timer: float = 0.0
        self._attack_active_frames: list[int] = []
        self._attack_current_frame: int = 0
        self._active_hitbox: pygame.Rect | None = None
        self._hitbox_consumed: bool = False
        self._cooldown_timer: float = 0.0

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

    # ──────────────────────────────────────────────
    # Properties (read-only public API)
    # ──────────────────────────────────────────────

    @property
    def current_health(self) -> float:
        """Read-only health value."""
        return self._health

    @property
    def state(self) -> PlayerState:
        """Read-only current state."""
        return self._state

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
        if (self._state == PlayerState.SHORT_ATTACK
                and self._active_hitbox is not None):
            return 0.5
        if (self._state == PlayerState.LONG_ATTACK
                and self._active_hitbox is not None):
            return 1.0
        return 0.0

    # ──────────────────────────────────────────────
    # Public methods
    # ──────────────────────────────────────────────

    def set_spawn(self, position: pygame.Vector2) -> None:
        """The ONLY sanctioned way to reposition the player."""
        self.position = pygame.Vector2(position)
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)
        self.velocity = pygame.Vector2(0.0, 0.0)

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
    ) -> None:
        """
        Apply damage to the player. No-op if invincibility is active.
        Emits PLAYER_DAMAGED and potentially PLAYER_DIED.
        """
        if self._invincibility_timer > 0:
            return
        if self._state == PlayerState.DYING:
            return

        self._health = max(0.0, self._health - amount)
        self._invincibility_timer = settings.PLAYER_INVINCIBILITY_DURATION
        self._flash_timer = 0.0

        # Knockback away from source
        dx = self.position.x - source_position[0]
        self.velocity.x = 150.0 * (1 if dx >= 0 else -1)
        self.velocity.y = -200.0
        self._knockback_timer = 0.3

        EventBus.emit(
            "PLAYER_DAMAGED",
            amount=amount,
            source=source_position,
        )

        if self._health <= 0.0:
            self._state = PlayerState.DYING
            self._animation_timer = 0.0
            self._animation_frame = 0
            EventBus.emit("PLAYER_DIED")
        else:
            self._state = PlayerState.HURT
            self._animation_timer = 0.0
            self._animation_frame = 0

    # ──────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────

    def update(
        self,
        dt: float,
        collision_rects: list[pygame.Rect] | None = None,
    ) -> None:
        """
        Main update loop. Called every frame.
        If collision_rects is provided, performs AABB collision resolution.
        """
        if collision_rects is None:
            collision_rects = []

        # Tick timers
        self._tick_timers(dt)

        # State machine
        self._run_state_machine(dt)

        # Physics (gravity + movement)
        self._apply_physics(dt)

        # Collision resolution (axis-separated)
        self._resolve_collision(dt, collision_rects)

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
        Draw the player placeholder (blue rectangle) to the surface.
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

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        # Determine size based on state
        if self._state == PlayerState.CROUCHING:
            w, h = 20, 20
        else:
            w, h = 20, 32

        # Blue placeholder rect
        pygame.draw.rect(
            surface,
            (0, 120, 255),
            (screen_x, screen_y, w, h),
        )
        # White border
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, w, h),
            1,
        )

        # Direction indicator (yellow line)
        cx = screen_x + w // 2
        tip_x = cx + (8 * self.facing_direction)
        pygame.draw.line(
            surface,
            (255, 255, 0),
            (cx, screen_y + 8),
            (tip_x, screen_y + 8),
            2,
        )

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

    # ──────────────────────────────────────────────
    # State machine
    # ──────────────────────────────────────────────

    def _run_state_machine(self, dt: float) -> None:
        """
        Evaluate current state and handle transitions.
        Input is read from InputManager via action checks.
        Falls back to no-input state (IDLE) if InputManager is unavailable.
        """
        # DYING is terminal
        if self._state == PlayerState.DYING:
            return

        # HURT: wait for knockback timer
        if self._state == PlayerState.HURT:
            if self._knockback_timer <= 0:
                self._change_state(PlayerState.IDLE)
            return

        # Attack states: animation-driven, input locked
        if self._state in (PlayerState.SHORT_ATTACK, PlayerState.LONG_ATTACK):
            self._update_attack_state(dt)
            return

        # Read input from InputManager (graceful fallback if unavailable)
        move_x = 0
        jump_pressed = False
        jump_held = False
        crouch_held = False
        short_attack = False
        long_attack = False

        try:
            from src.engine.input.input_manager import InputManager
            im = InputManager()
            if im.is_held("MOVE_LEFT"):
                move_x -= 1
            if im.is_held("MOVE_RIGHT"):
                move_x += 1
            jump_pressed = im.is_pressed("JUMP")
            jump_held = im.is_held("JUMP")
            crouch_held = im.is_held("CROUCH")
            short_attack = im.is_pressed("SHORT_ATTACK")
            long_attack = im.is_pressed("LONG_ATTACK")
        except Exception:
            pass

        # Attack input has priority
        if short_attack:
            self._start_attack(PlayerState.SHORT_ATTACK)
            return
        if long_attack:
            self._start_attack(PlayerState.LONG_ATTACK)
            return

        # Crouch
        if crouch_held and self.is_grounded:
            self._change_state(PlayerState.CROUCHING)
            self.velocity.x = 0.0
            return

        # Jump
        if jump_pressed and self._can_jump():
            self._do_jump()
            return

        # Horizontal movement
        if move_x != 0 and self.is_grounded:
            self.facing_direction = move_x
            self._change_state(PlayerState.WALKING)
            self.velocity.x = float(move_x) * settings.PLAYER_WALK_SPEED
        elif move_x == 0 and self.is_grounded:
            self._change_state(PlayerState.IDLE)
            self.velocity.x = 0.0

        # Airborne state tracking
        if not self.is_grounded:
            if self.velocity.y < 0:
                self._change_state(PlayerState.JUMPING)
            else:
                self._change_state(PlayerState.FALLING)

        # Jump cut
        if not jump_held and self.velocity.y < 0 and not self._jump_cut_applied:
            self.velocity.y *= 0.5
            self._jump_cut_applied = True

    def _can_jump(self) -> bool:
        """Check if the player can jump (grounded or within coyote time)."""
        return self.is_grounded or self._coyote_counter < settings.PLAYER_COYOTE_FRAMES

    def _do_jump(self) -> None:
        """Execute a jump."""
        self.velocity.y = settings.PLAYER_JUMP_FORCE
        self.is_grounded = False
        self._coyote_counter = settings.PLAYER_COYOTE_FRAMES + 1  # exhaust coyote
        self._jump_cut_applied = False
        self._change_state(PlayerState.JUMPING)

    def _change_state(self, new_state: PlayerState) -> None:
        """Change state and reset animation state."""
        if self._state == new_state:
            return
        self._state = new_state
        self._animation_timer = 0.0
        self._animation_frame = 0

    # ──────────────────────────────────────────────
    # Attack system
    # ──────────────────────────────────────────────

    def _start_attack(self, attack_type: PlayerState) -> None:
        """Begin an attack animation."""
        self._change_state(attack_type)
        self._attack_timer = 0.0
        self._attack_current_frame = 0
        self._active_hitbox = None
        self._hitbox_consumed = False
        self.velocity.x = 0.0

        if attack_type == PlayerState.SHORT_ATTACK:
            self._attack_active_frames = [2, 3, 4]  # 1-indexed active frames
        else:
            self._attack_active_frames = [4, 5, 6, 7]

    def _update_attack_state(self, dt: float) -> None:
        """Update attack animation and hitbox."""
        total_frames = 6 if self._state == PlayerState.SHORT_ATTACK else 10
        fps = 18.0 if self._state == PlayerState.SHORT_ATTACK else 16.0
        cooldown = 0 if self._state == PlayerState.SHORT_ATTACK else (4 / fps)

        self._attack_timer += dt
        frame_duration = 1.0 / fps

        if self._attack_timer >= frame_duration:
            self._attack_timer -= frame_duration
            self._attack_current_frame += 1

        # Current 1-indexed frame
        current_frame = self._attack_current_frame + 1

        # Check if hitbox should be active
        if current_frame in self._attack_active_frames and not self._hitbox_consumed:
            self._active_hitbox = self._build_attack_hitbox(current_frame)
        else:
            self._active_hitbox = None

        # Animation complete
        if self._attack_current_frame >= total_frames:
            self._active_hitbox = None
            if cooldown > 0:
                self._cooldown_timer = cooldown
            self._change_state(PlayerState.IDLE)

    def _build_attack_hitbox(self, frame: int) -> pygame.Rect:
        """
        Build the attack hitbox rect for the given 1-indexed frame.
        Uses offsets from 04_PLAYER_SPEC.md §10.
        """
        is_crouching = self._state == PlayerState.CROUCHING
        cx = self.rect.centerx
        cy = self.rect.centery

        if self._state == PlayerState.SHORT_ATTACK:
            offset_x = 8
            offset_y = -4 if not is_crouching else 8
            w, h = 20, 16
        else:
            # Long attack frame-by-frame offsets
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

        # Apply facing direction
        hx = cx + (offset_x * self.facing_direction) - (w // 2)
        hy = cy + offset_y - (h // 2)

        return pygame.Rect(hx, hy, w, h)

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
        1. Resolve X axis
        2. Resolve Y axis
        3. Update grounded state
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

        # --- X axis ---
        for tile in collision_rects:
            if player_rect.colliderect(tile):
                if self.velocity.x > 0:
                    # Moving right: push left
                    player_rect.right = tile.left
                elif self.velocity.x < 0:
                    # Moving left: push right
                    player_rect.left = tile.right
                self.velocity.x = 0.0

        self.position.x = float(player_rect.x)
        player_rect.x = int(self.position.x)

        # --- Y axis ---
        self.is_grounded = False
        for tile in collision_rects:
            if player_rect.colliderect(tile):
                if self.velocity.y > 0:
                    # Falling: land on top
                    player_rect.bottom = tile.top
                    self.velocity.y = 0.0
                    self.is_grounded = True
                elif self.velocity.y < 0:
                    # Moving up: push down
                    player_rect.top = tile.bottom
                    self.velocity.y = 0.0

        self.position.y = float(player_rect.y)

    # ──────────────────────────────────────────────
    # Rect / Hurtbox sizing
    # ──────────────────────────────────────────────

    def _update_rect_size(self) -> None:
        """Update rect size based on current state (crouching vs standing)."""
        if self._state == PlayerState.CROUCHING:
            self.rect.width = 20
            self.rect.height = 20
        else:
            self.rect.width = 20
            self.rect.height = 32

        # Keep rect aligned to position
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)