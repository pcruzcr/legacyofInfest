from __future__ import annotations
from typing import TYPE_CHECKING

import math

import pygame

from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.entities.enemy_shooter import Projectile

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyArcher(EnemyBase):
    """Archer enemy — fires arcing projectiles at the player.
    Uses predictive aim and variable arc height.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 2.5,
        damage_on_contact: float = 0.25,
        fire_rate: float = 0.4,
        projectile_speed: float = 90.0,
        projectile_damage: float = 0.75,
        zone: int = 0,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=220.0,
            detection_range_y=80.0,
            hurt_duration=0.35,
            invincibility_duration=0.35,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.rect.width = 16
        self.rect.height = 28
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        self.fire_rate: float = fire_rate
        self.projectile_speed: float = projectile_speed
        self.projectile_damage: float = projectile_damage
        self._active_projectiles: list[Projectile] = []
        self._max_projectiles: int = 4
        self._shoot_cooldown: float = 0.0
        self._collision_rects: list[pygame.Rect] = []
        self._fire_anim_timer: float = 0.0

        self._load_zone_sprites(zone, 12, 14)

    def _patrol_behavior(self, dt: float) -> None:
        """Slow horizontal patrol."""
        speed = 15.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 48:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        """Face player and fire arcing shots."""
        self._face_player()
        self._shoot_cooldown -= dt
        if self._shoot_cooldown <= 0 and self.fire_rate > 0:
            self._telegraph_timer = self._telegraph_duration
            self.state = EnemyState.TELEGRAPHING

    def _firing_behavior(self, dt: float) -> None:
        """Fire an arcing projectile."""
        self._face_player()
        self._fire_anim_timer -= dt
        if self._fire_anim_timer <= 0:
            self._fire_arc()
            self._shoot_cooldown = 1.5 / self.fire_rate if self.fire_rate > 0 else 3.0
            self._fire_anim_timer = 0.2
            self.state = EnemyState.ALERT

    def _fire_arc(self) -> bool:
        """Fire a projectile with arc trajectory toward the player."""
        if len(self._active_projectiles) >= self._max_projectiles:
            return False
        if self._player_ref is None:
            return False

        dx = self._player_ref.centerx - self.rect.centerx
        dy = self._player_ref.centery - self.rect.centery
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            dist = 1

        # Predict player movement
        predict_factor = 0.3
        target_x = self._player_ref.centerx + dx * predict_factor
        target_y = self._player_ref.centery

        # Calculate arc angle
        angle = math.atan2(target_y - self.rect.centery, target_x - self.rect.centerx)
        arc_angle = angle - 0.2  # slight upward arc

        vel = pygame.Vector2(
            math.cos(arc_angle) * self.projectile_speed,
            math.sin(arc_angle) * self.projectile_speed - 20.0,
        )

        projectile = Projectile(
            spawn_position=pygame.Vector2(self.rect.centerx, self.rect.centery),
            velocity=vel,
            damage=self.projectile_damage,
            lifetime=3.0,
        )
        self._active_projectiles.append(projectile)
        from src.engine.core.event_bus import emit
        from src.engine.core.events import Events
        emit(Events.SFX_PROJECTILE_FIRE)
        return True

    def _post_update(self, dt: float) -> None:
        """Update active projectiles and apply gravity to them for arc effect."""
        for p in self._active_projectiles:
            p.update(dt)
        self.clear_expired_projectiles()

    def clear_expired_projectiles(self) -> None:
        self._active_projectiles = [p for p in self._active_projectiles if p.is_active]

    def get_projectiles(self) -> list[Projectile]:
        return self._active_projectiles

    def check_player_contact(self, player: Player) -> None:
        """Check contact + projectile collision."""
        super()._check_player_contact(player)
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for p in list(self._active_projectiles):
            if p.is_active and p.rect.colliderect(player_hurtbox):
                if getattr(player, "_parry_active", False) and getattr(player, "_parry_window", 0) > 0:
                    from src.engine.core.event_bus import emit
                    from src.engine.core.events import Events
                    p._expired = True
                    p.is_active = False
                    player._parry_success = True
                    player._parry_active = False
                    player._parry_window = 0.0
                    emit(Events.VFX_PARRY, pos=(p.position.x, p.position.y))
                else:
                    player.apply_damage(p.damage, (self.position.x, self.position.y))
                    p.on_collision()

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(2, 4, 16, 28)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()
