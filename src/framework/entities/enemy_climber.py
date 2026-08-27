"""
Module: enemy_climber
System: framework.entities
Academic Unit: Unit III (Curves), Unit IV (Physics)
Description: Enemy that climbs Vines and rides Ziplines — F5.14 gap-cero.
AUD-627 — enemigo trepador para lianas y tirolesas.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.ecs.components import Liana, Tirolesa
from src.framework.entities.enemy_base import EnemyBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


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
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None)
        sid = str(species_id).lower() if species_id else None
        for key in ("climb", "zipline"):
            frames: list[pygame.Surface] = []
            # 1) especie-específico con fw,fh correctos (16×16)
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
            # 2) genérico de zona legacy (20×24) — sólo si fw,fh cuadra, si no ignorar
            if not frames:
                for legacy in [
                    base / f"enemy_climb_{zone_key}.png" if key == "climb" else base / f"enemy_zipline_{zone_key}.png",
                    base / f"enemy_{key}_{zone_key}.png",
                ]:
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
                # placeholder coloreado: no dejar en rojo
                placeholder = []
                col = (90, 72, 52) if key == "climb" else (160, 160, 180)
                for _ in range(4):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    pygame.draw.ellipse(surf, tuple(min(255, c + 30) for c in col), (1, 1, fw - 2, fh - 2))
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    # cuerda/tirolesa mínima
                    if key == "climb":
                        pygame.draw.line(surf, (200, 180, 140), (fw // 2, 0), (fw // 2, fh - 1))
                    else:
                        pygame.draw.line(surf, (180, 180, 190), (0, fh // 3), (fw - 1, fh // 3))
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder

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