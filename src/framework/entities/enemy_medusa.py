"""
Module: enemy_medusa
System: framework.entities
Academic Unit: Unit III (Curve Mathematics — herencia de EnemyFlying)
Description: AUD-575 — la medusa del 4-1b. Deriva en la columna de
agua de la esclusa rota (S4) y el pozo del drenaje (S5).

Presencia, como todo el ecosistema de la mina (regla del nivel: nada
daña). `EnemyFlying` ya resuelve "flotar sin gravedad" —el mismo motor
que usa el pez abismal para nadar—, así que esta clase sólo ajusta el
patrón de deriva: vaivén sinusoidal lento, sin persecución, sin daño y
sin empujón.

Por qué se distingue del pez abismal
=====================================
El pez es la amenaza del nivel: silueta oscura con un punto de luz que
pulsa, aparece de la nada y persigue. La medusa es plancton: campana
translúcida pálida, sin brillo propio, que deriva y no mira a nadie.
Si las dos criaturas compartieran paleta o lenguaje de movimiento, el
jugador no sabría cuál persigue y cuál no — y el terror del 2-2 depende
de que la amenaza sea siempre *una*, reconocible.
"""
from __future__ import annotations

import logging

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_flying import EnemyFlying

logger = logging.getLogger(__name__)

SPRITE_PATH = settings.ASSETS_DIR / "sprites" / "enemies" / "stage4_1b" / "enemy_medusa.png"


class EnemyMedusa(EnemyFlying):
    """La medusa de la mina: deriva en vaivén, no daña ni se deja
    dañar. `Stage4_1B` la instancia en los puntos de `FAUNA` del
    trazado — esta clase sólo sabe flotar."""

    SPRITE_ANCHO = 16
    SPRITE_ALTO = 14

    def __init__(self, spawn_position: pygame.Vector2, **kwargs) -> None:
        super().__init__(
            spawn_position=spawn_position,
            flight_mode="sine",
            flight_speed=26.0,
            sine_amplitude=14.0,
            sine_frequency=0.4,
            max_health=1.0,
            damage_on_contact=0.0,
        )
        self.contact_knockback = 0.0
        self.rect.width = 40
        self.rect.height = 36
        self._sprite_fw = self.SPRITE_ANCHO
        self._sprite_fh = self.SPRITE_ALTO

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        self._sprite_fw = self.SPRITE_ANCHO
        self._sprite_fh = self.SPRITE_ALTO
        fw = self.SPRITE_ANCHO
        fh = self.SPRITE_ALTO
        zone_key = f"zone{zone}" if zone > 0 else "zone4"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None) or "Medusa"
        sid = str(species_id).lower()
        for key, expected in [("walk", 4), ("hurt", 3), ("die", 5), ("fly", 4)]:
            frames: list[pygame.Surface] = []
            for cand in [
                base / f"enemy_{sid}_{key}.png",
                base / f"enemy_{sid}_walk.png" if key == "walk" else None,
                settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{species_id}_{key}.png",
                SPRITE_PATH if key in ("fly", "walk") else None,
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
            if frames:
                self._sprite_frames[key] = frames
                if key == "walk":
                    # compatibilidad: la medusa usa fly como anim_key, duplicar
                    self._sprite_frames["fly"] = frames
            else:
                # placeholder translúcido para medusa
                placeholder = []
                col = (96, 140, 148)
                if key == "hurt":
                    col = (190, 120, 140)
                elif key == "die":
                    col = (72, 106, 112)
                for _ in range(expected):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((0, 0, 0, 0))
                    pygame.draw.ellipse(surf, (*col, 190), (2, 1, fw - 4, fh - 4))
                    pygame.draw.ellipse(surf, (255, 255, 255, 40), (2, 1, fw - 4, fh - 4), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder
                if key == "walk":
                    self._sprite_frames["fly"] = placeholder

    def _get_animation_key(self) -> str:
        return "fly"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=2)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def apply_hit(self, damage: float, source_position: tuple[float, float],
                  canal: str | None = None) -> None:
        """No-op deliberado — ver el docstring del módulo: presencia."""
        return