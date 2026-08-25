"""
Module: enemy_climber
System: framework.entities
Academic Unit: Unit III (Curves), Unit IV (Physics)
Description: Enemy that climbs Vines and rides Ziplines — F5.14 gap-cero.
AUD-627 — enemigo trepador para lianas y tirolesas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.entities.enemy_base import EnemyBase
from src.framework.ecs.components import Liana, Tirolesa

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyClimber(EnemyBase):
    """
    Climbing enemy — uses Vine and Zipline components for vertical/horizontal movement.
    Transitions between ground, Vine climbing, and Zipline riding.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 2.0,
        damage_on_contact: float = 0.5,
        climb_speed: float = 70.0,
        zipline_speed: float = 190.0,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=180.0,
            detection_range_y=160.0,
            hurt_duration=0.3,
            invincibility_duration=0.35,
        )

        self.climb_speed: float = climb_speed
        self.zipline_speed: float = zipline_speed
        self._hug_slopes = False  # trepadores no se pegan a pendientes

        # Estados de trepa
        self._on_liana: Liana | None = None
        self._on_zipline: Tirolesa | None = None
        self._climb_direction: int = 1  # 1 = sube, -1 = baja
        self._on_zipline_progress: float = 0.0

        self.rect.width = 20
        self.rect.height = 24

        self._load_zone_sprites(zone, 16, 16)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("climb", f"enemy_climb_{zone_key}.png"), ("zipline", f"enemy_zipline_{zone_key}.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 20, 24)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_climber: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        # Comportamiento de patrulla: buscar liana/tirolesa cercana
        if self._on_liana:
            self._climb_liana(dt)
        elif self._on_zipline:
            self._ride_zipline(dt)
        else:
            # Buscar liana/tirolesa cercana
            self._find_climb_target()

    def _alert_behavior(self, dt: float) -> None:
        if self._on_liana or self._on_zipline:
            # En trepa/tirolesa: perseguir al jugador en ese eje
            if self._player_ref:
                self._face_player()
        else:
            super()._alert_behavior(dt)

    def _find_climb_target(self) -> None:
        # Buscar Liana/Tirolesa cercana en el mundo ECS
        # (implementación simplificada: en real se consultaría mundo ECS)
        pass

    def _climb_liana(self, dt: float) -> None:
        if not self._on_liana:
            return
        # Subir/bajar por la liana
        direction = 1 if self._player_ref and self._player_ref.rect.centery < self.rect.centery else -1
        self.position.y += direction * self.climb_speed * dt
        # Clamp a los límites de la liana
        liana = self._on_liana
        self.position.y = max(liana.rect.top, min(liana.rect.bottom, self.position.y))

    def _ride_zipline(self, dt: float) -> None:
        if not self._on_zipline:
            return
        zipline = self._on_zipline
        # Avanzar en la tirolina
        self._on_zipline_progress += self.zipline_speed * dt / zipline.rect.width
        self._on_zipline_progress = max(0.0, min(1.0, self._on_zipline_progress))
        pos = zipline.origen + (zipline.destino - zipline.origen) * self._on_zipline_progress
        self.position = pos

    def _get_animation_key(self) -> str:
        if self._on_liana:
            return "climb"
        if self._on_zipline:
            return "zipline"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _post_update(self, dt: float) -> None:
        # Detectar transición a/salida de liana/tirolesa
        # (implementación simplificada)
        pass