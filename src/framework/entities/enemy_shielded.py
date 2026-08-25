"""
Module: enemy_shielded
System: framework.entities
Academic Unit: Unit IV (Combat, Shield Mechanics)
Description: Enemy with frontal shield — vulnerable from behind/parry.
AUD-630 — arquetipo: enemigo con escudo frontal, vulnerable por detrás/parry.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.entities.enemy_base import EnemyBase, EnemyState

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyShielded(EnemyBase):
    """
    Shielded enemy — frontal shield blocks damage, vulnerable from behind/parry.
    Shield has HP, regenerates after delay. Parry breaks shield instantly.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 3.0,
        damage_on_contact: float = 0.5,
        shield_health: float = 3.0,
        shield_regen_delay: float = 5.0,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=180.0,
            detection_range_y=64.0,
            hurt_duration=0.3,
            invincibility_duration=0.4,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.patrol_length: float = 80.0
        self.patrol_speed: float = 35.0
        self.alert_speed: float = 55.0

        # Shield
        self.shield_health: float = shield_health
        self.shield_max_health: float = shield_health
        self.shield_regen_delay: float = shield_regen_delay
        self._shield_regen_timer: float = 0.0
        self._shield_broken: bool = False

        self.rect.width = 28
        self.rect.height = 24

        self._load_zone_sprites(zone, 16, 14)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_shielded_{zone_key}_walk.png"), ("shield", f"enemy_shielded_{zone_key}_shield.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 28, 24)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_shielded: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        speed = self.patrol_speed
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= self.patrol_length / 2:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        # Shielded avanza hacia el jugador con escudo al frente
        self.position.x += self.facing_direction * self.alert_speed * dt

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        # Hurtbox solo vulnerable por detrás
        if self.facing_direction > 0:
            return pygame.Rect(self.rect.width - 8, 2, 8, self.rect.height - 4)
        else:
            return pygame.Rect(0, 2, 8, self.rect.height - 4)

    def _build_hitbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_shielded_{zone_key}_walk.png"), ("shield", f"enemy_shielded_{zone_key}_shield.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 28, 24)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_shielded: failed to load sprite %s", path)

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        # Vulnerable solo por detrás del escudo
        if self.facing_direction > 0:
            return pygame.Rect(self.rect.width - 8, 2, 8, self.rect.height - 4)
        else:
            return pygame.Rect(0, 2, 8, self.rect.height - 4)

    def _build_hitbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_shielded_{zone_key}_walk.png"), ("shield", f"enemy_shielded_{zone_key}_shield.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 28, 24)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_shielded: failed to load sprite %s", path)

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        # Vulnerable solo por detrás
        if self.facing_direction > 0:
            return pygame.Rect(self.rect.width - 8, 2, 8, self.rect.height - 4)
        else:
            return pygame.Rect(0, 2, 8, self.rect.height - 4)

    def _build_hitbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def apply_hit(self, damage: float, source_position: tuple[float, float]) -> None:
        # Si golpea por delante (escudo), dañar escudo
        from_front = (source_position[0] < self.rect.centerx and self.facing_direction > 0) or \
                      (source_position[0] > self.rect.centerx and self.facing_direction < 0)

        if from_front and not self._shield_broken:
            self.shield_health -= damage
            if self.shield_health <= 0:
                self._shield_broken = True
                self._shield_regen_timer = self.shield_regen_delay
            # Knockback reducido
            super().apply_hit(damage * 0.25, source_position)
        else:
            # Por detrás o escudo roto: daño normal
            super().apply_hit(damage, source_position)

        # Parry rompe escudo instantáneamente
        if hasattr(self, '_parry_success') and self._parry_success:
            self._shield_broken = True
            self._shield_regen_timer = self.shield_regen_delay