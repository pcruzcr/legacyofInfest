"""
Module: enemy_terrain_shaper
System: framework.entities
Academic Unit: Unit IV (Terrain, Puzzles), Unit V (Materials)
Description: Enemy that creates/destroys terrain — PushBlock, BreakableBlock, HazardZone.
AUD-633 — arquetipo: modificador de terreno, puzzle dinámico.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.stage.bloques import BloqueEmpujable, BloqueDestructible

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.framework.ecs.world import World
    from src.framework.stage.stage_data import HazardZone


class EnemyTerrainShaper(EnemyBase):
    """
    Terrain Shaper — creates/destroys terrain blocks, places hazards.
    Dynamic puzzle creator.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 3.0,
        damage_on_contact: float = 0.5,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=200.0,
            detection_range_y=80.0,
            hurt_duration=0.35,
            invincibility_duration=0.4,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.patrol_length: float = 80.0
        self.patrol_speed: float = 30.0
        self.alert_speed: float = 45.0

        # Terrain manipulation
        self._action_cooldown: float = 0.0
        self._action_interval: float = 4.0
        self._action_type: int = 0  # 0=create block, 1=break block, 2=place hazard

        self.rect.width = 24
        self.rect.height = 20

        self._load_zone_sprites(zone, 16, 14)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_shaper_{zone_key}_walk.png"), ("action", f"enemy_shaper_{zone_key}_action.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 24, 20)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_terrain_shaper: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        speed = 25.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= self.patrol_length / 2:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        self._action_cooldown = max(0.0, self._action_cooldown - dt)
        if self._action_cooldown <= 0:
            self._perform_terrain_action()
            self._action_cooldown = self._action_interval

    def _perform_terrain_action(self) -> None:
        if not hasattr(self, "_mundo") or self._mundo is None:
            return

        action = self._action_type % 3
        x = self.rect.centerx + self.facing_direction * 48
        y = self.rect.centery

        if action == 0:
            # Crear bloque empujable
            from src.framework.stage.bloques import BloqueEmpujable
            bloque = BloqueEmpujable(
                rect=pygame.Rect(int(x), int(y), 32, 32),
                velocidad=45.0,
                con_gravedad=True,
            )
            # Añadir al mundo ECS
        elif action == 1:
            # Crear bloque destructible
            from src.framework.stage.bloques import BloqueDestructible
            bloque = BloqueDestructible(
                rect=pygame.Rect(int(x), int(y), 32, 32),
                golpes=2,
            )
        elif action == 2:
            # Colocar HazardZone
            from src.framework.stage.stage_data import HazardZone
            hazard = HazardZone(
                rect=pygame.Rect(int(x - 24), int(y), 48, 16),
                damage=0.5,
            )

        self._action_type = (self._action_type + 1) % 3

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_shaper_{zone_key}_walk.png"), ("action", f"enemy_shaper_{zone_key}_action.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 24, 20)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_terrain_shaper: failed to load sprite %s", path)

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()