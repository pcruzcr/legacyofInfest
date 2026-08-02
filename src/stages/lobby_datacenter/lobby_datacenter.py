"""
Module: stage_template
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

STUDENT INSTRUCTIONS:
1. Copy this entire folder to src/stages/<your_assignment_id>/
2. Rename this file to <your_assignment_id>.py
3. Rename stage_template.tmx to <your_assignment_id>.tmx
4. Update TMX_PATH and class attributes (STAGE_ID, STAGE_NAME, ZONE)
5. Fill in every # TODO(student) marker.
6. Do NOT modify StageScene or any engine/framework code.

Test with:
   python main.py --stage <your_assignment_id>
"""
from __future__ import annotations
from src.stages.lobby_datacenter.security_camera import SecurityCamera
from src.stages.lobby_datacenter.alarm_light import AlarmLight

import pygame
from pathlib import Path
from typing import TYPE_CHECKING

from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class LobbyDatacenter(StageScene):
    """El Lobby — Zona 2 (El Datacenter). Recepción entre la entrada/antenas
    (César) y las oficinas (Saúl). Demuestra: vectores (Unidad II),
    curvas (Unidad III), color/transparencia (Unidad V)."""

    STAGE_ID: str = "lobby_datacenter"
    STAGE_NAME: str = "EL LOBBY"
    ZONE: int = 2

    TMX_PATH = "assets/maps/lobby_datacenter/lobby_datacenter.tmx"

    # AUD-157 — había dos `__init__` idénticos seguidos. El primero no corría
    # nunca: Python se queda con el último de la clase. No cambiaba nada
    # —eran iguales— pero es la clase de descuido que el día que se editen por
    # separado produce un fallo imposible de leer.
    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is not None and hasattr(self, "_camera_sentry"):
            self._camera_sentry.update(dt, self._player)
        if hasattr(self, "_alarm_light"):
            self._alarm_light.update(dt)
    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if hasattr(self, "_camera_sentry"):
            self._camera_sentry.draw(surface, self._camera.offset)
        if hasattr(self, "_alarm_light"):
            self._alarm_light.draw(surface, self._camera.offset)
    # ── Optional lifecycle hooks ────────────────────────────────────
    # Override any of these to add custom behavior:

    def on_stage_start(self) -> None:
        """Called after the stage loads and setup completes."""
        self._camera_sentry = SecurityCamera(pygame.Vector2(300, 100))
        self._alarm_light = AlarmLight(pygame.Vector2(450, 170))
    def on_player_landed(self) -> None:
        """Called when the player first touches ground after being airborne.
        TODO(student): e.g., trigger a message, activate a hazard."""
        pass

    def on_enemy_died(self, enemy) -> None:
        """Called when an enemy dies.
        TODO(student): e.g., unlock a door, spawn a pickup."""
        pass

    def on_next_trigger_entered(self) -> None:
        """Called when the player touches NextTrigger.
        TODO(student): e.g., play a custom cutscene before stage ends."""
        pass

    def on_debug_toggle(self, enabled: bool) -> None:
        """Called when F1 is pressed to toggle debug overlay.
        TODO(student): e.g., show/hide additional debug info."""
        pass
