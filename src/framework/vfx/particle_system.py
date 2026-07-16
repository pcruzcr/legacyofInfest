from __future__ import annotations

import math
import random

import pygame


class Particle:
    __slots__ = (
        "x", "y", "vx", "vy", "life", "max_life", "size",
        "color", "alpha", "decay", "gravity", "friction",
    )

    def __init__(
        self, x: float, y: float, vx: float, vy: float,
        life: float, size: int, color: tuple[int, int, int],
        gravity: float = 0.0, friction: float = 1.0,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.alpha = 255
        self.decay = 1.0
        self.gravity = gravity
        self.friction = friction

    @property
    def is_dead(self) -> bool:
        return self.life <= 0

    def update(self, dt: float) -> None:
        self.life -= dt
        t = max(0.0, self.life / self.max_life) if self.max_life > 0 else 0.0
        self.alpha = int(255 * t)
        self.vy += self.gravity * dt
        self.vx *= self.friction ** dt
        self.vy *= self.friction ** dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        sx = int(self.x - offset.x)
        sy = int(self.y - offset.y)
        if self.alpha <= 0 or self.size <= 0:
            return
        c = (*self.color, min(255, self.alpha))
        sz = max(1, int(self.size * (0.5 + 0.5 * t))) if (t := self.life / max(self.max_life, 0.001)) > 0 else 1
        pygame.draw.rect(surface, c, (sx - sz // 2, sy - sz // 2, sz, sz))


class BurstConfig:
    def __init__(
        self, count: int, speed: float, lifetime: float,
        size: tuple[int, int], color: tuple[int, int, int],
        spread: float = 360.0, gravity: float = 0.0,
        friction: float = 1.0,
    ) -> None:
        self.count = count
        self.speed = speed
        self.lifetime = lifetime
        self.size_min, self.size_max = size
        self.color = color
        self.spread = spread
        self.gravity = gravity
        self.friction = friction


class ParticleEmitter:
    def __init__(self) -> None:
        self._particles: list[Particle] = []

    def emit(self, x: float, y: float, config: BurstConfig) -> None:
        for _ in range(config.count):
            angle = random.uniform(0, config.spread)
            rad = math.radians(angle)
            spd = random.uniform(config.speed * 0.5, config.speed)
            vx = math.cos(rad) * spd
            vy = math.sin(rad) * spd
            size = random.randint(config.size_min, config.size_max)
            p = Particle(
                x, y, vx, vy, config.lifetime, size, config.color,
                gravity=config.gravity, friction=config.friction,
            )
            self._particles.append(p)

    def emit_directed(
        self, x: float, y: float, angle: float, speed: float,
        count: int, lifetime: float, size: tuple[int, int],
        color: tuple[int, int, int], spread: float = 30.0,
        gravity: float = 0.0,
    ) -> None:
        for _ in range(count):
            a = angle + random.uniform(-spread, spread)
            rad = math.radians(a)
            spd = random.uniform(speed * 0.7, speed)
            sz = random.randint(size[0], size[1])
            p = Particle(
                x, y, math.cos(rad) * spd, math.sin(rad) * spd,
                lifetime, sz, color, gravity=gravity,
            )
            self._particles.append(p)

    def update(self, dt: float) -> None:
        for p in self._particles:
            p.update(dt)
        self._particles[:] = [p for p in self._particles if not p.is_dead]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for p in self._particles:
            p.draw(surface, offset)

    def clear(self) -> None:
        self._particles.clear()

    @property
    def count(self) -> int:
        return len(self._particles)


class ParticleSystem:
    def __init__(self) -> None:
        self._emitters: dict[str, ParticleEmitter] = {}

    def get_emitter(self, name: str = "_default") -> ParticleEmitter:
        if name not in self._emitters:
            self._emitters[name] = ParticleEmitter()
        return self._emitters[name]

    def update(self, dt: float) -> None:
        for em in self._emitters.values():
            em.update(dt)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for em in self._emitters.values():
            em.draw(surface, offset)

    def clear(self) -> None:
        self._emitters.clear()
