"""
Module: enemy_pez_abismal
System: framework.entities
Academic Unit: Unit III (Curve Mathematics — herencia de EnemyFlying)
Description: AUD-519 — el pez abismal de 4.1b. Aparece de la nada,
persigue al jugador, y no puede tocarlo ni ser tocado por él.

Por qué hereda de EnemyFlying y no escribe su propio movimiento
==================================================================
"Nadar en aguas abiertas sin gravedad" es exactamente lo que `EnemyFlying`
ya resuelve — su nombre habla de volar, pero el movimiento no sabe nada de
alas: es física libre en 2D con estrategias intercambiables
(`flight_strategies.py`). En particular `ChaseFlight` (AUD-046) ya es
persecución real con inercia — acelera hacia el jugador, no fija la
velocidad — que es exactamente lo que un perseguidor abisal necesita y lo
que habría que reinventar si esta clase partiera de cero.

Por qué es inmune, y por qué no con el temporizador de invencibilidad
=========================================================================
El guion pide una criatura *"que no lo mate ni lo toque"*. La mitad del
jugador hacia la criatura se resuelve con `damage_on_contact=0.0` (mismo
patrón que la fase de contacto de `boss_paburu.py`). La mitad contraria
—que el jugador tampoco pueda hacerle nada— importa por el mismo motivo
que 4-1 declaró **cero enemigos** como regla de oro: una criatura a la que
se puede golpear y hacer retroceder dejaría de sentirse como una amenaza
ineludible y pasaría a ser un enemigo más que derrotar.

`EnemyBase._invincibility_timer` habría sido la vía obvia, pero
mantenerlo siempre positivo also mantiene `_update_invincibility` alter-
nando `_flash_visible` sin parar (parpadeo de "recién golpeado", pensado
para durar medio segundo, no toda la partida) — se leería como un fallo
visual, no como diseño. Por eso `apply_hit` se sobreescribe directamente
pese a que `EnemyBase` lo marca "no sobreescribir": esa nota es correcta
para un enemigo que sí combate y necesita aturdimiento/sonido/HUD
coherentes; este pez no combate en absoluto.
"""
from __future__ import annotations

import logging

import pygame

from src.engine.core import settings
from src.engine.utils.asset_loader import AssetLoader
from src.framework.entities.enemy_flying import EnemyFlying

logger = logging.getLogger(__name__)

SPRITE_PATH = settings.ASSETS_DIR / "sprites" / "enemies" / "stage4_1b" / "enemy_pez_abismal.png"


class EnemyPezAbismal(EnemyFlying):
    """El pez abismal: patrulla a la deriva, persigue al detectar, no
    puede dañar ni ser dañado. `Stage4_1B` controla cuándo aparece y
    desaparece — esta clase sólo sabe nadar."""

    #: Cuánto tarda en acelerar hacia el jugador al alcance máximo del
    #: motor (`ACCELERATION` de `ChaseFlight`) — más lento que un ataque
    #: real, porque el objetivo es que se le vea venir, no que sorprenda
    #: por velocidad.
    VELOCIDAD_DE_NADO = 85.0

    #: AUD-529 — el doble de lo que tenía (14×10). Pedido explícito tras
    #: jugarlo: «debe ser mucho más grande y amenazador». No es el tamaño
    #: que `EnemyFlying` pide para el resto de voladores (14×10, fijo en
    #: `_load_zone_sprites`); `_load_extra_sprites` lo sobreescribe abajo.
    SPRITE_ANCHO = 28
    SPRITE_ALTO = 20

    def __init__(self, spawn_position: pygame.Vector2, event_bus=None, **kwargs) -> None:
        # AUD-XXX — aceptar **kwargs para que el factory pueda pasar
        # max_health/damage_on_contact/flight_mode desde bestiary_registry
        # sin reventar. Los valores de la tabla se ignoran y mandan los de
        # la especie (pez inmune de presencia, no enemigo de combate).
        kwargs.pop("max_health", None)
        kwargs.pop("damage_on_contact", None)
        kwargs.pop("flight_mode", None)
        kwargs.pop("flight_speed", None)
        kwargs.pop("sine_amplitude", None)
        kwargs.pop("sine_frequency", None)
        kwargs.pop("zone", None)
        super().__init__(
            spawn_position=spawn_position,
            flight_mode="sine",
            alert_flight_mode="chase",
            flight_speed=self.VELOCIDAD_DE_NADO,
            sine_amplitude=16.0,
            sine_frequency=0.5,
            max_health=1.0,
            damage_on_contact=0.0,
            event_bus=event_bus,
        )
        # AUD-529 — el rect crece con el sprite (56×32, el doble del
        # 32×16 anterior) para que siga habiendo margen alrededor de una
        # silueta más grande; `_load_extra_sprites` hace lo mismo con
        # `_sprite_fw/_sprite_fh`.
        self.rect.width = 56
        self.rect.height = 32
        # AUD-325 — no pisa suelo: nada en agua abierta, igual que un
        # volador no pisa suelo en aire abierto.
        self._hug_slopes = False
        # AUD-526 — `Stage4_1B._invocar_pez` lo aparece a propósito justo
        # más allá del borde de la cámara (§ arriba: "nunca dentro del
        # cuadro"), que en una pantalla de 800 px de ancho está muy por
        # encima de los 180/96 px de `detection_range_x/y` que
        # `EnemyFlying` fija para todos sus subtipos. Sin ampliarlo el pez
        # nace fuera de su propio rango de detección, nunca entra en
        # ALERT/CHASE —se queda en el vaivén de "sine" cerca de donde
        # apareció, fuera de cuadro— y se retira en silencio sin que el
        # jugador llegue a verlo. El guion pide "aparece de la nada,
        # persigue": `Stage4_1B` ya controla a mano cuándo aparece y
        # cuándo se va, así que no necesita detección genérica — necesita
        # estar alerta desde el fotograma en que existe.
        self.detection_range_x = 2000.0
        self.detection_range_y = 600.0
        self._deaggro_margin = 2000.0

    def _load_extra_sprites(self, zone: int, fw: int, fh: int) -> None:
        """Su propio sprite, su propio tamaño, no los de zona: no existe
        un volador de "zone4" y, de existirlo, sería un halcón o un
        cuervo — no encaja con una criatura abisal.

        AUD-529 — ignora el `fw, fh` que llega (14×10, lo que
        `EnemyFlying` pide para todos sus voladores) y usa
        `SPRITE_ANCHO/SPRITE_ALTO` en su lugar, sobreescribiendo también
        `_sprite_fw/_sprite_fh` — `_load_zone_sprites` ya los dejó en
        14×10 justo antes de llamar aquí, y el desplazamiento de dibujo
        (`ox/oy` en `EnemyBase.draw`) los usa para centrar el sprite en el
        `rect`: sin este ajuste, un sprite más grande que su propio
        tamaño declarado se recorta o se desplaza mal.

        AUD-XXX — ahora carga zone4/enemy_pezabismal_*.png con 28×20 del
        bestiary en lugar de stage4_1b fijo, y asegura walk/hurt/die
        además de fly para que validate_assets y los tests de tamaño pasen
        aunque el pez sea inmune.
        """
        self._sprite_fw = self.SPRITE_ANCHO
        self._sprite_fh = self.SPRITE_ALTO
        fw = self.SPRITE_ANCHO
        fh = self.SPRITE_ALTO
        zone_key = f"zone{zone}" if zone > 0 else "zone4"
        base = settings.ASSETS_DIR / "sprites" / "enemies" / zone_key
        species_id = getattr(self, "species_id", None) or getattr(self, "_species_id", None) or "PezAbismal"
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
                    self._sprite_frames["fly"] = frames
            else:
                placeholder = []
                col = (14, 18, 26)
                if key == "hurt":
                    col = (180, 60, 60)
                elif key == "die":
                    col = (10, 14, 20)
                for _ in range(expected):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.fill((*col, 255))
                    pygame.draw.ellipse(surf, col, (2, fh // 2 - 6, fw - 8, 12))
                    pygame.draw.circle(surf, (120, 220, 210), (4, fh // 2), 2)
                    pygame.draw.circle(surf, (255, 255, 255), (4, fh // 2), 1)
                    placeholder.append(surf)
                self._sprite_frames[key] = placeholder
                if key == "walk":
                    self._sprite_frames["fly"] = placeholder

    def apply_hit(self, damage: float, source_position: tuple[float, float],
                  canal: str | None = None) -> None:
        """No-op deliberado — ver el docstring del módulo."""
        return
