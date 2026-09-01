from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.framework.entities.player import Player

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.base_entity import BaseEntity
from src.framework.entities.enemy_base import EnemyBase, EnemyState

logger = logging.getLogger(__name__)


class HomingOrb(BaseEntity):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: float,
        lifetime: float = 3.0,
    ) -> None:
        super().__init__(spawn_position)
        self.velocity: pygame.Vector2 = velocity
        self.damage: float = damage
        self._lifetime: float = lifetime
        self._elapsed: float = 0.0
        self._expired: bool = False

        self.rect = pygame.Rect(
            int(self.position.x) - 6,
            int(self.position.y) - 6,
            12, 12
        )
        self.layer = 5
        self._player_ref: pygame.Rect | None = None

    def set_player_ref(self, player_rect: pygame.Rect) -> None:
        self._player_ref = player_rect

    def update(self, dt: float) -> None:
        if self._expired:
            self.is_active = False
            return

        self._elapsed += dt
        if self._elapsed >= self._lifetime:
            self._expired = True
            self.is_active = False
            return

        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.position.x
            dy = self._player_ref.centery - self.position.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 1:
                self.velocity.x += (dx / dist) * 60.0 * dt
                self.velocity.y += (dy / dist) * 60.0 * dt
                speed = math.sqrt(self.velocity.x ** 2 + self.velocity.y ** 2)
                if speed > 120.0:
                    self.velocity.x = (self.velocity.x / speed) * 120.0
                    self.velocity.y = (self.velocity.y / speed) * 120.0

        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.rect.center = (int(self.position.x), int(self.position.y))

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.is_visible or self._expired:
            return
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        pulse = abs(math.sin(self._elapsed * 6.0))
        radius = 6 + int(pulse * 3)
        pygame.draw.circle(surface, (180, 80, 255), (screen_x, screen_y), radius)
        pygame.draw.circle(surface, (220, 180, 255), (screen_x, screen_y), radius, 1)

    def on_collision(self) -> None:
        self._expired = True
        self.is_active = False


class EnemyCaster(EnemyBase):

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        max_health: float = 2.0,
        damage_on_contact: float = 0.25,
        zone: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            max_health=max_health,
            damage_on_contact=damage_on_contact,
            detection_range_x=250.0,
            detection_range_y=80.0,
            hurt_duration=0.3,
            invincibility_duration=0.35,
        )

        self._patrol_origin: pygame.Vector2 = pygame.Vector2(spawn_position)
        # AUD-455: el y del TMX es la esquina superior (semántica nativa de
        # Tiled); el descuento de altura hacía flotar a todos los enemigos de
        # suelo. Ver `enemy_walker` para el porqué completo.
        self.rect.width = 40
        self.rect.height = 56

        self._shoot_cooldown: float = 0.0
        self._fire_rate: float = 2.5
        self._orb_speed: float = 120.0
        self._orb_damage: float = 0.75
        self._active_orbs: list[HomingOrb] = []
        self._max_orbs: int = 5
        self._collision_rects: list[pygame.Rect] = []
        self._telegraph_duration = 0.3
        self._ideal_distance: float = 150.0

        # Cached surfaces
        self._charge_surf: pygame.Surface | None = None

        self._load_zone_sprites(zone, 14, 14)

    def _patrol_behavior(self, dt: float) -> None:
        speed = 15.0
        self.position.x += self.facing_direction * speed * dt
        distance = abs(self.position.x - self._patrol_origin.x)
        if distance >= 48:
            self.facing_direction *= -1

    def _alert_behavior(self, dt: float) -> None:
        self._face_player()
        if self._player_ref is not None:
            dx = self._player_ref.centerx - self.rect.centerx
            dist = abs(dx)
            if dist < self._ideal_distance - 20:
                self.position.x -= self.facing_direction * 30.0 * dt
            elif dist > self._ideal_distance + 20:
                self.position.x += self.facing_direction * 30.0 * dt
        self._shoot_cooldown -= dt
        if self._shoot_cooldown <= 0:
            self._telegraph_timer = self._telegraph_duration
            self.state = EnemyState.TELEGRAPHING
            self._event_bus.emit(Events.BOSS_ATTACK, pattern="caster_charge", rect=self.rect)

    def _firing_behavior(self, dt: float) -> None:
        self._face_player()
        self._fire_orb()
        self._shoot_cooldown = self._fire_rate
        self.state = EnemyState.ALERT

    def _fire_orb(self) -> bool:
        if len(self._active_orbs) >= self._max_orbs:
            return False
        if self._player_ref is None:
            return False

        dx = self._player_ref.centerx - self.rect.centerx
        dy = self._player_ref.centery - self.rect.centery
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            dist = 1

        vel = pygame.Vector2(
            (dx / dist) * self._orb_speed,
            (dy / dist) * self._orb_speed,
        )

        orb = HomingOrb(
            spawn_position=pygame.Vector2(self.rect.centerx, self.rect.centery),
            velocity=vel,
            damage=self._orb_damage,
            lifetime=3.0,
        )
        orb.set_player_ref(self._player_ref)
        self._active_orbs.append(orb)
        # AUD-489 — el conjuro suena desde el hechicero, no desde la cámara.
        self._event_bus.emit(Events.SFX_PROJECTILE_FIRE, pos=(self.rect.centerx, self.rect.centery))
        return True

    def _post_update(self, dt: float) -> None:
        for o in self._active_orbs:
            o.update(dt)
            o.set_player_ref(self._player_ref)
            if self._collision_rects:
                for rect in self._collision_rects:
                    if o.rect.colliderect(rect):
                        o.on_collision()
                        break
        self._active_orbs = [o for o in self._active_orbs if o.is_active]

    def set_collision_rects(self, rects: list[pygame.Rect], one_way: list[pygame.Rect] | None = None) -> None:
        self._collision_rects = rects

    def _check_player_contact(self, player: Player) -> None:
        """AUD-149 — se llamaba `check_player_contact`, sin guion bajo.

        El motor llama al privado; el público es un alias obsoleto que
        `EnemyBase` conserva para las entregas. Al sobreescribir el público,
        esta lógica no se ejecutaba nunca en el juego.
        """
        super()._check_player_contact(player)
        player_hurtbox = player.hurtbox if hasattr(player, "hurtbox") else player.rect
        for o in list(self._active_orbs):
            if o.is_active and o.rect.colliderect(player_hurtbox):
                if getattr(player, "_parry_active", False) and getattr(player, "_parry_window", 0) > 0:
                    o._expired = True
                    o.is_active = False
                    player._parry_success = True
                    player._parry_active = False
                    player._parry_window = 0.0
                    self._event_bus.emit(Events.VFX_PARRY, pos=(o.position.x, o.position.y))
                    # AUD-206: parar el orbe también interrumpe al lanzador.
                    # El porqué, en `enemy_archer._check_player_contact`.
                    self.stun(self.PARRY_STUN_DURATION)
                else:
                    player.apply_damage(o.damage, (self.position.x, self.position.y))
                    o.on_collision()

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
            if frames:
                self._sprite_frames[key] = frames
            else:
                placeholder = []
                col = (78, 118, 84)
                for _ in range(4):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    pygame.draw.circle(surf, (80, 220, 255), (fw // 2 + 3, fh // 3), 2)
                    pygame.draw.circle(surf, (255, 255, 255), (fw // 2 + 3, fh // 3), 1)
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder

    def _get_animation_key(self) -> str:
        # cast se muestra durante TELEGRAPHING/FIRING si hay sheet
        if self.state in (EnemyState.TELEGRAPHING, EnemyState.FIRING) and "cast" in self._sprite_frames:
            return "cast"
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        # AUD-108: mismo defecto que el resto del bestiario.
        return self.caja_ajustada(margen_x=1, margen_y=2)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        super().draw(surface, camera_offset)
        if not self.is_visible or not self.is_alive:
            return
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)

        if self.state == EnemyState.TELEGRAPHING:
            radius = 16
            center_x = screen_x + self.rect.width // 2
            center_y = screen_y + self.rect.height // 2
            if self._charge_surf is None:
                self._charge_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            charge_surf = self._charge_surf
            charge_surf.fill((0, 0, 0, 0))
            alpha = int(200 * (1.0 - self._telegraph_timer / max(self._telegraph_duration, 0.001)))
            pygame.draw.circle(charge_surf, (160, 60, 255, alpha), (radius, radius), radius)
            pygame.draw.circle(charge_surf, (200, 140, 255, min(255, alpha + 40)), (radius, radius), radius, 2)
            surface.blit(charge_surf, (center_x - radius, center_y - radius))

        self._active_orbs = [o for o in self._active_orbs if o.is_active]
        for o in self._active_orbs:
            o.draw(surface, camera_offset)
