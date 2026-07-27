"""
Benchmark tests — measure FPS, memory, load time.
Fail if they drop below thresholds.
"""
from __future__ import annotations

import time
import tracemalloc

import pytest

from src.engine.scenes.demo_common import build_default_sources
from src.framework.processing.filter_tools import FilterTools

# Thresholds
MIN_FPS = 30
MAX_LOAD_TIME = 2.0  # seconds
MAX_MEMORY_MB = 200


def test_load_time_vector_lab():
    """VectorLabScene should load within MAX_LOAD_TIME."""
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.engine.scenes.vector_lab_scene import VectorLabScene

    bus = EventBus()
    sm = SceneManager.__new__(SceneManager)
    ctx = GameContext(
        input_manager=InputManager(),
        scene_manager=sm,
        event_bus=bus,
        audio_manager=None,
    )
    SceneManager.__init__(sm, ctx)

    start = time.perf_counter()
    _ = VectorLabScene(ctx)
    elapsed = time.perf_counter() - start

    assert elapsed < MAX_LOAD_TIME, (
        f"VectorLabScene took {elapsed:.2f}s to load (max {MAX_LOAD_TIME}s)"
    )


def test_load_time_filter_demo():
    """FilterDemoScene should load within MAX_LOAD_TIME."""
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.engine.scenes.filter_demo_scene import FilterDemoScene

    bus = EventBus()
    sm = SceneManager.__new__(SceneManager)
    ctx = GameContext(
        input_manager=InputManager(),
        scene_manager=sm,
        event_bus=bus,
        audio_manager=None,
    )
    SceneManager.__init__(sm, ctx)

    start = time.perf_counter()
    _ = FilterDemoScene(ctx)
    elapsed = time.perf_counter() - start

    assert elapsed < MAX_LOAD_TIME, (
        f"FilterDemoScene took {elapsed:.2f}s to load (max {MAX_LOAD_TIME}s)"
    )


@pytest.mark.parametrize("image_size", [
    (320, 180),
    (640, 360),
])
def test_filter_performance(image_size):
    """Filter operations should complete within 0.5s on typical sizes."""
    import pygame
    surf = pygame.Surface(image_size)

    start = time.perf_counter()
    _ = FilterTools.adjust_brightness(surf, 1.5)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, (
        f"adjust_brightness on {image_size} took {elapsed:.3f}s"
    )

    start = time.perf_counter()
    _ = FilterTools.sobel_edge(surf)
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, (
        f"sobel_edge on {image_size} took {elapsed:.3f}s"
    )


def test_memory_usage():
    """Filter operations should not exceed memory threshold."""
    import pygame
    surf = pygame.Surface((640, 480))

    tracemalloc.start()
    for _ in range(10):
        _ = FilterTools.gaussian_blur(surf, 2.0)
        _ = FilterTools.apply_kernel(surf, FilterTools.get_standard_kernel("sharpen"))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / 1024 / 1024
    assert peak_mb < MAX_MEMORY_MB, (
        f"Filter operations used {peak_mb:.1f}MB (max {MAX_MEMORY_MB}MB)"
    )


def test_source_surface_manager_switching():
    """SourceSurfaceManager mode switch should be fast."""
    mgr = build_default_sources()
    modes = len(mgr._sources) if hasattr(mgr, "_sources") else 4

    start = time.perf_counter()
    for _ in range(modes * 2):
        mgr.cycle()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, (
        f"Source switching took {elapsed:.3f}s"
    )
