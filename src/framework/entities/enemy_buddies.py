"""
Module: enemy_buddies
System: framework.entities
Academic Unit: Unit V (AI, Buddies)
Description: Buddy system — rideable companions with unique abilities.
AUD-637 — 3 buddies: Rino (ground charge), Expresso (flying), Enguarde (water).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader

logger = logging.getLogger(__name__)
from src.framework.ecs.components import RideableComponent
from src.framework.entities.enemy_base import EnemyBase

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class BuddyBase(EnemyBase):
    """Base class for buddy companions. Inherits from EnemyBase but friendly."""
    
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        buddy_id: str,
        max_health: float = 3.0,
        damage_on_contact: float = 0.0,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=200.0,
            detection_range_y=100.0,
            hurt_duration=0.3,
            invincibility_duration=0.4,
        )
        
        self.buddy_id: str = buddy_id
        
        # Rideable component
        self._rideable = RideableComponent(
            buddy_id=buddy_id,
            mount_type="ground",  # overridden in subclasses
            mount_speed=120.0,
            jump_speed=-380.0,
        )
        
        # Buddy state
        self._is_mounted: bool = False
        self._rider: Player | None = None
        self._follow_distance: float = 60.0
        
        self.rect.width = 24
        self.rect.height = 24
        
        self._load_zone_sprites(zone, 24, 24)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Override in subclasses"""
        pass

    def _get_animation_key(self) -> str:
        if self._is_mounted:
            return "ride"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _patrol_behavior(self, dt: float) -> None:
        """Follow player when not mounted, patrol when idle."""
        if self._is_mounted or self._rider is not None:
            return
            
        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            
            if dist > self._follow_distance:
                self.facing_direction = 1 if dx > 0 else -1
                self.position.x += self.facing_direction * 30.0 * dt

    def _alert_behavior(self, dt: float) -> None:
        if self._is_mounted:
            return
        self._face_player()
        if self._player_ref:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            if dist > self._follow_distance:
                self.position.x += self.facing_direction * 25.0 * dt

    def mount(self, rider: Player) -> bool:
        """Attempt to mount this buddy. Returns True if successful."""
        if self._is_mounted or self._rider is not None:
            return False
            
        self._is_mounted = True
        self._rider = rider
        
        # Position rider on buddy
        offset = self._rideable.rider_offset
        rider.position.x = self.position.x + offset.x * self.facing_direction
        rider.position.y = self.position.y + offset.y
        
        # Disable player controls, buddy takes over movement
        rider._state_instance = None  # will be replaced by MountedState
        from src.framework.entities.states import MountedState
        rider._change_state_instance(MountedState(buddy=self))
        
        self._is_mounted = True
        self._rider = rider
        return True

    def dismount(self) -> None:
        if not self._is_mounted or self._rider is None:
            return
            
        self._is_mounted = False
        self._rider = None
        # Player lands next to buddy
        if self._rider:
            self._rider.position = pygame.Vector2(
                self.rect.centerx,
                self.rect.top - self._rider.rect.height
            )
            from src.framework.entities.states import IdleState
            self._rider._change_state_instance(IdleState())

    def update(self, dt: float) -> None:
        if self._is_mounted:
            # Sync position with rider
            self._rider.position.x = self.position.x + self._rideable.rider_offset.x * self.facing_direction
            self._rider.position.y = self.position.y + self._rideable.rider_offset.y
            self._rider._squash_x = 1.0
            self._rider._squash_y = 1.0
        
        super().update(dt)
        
        # Sync buddy position with rider
        if self._is_mounted and self._rider:
            self.position.x = self._rider.position.x - self._rideable.rider_offset.x * self.facing_direction
            self.position.y = self._rider.position.y - self._rideable.rider_offset.y
            self._is_mounted = True
            
    def can_mount(self, player: Player) -> bool:
        """Check if player can mount this buddy."""
        return not self._is_mounted and self._rider is None and self.is_alive

    def _check_mount_input(self, player: Player) -> bool:
        """Check if player presses mount button near buddy."""
        # Check if player is near buddy and presses grab
        # This is called from player's update or interactable system
        return False  # overridden in subclasses if needed

    def _get_animation_key(self) -> str:
        if self._is_mounted:
            return "ride"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()


class BuddyRino(BuddyBase):
    """Rino - Ground buddy that charges through obstacles."""
    
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            buddy_id="rino",
            max_health=5.0,
            damage_on_contact=0.0,
            zone=zone,
        )
        
        # Rino-specific rideable config
        self._rideable.mount_type = "ground"
        self._rideable.mount_speed = 180.0
        self._rideable.jump_speed = -380.0
        self._rideable.can_fly = False
        self._rideable.rider_offset = pygame.Vector2(0, -24)
        self._rideable.rider_hitbox_offset = pygame.Vector2(0, -12)
        
        self._follow_distance = 80.0
        self.rect.width = 32
        self.rect.height = 28
        
        # Charge ability
        self._charge_cooldown: float = 0.0
        self._charge_interval: float = 5.0
        self._is_charging: bool = False
        self._charge_timer: float = 0.0
        self._charge_speed: float = 300.0
        self._charge_duration: float = 0.8

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"buddy_rino_{zone_key}_walk.png"), 
                           ("ride", f"buddy_rino_{zone_key}_ride.png"),
                           ("charge", f"buddy_rino_{zone_key}_charge.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 32, 28)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("buddy_rino: failed to load sprite %s", path)

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        
        if self._is_mounted:
            return
            
        self._summon_cooldown = max(0.0, self._summon_cooldown - dt)
        
        if self._player_ref:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            if dist > 120:
                self.position.x += self.facing_direction * 25.0 * dt
                
            # Charge attack when close enough
            if self._summon_cooldown <= 0 and dist < 200 and abs(self._player_ref.centery - self.rect.centery) < 32:
                self._start_charge()

    def _start_charge(self):
        self._is_charging = True
        self._charge_timer = 0.8
        self._charge_dir = 1 if self._player_ref.centerx > self.rect.centerx else -1
        self._is_charging = True

    def _get_animation_key(self) -> str:
        if self._is_charging:
            return "charge"
        if self._is_mounted:
            return "ride"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=4, margen_y=2)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def update(self, dt: float) -> None:
        if self._is_charging:
            self._charge_timer -= dt
            if self._charge_timer <= 0:
                self._is_charging = False
            else:
                self.position.x += self._charge_dir * self._charge_speed * dt
                return
                
        if self._is_mounted:
            # Sync position with rider
            self._rider.position.x = self.position.x + self._rideable.rider_offset.x * self.facing_direction
            self._rider.position.y = self.position.y + self._rideable.rider_offset.y
            
        super().update(dt)
        
    def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
        if self._is_charging:
            # Invulnerable during charge
            return
        super().apply_hit(damage, source_position)


class BuddyExpresso(BuddyBase):
    """Expresso - Flying buddy that carries player through air."""
    
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            buddy_id="expresso",
            max_health=3.0,
            damage_on_contact=0.0,
            zone=zone,
        )
        
        self._rideable.mount_type = "flying"
        self._rideable.mount_speed = 150.0
        self._rideable.can_fly = True
        self._rideable.rider_offset = pygame.Vector2(0, -18)
        
        self.rect.width = 24
        self.rect.height = 20
        self._hug_slopes = False  # voladores no se pegan a pendientes
        
        self._flight_mode: str = "hover"
        self._hover_target_y: float = 0.0

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("fly", f"buddy_expresso_{zone_key}_fly.png"),
                           ("ride", f"buddy_expresso_{zone_key}_ride.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 24, 20)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("buddy_expresso: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        if self._is_mounted:
            return
        # Hover near player
        if self._player_ref:
            dx = self._player_ref.centerx - self.rect.centerx
            dy = self._player_ref.centery - self.rect.centery
            dist = (dx**2 + dy**2)**0.5
            if dist > 100:
                self._face_player()
                self.position.x += self.facing_direction * 40.0 * dt
                if dy < 0:
                    self.position.y -= 30.0 * dt
                elif dy > 0:
                    self.position.y += 30.0 * dt

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        if self._is_mounted:
            return
        # Fly towards player if far
        if self._player_ref:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            if dist > 100:
                self.position.x += self.facing_direction * 40.0 * dt

    def _get_animation_key(self) -> str:
        if self._is_mounted:
            return "ride"
        return "fly"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def update(self, dt: float) -> None:
        if self._is_mounted:
            # Sync with rider
            self._rider.position.x = self.position.x + self._rideable.rider_offset.x * self.facing_direction
            self._rider.position.y = self.position.y + self._rideable.rider_offset.y
            self._rider._squash_x = 1.0
            self._rider._squash_y = 1.0
            return
        super().update(dt)


class BuddyEnguarde(BuddyBase):
    """Enguarde - Water buddy that swims and provides underwater mobility."""
    
    def __init__(
        self,
        spawn_position: pygame.Vector2,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            buddy_id="enguarde",
            max_health=3.0,
            damage_on_contact=0.0,
            zone=zone,
        )
        
        self._rideable.mount_type = "water"
        self._rideable.mount_speed = 140.0
        self._rideable.can_fly = False  # underwater movement
        self._rideable.rider_offset = pygame.Vector2(0, -16)
        
        self.rect.width = 28
        self.rect.height = 22
        self._hug_slopes = False

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("swim", f"buddy_enguarde_{zone_key}_swim.png"),
                           ("ride", f"buddy_enguarde_{zone_key}_ride.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 28, 22)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("buddy_enguarde: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        if self._is_mounted:
            return
        # Swim patrol
        pass

    def _alert_behavior(self, dt: float) -> None:
        if self._is_mounted:
            return
        self._face_player()
        if self._player_ref:
            dx = self._player_ref.centerx - self.rect.centerx
            dy = self._player_ref.centery - self.rect.centery
            dist = (dx**2 + dy**2)**0.5
            if dist > 100:
                # Swim towards player
                if dx != 0:
                    self.facing_direction = 1 if dx > 0 else -1
                self.position.x += self.facing_direction * 50.0 * dt
                if dy < -30:
                    self.position.y -= 40.0 * dt
                elif dy > 30:
                    self.position.y += 40.0 * dt

    def _get_animation_key(self) -> str:
        if self._is_mounted:
            return "ride"
        return "swim"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=3, margen_y=2)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def update(self, dt: float) -> None:
        if self._is_mounted:
            # Sync position with rider
            self._rider.position.x = self.position.x + self._rideable.rider_offset.x * self.facing_direction
            self._rider.position.y = self.position.y + self._rideable.rider_offset.y
            self._rider._squash_x = 1.0
            self._rider._squash_y = 1.0
            return
        super().update(dt)