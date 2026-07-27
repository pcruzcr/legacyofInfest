"""Machine-portable performance regression gate (AUD-037).

Why this exists
---------------
``tests/benchmarks/baseline_v1.json`` records absolute timings captured on one
Windows machine with Python 3.14.6. Nothing ever compared against it, and
nothing sensibly could: absolute nanosecond counts are not transferable between
a developer laptop, a CI runner and a lab PC, so any threshold derived from them
is either so loose it catches nothing or so tight it fails constantly. The
result was a benchmark harness and a committed baseline that provided no
protection at all.

This module gates on **frame budget share** instead. At 60 fps a frame has
16.67 ms. Asserting that the HUD costs under 5% of that is a claim which holds
on fast and slow machines alike, because a regression that matters — an O(n²)
loop, a per-frame surface allocation, a re-decode of an asset — blows the budget
by an order of magnitude, not by 20%.

Thresholds are deliberately generous (roughly 10x the measured cost on the audit
machine). The goal is to catch *categorical* regressions, not to police noise.
"""
from __future__ import annotations

import gc
import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

# One frame at the target frame rate.
FRAME_BUDGET_MS = 1000.0 / 60.0


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


def _measure_ms(fn, iterations: int) -> float:
    """Median-of-three best-run timing, in milliseconds per iteration."""
    results = []
    for _ in range(3):
        gc.collect()
        start = time.perf_counter()
        for _ in range(iterations):
            fn()
        results.append((time.perf_counter() - start) / iterations * 1000.0)
    return min(results)


def _assert_within_budget(name: str, ms: float, budget_share: float) -> None:
    limit = FRAME_BUDGET_MS * budget_share
    assert ms < limit, (
        f"{name} costs {ms:.4f} ms/frame — {ms / FRAME_BUDGET_MS * 100:.1f}% of "
        f"the {FRAME_BUDGET_MS:.2f} ms frame budget, over the "
        f"{budget_share * 100:.0f}% ceiling. Something got categorically slower; "
        f"look for a new per-frame allocation or an O(n^2) loop."
    )


class TestFrameBudget:
    def test_hud_update_and_draw(self, display) -> None:
        """Measured at 0.048 ms on the audit machine; ceiling is 5%."""
        from src.engine.core.event_bus import EventBus
        from src.engine.ui.hud import HUD

        hud = HUD(EventBus())
        surface = pygame.Surface((800, 600))

        def frame() -> None:
            hud.update(1 / 60)
            hud.draw(surface)

        _assert_within_budget("HUD", _measure_ms(frame, 300), 0.05)

    def test_particle_system_at_realistic_load(self, display) -> None:
        """2000 live particles is a heavy combat moment. Ceiling is 25%."""
        from src.framework.vfx.particle_system import BurstConfig, ParticleEmitter

        emitter = ParticleEmitter()
        config = BurstConfig(
            count=2000, speed=120, lifetime=5.0, size=(2, 4),
            color=(255, 200, 80), gravity=200, friction=0.9,
        )
        emitter.emit(400, 300, config)
        emitter.update(1 / 60)  # warm the JIT if numba is present

        def frame() -> None:
            if emitter.count < 500:
                emitter.emit(400, 300, config)
            emitter.update(1 / 60)

        _assert_within_budget("Particles (2k)", _measure_ms(frame, 200), 0.25)

    def test_post_processing_pass(self, display) -> None:
        from src.framework.vfx.post_processing import PostProcessing

        post = PostProcessing()
        surface = pygame.Surface((800, 600))

        def frame() -> None:
            post.update(1 / 60)
            post.apply(surface)

        _assert_within_budget("Post-processing", _measure_ms(frame, 100), 0.40)


class TestAllocationDiscipline:
    """Guards against per-frame allocation creeping back into hot paths."""

    def test_hud_does_not_allocate_per_frame(self, display) -> None:
        """AUD-023: the render path should reuse surfaces, not build them.

        A steady-state HUD frame must not create new Python objects in any
        meaningful quantity. If this fails, someone has added a
        `pygame.Surface(...)` or a `font.render(...)` inside `draw`.
        """
        import tracemalloc

        from src.engine.core.event_bus import EventBus
        from src.engine.ui.hud import HUD

        hud = HUD(EventBus())
        surface = pygame.Surface((800, 600))

        # Warm up: first frames legitimately build and cache their surfaces.
        for _ in range(30):
            hud.update(1 / 60)
            hud.draw(surface)

        gc.collect()
        tracemalloc.start()
        for _ in range(120):
            hud.update(1 / 60)
            hud.draw(surface)
        current, _peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        per_frame_bytes = current / 120
        assert per_frame_bytes < 2048, (
            f"HUD allocates ~{per_frame_bytes:.0f} bytes/frame in steady state. "
            "Something in the draw path is building a new object every frame — "
            "check for pygame.Surface(...) or font.render(...) inside draw()."
        )


class TestStageLoadCost:
    def test_respawn_reuses_the_parsed_map(self, display) -> None:
        """AUD-027: respawn must not re-parse the TMX.

        Re-parsing cost 184 ms — eleven dropped frames at the exact moment the
        player is watching for feedback. The parse is cached, so a second load
        of the same map must be dramatically cheaper than the first.
        """
        from src.framework.entities import entity_factory
        from src.framework.stage.stage_loader import StageLoader

        tmx = "assets/maps/stage0/stage0.tmx"
        if not os.path.exists(tmx):
            pytest.skip("stage0 map not present")

        entity_factory.ensure_registered()

        StageLoader.clear_tmx_cache()
        start = time.perf_counter()
        StageLoader.load(tmx)
        cold_ms = (time.perf_counter() - start) * 1000

        warm_times = []
        for _ in range(3):
            start = time.perf_counter()
            StageLoader.load(tmx)
            warm_times.append((time.perf_counter() - start) * 1000)
        warm_ms = min(warm_times)

        assert warm_ms < cold_ms / 3, (
            f"respawn cost {warm_ms:.1f} ms vs {cold_ms:.1f} ms cold — the TMX "
            "parse cache is not being hit, so every death re-parses the map"
        )
