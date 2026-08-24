"""Benchmark: memory allocation patterns.

Measures heap allocation rate and GC pressure from common operations.
Establishes baseline for P0-005 (Surface Object Pool) effectiveness.
"""
from __future__ import annotations

import gc
import tracemalloc

import pytest

# pytest-benchmark is an optional dev dependency (`pip install -e ".[dev]"`).
# Without it the `benchmark` fixture does not exist and every test in this
# module ERRORs rather than skipping — which made a plain `pytest` run look
# broken on a minimal install. Skip cleanly instead.
pytest.importorskip("pytest_benchmark")


def test_surface_allocation_vs_pool(benchmark) -> None:
    """Benchmark raw Surface creation (baseline for pool comparison)."""
    surfs: list = []

    def raw_alloc() -> None:
        nonlocal surfs
        surfs = [__import__("pygame").Surface((32, 32)) for _ in range(500)]
        surfs.clear()

    benchmark(raw_alloc)


def test_pooled_allocation_benchmark(benchmark) -> None:
    """Specifically benchmark the pooled path for comparison."""
    from src.engine.utils.surface_pool import SurfacePool

    pool = SurfacePool()

    def run() -> None:
        surfs = [pool.borrow(32, 32) for _ in range(500)]
        for s in surfs:
            pool.return_surface(s)

    benchmark(run)


def test_gc_collections_per_frame(benchmark) -> None:
    """Measure how many GC collections occur during a burst of Surface create/destroy."""
    gc.collect()
    gc.disable()

    def _create_destroy() -> None:
        for _ in range(300):
            s = __import__("pygame").Surface((32, 32), __import__("pygame").SRCALPHA)
            s.fill((255, 0, 0, 128))
            del s

    try:
        benchmark(_create_destroy)
    finally:
        gc.enable()


def test_tracemalloc_peak_on_burst(benchmark) -> None:
    """Track peak memory usage during a burst of surface operations."""
    tracemalloc.start()

    def _burst() -> None:
        surfs = [__import__("pygame").Surface((64, 64)) for _ in range(200)]
        surfs.clear()

    benchmark(_burst)
    tracemalloc.stop()
