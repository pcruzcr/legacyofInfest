from __future__ import annotations

import random

import pygame

from src.engine.core import settings
from src.framework.vfx.particle_system import ParticleEmitter


class AmbientParticleSystem:
    """Spawns environmental particles (dust, leaves, embers) in the camera view."""

    def __init__(self) -> None:
        self._emitter = ParticleEmitter()
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

        self._emitter.update(dt)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        self._emitter.draw(surface, offset)

    def clear(self) -> None:
        self._emitter.clear()

    @property
    def _particles(self) -> list:  # backward compat for tests
        return []

    def _spawn(self, camera_offset: pygame.Vector2) -> None:
        sx = camera_offset.x + random.uniform(0, settings.INTERNAL_WIDTH)
        sy = camera_offset.y + random.uniform(0, settings.INTERNAL_HEIGHT)

        if self._particle_type == "dust":
            self._emitter.emit_directed(
                sx, sy, angle=270, speed=random.uniform(5, 15),
                count=1, lifetime=random.uniform(2, 4),
                size=(1, 2), color=(120, 100, 80), spread=30,
                gravity=0,
            )
        elif self._particle_type == "leaves":
            self._emitter.emit_directed(
                sx, sy, angle=random.uniform(60, 120), speed=random.uniform(10, 30),
                count=1, lifetime=random.uniform(3, 6),
                size=(2, 4), color=(60, 140, 40), spread=20,
                gravity=0,
            )
        elif self._particle_type == "embers":
            self._emitter.emit_directed(
                sx, sy, angle=270, speed=random.uniform(3, 30),
                count=1, lifetime=random.uniform(1, 3),
                size=(2, 3), color=(255, 150, 50), spread=15,
                gravity=0,
            )
