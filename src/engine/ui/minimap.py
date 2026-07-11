from __future__ import annotations
from typing import Sequence

import pygame

from src.engine.core import settings


class Minimap:
    """Minimap overlay showing explored rooms, player position, and enemies."""

    def __init__(self) -> None:
        self._map_size: tuple[int, int] = (0, 0)
        self._explored_rects: list[pygame.Rect] = []
        self._player_pos: tuple[float, float] = (0.0, 0.0)
        self._player_dir: int = 1
        self._enemy_positions: Sequence[tuple[float, float]] = []
        self._boss_positions: Sequence[tuple[float, float]] = []
        self._checkpoint_positions: Sequence[tuple[float, float]] = []
        self._activated_checkpoints: set[int] = set()
        self._visible: bool = True

        # Minimap dimensions
        self._minimap_w: int = 80
        self._minimap_h: int = 56
        self._minimap_x: int = settings.INTERNAL_WIDTH - self._minimap_w - 4
        self._minimap_y: int = 4

        # Pixel per world unit scaling - auto-calculated
        self._scale: float = 1.0

        self._bg_color: tuple[int, int, int] = (10, 10, 20)
        self._border_color: tuple[int, int, int] = (60, 60, 80)
        self._explored_color: tuple[int, int, int] = (30, 40, 60)
        self._player_color: tuple[int, int, int] = (100, 220, 255)
        self._enemy_color: tuple[int, int, int] = (255, 80, 80)
        self._boss_color: tuple[int, int, int] = (255, 50, 50)
        self._checkpoint_color: tuple[int, int, int] = (255, 220, 80)
        self._fog_color: tuple[int, int, int] = (5, 5, 15)

        self._fow_surf: pygame.Surface | None = None

    def set_map_size(self, world_w: int, world_h: int) -> None:
        self._map_size = (world_w, world_h)
        sx = self._minimap_w / max(world_w, 1)
        sy = self._minimap_h / max(world_h, 1)
        self._scale = min(sx, sy, 1.0)

    def explore_rect(self, rect: pygame.Rect) -> None:
        for er in self._explored_rects:
            if er.contains(rect):
                return
        self._explored_rects.append(rect.copy())

    def update(
        self,
        player_pos: tuple[float, float],
        player_dir: int,
        enemy_positions: Sequence[tuple[float, float]],
        boss_positions: Sequence[tuple[float, float]],
        checkpoint_positions: Sequence[tuple[float, float]],
        activated_checkpoints: set[int],
    ) -> None:
        self._player_pos = player_pos
        self._player_dir = player_dir
        self._enemy_positions = enemy_positions
        self._boss_positions = boss_positions
        self._checkpoint_positions = checkpoint_positions
        self._activated_checkpoints = activated_checkpoints

    def _world_to_minimap(self, wx: float, wy: float) -> tuple[int, int]:
        mx = int(self._minimap_x + wx * self._scale)
        my = int(self._minimap_y + wy * self._scale)
        return mx, my

    def draw(self, surface: pygame.Surface) -> None:
        if not self._visible:
            return

        # Background
        bg = pygame.Surface((self._minimap_w, self._minimap_h), pygame.SRCALPHA)
        bg.fill((*self._bg_color, 200))
        surface.blit(bg, (self._minimap_x, self._minimap_y))

        # Border
        pygame.draw.rect(
            surface, self._border_color,
            (self._minimap_x, self._minimap_y, self._minimap_w, self._minimap_h), 1,
        )

        # Explored areas
        for rect in self._explored_rects:
            rx = int(self._minimap_x + rect.x * self._scale)
            ry = int(self._minimap_y + rect.y * self._scale)
            rw = max(1, int(rect.width * self._scale))
            rh = max(1, int(rect.height * self._scale))
            pygame.draw.rect(surface, self._explored_color, (rx, ry, rw, rh))

        # Checkpoints
        for i, (cx, cy) in enumerate(self._checkpoint_positions):
            color = self._checkpoint_color if i in self._activated_checkpoints else (80, 70, 40)
            mx, my = self._world_to_minimap(cx, cy)
            pygame.draw.rect(surface, color, (mx - 1, my - 1, 3, 3))

        # Enemies
        for ex, ey in self._enemy_positions:
            mx, my = self._world_to_minimap(ex, ey)
            pygame.draw.rect(surface, self._enemy_color, (mx - 1, my - 1, 2, 2))

        # Bosses
        for bx, by in self._boss_positions:
            mx, my = self._world_to_minimap(bx, by)
            pygame.draw.rect(surface, self._boss_color, (mx - 2, my - 2, 4, 4))

        # Player arrow
        px, py = self._player_pos
        mx, my = self._world_to_minimap(px, py)
        dir_arrow = self._player_dir
        points = [
            (mx + dir_arrow * 3, my),
            (mx - dir_arrow * 2, my - 2),
            (mx - dir_arrow * 2, my + 2),
        ]
        pygame.draw.polygon(surface, self._player_color, points)
