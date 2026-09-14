"""
Module: enemy_cangrejo
System: framework.entities
Academic Unit: Unit II (Vectors, Collision) — patrón del caminante
Description: AUD-575 — el cangrejo de la mina inundada del 4-1b.

La fauna del nivel es presencia, nunca combate (regla del 4-1b:
*nada daña* — la mina estresa por el espacio cerrado y la persecución,
no por enemigos que quitan vida). Este cangrejo patrulla el lecho y el
anden seco del patio de carga (S3) exactamente como un `EnemyWalker`
patrulla el suelo: detecta bordes, invierte, se pega al terreno. Sólo
que `damage_on_contact=0.0` y `contact_knockback=0.0`: lo atraviesa el
jugador sin daño y sin empujón —es un *habitante* de la mina, no una
amenaza—, pero ocupa el camino y obliga a rodearlo o a esperar, que es
el "obstáculo" que pide el guion sin romper la regla del nivel.

Por qué no carga ni entra en alerta como el Walker genérico
============================================================
`EnemyWalker` trae embestida (`_charge_timer`, `_charge_speed`,
`_alert_behavior`) y daño de contacto. Un cangrejo que se abalanza a
1.5 de daño sería un enemigo de combate — exactamente lo que la regla
prohíbe. Por eso `_alert_behavior` se sobreescribe: al detectar al
jugador se limita a mirarlo y patrullar algo más deprisa (la misma
reacción de una criatura que no quiere líos), y nunca cambia su daño.
"""
from __future__ import annotations

import logging

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_walker import EnemyWalker

logger = logging.getLogger(__name__)

SPRITE_PATH = settings.ASSETS_DIR / "sprites" / "enemies" / "stage4_1b" / "enemy_cangrejo.png"


class EnemyCangrejo(EnemyWalker):
    """El cangrejo de la mina: patrulla, se pega al suelo, no daña ni
    se deja dañar. `Stage4_1B` lo instancia en los puntos de `FAUNA` del
    trazado — esta clase sólo sabe caminar."""

    SPRITE_ANCHO = 20
    SPRITE_ALTO = 14

    def __init__(
        self,
        spawn_position: pygame.Vector2,
        patrol_length: float = 80.0,
        facing: str = "left",
        patrol_speed: float = 22.0,
        zone: int = 4,
        **kwargs,
    ) -> None:
        super().__init__(
            spawn_position=spawn_position,
            patrol_length=patrol_length,
            facing=facing,
            patrol_speed=patrol_speed,
            alert_speed=patrol_speed * 1.6,
            damage_on_contact=0.0,
            max_health=1.0,
            zone=zone,
        )
        # La regla del nivel: nada daña. Ni siquiera el empujón que
        # `Player.apply_damage` aplica a un contacto de daño cero — ese
        # empujón mete al jugador en `HurtState` (más i-frames), que es
        # una agresión de facto contra un nivel "de presencia".
        self.contact_knockback = 0.0
        # El cangrejo es bajo: su caja no es la de un caminante humanoide.
        self.rect.width = 44
        self.rect.height = 32
        # Asegurar tamaño correcto tras el super que cargó 16×12
        self._sprite_fw = self.SPRITE_ANCHO
        self._sprite_fh = self.SPRITE_ALTO

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        # AUD-XXX — usa zone4/enemy_{sid}_*.png con w,h del bestiary en lugar de stage4_1b fijo
        # Mantener compatibilidad con el archivo legacy stage4_1b como fallback.
        self._sprite_fw = self.SPRITE_ANCHO
        self._sprite_fh = self.SPRITE_ALTO
        fw = self.SPRITE_ANCHO
        fh = self.SPRITE_ALTO
        zone_key = f"zone{zone}" if zone > 0 else "zone4"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None) or "Cangrejo"
        sid = str(species_id).lower()
        for key, expected in [("walk", 4), ("hurt", 3), ("die", 5)]:
            frames: list[pygame.Surface] = []
            # 1) zona/species con w,h correctos
            for cand in [
                base / f"enemy_{sid}_{key}.png",
                settings.ASSETS_DIR / "sprites" / "enemies" / "species" / f"{species_id}_{key}.png",
                SPRITE_PATH if key == "walk" else None,
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
            else:
                # placeholder para que walk/hurt/die nunca queden en rojo (aunque no se usan, evita validate_assets)
                placeholder = []
                col = (150, 86, 52)
                if key == "hurt":
                    col = (190, 60, 50)
                elif key == "die":
                    col = (80, 30, 30)
                for _ in range(expected):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    pygame.draw.ellipse(surf, tuple(min(255, c + 30) for c in col), (2, 2, fw - 2, fh - 2))
                    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder
        # Compatibilidad: walk también en clave legacy sin sufijo para Stage4_1B que hacía
        # Stage4_1B: self._sprite_frames["walk"] ya está; el caller puede usar walk.

    def _alert_behavior(self, dt: float) -> None:
        """No embiste: mira al jugador y aprieta el paso patrullando. Un
        cangrejo de mina no es un perro guardián; su reacción al intruso
        es moverse más deprisa, no atacar — y así el nivel mantiene la
        regla de que nada daña sin que el animal parezca indiferente."""
        self._face_player()
        self._patrol_behavior(dt)

    def _get_animation_key(self) -> str:
        return "walk"

    def _build_hurtbox(self) -> pygame.Rect:
        return self.caja_ajustada(margen_x=2, margen_y=1)

    def _build_hitbox(self) -> pygame.Rect:
        return self._build_hurtbox()

    def apply_hit(self, damage: float, source_position: tuple[float, float],
                  canal: str | None = None) -> None:
        """No-op deliberado — ver el docstring del módulo: presencia."""
        return