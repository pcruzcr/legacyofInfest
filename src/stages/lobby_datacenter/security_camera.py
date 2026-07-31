"""
Module: security_camera
Academic Unit: Unit II (Vectors) — vec2_normalize, vec2_dot, vec2_distance
Description: Wall-mounted security camera. Sweeps a fixed arc and detects
the player using explicit vector math: direction (normalize), field-of-view
alignment (dot product), and range (Euclidean distance).
"""
from __future__ import annotations

import math
import pygame

from src.engine.utils.math_utils import vec2_normalize, vec2_dot, vec2_distance


class SecurityCamera:
    """Rotating security camera that lights up red when it 'sees' the player."""

    def __init__(
        self,
        position: pygame.Vector2,
        detection_range: float = 140.0,
        fov_cos_threshold: float = 0.85,
        sweep_speed: float = 1.2,
        sweep_arc: float = 1.0,
    ) -> None:
        self.position = pygame.Vector2(position)
        self.detection_range = detection_range
        self.fov_cos_threshold = fov_cos_threshold
        self.sweep_speed = sweep_speed
        self.sweep_arc = sweep_arc

        self._base_angle = math.pi / 2
        self._t = 0.0
        self.facing = pygame.Vector2(0, 1)
        self.is_alerted = False
        self.rect = pygame.Rect(int(self.position.x) - 8, int(self.position.y) - 8, 16, 16)

    def update(self, dt: float, player) -> None:
        self._t += dt * self.sweep_speed
        angle = self._base_angle + math.sin(self._t) * self.sweep_arc
        self.facing = pygame.Vector2(math.cos(angle), math.sin(angle))

        player_pos = pygame.Vector2(player.rect.centerx, player.rect.centery)
        distance = vec2_distance(self.position, player_pos)

        if distance <= self.detection_range and distance > 0:
            direction_to_player = vec2_normalize(player_pos - self.position)
            alignment = vec2_dot(self.facing, direction_to_player)
            self.is_alerted = alignment >= self.fov_cos_threshold
        else:
            self.is_alerted = False

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        screen_pos = self.position - camera_offset
        color = (255, 40, 40) if self.is_alerted else (60, 120, 220)
        pygame.draw.circle(surface, color, (int(screen_pos.x), int(screen_pos.y)), 6)
        end = screen_pos + self.facing * 24
        pygame.draw.line(surface, color, screen_pos, end, 2)