from __future__ import annotations

import random

import pygame

from src.engine.core import settings


class DamageNumber:
    def __init__(self, x: float, y: float, amount_text: str, is_critical: bool = False) -> None:
        self.x = x
        self.y = y
        self.amount_text = amount_text
        self.is_critical = is_critical
        self.life: float = 1.0
        self.max_life: float = 1.0
        self.vy: float = -60.0 - random.random() * 30.0
        self.vx: float = random.uniform(-20.0, 20.0)

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
        font = pygame.font.Font(None, 18 if self.is_critical else 14)
        color = (255, 220, 50) if self.is_critical else (255, 255, 200)
        surf = font.render(self.amount_text, True, color)
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(sx, sy))
        if self.is_critical:
            scale = 1.0 + 0.3 * (1.0 - self.life / self.max_life)
            w, h = surf.get_size()
            surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
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
