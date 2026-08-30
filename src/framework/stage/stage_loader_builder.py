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
        # Guarda todo para que StageData lo reparta por dominio (física/atmósfera/progresión)
        # vía su __init__ que ya hace el dispatch. Así el Builder no duplica la lógica
        # de “qué campo va en qué sub-objeto” y sigue siendo testeable por dominio.
        if not hasattr(self, "_extra"):
            self._extra: dict[str, Any] = {}
        self._extra.update(kw)
        # También setea directamente en los sub-objetos para que el builder sea
        # inspeccionable antes de build() (útil en tests de dominio).
        for k, v in kw.items():
            if hasattr(self.physics, k):
                setattr(self.physics, k, v)
            elif hasattr(self.atmosphere, k):
                setattr(self.atmosphere, k, v)
            elif hasattr(self.progression, k):
                setattr(self.progression, k, v)
        return self

    def build(self) -> StageData:
        extra = getattr(self, "_extra", {})
        return StageData(
            map_layer=self.map_layer,
            map_pixel_size=self.map_pixel_size,
            physics=self.physics,
            atmosphere=self.atmosphere,
            progression=self.progression,
            **extra,
        )
