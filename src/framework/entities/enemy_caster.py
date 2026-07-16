from __future__ import annotations
from typing import TYPE_CHECKING

import math

import pygame

if TYPE_CHECKING:
    from src.framework.entities.player import Player

from src.engine.core.event_bus import _get_bus as _bus
_emit = lambda *a, **kw: _bus().emit(*a, **kw)
from src.engine.core.events import Events
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase, EnemyState


class HomingOrb(BaseEntity):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: float,
        lifetime: float = 3.0,
    ) -> None:
        super().__init__(spawn_position)
        self.velocity: pygame.Vector2 = velocity
        self.damage: float = damage
        self._lifetime: float = lifetime
        self._elapsed: float = 0.0
        self._expired: bool = False

        self.rect = pygame.Rect(
            int(self.position.x) - 6,
            int(self.position.y) - 6,
            12, 12
        )
        self.layer = 5
        self._player_ref: pygame.Rect | None = None

    def set_player_ref(self, player_rect: pygame.Rect) -> None:
        self._player_ref = player_rect

    def update(self, dt: float) -> None:
        if self._expired:
            self.is_active = False
            return

        self._elapsed += dt
        if self._elapsed >= self._lifetime:
            self._expired = True
            self.is_active = False
            return

        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.position.x
            dy = self._player_ref.centery - self.position.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 1:
                self.velocity.x += (dx / dist) * 60.0 * dt
                self.velocity.y += (dy / dist) * 60.0 * dt
                speed = math.sqrt(self.velocity.x ** 2 + self.velocity.y ** 2)
                if speed > 120.0:
                    self.velocity.x = (self.velocity.x / speed) * 120.0
                    self.velocity.y = (self.velocity.y / speed) * 120.0

        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.rect.center = (int(self.position.x), int(self.position.y))

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.is_visible or self._expired:
            return
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        pulse = abs(math.sin(self._elapsed * 6.0))
        radius = 6 + int(pulse * 3)
        pygame.draw.circle(surface, (180, 80, 255), (screen_x, screen_y), radius)
        pygame.draw.circle(surface, (220, 180, 255), (screen_x, screen_y), radius, 1)

    def on_collision(self) -> None:
        self._expired = True
        self.is_active = False


class EnemyCaster(EnemyBase):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 2.0,
        damage_on_contact: float = 0.25,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=250.0,
            detection_range_y=80.0,
            hurt_duration=0.3,
            invincibility_duration=0.35,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.rect.width = 20
        self.rect.height = 28
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        self._shoot_cooldown: float = 0.0
        self._fire_rate: float = 2.5
        self._orb_speed: float = 120.0
        self._orb_damage: float = 0.75
        self._active_orbs: list[HomingOrb] = []
        self._max_orbs: int = 5
        self._collision_rects: list[pygame.Rect] = []
        self._telegraph_duration = 0.3
        self._ideal_distance: float = 150.0

        # Cached surfaces
        self._charge_surf: pygame.Surface | None = None

        self._load_zone_sprites(zone, 14, 14)

    def _patrol_behavior(self, dt: float) -> None:
        speed = 15.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 48:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            if dist < self._ideal_distance - 20:
                self.position.x -= self.facing_direction * 30.0 * dt
            elif dist > self._ideal_distance + 20:
                self.position.x += self.facing_direction * 30.0 * dt
        self._shoot_cooldown -= dt
        if self._shoot_cooldown <= 0:
            self._telegraph_timer = self._telegraph_duration
            self.state = EnemyState.TELEGRAPHING
            _emit(Events.BOSS_ATTACK, pattern="caster_charge", rect=self.rect)

    def _firing_behavior(self, dt: float) -> None:
        self._face_player()
        self._fire_orb()
        self._shoot_cooldown = self._fire_rate
        self.state = EnemyState.ALERT

    def _fire_orb(self) -> bool:
        if len(self._active_orbs) >= self._max_orbs:
            return False
        if self._player_ref is None:
            return False

        dx = self._player_ref.centerx - self.rect.centerx
        dy = self._player_ref.centery - self.rect.centery
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            dist = 1

        vel = pygame.Vector2(
            (dx / dist) * self._orb_speed,
            (dy / dist) * self._orb_speed,
        )

        orb = HomingOrb(
            spawn_position=pygame.Vector2(self.rect.centerx, self.rect.centery),
            velocity=vel,
            damage=self._orb_damage,
            lifetime=3.0,
        )
        orb.set_player_ref(self._player_ref)
        self._active_orbs.append(orb)
        _emit(Events.SFX_PROJECTILE_FIRE)
        return True

    def _post_update(self, dt: float) -> None:
        for o in self._active_orbs:
            o.update(dt)
            o.set_player_ref(self._player_ref)
            if self._collision_rects:
                for rect in self._collision_rects:
                    if o.rect.colliderect(rect):
                        o.on_collision()
                        break
        self._active_orbs = [o for o in self._active_orbs if o.is_active]

    def set_collision_rects(self, rects: list[pygame.Rect], one_way: list[pygame.Rect] | None = None) -> None:
        self._collision_rects = rects

    def check_player_contact(self, player: Player) -> None:
        super()._check_player_contact(player)
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for o in list(self._active_orbs):
            if o.is_active and o.rect.colliderect(player_hurtbox):
                if getattr(player, "_parry_active", False) and getattr(player, "_parry_window", 0) > 0:
                    o._expired = True
                    o.is_active = False
                    player._parry_success = True
                    player._parry_active = False
                    player._parry_window = 0.0
                    _emit(Events.VFX_PARRY, pos=(o.position.x, o.position.y))
                else:
                    player.apply_damage(o.damage, (self.position.x, self.position.y))
                    o.on_collision()

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(2, 4, 20, 28)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if not self.is_visible or not self.is_alive:
            return
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        if self.state == EnemyState.TELEGRAPHING:
            radius = 16
            center_x = screen_x + self.rect.width // 2
            center_y = screen_y + self.rect.height // 2
            if self._charge_surf is None:
                self._charge_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            charge_surf = self._charge_surf
            charge_surf.fill((0, 0, 0, 0))
            alpha = int(200 * (1.0 - self._telegraph_timer / max(self._telegraph_duration, 0.001)))
            pygame.draw.circle(charge_surf, (160, 60, 255, alpha), (radius, radius), radius)
            pygame.draw.circle(charge_surf, (200, 140, 255, min(255, alpha + 40)), (radius, radius), radius, 2)
            surface.blit(charge_surf, (center_x - radius, center_y - radius))

        self._active_orbs = [o for o in self._active_orbs if o.is_active]
        for o in self._active_orbs:
            o.draw(surface, camera_offset)
