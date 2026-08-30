"""
Module: enemy_flying_bomber
System: framework.entities
Academic Unit: Unit III (Projectiles), Unit IV (Area Denial)
Description: Flying enemy that drops hazards from air — zone denial.
AUD-632 — arquetipo: bombardero aéreo, denegación de zona.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_flying import EnemyFlying
from src.framework.entities.enemy_shooter import Projectile

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class EnemyFlyingBomber(EnemyFlying):
    """
    Flying Bomber — flies and drops explosive/projectile hazards.
    Zone denial from above.
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
            zone=zone,
            flight_mode="sine",
            flight_speed=50.0,
            sine_amplitude=30.0,
            sine_frequency=1.0,
        )

        # Bombing
        self._drop_cooldown: float = 0.0
        self._drop_interval: float = 2.5
        self._bomb_damage: float = 1.0
        self._bomb_radius: float = 48.0
        self._active_bombs: list[Projectile] = []

        self._load_zone_sprites(zone, 20, 14)

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None)
        sid = str(species_id).lower() if species_id else None
        for key in ("fly", "drop"):
            frames: list[pygame.Surface] = []
            if sid:
                for cand in [
                    base / f"enemy_{sid}_{key}.png",
                    base / f"enemy_{sid}_fly.png" if key == "fly" else None,
                    settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{species_id}_{key}.png",
                ]:
                    if cand is None or not cand.exists():
                        continue
                    try:
                        tmp = AssetLoader.load_sprite_sheet(cand, fw, fh)
                    except Exception:
                        continue
                    if tmp and tmp[0].get_size() == (fw, fh):
                        frames = tmp
                        break
            if not frames:
                # legacy genérico
                legacy = base / f"enemy_bomber_{zone_key}_{key}.png"
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
                col = (112, 116, 128)
                for _ in range(4):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    # hélices
                    pygame.draw.rect(surf, (64, 68, 78), (2, 1, fw - 4, 2))
                    pygame.draw.ellipse(surf, (40, 40, 50), (fw // 2 - 2, fh - 4, 4, 3))
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    if key == "drop":
                        pygame.draw.ellipse(surf, (80, 80, 90), (fw // 2 - 2, fh - 6, 4, 4))
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder

    def _alert_behavior(self, dt: float) -> None:
        super()._alert_behavior(dt)

        # Soltar bomba
        self._drop_cooldown = max(0.0, self._drop_cooldown - dt)
        if self._drop_cooldown <= 0 and self._player_ref:
            self._drop_bomb()
            self._drop_cooldown = self._drop_interval

    def _drop_bomb(self) -> None:
        if self._player_ref is None:
            return

        # Bomba cae verticalmente con daño en área
        bomb = Projectile(
            spawn_position=pygame.Vector2(self.rect.centerx, self.rect.bottom),
            velocity=pygame.Vector2(0, 200.0),
            damage=self._bomb_damage,
            lifetime=3.0,
        )
        bomb._bomb_radius = self._bomb_radius  # para explosión en área
        self._active_bombs.append(bomb)
        self._event_bus.emit(Events.SFX_PROJECTILE_FIRE, pos=(self.rect.centerx, self.rect.centery))

    def _post_update(self, dt: float) -> None:
        # Actualizar bombas y área — colisión con terreno + expiración
        for bomb in list(self._active_bombs):
            bomb.update(dt)
            if self._collision_rects:
                for tile in self._collision_rects:
                    if bomb.rect.colliderect(tile):
                        bomb._expired = True
                        bomb.is_active = False
                        break
            if not bomb.is_active:
                self._active_bombs.remove(bomb)
                # Explosión en área — chequeo correcto contra el rect del jugador
                if hasattr(bomb, "_bomb_radius") and self._player_ref is not None:
                    jugador_rect = getattr(self._player_ref, "rect", None)
                    if jugador_rect is not None and bomb.rect.colliderect(jugador_rect):
                        # Daño en área: el Projectile ya habría hecho colisión,
                        # esto es el radio de explosión adicional
                        if hasattr(self._player_ref, "apply_damage"):
                            self._player_ref.apply_damage(
                                bomb.damage, (bomb.rect.centerx, bomb.rect.centery)
                            )

    def _get_animation_key(self) -> str:
        return "fly"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()
