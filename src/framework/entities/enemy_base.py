"""
Module: enemy_base
System: framework.entities
Academic Unit: Unit II (Vectors, Collision), Unit III (State Machines)
Description: Abstract base class for all enemy entities. Provides FSM
(PATROL/ALERT/HURT/DYING), detection system, contact damage, invincibility,
hitbox/hurtbox infrastructure, and death handling.
"""
from __future__ import annotations

from abc import abstractmethod
from enum import Enum

import pygame

from src.engine.core.event_bus import EventBus
from src.framework.entities.base_entity import BaseEntity


class EnemyState(str, Enum):
    """All possible enemy states as defined in 05_ENEMY_SPEC.md §7."""
    PATROL = "PATROL"
    ALERT = "ALERT"
    HURT = "HURT"
    DYING = "DYING"


class EnemyBase(BaseEntity):
    """
    Abstract root class for all enemies. Inherits from BaseEntity.
    Subclasses implement _patrol_behavior, _alert_behavior,
    _get_animation_state, _build_hitbox, _build_hurtbox.
    Do NOT override update() — use the master update pattern.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float,
        damage_on_contact: float = 0.5,
        contact_knockback: float = 120.0,
        detection_range_x: float = 160.0,
        detection_range_y: float = 64.0,
    ) -> None:
        """Initialize the enemy at the given spawn position."""
        super().__init__(spawn_position)

        # --- Health ---
        self.max_health: float = max_health
        self.current_health: float = max_health
        self.is_alive: bool = True

        # --- Combat ---
        self.damage_on_contact: float = damage_on_contact
        self.contact_knockback: float = contact_knockback
        self._invincibility_timer: float = 0.0
        self._contact_cooldown: float = 0.0
        self._hurt_timer: float = 0.0
        self._death_timer: float = 0.0

        # --- Detection ---
        self.detection_range_x: float = detection_range_x
        self.detection_range_y: float = detection_range_y
        self._deaggro_margin: float = 32.0

        # --- State ---
        self.state: EnemyState = EnemyState.PATROL
        self.facing_direction: int = 1  # -1 left, 1 right

        # --- Hitbox / Hurtbox (world-space, recomputed each frame) ---
        self.hitbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.hurtbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        # --- Animation ---
        self._animation_timer: float = 0.0
        self._animation_frame: int = 0

        # --- Rect ---
        self.rect = pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            24,
            28,
        )

    # ──────────────────────────────────────────────
    # Master update (do NOT override in subclasses)
    # ──────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Master update. Called every frame.
        Order: invincibility -> state machine -> rects -> contact.
        Subclasses do NOT override this method.
        """
        self._update_invincibility(dt)
        self._run_state_machine(dt)
        self._update_rects()
        self._tick_cooldowns(dt)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """
        Draw the enemy placeholder to the surface.
        Subclasses may override for custom rendering.
        """
        if not self.is_visible or not self.is_alive:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        # Default placeholder: red rect with white border
        pygame.draw.rect(
            surface,
            (200, 0, 0),
            (screen_x, screen_y, self.rect.width, self.rect.height),
        )
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (screen_x, screen_y, self.rect.width, self.rect.height),
            1,
        )

    # ──────────────────────────────────────────────
    # Public methods (provided, do not override)
    # ──────────────────────────────────────────────

    def apply_hit(
        self,
        damage: float,
        source_position: tuple[float, float],
    ) -> None:
        """
        Apply damage to the enemy. No-op if invincibility is active
        or if already dying. Emits ENEMY_DIED on death.
        """
        if self._invincibility_timer > 0:
            return
        if self.state == EnemyState.DYING:
            return

        self.current_health -= damage
        self._invincibility_timer = 0.5
        self._hurt_timer = 0.25

        if self.current_health <= 0:
            self._die()
        else:
            self.state = EnemyState.HURT

    def _die(self) -> None:
        """Handle death: set state, emit event, schedule removal."""
        self.state = EnemyState.DYING
        self.is_alive = False
        self._death_timer = 0.5
        EventBus.emit(
            "ENEMY_DIED",
            entity_id=f"{type(self).__name__}_{id(self)}",
            position=(self.position.x, self.position.y),
        )

    # ──────────────────────────────────────────────
    # Required overrides (abstract)
    # ──────────────────────────────────────────────

    @abstractmethod
    def _patrol_behavior(self, dt: float) -> None:
        """Default movement/AI when no player detected."""

    @abstractmethod
    def _alert_behavior(self, dt: float) -> None:
        """AI when player is within detection range."""

    @abstractmethod
    def _get_animation_state(self) -> str:
        """Return animation key for current state."""

    @abstractmethod
    def _build_hitbox(self) -> pygame.Rect:
        """Returns LOCAL-space rect (offset from entity position)."""

    @abstractmethod
    def _build_hurtbox(self) -> pygame.Rect:
        """Returns LOCAL-space rect (offset from entity position)."""

    # ──────────────────────────────────────────────
    # Provided methods (do not override)
    # ──────────────────────────────────────────────

    def _update_invincibility(self, dt: float) -> None:
        """Tick down invincibility timer."""
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt

    def _check_player_contact(self, player) -> None:
        """
        Check if this enemy's hurtbox overlaps the player's hurtbox.
        If so, deal contact damage (respecting cooldown).
        player: Player — imported locally to avoid circular imports.
        """
        if not self.is_alive:
            return
        if self._contact_cooldown > 0:
            return
        if self.hurtbox.colliderect(player.rect):
            player.apply_damage(
                self.damage_on_contact,
                self.rect.center,
            )
            self._contact_cooldown = 0.3

    def _update_rects(self) -> None:
        """Recompute hitbox and hurtbox world positions from local offsets."""
        local_hitbox = self._build_hitbox()
        local_hurtbox = self._build_hurtbox()

        self.hitbox = pygame.Rect(
            self.position.x + local_hitbox.x,
            self.position.y + local_hitbox.y,
            local_hitbox.width,
            local_hitbox.height,
        )
        self.hurtbox = pygame.Rect(
            self.position.x + local_hurtbox.x,
            self.position.y + local_hurtbox.y,
            local_hurtbox.width,
            local_hurtbox.height,
        )

        # Update main rect
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def _tick_cooldowns(self, dt: float) -> None:
        """Tick contact cooldown and hurt/death timers."""
        if self._contact_cooldown > 0:
            self._contact_cooldown -= dt
        if self._hurt_timer > 0:
            self._hurt_timer -= dt
        if self._death_timer > 0:
            self._death_timer -= dt
            if self._death_timer <= 0:
                self.is_active = False

    # ──────────────────────────────────────────────
    # State machine runner
    # ──────────────────────────────────────────────

    def _run_state_machine(self, dt: float) -> None:
        """
        Evaluate current state and dispatch to the appropriate behavior.
        Priority: DYING > HURT > ALERT > PATROL
        """
        if self.state == EnemyState.DYING:
            return

        if self.state == EnemyState.HURT:
            if self._hurt_timer <= 0:
                self.state = EnemyState.PATROL
            return

        # Check if player is in detection range
        player_in_range = self._check_detection_range()

        if player_in_range:
            self.state = EnemyState.ALERT
            self._alert_behavior(dt)
        else:
            self.state = EnemyState.PATROL
            self._patrol_behavior(dt)

    def _check_detection_range(self) -> bool:
        """
        Check if player is within detection range.
        Returns True if player is close enough.
        """
        # This is a simplified check — the actual player reference
        # must be provided by the stage collision system.
        # Returns False by default; subclasses or stage code
        # should override or provide player reference.
        return False

    def _player_in_range(self, player_rect: pygame.Rect) -> bool:
        """
        Check if the given player rect is within detection range.
        Called by stage code.
        """
        dx = abs(player_rect.centerx - self.rect.centerx)
        dy = abs(player_rect.centery - self.rect.centery)
        return dx <= self.detection_range_x and dy <= self.detection_range_y