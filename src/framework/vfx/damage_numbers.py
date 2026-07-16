from __future__ import annotations

import random

import pygame

from src.engine.core import settings


class DamageNumber:

    _font_cache: dict[int, pygame.font.Font] = {}
    _render_cache: dict[tuple[str, bool], pygame.Surface] = {}

    def __init__(self, x: float, y: float, amount_text: str, is_critical: bool = False) -> None:
        self.x = x
        self.y = y
        self.amount_text = amount_text
        self.is_critical = is_critical
        self.life: float = 1.0
        self.max_life: float = 1.0
        self.vy: float = -60.0 - random.random() * 30.0
        self.vx: float = random.uniform(-20.0, 20.0)
        size = 18 if is_critical else 14
        font = self._font_cache.get(size)
        if font is None:
            font = pygame.font.Font(None, size)
            self._font_cache[size] = font
        color = (255, 220, 50) if is_critical else (255, 255, 200)
        cache_key = (amount_text, is_critical)
        surf = self._render_cache.get(cache_key)
        if surf is None:
            surf = font.render(amount_text, True, color)
            self._render_cache[cache_key] = surf
        if is_critical:
            scale = 1.0 + 0.3 * (1.0 - self.life / self.max_life)
            w, h = surf.get_size()
            self._scaled_surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
        else:
            self._surf = surf

    @property
    def alive(self) -> bool:
        return self.life > 0

    def update(self, dt: float) -> None:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 120.0 * dt

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if not self.alive:
            return
        alpha = int(min(255, (self.life / self.max_life) * 255))
        sx = int(self.x - camera_offset.x)
        sy = int(self.y - camera_offset.y)
        if sx < -50 or sx > settings.INTERNAL_WIDTH + 50 or sy < -50 or sy > settings.INTERNAL_HEIGHT + 50:
            return
        surf = self._scaled_surf if self.is_critical else self._surf
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(sx, sy))
        surface.blit(surf, rect)


class DamageNumberManager:
    def __init__(self) -> None:
        self._numbers: list[DamageNumber] = []

    def add(self, x: float, y: float, text: str, is_critical: bool = False) -> None:
        self._numbers.append(DamageNumber(x, y, text, is_critical))

    def clear(self) -> None:
        self._numbers.clear()

    def update(self, dt: float) -> None:
        for n in self._numbers:
            n.update(dt)
        self._numbers = [n for n in self._numbers if n.alive]

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        for n in self._numbers:
            n.draw(surface, camera_offset)
