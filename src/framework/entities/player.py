"""
Module: player
System: framework
Academic Unit: Player character
Description: Player movement and physics per 04_PLAYER_SPEC.md §4.
"""

from __future__ import annotations

import pygame

from src.engine.utils.math_utils import clamp
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.player_state import PlayerState
from src.engine.core.event_bus import EventBus
from src.engine.core import settings


class Player(BaseEntity):
    # Walk/jump/gravity/coyote-time/jump-cut per 04_PLAYER_SPEC.md §4.
    WALK_SPEED: float = 90.0
    GRAVITY: float = 800.0
    JUMP_VELOCITY: float = -380.0
    MAX_FALL_SPEED: float = 500.0
    COYOTE_FRAMES: int = 6
    JUMP_CUT_MULT: float = 0.5
    INVINCIBILITY_DURATION: float = 1.5

    def __init__(self, x: float, y: float) -> None:
        """Spawn the player at (*x*, *y*) in world coordinates."""
        self.pos: pygame.Vector2 = pygame.Vector2(x, y)
        self.vel: pygame.Vector2 = pygame.Vector2(0.0, 0.0)
        self.facing_direction: int = 1

        self._width: int = 16
        self._height: int = 24
        self._crouch_height: int = 12

        self.is_grounded: bool = False
        self._coyote_timer: float = 0.0
        self._invincibility_timer: float = 0.0

        self._health: float = settings.PLAYER_MAX_HEALTH
        self._crouching: bool = False
        self._direction: int = 0
        self._attack_input: str = ""
        self.state: PlayerState = PlayerState.IDLE
        self._knockback_timer: float = 0.0

    # -- helpers ----------------------------------------------------------

    @property
    def rect(self) -> pygame.Rect:
        """Axis-aligned bounding box for collision queries."""
        h = self._crouch_height if self._crouching else self._height
        return pygame.Rect(
            int(self.pos.x), int(self.pos.y - h), self._width, h
        )

    def _resolve_collisions(self, rects: list[pygame.Rect]) -> None:
        """Axis-separated collision resolution against *rects*."""
        # Horizontal pass
        self.pos.x += self.vel.x
        hit = self.rect
        for r in rects:
            if hit.colliderect(r):
                if self.vel.x > 0:
                    self.pos.x = r.left - self._width
                elif self.vel.x < 0:
                    self.pos.x = r.right
                self.vel.x = 0.0
                hit = self.rect

        # Vertical pass
        self.pos.y += self.vel.y
        hit = self.rect
        self.is_grounded = False
        for r in rects:
            if hit.colliderect(r):
                if self.vel.y > 0:
                    h = (
                        self._crouch_height
                        if self._crouching
                        else self._height
                    )
                    self.pos.y = r.top - h
                    self.vel.y = 0.0
                    self.is_grounded = True
                    self._coyote_timer = (
                        self.COYOTE_FRAMES / 60.0
                    )
                elif self.vel.y < 0:
                    h = (
                        self._crouch_height
                        if self._crouching
                        else self._height
                    )
                    self.pos.y = r.bottom + h
                    self.vel.y = 0.0
                hit = self.rect

    # -- lifecycle --------------------------------------------------------

    def on_enter(self) -> None:
        """Spawn hook."""

    def on_exit(self) -> None:
        """Despawn hook."""

    # -- frame update -----------------------------------------------------

    def update(
        self, dt: float, collision_rects: list[pygame.Rect] | None = None
    ) -> None:
        """Advance physics and movement by *dt* seconds."""
        if collision_rects is None:
            collision_rects = []

        # Timers
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt
        if self._knockback_timer > 0:
            self._knockback_timer -= dt
        if self.is_grounded:
            self._coyote_timer = self.COYOTE_FRAMES / 60.0
        elif self._coyote_timer > 0:
            self._coyote_timer -= dt

        # Direction-driven transitions
        if self.state in (PlayerState.IDLE, PlayerState.WALKING):
            if self._crouching:
                self.state = PlayerState.CROUCHING
            elif self._direction != 0:
                self.state = PlayerState.WALKING
            else:
                self.state = PlayerState.IDLE
        elif self.state == PlayerState.JUMPING:
            if self.vel.y > 0:
                self.state = PlayerState.FALLING
        elif self.state == PlayerState.FALLING:
            if self.is_grounded:
                self.state = PlayerState.IDLE
        elif self.state == PlayerState.CROUCHING:
            if not self._crouching:
                self.state = PlayerState.IDLE
            elif self._attack_input == "short":
                self.state = PlayerState.SHORT_ATTACK
            elif self._attack_input == "long":
                self.state = PlayerState.LONG_ATTACK
        elif self.state == PlayerState.HURT:
            if self._invincibility_timer <= 0:
                self.state = PlayerState.IDLE
        elif self.state == PlayerState.DYING:
            pass  # terminal state

        # Ignore input during knockback
        if self._knockback_timer > 0:
            direction = 0
            self._attack_input = ""

        # Horizontal input placeholder (direction from InputManager later)
        direction = self._direction if self._knockback_timer <= 0 else 0

        self.vel.x = direction * self.WALK_SPEED * dt

        # Gravity
        self.vel.y += self.GRAVITY * dt
        self.vel.y = clamp(self.vel.y, -500.0, self.MAX_FALL_SPEED)

        # Move and collide
        self._resolve_collisions(collision_rects)

    def start_jump(self) -> None:
        """Initiate a jump if grounded or within coyote time."""
        if self.is_grounded or self._coyote_timer > 0:
            self.vel.y = self.JUMP_VELOCITY
            self.is_grounded = False
            self._coyote_timer = 0.0
            self.state = PlayerState.JUMPING

    def release_jump(self) -> None:
        """Apply jump cut if still ascending."""
        if self.vel.y < 0:
            self.vel.y *= self.JUMP_CUT_MULT

    def set_crouch(self, crouching: bool) -> None:
        """Set crouch state (only when grounded)."""
        if self.is_grounded:
            self._crouching = crouching

    def take_damage(
        self,
        amount: float,
        source: tuple[float, float] | None = None,
    ) -> None:
        """Apply damage per 04_PLAYER_SPEC.md §6.2."""
        if self._invincibility_timer > 0:
            return
        self._health = max(
            0.0, min(settings.PLAYER_MAX_HEALTH, self._health - amount)
        )
        self._invincibility_timer = self.INVINCIBILITY_DURATION
        if source is not None:
            dx = self.pos.x - source[0]
            self.vel.x = (1.0 if dx >= 0 else -1.0) * 150.0
            self.vel.y = -200.0
        self._knockback_timer = 0.3
        EventBus.emit("PLAYER_DAMAGED", amount=amount, source=source)
        if self._health <= 0.0:
            self._health = 0.0
            self.state = PlayerState.DYING
            EventBus.emit("PLAYER_DIED")
        else:
            self.state = PlayerState.HURT

    def draw(self, surface: pygame.Surface) -> None:
        """Render the player as a placeholder coloured rect."""
        if (
            self._invincibility_timer > 0
            and int(self._invincibility_timer * 10) % 2 == 0
        ):
            return
        colour = (180, 60, 60) if not self._crouching else (140, 40, 40)
        pygame.draw.rect(surface, colour, self.rect)
