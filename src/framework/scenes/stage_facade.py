"""
StageFacade — Fachada estructural para StageScene.

StageScene expone 40+ atributos (_player, _camera, _hud, _collision, etc.)
y 15 mixins. La Fachada ofrece una vista simplificada para clientes que
sólo necesitan “escenario jugable” sin conocer la red interna de VFX,
ECS y audio. También actúa como Mediator ligero entre subsistemas que
hoy se llaman vía self (SquadBrain ↔ CombatManager).

Patrón: Facade + Mediator
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from src.framework.entities.player import Player
    from src.framework.stage.camera import Camera
    from src.framework.stage.stage_loader import StageData


class StageFacade:
    """Fachada de lectura para el escenario jugable."""

    def __init__(self, scene: Any) -> None:
        self._scene = scene

    @property
    def player(self) -> Player | None:
        return getattr(self._scene, "_player", None)

    @property
    def camera(self) -> Camera | None:
        return getattr(self._scene, "_camera", None)

    @property
    def stage_data(self) -> StageData | None:
        return getattr(self._scene, "_stage_data", None)

    @property
    def is_complete(self) -> bool:
        return bool(getattr(self._scene, "_stage_complete", False))

    @property
    def is_paused(self) -> bool:
        return bool(getattr(self._scene, "_paused", False))

    def world_to_screen(self, world_pos: pygame.Vector2) -> pygame.Vector2:
        cam = self.camera
        if cam is None:
            return world_pos
        return cam.world_to_screen(world_pos)

    def request_pause(self) -> None:
        if hasattr(self._scene, "_paused"):
            self._scene._paused = not self._scene._paused
            if hasattr(self._scene, "_set_paused_side_effects"):
                self._scene._set_paused_side_effects(self._scene._paused)
