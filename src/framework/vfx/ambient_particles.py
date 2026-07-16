from __future__ import annotations

import random

import pygame

from src.engine.core import settings
from src.framework.vfx.particle_system import Particle


class AmbientParticleSystem:
    """Spawns environmental particles (dust, leaves, embers) in the camera view."""

    def __init__(self) -> None:
        self._particles: list[Particle] = []
        self._rate: float = 0.0
        self._timer: float = 0.0
        self._particle_type: str = "dust"

    def set_effect(self, particle_type: str, rate: float = 10.0) -> None:
        self._particle_type = particle_type
        self._rate = rate

    def update(self, dt: float, camera_offset: pygame.Vector2) -> None:
        self._timer += dt
        spawn_rate = 1.0 / max(self._rate, 0.1)
        while self._timer >= spawn_rate:
            self._timer -= spawn_rate
            self._spawn(camera_offset)

        for p in self._particles:
            p.update(dt)
        self._particles = [p for p in self._particles if not p.is_dead]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for p in self._particles:
            p.draw(surface, offset)

    def clear(self) -> None:
        self._particles.clear()

    def _spawn(self, camera_offset: pygame.Vector2) -> None:
        sx = camera_offset.x + random.uniform(0, settings.INTERNAL_WIDTH)
        sy = camera_offset.y + random.uniform(0, settings.INTERNAL_HEIGHT)

        if self._particle_type == "dust":
            self._particles.append(Particle(
                sx, sy,
                random.uniform(-5, 5), random.uniform(-15, -5),
                random.uniform(2, 4),
                random.randint(1, 2),
                (120, 100, 80),
            ))
        elif self._particle_type == "leaves":
            self._particles.append(Particle(
                sx, sy,
                random.uniform(-10, 10), random.uniform(10, 30),
                random.uniform(3, 6),
                random.randint(2, 4),
                (60, 140, 40),
            ))
        elif self._particle_type == "embers":
            self._particles.append(Particle(
                sx, sy,
                random.uniform(-3, 3), random.uniform(-30, -10),
                random.uniform(1, 3),
                random.randint(2, 3),
                (255, 150, 50),
            ))
