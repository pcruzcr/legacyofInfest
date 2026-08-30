"""
Stage Pokemon Cenital — ejemplo monster-tamer 100% cenital.

Vista cenital estilo Pokemon: hierba alta con encuentros aleatorios,
captura con Recogible (Pokeball), y PC (Cofre) para guardar.
Usa solo sistemas existentes: vista=cenital, Efectos, Inventory, Dialogue.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene

# Reusa enemigos existentes como "monstruos salvajes" — sin IP
# WalkerInsect = planta, FlyingBoa = volador, ShooterSerpienteArbol = fuego
MONSTRUOS_SALVAJES = ["WalkerInsect", "FlyingBoa", "ShooterSerpienteArbol"]


class StagePokemonCenital(StageScene):
    """Escenario cenital demo — hierba alta + captura."""

    STAGE_ID = "stage_pokemon_cenital"
    STAGE_NAME = "BOSQUE MONSTRUOS — CENITAL"
    TMX_PATH = settings.ASSETS_DIR / "maps/stage_pokemon_cenital/stage_pokemon_cenital.tmx"
    ZONE = 1

    def __init__(self, context) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        self._encuentros = 0
        self._capturas = 0

    def on_stage_start(self) -> None:
        super().on_stage_start()
        # Asegura 5 Pokeballs iniciales si el inventario está vacío
        try:
            from src.engine.core.inventory import get_inventory
            inv = get_inventory()
            if inv.count("pokeball") == 0:
                inv.collect("pokeball", 5)
        except Exception:
            pass
        # Mensaje tutorial
        try:
            self.context.event_bus.emit(
                "SHOW_MESSAGE",
                text="¡Hierba alta! Entra y pulsa Z para capturar. X: PC",
                duration=6.0,
            )
        except Exception:
            pass

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        # Hierba alta = HazardZone rect; si player dentro y random, encuentro
        import random
        for hz in self._stage_data.hazard_zones:
            if hz.rect.colliderect(self._player.rect) and random.random() < 0.008:
                self._encuentros += 1
                # Efecto veneno leve al entrar (parálisis hierba)
                try:
                    from src.framework.combate import efectos
                    from src.framework.ecs.components import Efectos
                    # Busca componente Efectos del player
                    if hasattr(self._player, "efectos"):
                        efectos.aplicar(self._player.efectos, "lentitud", duracion=1.5)
                except Exception:
                    pass
                # Sonido
                try:
                    self.context.event_bus.emit("SFX_HAZARD_ZONE", pos=self._player.rect.center)
                    self.context.event_bus.emit("VFX_POISON", pos=self._player.rect.center)
                except Exception:
                    pass
                break

    def on_next_trigger_entered(self) -> None:
        # No NextTrigger en cenital sala — usa PC (Cofre) para guardar
        super().on_next_trigger_entered()

    @property
    def debug_stats(self) -> dict:
        return {"encuentros": self._encuentros, "capturas": self._capturas}
