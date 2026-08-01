"""
Module: fog_of_war
System: framework.vfx
Academic Unit: N/A
Description: Fog of war overlay — hides unexplored areas with
editable holes revealed by player/enemy positions.

AUD-111 — enchufado
===================
Este módulo estuvo escrito, documentado (`docs/46_FOG_OF_WAR.md`) y probado en
aislamiento durante meses, y **ninguna escena lo instanciaba**: un jugador no
podía llegar a él por ningún camino. Las pruebas lo mantenían verde y eso
escondía que nadie lo usaba — confirmaban que la pieza funciona, no que
estuviera enchufada.

Ahora lo enciende `StageScene` cuando el TMX declara la propiedad de mapa
`fog_of_war` con un radio en píxeles. Se dibuja **entre el mundo y la
iluminación**: después de la luz taparía los focos que definen lo que se ve, y
antes del mundo no taparía nada.
"""
from __future__ import annotations

import pygame

from src.engine.core import settings


class FogOfWar:
    """Black overlay with alpha holes around revealed positions."""

    def __init__(self, width: int = settings.INTERNAL_WIDTH, height: int = settings.INTERNAL_HEIGHT,
                 radius: int = 80, hardness: float = 0.6) -> None:
        self._width = width
        self._height = height
        self._radius = radius
        self._hardness = hardness
        self._overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self._revealed: set[tuple[int, int]] = set()
        self._hole_mask = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self._hole_mask.fill((0, 0, 0, 0))
        pygame.draw.circle(self._hole_mask, (0, 0, 0, 255), (radius, radius), radius)

    def clear(self) -> None:
        self._revealed.clear()

    def reveal(self, x: float, y: float) -> None:
        self._revealed.add((int(x), int(y)))

    def reveal_all(self, points: list[tuple[float, float]]) -> None:
        for x, y in points:
            self._revealed.add((int(x), int(y)))

    def update(self, dt: float) -> None:
        """No-op placeholder for future fading."""

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        self._overlay.fill((0, 0, 0, 220))
        for x, y in self._revealed:
            sx = x - int(offset.x)
            sy = y - int(offset.y)
            self._overlay.blit(self._hole_mask,
                               (sx - self._radius, sy - self._radius),
                               special_flags=pygame.BLEND_RGBA_SUB)
        surface.blit(self._overlay, (0, 0))
