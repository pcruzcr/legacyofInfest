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

from src.engine.core import settings
from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
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
        hurt_duration: float = 0.25,
        invincibility_duration: float = 0.5,
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
        self._hurt_duration: float = hurt_duration
        self._invincibility_duration: float = invincibility_duration

        # --- Detection ---
        self.detection_range_x: float = detection_range_x
        self.detection_range_y: float = detection_range_y
        self._deaggro_margin: float = 32.0
        self._player_ref: pygame.Rect | None = None

        # --- State ---
        self.state: EnemyState = EnemyState.PATROL
        self.facing_direction: int = 1  # -1 left, 1 right

        # --- Hitbox / Hurtbox (world-space, recomputed each frame) ---
        self.hitbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.hurtbox: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        # --- Animation ---
        self._animation_timer: float = 0.0
        self._animation_frame: int = 0

        # --- Invincibility flash ---
        self._flash_counter: float = 0.0
        self._flash_visible: bool = True

        # --- Sprite ---
        self._sprite_zone: int = 0
        self._sprite_frames: dict[str, list[pygame.Surface]] = {}
        self._sprite_fw: int = 16
        self._sprite_fh: int = 12

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
        Order: pre_update -> invincibility -> state machine -> rects ->
               contact -> animation -> post_update.
        Subclasses override _pre_update or _post_update instead.
        TEMPLATE METHOD: algorithm skeleton fixed; hook methods supply
        per-subclass behavior without overriding the skeleton.
        """
        if self._pre_update(dt):
            return
        self._update_invincibility(dt)
        self._run_state_machine(dt)
        self._update_rects()
        self._tick_cooldowns(dt)
        self._advance_animation(dt)
        self._post_update(dt)

    def _pre_update(self, dt: float) -> bool:
        """
        Optional pre-update hook. Return True to skip the rest of update().
        Used by BossBase for phase transitions.
        """
        return False

    def _post_update(self, dt: float) -> None:
        """
        Optional post-update hook.
        Used by EnemyShooter to update projectiles.
        """

    def _load_zone_sprites(self, zone: int, sprite_name: str, fw: int, fh: int) -> None:
        """Load zone-specific enemy sprite sheets."""
        self._sprite_zone = zone
        self._sprite_fw = fw
        self._sprite_fh = fh
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_{zone_key}_walk.png"),
                           ("hurt", f"enemy_{zone_key}_hurt.png"),
                           ("die", f"enemy_{zone_key}_die.png")]:
            path = base / fname
            frames = AssetLoader.load_sprite_sheet(path, fw, fh)
            self._sprite_frames[key] = frames
        # Also try fly/shoot sprites
        extra = {"fly": f"enemy_fly_{zone_key}.png", "shoot": f"enemy_shoot_{zone_key}.png"}
        for key, fname in extra.items():
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, fw, fh)
                self._sprite_frames[key] = frames
            except Exception:
                pass

    def _advance_animation(self, dt: float) -> None:
        """Advance the sprite animation frame at ~10 FPS."""
        fps = 10.0
        frame_duration = 1.0 / fps
        self._animation_timer += dt
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if not frames:
            return
        if self._animation_timer >= frame_duration:
            self._animation_timer -= frame_duration
            self._animation_frame = (self._animation_frame + 1) % len(frames)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """
        Draw the enemy via sprite sheet or placeholder fallback.
        """
        if not self.is_visible or not self.is_alive:
            return

        # Invincibility flash: skip draw when invisible
        if not self._flash_visible:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        # Try sprite rendering
        anim_key = self._get_animation_state()
        frames = self._sprite_frames.get(anim_key)
        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            frame = frames[frame_idx]
            if self.facing_direction < 0:
                frame = pygame.transform.flip(frame, True, False)
            ox = (self.rect.width - self._sprite_fw) // 2
            oy = self.rect.height - self._sprite_fh
            surface.blit(frame, (screen_x + ox, screen_y + oy))
            return

        # Fallback placeholder
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
        self._invincibility_timer = self._invincibility_duration
        self._hurt_timer = self._hurt_duration

        if self.current_health <= 0:
            self._die()
        else:
            self.state = EnemyState.HURT

    def _die(self) -> None:
        """Handle death: set state, emit event, schedule removal."""
        self.state = EnemyState.DYING
        self.is_alive = False
        self._death_timer = 0.5
        emit(
            Events.ENEMY_DIED,
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
    def _get_animation_key(self) -> str:
        """Return animation key for the current non-DYING, non-HURT state."""

    @abstractmethod
    def _build_hurtbox(self) -> pygame.Rect:
        """Returns LOCAL-space rect (offset from entity position)."""

    # ──────────────────────────────────────────────
    # Concrete hooks with sensible defaults
    # ──────────────────────────────────────────────

    def _get_animation_state(self) -> str:
        """
        TEMPLATE METHOD: fixed mapping for DYING/HURT states;
        subclasses provide _get_animation_key() for the rest.
        """
        if self.state == EnemyState.DYING:
            return "die"
        if self.state == EnemyState.HURT:
            return "hurt"
        return self._get_animation_key()

    def _build_hitbox(self) -> pygame.Rect:
        """
        Default: no active attack hitbox — damage is contact-based.
        Subclasses override to introduce weapon hitboxes.
        """
        return pygame.Rect(0, 0, 0, 0)

    def _face_player(self) -> None:
        """Face toward the player's horizontal position."""
        if self._player_ref is not None:
            self.facing_direction = (
                1 if self._player_ref.centerx >= self.rect.centerx else -1
            )

    # ──────────────────────────────────────────────
    # Provided methods (do not override)
    # ──────────────────────────────────────────────

    _INV_FLASH_INTERVAL: float = 4.0 / 60.0

    def _update_invincibility(self, dt: float) -> None:
        """Tick down invincibility timer and toggle flash."""
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt
            self._flash_counter += dt
            if self._flash_counter >= self._INV_FLASH_INTERVAL:
                self._flash_counter -= self._INV_FLASH_INTERVAL
                self._flash_visible = not self._flash_visible
        else:
            self._flash_visible = True
            self._flash_counter = 0.0

    def check_player_contact(self, player) -> None:
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
        Deaggro hysteresis: once ALERT, player must leave detection range
        + deaggro_margin to return to PATROL.
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
        elif self.state == EnemyState.ALERT:
            # Deaggro hysteresis: use extended range before leaving ALERT
            still_in_range = self._player_in_range(
                self._player_ref, margin=self._deaggro_margin
            )
            if not still_in_range:
                self.state = EnemyState.PATROL
                self._patrol_behavior(dt)
        else:
            self.state = EnemyState.PATROL
            self._patrol_behavior(dt)

    def set_player_ref(self, player_rect: pygame.Rect) -> None:
        """Set or update the reference to the player's rect for detection."""
        self._player_ref = player_rect

    def _check_detection_range(self) -> bool:
        """
        Check if player is within detection range.
        Returns True if player is close enough.
        """
        if self._player_ref is None:
            return False
        return self._player_in_range(self._player_ref)

    def _player_in_range(
        self, player_rect: pygame.Rect | None = None, margin: float = 0.0
    ) -> bool:
        """
        Check if the given player rect is within detection range.
        Optional margin extends the detection zone (for deaggro hysteresis).
        Called by stage code.
        """
        pr = player_rect if player_rect is not None else self._player_ref
        if pr is None:
            return False
        dx = abs(pr.centerx - self.rect.centerx)
        dy = abs(pr.centery - self.rect.centery)
        return (
            dx <= self.detection_range_x + margin
            and dy <= self.detection_range_y + margin
        )
