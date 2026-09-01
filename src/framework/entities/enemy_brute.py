from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_base import EnemyBase, EnemyState

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyBrute(EnemyBase):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 5.0,
        damage_on_contact: float = 0.5,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=120.0,
            detection_range_y=60.0,
            hurt_duration=0.35,
            invincibility_duration=0.5,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        # AUD-455: el y del TMX es la esquina superior (semántica nativa de
        # Tiled); el descuento de altura hacía flotar a todos los enemigos de
        # suelo. Ver `enemy_walker` para el porqué completo.
        # AUD-PROP: 100x60 era 4x el sprite 24x18 y dejaba hitbox gigante con
        # visual diminuto (placeholder). Ahora 32x28 es 1.33x el sprite, igual
        # que Walker (24x28 vs 16x12) y mantiene proporciones legibles.
        self.rect.width = 64
        self.rect.height = 56
        # Para que el loader encuentre el sprite de especie correcto
        self._species_id = "BruteGolemHielo"

        self._slam_cooldown: float = 3.0
        self._telegraph_duration = 0.3
        self._shockwave_active: bool = False
        self._shockwave_timer: float = 0.0
        self._shockwave_has_hit: bool = False
        self._shockwave_duration: float = 0.4

        # Cached surfaces
        self._brute_warning_surf: pygame.Surface | None = None
        self._brute_warning_size: tuple[int, int] = (0, 0)
        self._shock_surf: pygame.Surface | None = None

        self._load_zone_sprites(zone, 24, 18)

    def _patrol_behavior(self, dt: float) -> None:
        speed = 40.0
        self.position.x += self.facing_direction * speed * dt
        # Colisión con muros
        if self._collision_rects:
            rect = pygame.Rect(int(self.position.x), int(self.position.y), self.rect.width, self.rect.height)
            for tile in self._collision_rects:
                if rect.colliderect(tile):
                    if self.facing_direction > 0:
                        self.position.x = float(tile.left - self.rect.width)
                    else:
                        self.position.x = float(tile.right)
                    self.facing_direction *= -1
                    break
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 64:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        self._slam_cooldown -= dt
        if self._slam_cooldown <= 0:
            self._telegraph_timer = self._telegraph_duration
            self.state = EnemyState.TELEGRAPHING
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="ground_slam", rect=self.rect)

    def _firing_behavior(self, dt: float) -> None:
        self._shockwave_active = True
        self._shockwave_timer = self._shockwave_duration
        self._shockwave_has_hit = False
        self._slam_cooldown = 3.0
        # AUD-489 — el golpe de suelo suena desde donde golpea el bruto.
        self._event_bus.emit(Events.SFX_HIT_CONNECT, pos=(self.rect.centerx, self.rect.centery))
        self.state = EnemyState.ALERT

    def _post_update(self, dt: float) -> None:
        if self._shockwave_active:
            self._shockwave_timer -= dt
            if self._shockwave_timer <= 0:
                self._shockwave_active = False

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        zone_key = f"zone{zone}" if zone > 0 else "zone1"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None)
        sid = str(species_id).lower() if species_id else None
        for key in ("attack",):
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
                legacy = base / f"enemy_{key}_{zone_key}.png"
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
                # placeholder con masa/mazo enorme distinguible de walk
                placeholder = []
                col = (158, 216, 244)
                for _ in range(4):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    # maza arriba
                    pygame.draw.rect(surf, (120, 100, 80), (fw // 2 - 2, 1, 4, 6))
                    pygame.draw.rect(surf, (80, 60, 40), (fw // 2 - 1, 7, 2, fh // 2))
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder

    def _get_animation_key(self) -> str:
        if self._shockwave_active:
            return "attack"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=2)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _check_player_contact(self, player: Player) -> None:
        """AUD-149 — se llamaba `check_player_contact`, sin guion bajo.

        El motor llama al privado; el público es un alias obsoleto que
        `EnemyBase` conserva para las entregas. Al sobreescribir el público,
        esta lógica no se ejecutaba nunca en el juego.
        """
        if self._shockwave_active and not self._shockwave_has_hit:
            shockwave_rect = pygame.Rect(
                self.position.x + (self.rect.width - 32) // 2,
                self.position.y + self.rect.height - 12,
                32, 12
            )
            player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
            if shockwave_rect.colliderect(player_hurtbox):
                player.apply_damage(1.5, (self.position.x, self.position.y))
                self._shockwave_has_hit = True
        super()._check_player_contact(player)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if not self.is_visible or not self.is_alive:
            return
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        if self.state == EnemyState.TELEGRAPHING:
            ratio = 1.0 - self._telegraph_timer / max(self._telegraph_duration, 0.001)
            width = int(60 * ratio)
            height = 8
            indicator_x = screen_x + (self.rect.width - width) // 2
            indicator_y = screen_y - 16
            size = (width, height)
            if (self._brute_warning_surf is None
                    or self._brute_warning_size != size):
                self._brute_warning_surf = pygame.Surface(size, pygame.SRCALPHA)
                self._brute_warning_size = size
            warning_surf = self._brute_warning_surf
            warning_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(warning_surf, (255, 255, 0, 200), (0, 0, width, height))
            surface.blit(warning_surf, (indicator_x, indicator_y))

        if self._shockwave_active:
            shock_x = screen_x + (self.rect.width - 32) // 2
            shock_y = screen_y + self.rect.height - 12
            if self._shock_surf is None:
                self._shock_surf = pygame.Surface((32, 12), pygame.SRCALPHA)
            shock_surf = self._shock_surf
            if shock_surf.get_size() != (32, 12):
                self._shock_surf = pygame.Surface((32, 12), pygame.SRCALPHA)
                shock_surf = self._shock_surf
            shock_surf.fill((0, 0, 0, 0))
            alpha = int(180 * (self._shockwave_timer / max(self._shockwave_duration, 0.001)))
            pygame.draw.ellipse(shock_surf, (200, 180, 100, alpha), (0, 0, 32, 12))
            surface.blit(shock_surf, (shock_x, shock_y))
