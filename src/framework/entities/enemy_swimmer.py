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
        self.patrol_speed: float = 30.0
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

        self.rect.width = 48
        self.rect.height = 32

        self._load_zone_sprites(zone, 16, 12)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None)
        sid = str(species_id).lower() if species_id else None
        frames: list[pygame.Surface] = []
        if sid:
            for cand in [
                base / f"enemy_{sid}_swim.png",
                base / f"enemy_{sid}_walk.png",
                settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{species_id}_swim.png",
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
            for legacy in [base / f"enemy_swim_{zone_key}.png", base / f"enemy_swim_{zone_key}.png"]:
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
            self._sprite_frames["swim"] = frames
            # walk también usa swim para nadador; asegurar que walk no quede vacío
            if "walk" not in self._sprite_frames or not self._sprite_frames["walk"]:
                self._sprite_frames["walk"] = frames
        else:
            placeholder = []
            col = (38, 78, 148)
            for _ in range(4):
                surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                surf.fill((*col, 255))
                pygame.draw.ellipse(surf, tuple(min(255, c + 30) for c in col), (1, 1, fw - 2, fh - 2))
                pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                # aletas mínimas
                pygame.draw.polygon(surf, (68, 148, 188), [(fw - 2, fh // 2), (fw - 1, fh // 2 - 2), (fw - 1, fh // 2 + 2)])  # noqa: E501
                placeholder.append(surf)
            self._sprite_frames["swim"] = placeholder
            if "walk" not in self._sprite_frames or not self._sprite_frames["walk"]:
                self._sprite_frames["walk"] = placeholder

    def _patrol_behavior(self, dt: float) -> None:
        # Nadar en patrón: seguir corriente + explorar
        if self._in_water and self._current_zone:
            # Seguir corriente
            current = self._current_zone.corriente
            if current.length_squared() > 0:
                self._swim_direction = current.normalize()
            self.position += self._swim_direction * self.swim_speed * dt * 0.5
        else:
            # Fuera del agua: patrulla horizontal simple
            self.position.x += self.facing_direction * self.patrol_speed * dt
            # Rebotar en limites de arena si existe
            if self.arena_bounds is not None:
                if self.position.x <= self.arena_bounds.left or self.position.x + self.rect.width >= self.arena_bounds.right:  # noqa: E501
                    self.facing_direction *= -1

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
        # Si tiene mundo ECS, busca ZonaDeAgua que lo contenga
        try:
            if hasattr(self, "_mundo"):
                from src.framework.ecs.components import ZonaDeAgua
                for _, zona in self._mundo.cada(ZonaDeAgua):  # type: ignore[attr-defined]
                    if zona.rect.colliderect(self.rect):
                        self._in_water = True
                        self._current_zone = zona
                        return
        except Exception:
            pass
        # Fallback: si no hay ECS, asume fuera del agua pero patrulla igual
        # Para no quedar inerte fuera del agua, usa movimiento normal
        if not self._in_water:
            # No hay zona, pero permite patrulla en tierra
            self._current_zone = None
        # Si estaba en agua y ya no colisiona, sale
        if self._in_water and self._current_zone is not None:
            if not self._current_zone.rect.colliderect(self.rect):
                self._in_water = False
                self._current_zone = None
        # Si nunca entró, al menos permite movimiento terrestre
        if not self._in_water:
            self._current_zone = None

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