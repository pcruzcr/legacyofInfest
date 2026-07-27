from __future__ import annotations

import math

import numpy as np
import pygame


class LightSource:
    """A 2D point light with position, radius, color, and intensity."""

    _gradient_cache: dict[tuple[int, int], pygame.Surface] = {}

    def __init__(
        self,
        position: pygame.Vector2,
        radius: float = 80.0,
        color: tuple[int, int, int] = (255, 255, 200),
        intensity: float = 0.8,
        flicker: bool = False,
        flicker_speed: float = 4.0,
        flicker_amount: float = 0.15,
    ) -> None:
        self.position = position
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.flicker = flicker
        self.flicker_speed = flicker_speed
        self.flicker_amount = flicker_amount
        self._elapsed: float = 0.0
        self._gradient: pygame.Surface | None = None
        self._cached_radius: float = 0.0
        self._cached_color: tuple[int, int, int] = (0, 0, 0)

    def update(self, dt: float) -> None:
        self._elapsed += dt

    def get_current_radius(self) -> float:
        if not self.flicker:
            return self.radius
        flicker = 1.0 + math.sin(self._elapsed * self.flicker_speed) * self.flicker_amount
        return self.radius * flicker

    def get_current_intensity(self) -> float:
        if not self.flicker:
            return self.intensity
        flicker = 1.0 + math.sin(self._elapsed * self.flicker_speed * 1.5 + 1.0) * self.flicker_amount
        return self.intensity * max(0.5, flicker)

    def build_gradient(self, radius: float, color: tuple[int, int, int]) -> pygame.Surface:
        r = int(radius)
        if r <= 0:
            r = 1
        key = (r, int(self.intensity * 100), color)
        if key in self._gradient_cache:
            return self._gradient_cache[key]
        size = r * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        ys, xs = np.ogrid[:size, :size]
        dist = np.sqrt((xs - r) ** 2 + (ys - r) ** 2)
        falloff = np.clip(1.0 - dist / r, 0.0, 1.0)
        mask = dist <= r
        val = (self.intensity * falloff * 255).astype(np.uint8)
        arr = pygame.surfarray.pixels3d(surf)
        try:
            arr[:, :, 0] = (val * color[0] / 255).astype(np.uint8)
            arr[:, :, 1] = (val * color[1] / 255).astype(np.uint8)
            arr[:, :, 2] = (val * color[2] / 255).astype(np.uint8)
            arr[~mask] = 0
        finally:
            del arr
        self._gradient_cache[key] = surf
        return surf

    def get_cached_gradient(self) -> pygame.Surface:
        current_radius = self.get_current_radius()
        if (
            self._gradient is None
            or abs(current_radius - self._cached_radius) > 2
            or self._cached_color != self.color
        ):
            self._gradient = self.build_gradient(current_radius, self.color)
            self._cached_radius = current_radius
            self._cached_color = self.color
        return self._gradient


class LightSystem:
    """Manages all 2D light sources and renders a light overlay."""

    def __init__(self, ambient_brightness: float = 0.3) -> None:
        self.lights: list[LightSource] = []
        self.ambient_brightness = ambient_brightness
        self._darkness_surf: pygame.Surface | None = None
        self._multiplier: pygame.Surface | None = None

    def add_light(self, light: LightSource) -> None:
        self.lights.append(light)

    def remove_light(self, light: LightSource) -> None:
        if light in self.lights:
            self.lights.remove(light)

    def clear(self) -> None:
        self.lights.clear()

    def update(self, dt: float, camera_offset: pygame.Vector2) -> None:
        for light in self.lights:
            light.update(dt)

    def render(self, target: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        w, h = target.get_size()

        ambient_val = int(self.ambient_brightness * 255)
        if self._multiplier is None or self._multiplier.get_size() != (w, h):
            self._multiplier = pygame.Surface((w, h), pygame.SRCALPHA)
        self._multiplier.fill((ambient_val, ambient_val, ambient_val))

        for light in self.lights:
            screen_pos = (
                int(light.position.x - camera_offset.x),
                int(light.position.y - camera_offset.y),
            )
            gradient = light.get_cached_gradient()
            gw, gh = gradient.get_size()
            blit_x = screen_pos[0] - gw // 2
            blit_y = screen_pos[1] - gh // 2
            self._multiplier.blit(gradient, (blit_x, blit_y), special_flags=pygame.BLEND_RGBA_MAX)

        target.blit(self._multiplier, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def get_player_light(self, player_pos: pygame.Vector2, is_combat: bool) -> LightSource:
        """Create/return a dynamic light for the player."""
        radius = 100 if is_combat else 60
        intensity = 0.9 if is_combat else 0.6
        color = (255, 220, 180) if not is_combat else (255, 200, 100)
        return LightSource(
            position=player_pos,
            radius=radius,
            color=color,
            intensity=intensity,
            flicker=True,
            flicker_speed=3.0,
            flicker_amount=0.1,
        )
