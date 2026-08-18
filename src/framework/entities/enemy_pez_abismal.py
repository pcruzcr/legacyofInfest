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

    def __init__(self, spawn_position: pygame.Vector2, event_bus=None) -> None:
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
        self.rect.width = 32
        self.rect.height = 16
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
        """Su propio sprite, no el de zona: no existe un volador de
        "zone4" y, de existirlo, sería un halcón o un cuervo — no encaja
        con una criatura abisal."""
        try:
            self._sprite_frames["fly"] = AssetLoader.load_sprite_sheet(
                SPRITE_PATH, fw, fh)
        except (pygame.error, FileNotFoundError, PermissionError):
            logger.warning("enemy_pez_abismal: failed to load sprite %s", SPRITE_PATH)

    def apply_hit(self, damage: float, source_position: tuple[float, float],
                  canal: str | None = None) -> None:
        """No-op deliberado — ver el docstring del módulo."""
        return
