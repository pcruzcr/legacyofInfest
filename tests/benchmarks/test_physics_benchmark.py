"""Benchmark: entity physics update throughput.

Measures the cost of per-frame physics (gravity, velocity, position)
across varying entity counts.
"""
from __future__ import annotations

import pygame
import pytest

# pytest-benchmark is an optional dev dependency (`pip install -e ".[dev]"`).
# Without it the `benchmark` fixture does not exist and every test in this
# module ERRORs rather than skipping — which made a plain `pytest` run look
# broken on a minimal install. Skip cleanly instead.
pytest.importorskip("pytest_benchmark")


class _BenchEntity:
    __slots__ = ("grounded", "pos", "vel")

    def __init__(self, x: float, y: float) -> None:
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0.0, 0.0)
        self.grounded = False

    def update(self, dt: float, gravity: float) -> None:
        if not self.grounded:
            self.vel.y += gravity * dt
        self.pos += self.vel * dt
        if self.pos.y >= 500:
            self.pos.y = 500
            self.vel.y = 0
            self.grounded = True


def _run_entities(count: int, steps: int = 60) -> None:
    """Simulate *steps* frames of physics for *count* entities."""
    ents = [_BenchEntity(float(i * 20), 0.0) for i in range(count)]
    dt = 1.0 / 60.0
    for _ in range(steps):
        for e in ents:
            e.update(dt, 980.0)


def test_physics_100_entities(benchmark) -> None:
    benchmark(_run_entities, 100)


def test_physics_500_entities(benchmark) -> None:
    benchmark(_run_entities, 500)


def test_physics_1000_entities(benchmark) -> None:
    benchmark(_run_entities, 1000)
