"""Benchmark: surface rendering throughput at various sprite counts.

Measures CPU-bound blitting performance — the current primary bottleneck.
Provides baseline data for P0-004 (Sprite Batch System).
"""
from __future__ import annotations

import pygame
import pytest

# pytest-benchmark is an optional dev dependency (`pip install -e ".[dev]"`).
# Without it the `benchmark` fixture does not exist and every test in this
# module ERRORs rather than skipping — which made a plain `pytest` run look
# broken on a minimal install. Skip cleanly instead.
pytest.importorskip("pytest_benchmark")


def _render_sprites(count: int, surf_size: tuple[int, int] = (32, 32),
                    target_size: tuple[int, int] = (800, 600)) -> None:
    """Create *count* sprite surfaces and blit them to a target surface."""
    target = pygame.Surface(target_size)
    sprites = [pygame.Surface(surf_size) for _ in range(count)]
    for s in sprites:
        s.fill((255, 255, 255))
    for i, s in enumerate(sprites):
        target.blit(s, (i * 17 % 800, i * 13 % 600))


def test_render_500_sprites(benchmark) -> None:
    benchmark(_render_sprites, 500)


def test_render_1000_sprites(benchmark) -> None:
    benchmark(_render_sprites, 1000)


def test_render_2000_sprites(benchmark) -> None:
    benchmark(_render_sprites, 2000)


def test_render_with_surface_pool(benchmark) -> None:
    """Benchmark using SurfacePool for borrow/return pattern."""
    from src.engine.utils.surface_pool import SurfacePool

    pool = SurfacePool()
    target = pygame.Surface((800, 600))

    def run() -> None:
        surfs = [pool.borrow(32, 32) for _ in range(500)]
        for i, s in enumerate(surfs):
            target.blit(s, (i * 17 % 800, i * 13 % 600))
        for s in surfs:
            pool.return_surface(s)

    benchmark(run)
