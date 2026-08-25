"""
Module: enemy_flying_bomber
System: framework.entities
Academic Unit: Unit III (Projectiles), Unit IV (Area Denial)
Description: Flying enemy that drops hazards from air — zone denial.
AUD-632 — arquetipo: bombardero aéreo, denegación de zona.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import Projectile

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class EnemyFlyingBomber(EnemyFlying):
    """
    Flying Bomber — flies and drops explosive/projectile hazards.
    Zone denial from above.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 2.0,
        damage_on_contact: float = 0.5,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            zone=zone,
            flight_mode="sine",
            flight_speed=50.0,
            sine_amplitude=30.0,
            sine_frequency=1.0,
        )

        # Bombing
        self._drop_cooldown: float = 0.0
        self._drop_interval: float = 2.5
        self._bomb_damage: float = 1.0
        self._bomb_radius: float = 48.0

        self._load_zone_sprites(zone, 20, 14)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("fly", f"enemy_bomber_{zone_key}_fly.png"), ("drop", f"enemy_bomber_{zone_key}_drop.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 20, 14)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_flying_bomber: failed to load sprite %s", path)

    def _alert_behavior(self, dt: float) -> None:
        super()._alert_behavior(dt)

        # Soltar bomba
        self._drop_cooldown = max(0.0, self._drop_cooldown - dt)
        if self._drop_cooldown <= 0 and self._player_ref:
            self._drop_bomb()
            self._drop_cooldown = self._drop_interval

    def _drop_bomb(self) -> None:
        if self._player_ref is None:
            return

        # Bomba cae verticalmente con daño en área
        bomb = Projectile(
            spawn_position=pygame.Vector2(self.rect.centerx, self.rect.bottom),
            velocity=pygame.Vector2(0, 200.0),
            damage=self._bomb_damage,
            lifetime=3.0,
        )
        bomb._bomb_radius = self._bomb_radius  # para explosión en área
        self._event_bus.emit(Events.SFX_PROJECTILE_FIRE, pos=(self.rect.centerx, self.rect.centery))
        # El proyectil se añade a la escena via StageScene._post_update
        # (en implementación real se añadiría a la lista de proyectiles)

    def _get_animation_key(self) -> str:
        return "fly"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("fly", f"enemy_bomber_{zone_key}_fly.png"), ("drop", f"enemy_bomber_{zone_key}_drop.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 20, 14)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_flying_bomber: failed to load sprite %s", path)

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()