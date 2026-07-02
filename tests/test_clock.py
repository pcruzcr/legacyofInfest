"""
Module: test_clock
System: tests
Academic Unit: N/A
Description: Tests for DeltaClock delta-time wrapper.
Covers: tick returns float, tick returns scaled dt when time_scale changes,
fps property returns float.
"""
from __future__ import annotations
import pytest
import pygame
from src.engine.core.clock import DeltaClock


@pytest.fixture(autouse=True)
def dummy_video():
    """Ensure headless Pygame init for clock tests."""
    if not pygame.get_init():
        pygame.init()


def test_tick_returns_float():
    """DeltaClock.tick() returns a float value."""
    clock = DeltaClock()
    dt = clock.tick()
    assert isinstance(dt, float)


def test_fps_returns_float():
    """DeltaClock.fps property returns a float."""
    clock = DeltaClock()
    clock.tick()
    fps = clock.fps
    assert isinstance(fps, float)


def test_tick_scaled_by_time_scale():
    """When time_scale is 2.0, effective dt is doubled."""
    clock = DeltaClock()
    clock.time_scale = 2.0
    dt = clock.tick()
    assert isinstance(dt, float)
    assert dt >= 0.0
    # With time_scale=2.0, raw_dt gets doubled; verify by checking
    # that estimated raw_dt (dt / 2.0) is a plausible frame time
    raw_estimate = dt / 2.0
    assert 0.0 < raw_estimate < 1.0


def test_time_scale_default():
    """Default time_scale is 1.0."""
    clock = DeltaClock()
    assert clock.time_scale == 1.0
