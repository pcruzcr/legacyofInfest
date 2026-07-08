"""
Module: enemy_shooter
System: framework.entities
Academic Unit: Unit II (Vectors, Trigonometry), Unit IV (Sprite Animation)
Description: Shooter enemy that fires projectiles at the player when
detected. Uses atan2 for angle calculation. Projectile is a lightweight
sub-entity with velocity, lifetime, and collision.
"""
from __future__ import annotations

import math

import pygame

from src.engine.core import settings
from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase, EnemyState


class Projectile(BaseEntity):
    """
    Lightweight projectile entity fired by EnemyShooter.
    Travels in a straight line at constant velocity.
    Expires after lifetime or on collision.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: float,
        lifetime: float = 3.0,
    ) -> None:
        """Initialize the projectile."""
        super().__init__(spawn_position)
        self.velocity: pygame.Vector2 = velocity
        self.damage: float = damage
        self._lifetime: float = lifetime
        self._elapsed: float = 0.0
        self._expired: bool = False

        # Small circular hitbox
        self.rect = pygame.Rect(
            int(self.position.x) - 2,
            int(self.position.y) - 2,
            4,
            4,
        )
        self.layer = 5

    def update(self, dt: float) -> None:
        """Move projectile and check expiration."""
        if self._expired:
            self.is_active = False
            return

        self._elapsed += dt
        if self._elapsed >= self._lifetime:
            self._expired = True
            self.is_active = False
            return

        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.rect.center = (int(self.position.x), int(self.position.y))

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """Draw the projectile as a small yellow circle."""
        if not self.is_visible or self._expired:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        pygame.draw.circle(surface, (255, 255, 0), (screen_x, screen_y), 4)
        pygame.draw.circle(
            surface, (255, 255, 255), (screen_x, screen_y), 4, 1
        )

    def on_collision(self) -> None:
        """Handle collision with a solid tile or player."""
        self._expired = True
        self.is_active = False


class EnemyShooter(EnemyBase):
    """
    Shooter enemy — fires projectiles at the player when detected.
    May be stationary or perform slow patrol.
    States: PATROL, ALERT (aim), FIRING (fire animation + projectile), HURT, DYING.
    FIRING state added per 05_ENEMY_SPEC.md §5.5.
    """

    _ANIM_FPS = {
        "walk": 6.0, "aim": 8.0, "fire": 16.0, "shoot": 16.0,
        "hurt": 12.0, "die": 10.0,
    }

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        fire_rate: float = 0.5,
        projectile_speed: float = 120.0,
        projectile_damage: float = 0.5,
        patrol_length: float = 0.0,
        max_health: float = 3.0,
        damage_on_contact: float = 0.25,
        zone: int = 0,
    ) -> None:
        """Initialize the shooter enemy."""
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=200.0,
            detection_range_y=64.0,
            hurt_duration=0.4,
            invincibility_duration=0.4,
        )

        self.fire_rate: float = fire_rate  # shots per second
        self.projectile_speed: float = projectile_speed
        self.projectile_damage: float = projectile_damage
        self.patrol_length: float = patrol_length
        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self._active_projectiles: list[Projectile] = []
        self._max_projectiles: int = 3
        self._shoot_cooldown: float = 0.0
        self._fire_anim_timer: float = 0.0
        self._collision_rects: list[pygame.Rect] = []

        # Rect size — offset Y so the bottom aligns with spawn Y (feet on floor)
        self.rect.width = 16
        self.rect.height = 24
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        # Load sprites
        self._load_zone_sprites(zone, 12, 12)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Load aim and fire animation sprites. Generate placeholder if missing."""
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        colors = {"aim": (180, 100, 220), "fire": (220, 80, 80)}
        for key, fname in [("aim", f"enemy_aim_{zone_key}.png"),
                           ("fire", f"enemy_fire_{zone_key}.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, fw, fh)
                self._sprite_frames[key] = frames
            except Exception:
                placeholder = pygame.Surface((fw, fh), pygame.SRCALPHA)
                placeholder.fill(colors.get(key, (200, 0, 200)))
                self._sprite_frames[key] = [placeholder]

    def _check_player_contact(self, player) -> None:
        """Check body contact against the player."""
        super()._check_player_contact(player)
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for p in self._active_projectiles:
            if p.is_active and p.rect.colliderect(player_hurtbox):
                player.apply_damage(p.damage, (self.position.x, self.position.y))
                p.on_collision()

    def check_player_contact(self, player) -> None:
        self._check_player_contact(player)

    def get_projectiles(self) -> list[Projectile]:
        """Return the list of active projectiles."""
        return self._active_projectiles

    def clear_expired_projectiles(self) -> None:
        """Remove expired projectiles from the active list."""
        self._active_projectiles = [
            p for p in self._active_projectiles if p.is_active
        ]

    def set_collision_rects(
        self,
        rects: list[pygame.Rect],
        one_way: list[pygame.Rect] | None = None,
    ) -> None:
        self._collision_rects = rects
        self._one_way_rects = one_way if one_way is not None else []

    # ──────────────────────────────────────────────
    # Behavior implementations
    # ──────────────────────────────────────────────

    def _patrol_behavior(self, dt: float) -> None:
        """Slow horizontal movement or stationary (walk animation)."""
        speed = self.facing_direction * 20.0 * dt
        if self.patrol_length > 0:
            self.position.x += speed
            distance = abs(self.position.x - self._patrol_origin.x)
            if distance >= self.patrol_length / 2:
                self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        """Aim phase: face player, aim animation, then transition to FIRING."""
        self._face_player()
        self._shoot_cooldown -= dt
        # Slow patrol while alert
        if self.patrol_length > 0:
            self.position.x += self.facing_direction * 20.0 * dt
        if self._shoot_cooldown <= 0 and self.fire_rate > 0:
            self._fire_anim_timer = 0.3  # ~5 frames at 16 FPS fire animation
            self.state = EnemyState.FIRING

    def _firing_behavior(self, dt: float) -> None:
        """Fire phase: fire projectile, stay in FIRING for animation duration."""
        self._face_player()
        self._fire_anim_timer -= dt
        if self._fire_anim_timer <= 0:
            self._fire()
            self._shoot_cooldown = 1.0 / self.fire_rate if self.fire_rate > 0 else 1.0
            self.state = EnemyState.ALERT

    def _fire(self) -> bool:
        """Fire a projectile toward the player. Returns True if fired."""
        if len(self._active_projectiles) >= self._max_projectiles:
            return False

        if self._player_ref is None:
            return False

        # Calculate angle to player (atan2)
        dx = self._player_ref.centerx - self.rect.centerx
        dy = self._player_ref.centery - self.rect.centery
        angle = math.atan2(dy, dx)

        # Create projectile velocity
        vel = pygame.Vector2(
            math.cos(angle) * self.projectile_speed,
            math.sin(angle) * self.projectile_speed,
        )

        spawn_pos = pygame.Vector2(
            self.rect.centerx + (self.facing_direction * 10),
            self.rect.y + 4,
        )

        projectile = Projectile(
            spawn_position=spawn_pos,
            velocity=vel,
            damage=self.projectile_damage,
            lifetime=3.0,
        )
        self._active_projectiles.append(projectile)
        emit(Events.SFX_PROJECTILE_FIRE)
        return True

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _get_animation_key(self) -> str:
        """Return animation key for non-DYING, non-HURT state."""
        if self.state == EnemyState.FIRING:
            return "fire"
        if self.state == EnemyState.ALERT:
            return "aim"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        """Return local-space hurtbox rect."""
        return pygame.Rect(4, 2, 24, 30)

    # ──────────────────────────────────────────────
    # Sprite rendering
    # ──────────────────────────────────────────────

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: pygame.Vector2,
    ) -> None:
        """Draw shooter using sprite, then overlay projectiles."""
        if not self.is_visible or not self.is_alive:
            return

        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        # Sprite or fallback
        frames = self._sprite_frames.get(self._get_animation_state())
        if frames:
            frame_idx = min(self._animation_frame, len(frames) - 1)
            frame = frames[frame_idx]
            if self.facing_direction < 0:
                frame = pygame.transform.flip(frame, True, False)
            ox = (self.rect.width - self._sprite_fw) // 2
            oy = self.rect.height - self._sprite_fh
            surface.blit(frame, (screen_x + ox, screen_y + oy))
        else:
            pygame.draw.rect(surface, (150, 0, 200),
                             (screen_x, screen_y, self.rect.width, self.rect.height))
            pygame.draw.rect(surface, (255, 255, 255),
                             (screen_x, screen_y, self.rect.width, self.rect.height), 1)

        # Draw active projectiles
        self.clear_expired_projectiles()
        for p in self._active_projectiles:
            p.draw(surface, camera_offset)

    def _post_update(self, dt: float) -> None:
        """Update projectiles after the base template finishes."""
        for p in self._active_projectiles:
            p.update(dt)
            # Check projectile collision with tiles
            if p.is_active and self._collision_rects:
                for rect in self._collision_rects:
                    if p.rect.colliderect(rect):
                        p.on_collision()
                        break
        self.clear_expired_projectiles()
