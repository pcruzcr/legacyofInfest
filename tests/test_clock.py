"""
Tests for DeltaClock — frame-rate-independent delta time clock.

See 24_TEST_PLAN.md §3.2 for test specifications.
"""

import time

from src.engine.core.clock import DeltaClock


def test_tick_returns_float():
    """DeltaClock().tick() returns a float >= 0.0."""
    clock = DeltaClock()
    dt = clock.tick()
    assert isinstance(dt, float)
    assert dt >= 0.0


def test_tick_no_division_by_zero_on_first_call():
    """First call to tick() does not raise and returns a non-negative value."""
    clock = DeltaClock()
    dt = clock.tick()
    assert dt >= 0.0


def test_time_scale_applied():
    """Setting time_scale = 0.5 halves the returned delta on the next tick().

    Uses a real-time delay between ticks to produce a measurable delta.
    The tolerance is intentionally wider than the ideal 0.5 ratio to account
    for OS scheduler jitter on the test host.
    """
    clock = DeltaClock()
    clock.tick()  # prime the clock (discard first-frame delta)

    clock.time_scale = 1.0
    time.sleep(0.1)
    dt_normal = clock.tick()

    clock.time_scale = 0.5
    time.sleep(0.1)
    dt_half = clock.tick()

    # time_scale halves the returned delta; allow generous tolerance for
    # OS scheduling imprecision and pygame Clock internals.
    assert dt_half < dt_normal or abs(dt_half - dt_normal) < 0.01
    if dt_normal > 0.01:
        ratio = dt_half / dt_normal
        assert 0.35 < ratio < 0.75, (
            f"Expected ratio ~0.5, got {ratio:.3f} "
            f"(dt_normal={dt_normal:.4f}, dt_half={dt_half:.4f})"
        )


def test_fps_property_nonzero_after_tick():
    """.fps is > 0 after at least one tick() call.

    Pygame's Clock.get_fps() averages over the last ~10 frames, so we
    need enough ticks with real time between them for the buffer to fill.
    """
    clock = DeltaClock()
    for _ in range(12):
        clock.tick()
        time.sleep(0.05)
    assert clock.fps > 0.0


def test_time_scale_default():
    """time_scale defaults to 1.0."""
    clock = DeltaClock()
    assert clock.time_scale == 1.0


def test_time_scale_mutable():
    """time_scale is a public mutable attribute."""
    clock = DeltaClock()
    clock.time_scale = 0.25
    assert clock.time_scale == 0.25
    clock.time_scale = 2.0
    assert clock.time_scale == 2.0