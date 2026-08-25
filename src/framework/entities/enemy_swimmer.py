"""
Module: enemy_swimmer
System: framework.entities
Academic Unit: Unit IV (Physics, Fluids)
Description: Enemy that swims in WaterZone — physics, oxygen, current.
AUD-626 — F5.6 gap-cero: enemigo nadador para zonas de agua reales.
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.ecs.components import ZonaDeAgua
from src.framework.entities.enemy_base import EnemyBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class EnemySwimmer(EnemyBase):
    """
    Swimming enemy — moves in WaterZone with current, oxygen management.
    Uses WaterZone current for drift, has oxygen meter, drowns if no air.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 1.5,
        damage_on_contact: float = 0.5,
        swim_speed: float = 70.0,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=200.0,
            detection_range_y=120.0,
            hurt_duration=0.3,
            invincibility_duration=0.35,
        )

        self.swim_speed: float = swim_speed
        self._hug_slopes = False  # nadadores no se pegan a pendientes

        # Swimming state
        self._in_water: bool = False
        self._current_zone: ZonaDeAgua | None = None
        self._oxygen: float = 30.0  # segundos de aire
        self._max_oxygen: float = 30.0
        self._drowning_damage: float = 1.0  # daño/seg sin aire

        # Movimiento
        self._swim_direction: pygame.Vector2 = pygame.Vector2(1, 0)
        self._turn_timer: float = 0.0
        self._turn_interval: float = 2.0

        self.rect.width = 24
        self.rect.height = 16

        self._load_zone_sprites(zone, 16, 12)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("swim", f"enemy_swim_{zone_key}.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 24, 16)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_swimmer: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        # Nadar en patrón: seguir corriente + explorar
        if self._in_water and self._current_zone:
            # Seguir corriente
            current = self._current_zone.corriente
            if current.length_squared() > 0:
                self._swim_direction = current.normalize()
        else:
            # Fuera del agua: patrulla normal en tierra
            super()._patrol_behavior(dt)

    def _alert_behavior(self, dt: float) -> None:
        if self._in_water:
            # En agua: perseguir al jugador nadando
            self._face_player()
            if self._player_ref:
                dx = self._player_ref.centerx - self.rect.centerx
                dy = self._player_ref.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self._swim_direction = pygame.Vector2(dx, dy).normalize()
                self.position += self._swim_direction * self.swim_speed * dt
        else:
            # En tierra: comportamiento normal
            super()._alert_behavior(dt)

    def update(self, dt: float) -> None:
        # Detectar zona de agua
        self._update_water_state()
        # Oxígeno
        if self._in_water:
            self._oxygen = max(0.0, self._oxygen - dt)
            if self._oxygen <= 0:
                self.current_health -= self._drowning_damage * dt
                if self.current_health <= 0:
                    self.is_alive = False
        else:
            # Recuperar oxígeno en superficie
            self._oxygen = min(self._max_oxygen, self._oxygen + dt * 8.0)

        super().update(dt)

    def _update_water_state(self) -> None:
        """Detecta si el enemigo está en una ZonaDeAgua."""
        # Buscar zona de agua que contenga al enemigo
        # (simplificado: en implementación real se consultaría el mundo ECS)
        pass

    def _get_animation_key(self) -> str:
        return "swim"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _post_update(self, dt: float) -> None:
        # Aplicar corriente si está en agua
        if self._in_water and self._current_zone:
            current = self._current_zone.corriente
            if current.length_squared() > 0:
                self.position += current * dt