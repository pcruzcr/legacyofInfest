from __future__ import annotations
from typing import TYPE_CHECKING

import pygame

from src.engine.core.event_bus import emit
from src.engine.core.events import Events
from src.framework.entities.enemy_base import EnemyBase, EnemyState

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyBrute(EnemyBase):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 5.0,
        damage_on_contact: float = 0.5,
        zone: int = 0,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=120.0,
            detection_range_y=60.0,
            hurt_duration=0.35,
            invincibility_duration=0.5,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.rect.width = 100
        self.rect.height = 60
        self.position.y -= self.rect.height
        self.rect.y = int(self.position.y)

        self._slam_cooldown: float = 3.0
        self._telegraph_duration = 0.3
        self._shockwave_active: bool = False
        self._shockwave_timer: float = 0.0
        self._shockwave_has_hit: bool = False
        self._shockwave_duration: float = 0.4

        self._load_zone_sprites(zone, 24, 18)

    def _patrol_behavior(self, dt: float) -> None:
        speed = 40.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 64:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        self._slam_cooldown -= dt
        if self._slam_cooldown <= 0:
            self._telegraph_timer = self._telegraph_duration
            self.state = EnemyState.TELEGRAPHING
            emit(Events.BOSS_ATTACK, pattern="ground_slam", rect=self.rect)

    def _firing_behavior(self, dt: float) -> None:
        self._shockwave_active = True
        self._shockwave_timer = self._shockwave_duration
        self._shockwave_has_hit = False
        self._slam_cooldown = 3.0
        emit(Events.SFX_HIT_CONNECT)
        self.state = EnemyState.ALERT

    def _post_update(self, dt: float) -> None:
        if self._shockwave_active:
            self._shockwave_timer -= dt
            if self._shockwave_timer <= 0:
                self._shockwave_active = False

    def _get_animation_key(self) -> str:
        if self._shockwave_active:
            return "attack"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return pygame.Rect(0, 0, 100, 60)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def check_player_contact(self, player: Player) -> None:
        super()._check_player_contact(player)
        if self._shockwave_active and not self._shockwave_has_hit:
            shockwave_rect = pygame.Rect(
                self.position.x + (self.rect.width - 60) // 2,
                self.position.y + self.rect.height - 20,
                60, 20
            )
            player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
            if shockwave_rect.colliderect(player_hurtbox):
                player.apply_damage(1.5, (self.position.x, self.position.y))
                self._shockwave_has_hit = True

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if not self.is_visible or not self.is_alive:
            return
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        if self.state == EnemyState.TELEGRAPHING:
            ratio = 1.0 - self._telegraph_timer / max(self._telegraph_duration, 0.001)
            width = int(60 * ratio)
            height = 8
            indicator_x = screen_x + (self.rect.width - width) // 2
            indicator_y = screen_y - 16
            warning_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.rect(warning_surf, (255, 255, 0, 200), (0, 0, width, height))
            surface.blit(warning_surf, (indicator_x, indicator_y))

        if self._shockwave_active:
            shock_x = screen_x + (self.rect.width - 60) // 2
            shock_y = screen_y + self.rect.height - 20
            shock_surf = pygame.Surface((60, 20), pygame.SRCALPHA)
            alpha = int(180 * (self._shockwave_timer / max(self._shockwave_duration, 0.001)))
            pygame.draw.ellipse(shock_surf, (200, 180, 100, alpha), (0, 0, 60, 20))
            surface.blit(shock_surf, (shock_x, shock_y))
