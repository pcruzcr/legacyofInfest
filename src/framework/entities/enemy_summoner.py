"""
Module: enemy_summoner
System: framework.entities
Academic Unit: Unit IX (AI, Summoning)
Description: Enemy that spawns minions — pacing, area control.
AUD-631 — arquetipo: invocador de esbirros, control de zona.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import azar, settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_base import EnemyBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


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
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None)
        sid = str(species_id).lower() if species_id else None
        for key in ("cast",):
            frames: list[pygame.Surface] = []
            if sid:
                for cand in [
                    base / f"enemy_{sid}_{key}.png",
                    settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{species_id}_{key}.png",
                ]:
                    if not cand.exists():
                        continue
                    try:
                        tmp = AssetLoader.load_sprite_sheet(cand, fw, fh)
                    except Exception:
                        continue
                    if tmp and tmp[0].get_size() == (fw, fh):
                        frames = tmp
                        break
            if not frames:
                legacy = base / f"enemy_summoner_{zone_key}_{key}.png"
                if legacy.exists():
                    try:
                        tmp = AssetLoader.load_sprite_sheet(legacy, fw, fh)
                    except Exception:
                        tmp = []
                    if tmp and tmp[0].get_size() == (fw, fh):
                        frames = tmp
            if frames:
                self._sprite_frames[key] = frames
            else:
                placeholder = []
                col = (96, 64, 132)
                for _ in range(4):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    # orbe
                    pygame.draw.circle(surf, (180, 80, 255), (fw // 2 + 2, fh // 3), 2)
                    pygame.draw.circle(surf, (255, 255, 255), (fw // 2 + 2, fh // 3), 1)
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder

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

    def _get_animation_key(self) -> str:
        if self._summon_cooldown > self._summon_interval - 0.5:
            return "cast"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()
