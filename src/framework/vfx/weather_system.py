from __future__ import annotations

import random

import pygame

from src.engine.core import settings
from src.framework.vfx.particle_system import ParticleEmitter


class WeatherSystem:
    """Stage weather effects (rain, snow, fog, storm) driven by TMX climate property."""

    CLIMATE_PARAMS: dict[str, dict] = {
        "clear":  {"particles": 0,  "overlay_alpha": 0,   "overlay_color": (0, 0, 0)},
        "rain":   {"particles": 60, "overlay_alpha": 30,  "overlay_color": (60, 70, 90)},
        "snow":   {"particles": 40, "overlay_alpha": 50,  "overlay_color": (200, 210, 220)},
        "fog":    {"particles": 0,  "overlay_alpha": 80,  "overlay_color": (180, 180, 190)},
        "storm":  {"particles": 100,"overlay_alpha": 60,  "overlay_color": (40, 40, 50)},
    }

    def __init__(self, climate: str = "clear") -> None:
        self._emitter = ParticleEmitter()
        self._timer: float = 0.0
        self._climate: str = climate
        self._overlay = pygame.Surface(
            (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA
        )
        self._wind: float = 0.0
        self._set_climate_params()

    def _set_climate_params(self) -> None:
        params = self.CLIMATE_PARAMS.get(self._climate, self.CLIMATE_PARAMS["clear"])
        self._particle_rate: float = float(params["particles"])
        self._overlay_alpha: int = params["overlay_alpha"]
        self._overlay_color: tuple[int, int, int] = params["overlay_color"]
        self._wind = random.uniform(-30, 30) if self._climate == "storm" else 0.0

    def set_climate(self, climate: str) -> None:
        if climate == self._climate:
            return
        self._climate = climate
        self._emitter.clear()
        self._set_climate_params()

    @property
    def climate(self) -> str:
        return self._climate

    @property
    def _particles(self) -> list:  # backward compat for tests
        return []

    def update(self, dt: float, camera_offset: pygame.Vector2) -> None:
        self._timer += dt
        if self._particle_rate > 0:
            spawn_interval = 1.0 / self._particle_rate
            max_spawn = max(1, int(self._particle_rate * dt))
            spawned = 0
            while self._timer >= spawn_interval and spawned < max_spawn:
                self._timer -= spawn_interval
                self._spawn_particle(camera_offset)
                spawned += 1

        self._emitter.update(dt)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        self._emitter.draw(surface, camera_offset)

        if self._overlay_alpha > 0:
            self._overlay.fill((*self._overlay_color, self._overlay_alpha))
            surface.blit(self._overlay, (0, 0))

    def clear(self) -> None:
        self._emitter.clear()

    def _spawn_particle(self, camera_offset: pygame.Vector2) -> None:
        sx = camera_offset.x + random.uniform(-20, settings.INTERNAL_WIDTH + 20)
        sy = camera_offset.y - 10
        color = self._get_particle_color()

        if self._climate == "rain":
            self._emitter.emit_directed(
                sx, sy, angle=90, speed=280,
                count=1, lifetime=random.uniform(0.3, 0.6),
                size=(1, 2), color=color, spread=5,
                gravity=980, friction=0.99,
            )
        elif self._climate == "snow":
            self._emitter.emit_directed(
                sx, sy, angle=90, speed=random.uniform(30, 60),
                count=1, lifetime=random.uniform(2.0, 4.0),
                size=(2, 4), color=color, spread=20,
                gravity=50, friction=0.95,
            )
        elif self._climate == "storm":
            random.choice([-1, 1]) * random.uniform(50, 100)
            self._emitter.emit_directed(
                sx, sy, angle=90, speed=280,
                count=1, lifetime=random.uniform(0.3, 0.5),
                size=(1, 3), color=color, spread=10,
                gravity=980, friction=0.99,
            )

    def _get_particle_color(self) -> tuple[int, int, int]:
        if self._climate == "rain":
            return (150, 170, 200)
        elif self._climate == "snow":
            return (230, 235, 240)
        elif self._climate == "storm":
            return (120, 130, 150)
        return (200, 200, 200)

    def get_ambient_audio_key(self) -> str | None:
        audio_map: dict[str, str | None] = {
            "clear": None,
            "rain": "rain",
            "snow": "wind",
            "fog": "wind",
            "storm": "storm",
        }
        return audio_map.get(self._climate)
