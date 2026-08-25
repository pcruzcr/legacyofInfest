"""

Module: enemy_parry_teacher

System: framework.entities

Academic Unit: Unit IV (Combat, Reaction)

Description: Enemy that teaches parry — generous telegraph, long stun on parry.

AUD-629 — gap-cero: enemigo profesor de parry, enseña la mecánica.

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_base import EnemyBase, EnemyState

logger = logging.getLogger(__name__)



if TYPE_CHECKING:

    pass





class EnemyParryTeacher(EnemyBase):

    """

    Parry Teacher enemy — generous telegraph window, long stun if parried.

    Teaches the player to parry instead of just dodging.

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

            detection_range_x=200.0,

            detection_range_y=80.0,

            hurt_duration=0.25,

            invincibility_duration=0.4,

        )



        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)

        self.patrol_length: float = 96.0

        self.patrol_speed: float = 40.0

        self.alert_speed: float = 60.0



        # Parry teaching

        self._telegraph_duration: float = 1.2  # ventana larga de parry

        self._parry_stun_duration: float = 2.0  # stun largo si parry acertado

        self._attack_cooldown: float = 0.0

        self._attack_duration: float = 0.4



        self._load_zone_sprites(zone, 16, 14)



    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:

        zone_key = f"zone{zone}" if zone > 0 else "zone1"

        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key

        for key, fname in [("walk", f"enemy_teacher_{zone_key}_walk.png"), ("telegraph", f"enemy_teacher_{zone_key}_telegraph.png")]:  # noqa: E501

            path = base / fname

            try:

                frames = AssetLoader.load_sprite_sheet(path, 16, 14)

                self._sprite_frames[key] = frames

            except (pygame.error, FileNotFoundError, PermissionError):

                logger.warning("enemy_parry_teacher: failed to load sprite %s", path)



    def _patrol_behavior(self, dt: float) -> None:

        # Patrulla lenta

        speed = self.patrol_speed

        self.position.x += self.facing_direction * speed * dt

        distance = abs(self.position.x - self._patrol_origin.x)

        if distance >= self.patrol_length / 2:

            self.facing_direction *= -1



    def _alert_behavior(self, dt: float) -> None:

        self._face_player()



        self._attack_cooldown = max(0.0, self._attack_cooldown - dt)

        if self._attack_cooldown <= 0:

            self._telegraph_timer = self._telegraph_duration

            self.state = EnemyState.TELEGRAPHING

            return



        if self.state == EnemyState.TELEGRAPHING:

            self._telegraph_timer -= dt

            if self._telegraph_timer <= 0:

                # Iniciar ataque

                self._attack_cooldown = 2.0

                self._attack_timer = self._attack_duration

                self.state = EnemyState.FIRING



    def _firing_behavior(self, dt: float) -> None:

        # Ataque simple: golpe cuerpo a cuerpo

        self._attack_timer -= dt

        if self._attack_timer <= 0:

            self._attack_cooldown = 2.0

            self.state = EnemyState.RECOVER

            self._recover_timer = 0.8  # ventana de castigo larga



    def _recover_behavior(self, dt: float) -> None:

        # Ventana de castigo: vulnerable a parry

        pass



    def _get_animation_key(self) -> str:

        if self.state == EnemyState.TELEGRAPHING:

            return "telegraph"

        return "walk"



    def _build_hurtbox(self) -> pygame.Rect:

        return self.caja_ajustada(margen_x=2, margen_y=1)



    def _build_hitbox(self) -> pygame.Rect:

        return self._build_hurtbox()



    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:

        zone_key = f"zone{zone}" if zone > 0 else "zone1"

        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key

        for key, fname in [("walk", f"enemy_teacher_{zone_key}_walk.png"), ("telegraph", f"enemy_teacher_{zone_key}_telegraph.png")]:  # noqa: E501

            path = base / fname

            try:

                frames = AssetLoader.load_sprite_sheet(path, 16, 14)

                self._sprite_frames[key] = frames

            except (pygame.error, FileNotFoundError, PermissionError):

                logger.warning("enemy_parry_teacher: failed to load sprite %s", path)



    def _build_hurtbox(self) -> pygame.Rect:

        return self.caja_ajustada(margen_x=2, margen_y=1)



    def _build_hitbox(self) -> pygame.Rect:

        return self._build_hurtbox()



    def _get_animation_key(self) -> str:

        if self.state == EnemyState.TELEGRAPHING:

            return "telegraph"

        return "walk"