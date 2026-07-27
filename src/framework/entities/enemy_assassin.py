from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core.events import Events
from src.framework.entities.enemy_base import EnemyBase

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyAssassin(EnemyBase):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 1.5,
        damage_on_contact: float = 0.25,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=280.0,
            detection_range_y=80.0,
            hurt_duration=0.25,
            invincibility_duration=0.35,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.rect.width = 16
        self.rect.height = 24
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        self._is_cloaked: bool = False
        self._is_lunging: bool = False
        self._lunge_timer: float = 0.0
        self._lunge_duration: float = 0.3
        self._lunge_speed: float = 200.0
        self._lunge_dir: int = 1
        self._lunge_damage: float = 1.0
        self._lunge_has_hit: bool = False
        self._retreat_timer: float = 0.0
        self._retreat_duration: float = 2.0
        self._in_retreat: bool = False
        self._cloak_alpha: int = 80
        self._approach_range: float = 40.0

        # Cached surfaces
        self._cloak_fade_surf: pygame.Surface | None = None

        self._load_zone_sprites(zone, 12, 12)

    def _patrol_behavior(self, dt: float) -> None:
        speed = 120.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 64:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()

        if self._in_retreat:
            self._retreat_timer -= dt
            if not self._is_cloaked:
                self._is_cloaked = True
            self.position.x -= self.facing_direction * 120.0 * dt
            if self._retreat_timer <= 0:
                self._in_retreat = False
                self._is_cloaked = False
            return

        if self._is_lunging:
            self._lunge_timer -= dt
            self.position.x += self._lunge_dir * self._lunge_speed * dt
            if self._lunge_timer <= 0:
                self._is_lunging = False
                self._in_retreat = True
                self._retreat_timer = self._retreat_duration
            return

        if self._player_ref is None:
            return

        dx = self._player_ref.centerx - self.rect.centerx
        dist = abs(dx)

        if dist <= self._approach_range:
            if self._is_cloaked:
                self._is_cloaked = False
            self._is_lunging = True
            self._lunge_timer = self._lunge_duration
            self._lunge_dir = 1 if dx >= 0 else -1
            self._lunge_has_hit = False
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="assassin_lunge", rect=self.rect)
            return

        if not self._is_cloaked:
            self._is_cloaked = True

        flank_dir = 1 if dx < 0 else -1
        self.position.x += flank_dir * 80.0 * dt

    def _get_animation_key(self) -> str:
        if self._is_lunging:
            return "attack"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(2, 2, 16, 24)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def check_player_contact(self, player: Player) -> None:
        if self._is_cloaked and not self._is_lunging:
            return
        if self._is_lunging and not self._lunge_has_hit:
            player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
            if self.hurtbox.colliderect(player_hurtbox):
                player.apply_damage(self._lunge_damage, (self.position.x, self.position.y))
                self._lunge_has_hit = True
        super()._check_player_contact(player)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if not self.is_visible or not self.is_alive:
            return
        if self._is_cloaked:
            screen_x = int(self.position.x - camera_offset.x)
            screen_y = int(self.position.y - camera_offset.y)
            if self._cloak_fade_surf is None:
                self._cloak_fade_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            fade = self._cloak_fade_surf
            fade.fill((0, 0, 0, 0))
            fade.set_alpha(255 - self._cloak_alpha)
            fade.fill((30, 40, 60))
            surface.blit(fade, (screen_x, screen_y))
