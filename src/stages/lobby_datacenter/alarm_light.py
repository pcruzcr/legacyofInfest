"""
Module: alarm_light
Academic Unit: Unit V (Color Spaces) — rgb_to_hsv, hsv_to_rgb
Description: Pulsing red warning light using HSV brightness oscillation.
"""
from __future__ import annotations

import math
import pygame

from src.framework.processing.color_tools import ColorTools


class AlarmLight:
    """Server-rack warning light that pulses via HSV brightness modulation."""

    def __init__(
        self,
        position: pygame.Vector2,
        base_color: tuple[int, int, int] = (220, 30, 30),
        pulse_speed: float = 2.5,
    ) -> None:
        self.position = pygame.Vector2(position)
        self.base_color = base_color
        self.pulse_speed = pulse_speed
        self._t = 0.0
        self.rect = pygame.Rect(int(self.position.x) - 5, int(self.position.y) - 5, 10, 10)

    def update(self, dt: float) -> None:
        self._t += dt * self.pulse_speed

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        h, s, v = ColorTools.rgb_to_hsv(*self.base_color)
        pulse = (math.sin(self._t) + 1.0) / 2.0        # oscila 0..1
        v_pulsed = v * (0.4 + pulse * 0.6)              # brillo pulsante, mismo tono
        r, g, b = ColorTools.hsv_to_rgb(h, s, v_pulsed)

        screen_pos = self.position - camera_offset
        pygame.draw.circle(surface, (r, g, b), (int(screen_pos.x), int(screen_pos.y)), 6)

        glow_radius = 10 + int(pulse * 6)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (r, g, b, 70), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (screen_pos.x - glow_radius, screen_pos.y - glow_radius))