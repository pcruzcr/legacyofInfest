from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_base import EnemyBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class EnemyAssassin(EnemyBase):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 1.5,
        damage_on_contact: float = 0.25,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=280.0,
            detection_range_y=80.0,
            hurt_duration=0.25,
            invincibility_duration=0.35,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        # AUD-455: el y del TMX es la esquina superior (semántica nativa de
        # Tiled); el descuento de altura hacía flotar a todos los enemigos de
        # suelo. Ver `enemy_walker` para el porqué completo.
        self.rect.width = 16
        self.rect.height = 24

        self._is_cloaked: bool = False
        self._is_lunging: bool = False
        self._lunge_timer: float = 0.0
        self._lunge_duration: float = 0.3
        self._lunge_speed: float = 200.0
        self._lunge_dir: int = 1
        self._lunge_damage: float = 1.0
        self._lunge_has_hit: bool = False
        self._retreat_timer: float = 0.0
        self._retreat_duration: float = 2.0
        self._in_retreat: bool = False
        self._cloak_alpha: int = 80
        self._approach_range: float = 40.0

        # Cached surfaces
        self._cloak_fade_surf: pygame.Surface | None = None

        self._load_zone_sprites(zone, 12, 12)

    def _patrol_behavior(self, dt: float) -> None:
        speed = 120.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 64:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()

        if self._in_retreat:
            self._retreat_timer -= dt
            if not self._is_cloaked:
                self._is_cloaked = True
            self.position.x -= self.facing_direction * 120.0 * dt
            if self._retreat_timer <= 0:
                self._in_retreat = False
                self._is_cloaked = False
            return

        if self._is_lunging:
            self._lunge_timer -= dt
            self.position.x += self._lunge_dir * self._lunge_speed * dt
            if self._lunge_timer <= 0:
                self._is_lunging = False
                self._in_retreat = True
                self._retreat_timer = self._retreat_duration
            return

        if self._player_ref is None:
            return

        dx = self._player_ref.centerx - self.rect.centerx
        dist = abs(dx)

        if dist <= self._approach_range:
            if self._is_cloaked:
                self._is_cloaked = False
            self._is_lunging = True
            self._lunge_timer = self._lunge_duration
            self._lunge_dir = 1 if dx >= 0 else -1
            self._lunge_has_hit = False
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="assassin_lunge", rect=self.rect)
            return

        if not self._is_cloaked:
            self._is_cloaked = True

        flank_dir = 1 if dx < 0 else -1
        self.position.x += flank_dir * 80.0 * dt

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
            if frames:
                self._sprite_frames[key] = frames
            else:
                placeholder = []
                col = (44, 44, 58)
                for _ in range(4):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    # daga extendida para attack
                    pygame.draw.ellipse(surf, tuple(min(255, c + 30) for c in col), (1, 1, fw - 2, fh - 2))
                    pygame.draw.line(surf, (180, 180, 190), (fw // 2, fh // 2), (fw - 1, fh // 2))
                    pygame.draw.polygon(surf, (220, 220, 230), [(fw - 1, fh // 2 - 1), (fw - 1, fh // 2 + 1), (fw - 3, fh // 2)])
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder

    def _get_animation_key(self) -> str:
        if self._is_lunging:
            return "attack"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        # AUD-108: era el cuerpo (16 × 24) desplazado 2 px en ambos ejes.
        return self.caja_ajustada(margen_x=1, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def _check_player_contact(self, player: Player) -> None:
        """AUD-149 — este método se llamaba `check_player_contact`, sin guion.

        El motor llama al PRIVADO —`StageScene` hace
        `enemy._check_player_contact(player)`—, y el público es sólo un alias
        obsoleto que `EnemyBase` conserva para las entregas de estudiantes.
        Al sobreescribir el público, esta lógica **nunca se ejecutaba en el
        juego**: la clase estaba completa, probada por su nombre, y el camino
        real pasaba de largo por la implementación de la base.

        Es el mismo patrón que el sistema de diálogo (AUD-127) y el reloj
        musical (AUD-139), con un agravante: aquí no faltaba un dato, sino que
        sobraba un guion bajo.
        """
        if self._is_cloaked and not self._is_lunging:
            return
        if self._is_lunging and not self._lunge_has_hit:
            player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
            if self.hurtbox.colliderect(player_hurtbox):
                player.apply_damage(self._lunge_damage, (self.position.x, self.position.y))
                self._lunge_has_hit = True
        super()._check_player_contact(player)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if not self.is_visible or not self.is_alive:
            return
        if self._is_cloaked:
            screen_x = int(self.position.x - camera_offset.x)
            screen_y = int(self.position.y - camera_offset.y)
            if self._cloak_fade_surf is None:
                self._cloak_fade_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            fade = self._cloak_fade_surf
            fade.fill((0, 0, 0, 0))
            fade.set_alpha(255 - self._cloak_alpha)
            fade.fill((30, 40, 60))
            surface.blit(fade, (screen_x, screen_y))
