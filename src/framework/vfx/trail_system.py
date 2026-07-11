from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.framework.entities.player import Player


class TrailPoint:
    __slots__ = ("x", "y", "alpha", "surface")

    def __init__(self, x: float, y: float, surface: pygame.Surface, alpha: int = 180) -> None:
        self.x = x
        self.y = y
        self.alpha = alpha
        self.surface = surface


class TrailSystem:
    """Captures entity snapshots and draws fading afterimages."""

    def __init__(self) -> None:
        self._points: list[TrailPoint] = []
        self._capture_interval: float = 0.03
        self._timer: float = 0.0

    def capture(self, player: Player) -> None:
        """Capture a snapshot of the player for the trail."""
        if player.rect is None:
            return
        p = TrailPoint(
            player.position.x, player.position.y,
            self._capture_player_surface(player),
        )
        self._points.append(p)

    def _capture_player_surface(self, player: Player) -> pygame.Surface:
        """Render the player silhouette for the trail."""
        w, h = player.rect.width, player.rect.height
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (100, 150, 255, 120) if player._dash_timer > 0 else (200, 200, 255, 80)
        pygame.draw.rect(surf, color, (0, 0, w, h))
        return surf

    def update(self, dt: float) -> None:
        self._timer += dt
        for p in list(self._points):
            p.alpha -= int(400 * dt)
            if p.alpha <= 0:
                self._points.remove(p)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for p in self._points:
            if p.alpha <= 0:
                continue
            sx = int(p.x - offset.x)
            sy = int(p.y - offset.y)
            p.surface.set_alpha(p.alpha)
            surface.blit(p.surface, (sx, sy))

    def clear(self) -> None:
        self._points.clear()
