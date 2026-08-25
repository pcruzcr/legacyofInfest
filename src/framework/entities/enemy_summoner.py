"""
Module: enemy_summoner
System: framework.entities
Academic Unit: Unit IX (AI, Summoning)
Description: Enemy that spawns minions — pacing, area control.
AUD-631 — arquetipo: invocador de esbirros, control de zona.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core import azar
from src.engine.core.events import Events
from src.framework.entities.enemy_base import EnemyBase, EnemyState
from src.framework.entities.enemy_walker import EnemyWalker

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.framework.ecs.world import World


class EnemySummoner(EnemyBase):
    """
    Summoner enemy — spawns minions periodically, manages area control.
    Uses SummonTracker logic adapted from BossBase.
    """

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 4.0,
        damage_on_contact: float = 0.5,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=220.0,
            detection_range_y=100.0,
            hurt_duration=0.35,
            invincibility_duration=0.4,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        self.patrol_length: float = 60.0
        self.patrol_speed: float = 25.0
        self.alert_speed: float = 40.0

        # Summoning
        self._summon_cooldown: float = 0.0
        self._summon_interval: float = 8.0
        self._summon_type: str = "WalkerInsect"  # species_id a invocar
        self._max_minions: int = 3
        self._active_minions: int = 0

        self._load_zone_sprites(zone, 16, 16)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_summoner_{zone_key}_walk.png"), ("cast", f"enemy_summoner_{zone_key}_cast.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 16, 16)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_summoner: failed to load sprite %s", path)

    def _patrol_behavior(self, dt: float) -> None:
        # Movimiento muy lento, casi estático
        speed = 15.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= self.patrol_length / 2:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()

        # Intentar invocar
        self._summon_cooldown = max(0.0, self._summon_cooldown - dt)
        if self._summon_cooldown <= 0 and self._active_minions < self._max_minions:
            self._summon()
            self._summon_cooldown = self._summon_interval

        # Movimiento lento hacia/away del jugador
        if self._player_ref:
            dx = self._player_ref.centerx - self.rect.centerx
            if abs(dx) > 120:
                self.position.x += self.facing_direction * 20.0 * dt

    def _summon(self) -> None:
        if self._active_minions >= self._max_minions:
            return

        from src.framework.ecs.world import World
        from src.framework.entities import entity_factory

        # Spawnear esbirro cerca del invocador
        spawn_pos = pygame.Vector2(
            self.rect.centerx + azar.generador().uniform(-64, 64),
            self.rect.centery - 32,
        )

        try:
            minion = entity_factory.create_entity(
                self._summon_type,
                spawn_pos,
                zone=self._sprite_zone,
            )
            if minion:
                self._active_minions += 1
                # Callback al morir
                original_die = minion._die
                def on_die():
                    self._active_minions -= 1
                    original_die()
                minion._die = on_die
        except Exception as e:
            logger.warning("EnemySummoner: failed to spawn minion: %s", e)

    def _patrol_behavior(self, dt: float) -> None:
        # Movimiento muy lento, casi estático
        speed = 15.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= self.patrol_length / 2:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()

        # Intentar invocar
        self._summon_cooldown = max(0.0, self._summon_cooldown - dt)
        if self._summon_cooldown <= 0 and self._active_minions < self._max_minions:
            self._summon()
            self._summon_cooldown = self._summon_interval

        # Movimiento lento hacia/away del jugador
        if self._player_ref:
            dx = self._player_ref.centerx - self.rect.centerx
            if abs(dx) > 120:
                self.position.x += self.facing_direction * 20.0 * dt

    def _summon(self) -> None:
        if self._active_minions >= self._max_minions:
            return

        from src.framework.ecs.world import World
        from src.framework.entities import entity_factory

        # Spawnear esbirro cerca del invocador
        spawn_pos = pygame.Vector2(
            self.rect.centerx + azar.generador().uniform(-64, 64),
            self.rect.centery - 32,
        )

        try:
            minion = entity_factory.create_entity(
                self._summon_type,
                spawn_pos,
                zone=self._sprite_zone,
            )
            if minion:
                self._active_minions += 1
                # Callback al morir
                original_die = minion._die
                def on_die():
                    self._active_minions -= 1
                    original_die()
                minion._die = on_die
        except Exception as e:
            logger.warning("EnemySummoner: failed to spawn minion: %s", e)

    def _patrol_behavior(self, dt: float) -> None:
        # Movimiento muy lento, casi estático
        speed = 15.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= self.patrol_length / 2:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        self._summon_cooldown = max(0.0, self._summon_cooldown - dt)
        if self._summon_cooldown <= 0 and self._active_minions < self._max_minions:
            self._summon()
            self._summon_cooldown = self._summon_interval

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        for key, fname in [("walk", f"enemy_summoner_{zone_key}_walk.png"), ("cast", f"enemy_summoner_{zone_key}_cast.png")]:
            path = base / fname
            try:
                frames = AssetLoader.load_sprite_sheet(path, 16, 16)
                self._sprite_frames[key] = frames
            except (pygame.error, FileNotFoundError, PermissionError):
                logger.warning("enemy_summoner: failed to load sprite %s", path)

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()