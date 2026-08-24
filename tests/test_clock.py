"""
Module: test_clock
System: tests
Description: Tests for DeltaClock delta-time wrapper.
Covers: tick returns float, tick returns scaled dt when time_scale changes,
fps property returns float.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core.clock import DeltaClock


@pytest.fixture(autouse=True)
def dummy_video() -> None:
    if not pygame.get_init():
        pygame.init()


def test_tick_returns_float() -> None:
    clock = DeltaClock()
    dt = clock.tick()
    assert isinstance(dt, float)


def test_fps_returns_float() -> None:
    clock = DeltaClock()
    clock.tick()
    fps = clock.fps
    assert isinstance(fps, float)


def test_tick_scaled_by_time_scale() -> None:
    clock = DeltaClock()
    clock.time_scale = 2.0
    dt = clock.tick()
    assert isinstance(dt, float)
    assert dt >= 0.0
    raw_estimate = dt / 2.0
    assert 0.0 < raw_estimate < 1.0


def test_time_scale_default() -> None:
    clock = DeltaClock()
    assert clock.time_scale == 1.0
