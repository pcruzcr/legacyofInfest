"""
StageLoaderBuilder — Builder para StageLoader/StageData.

StageLoader._build_stage_data era 134 líneas construyendo 50 campos a mano.
El Builder permite construir StageData por pasos testeables y deja
StageLoader como Director que orquesta, no que construye.

Patrón: Builder + Director
"""
from __future__ import annotations

from typing import Any

from src.framework.stage.stage_data import StageAtmosphere, StageData, StagePhysics, StageProgression


class StageDataBuilder:
    """Builder para StageData por dominios (física, atmósfera, progresión)."""

    def __init__(self) -> None:
        self.physics = StagePhysics()
        self.atmosphere = StageAtmosphere()
        self.progression = StageProgression()
        self.map_layer: Any = None
        self.map_pixel_size: tuple[int, int] = (0, 0)

    def with_map(self, layer: Any, size: tuple[int, int]) -> StageDataBuilder:
        self.map_layer = layer
        self.map_pixel_size = size
        return self

    def with_physics(self, **kw: Any) -> StageDataBuilder:
        for k, v in kw.items():
            if hasattr(self.physics, k):
                setattr(self.physics, k, v)
        return self

    def build(self) -> StageData:
        return StageData(
            map_layer=self.map_layer,
            map_pixel_size=self.map_pixel_size,
            physics=self.physics,
            atmosphere=self.atmosphere,
            progression=self.progression,
        )
