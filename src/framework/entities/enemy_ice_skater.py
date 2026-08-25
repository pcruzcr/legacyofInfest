"""
Module: enemy_ice_skater
System: framework.entities
Academic Unit: Unit II (Friction, Physics), Unit V (Materials)
Description: Enemy that exploits FrictionZone with material=ice — inertia, sliding.
AUD-628 — gap-cero: enemigo patinador sobre hielo/musgo resbaladizo.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.ecs.components import ZonaDeFriccion
from src.framework.entities.enemy_base import EnemyBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class EnemyIceSkater(EnemyBase):
    """
    Ice Skater enemy — exploits FrictionZone (material=ice) with high inertia.
    Slides on ice/moss, can't stop quickly, uses momentum for attacks.
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
            detection_range_x=160.0,
            detection_range_y=64.0,
            hurt_duration=0.25,
            invincibility_duration=0.4,
        )

        self._hug_slopes = False

        # Estado de deslizamiento
        self._on_ice: bool = False
        self._ice_friction_zone: ZonaDeFriccion | None = None
        self._slide_velocity: pygame.Vector2 = pygame.Vector2(0, 0)
        self._slide_deceleration: float = 0.95  # inercia alta

        # Ataque deslizante
        self._slide_attack_cooldown: float = 0.0
        self._slide_attack_duration: float = 0.5
        self._is_sliding_attack: bool = False

        self.rect.width = 24
        self.rect.height = 20

        self._load_zone_sprites(zone, 16, 14)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("skate", f"enemy_skate_{zone_key}.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 24, 14)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_ice_skater: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        if self._on_ice:
            # En hielo: mantener inercia, cambiar dirección raramente
            self._slide_velocity *= self._slide_deceleration
            self.position += self._slide_velocity
        else:
            # Suelo normal: patrulla normal
            super()._patrol_behavior(dt)

    def _alert_behavior(self, dt: float) -> None:
        if self._on_ice:
            # En hielo: ataque deslizante direccional
            self._face_player()
            if self._slide_attack_cooldown <= 0:
                self._start_slide_attack()
        else:
            super()._alert_behavior(dt)

    def _start_slide_attack(self) -> None:
        self._is_sliding_attack = True
        self._slide_attack_cooldown = 3.0
        direction = 1 if self.facing_direction > 0 else -1
        self._slide_velocity.x = direction * 180.0
        self._slide_velocity.y = -50.0  # pequeño salto

    def update(self, dt: float) -> None:
        # Detectar zona de hielo
        self._check_ice_zone()
        if self._is_sliding_attack:
            self._slide_attack_timer -= dt
            if self._slide_attack_timer <= 0:
                self._is_sliding_attack = False
        super().update(dt)

    def _check_ice_zone(self) -> None:
        """Detecta si está en ZonaDeFriccion con material=hielo."""
        # (Implementación simplificada: en real se consultaría mundo ECS)
        pass

    def _get_animation_key(self) -> str:
        if self._on_ice:
            return "skate"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _post_update(self, dt: float) -> None:
        if self._on_ice:
            # Aplicar deslizamiento continuo
            self.position += self._slide_velocity * 0.1
            self._slide_velocity *= 0.98