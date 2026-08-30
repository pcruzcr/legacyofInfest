"""
Module: enemy_shielded
System: framework.entities
Academic Unit: Unit IV (Combat, Shield Mechanics)
Description: Enemy with frontal shield — vulnerable from behind/parry.
AUD-630 — arquetipo: enemigo con escudo frontal, vulnerable por detrás/parry.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_base import EnemyBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


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
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None)
        sid = str(species_id).lower() if species_id else None
        # Shield state — el escudo frontal es la silueta distintiva PSX con placa metálica
        for key in ("shield",):
            frames: list[pygame.Surface] = []
            if sid:
                for cand in [
                    base / f"enemy_{sid}_{key}.png",
                    base / f"enemy_{sid}_walk.png",
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
                for legacy in [base / f"enemy_shielded_{zone_key}_shield.png", base / f"enemy_shielded_{zone_key}_walk.png"]:  # noqa: E501
                    if not legacy.exists():
                        continue
                    try:
                        tmp = AssetLoader.load_sprite_sheet(legacy, fw, fh)
                    except Exception:
                        continue
                    if tmp and tmp[0].get_size() == (fw, fh):
                        frames = tmp
                        break
            if frames:
                self._sprite_frames[key] = frames
            else:
                # placeholder con escudo metálico para que no quede rojo
                placeholder = []
                col = (54, 64, 118)
                shield_col = (168, 172, 188)
                for _ in range(4):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    # escudo frontal grande
                    pygame.draw.rect(surf, shield_col, (fw // 2, 1, fw // 2 - 1, fh - 2))
                    pygame.draw.rect(surf, tuple(max(0, c - 40) for c in shield_col), (fw // 2, 1, fw // 2 - 1, fh - 2), 1)  # noqa: E501
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder

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
        # Si el escudo sigue intacto se muestra la placa; si se rompe se ve walk sin escudo
        if not self._shield_broken and "shield" in self._sprite_frames and self._sprite_frames["shield"]:
            return "shield"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        # Hurtbox solo vulnerable por detrás
        if self.facing_direction > 0:
            return pygame.Rect(self.rect.width - 8, 2, 8, self.rect.height - 4)
        else:
            return pygame.Rect(0, 2, 8, self.rect.height - 4)

    def _build_hitbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def apply_hit(self, damage: float, source_position: tuple[float, float], canal: str | None = None) -> None:
        # Si golpea por delante (escudo), dañar escudo
        from_front = (
            (source_position[0] < self.rect.centerx and self.facing_direction > 0)
            or (source_position[0] > self.rect.centerx and self.facing_direction < 0)
        )
        if from_front and not self._shield_broken:
            self.shield_health -= damage
            if self.shield_health <= 0:
                self._shield_broken = True
                self._shield_regen_timer = self.shield_regen_delay
            # Knockback reducido
            super().apply_hit(damage * 0.25, source_position, canal)
        else:
            # Por detrás o escudo roto: daño normal
            super().apply_hit(damage, source_position, canal)
        # Regen se maneja en _post_update; no reiniciar el temporizador aquí
        # salvo en el fotograma exacto en que se rompe (arriba).

    def _post_update(self, dt: float) -> None:
        # Regen del escudo tras delay
        if self._shield_broken:
            self._shield_regen_timer -= dt
            if self._shield_regen_timer <= 0:
                self.shield_health = self.shield_max_health
                self._shield_broken = False
