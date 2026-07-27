"""
Shared test fixtures for the Legacy of InFest test suite.
"""
from __future__ import annotations

import os

# Set dummy video driver BEFORE any pygame import so display.set_mode
# never triggers the "no fast renderer available" warning.
os.environ["SDL_VIDEODRIVER"] = "dummy"
# Also hide pygame support prompt
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import warnings

import pygame
import pytest

# Suppress harmless pygame-ce SCALED warning under dummy driver
warnings.filterwarnings("ignore", message="no fast renderer available", category=Warning)


@pytest.fixture(scope="session")
def _pygame_init():
    """Initialize pygame once per test session for surface-dependent tests."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def event_bus():
    """Provide a fresh EventBus instance for each test."""
    from src.engine.core.event_bus import EventBus
    return EventBus()


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Reset global singletons before each test to prevent cross-test contamination.

    AUD-019: there is no longer a module-level default EventBus to clear —
    every consumer receives its bus by injection, so a test's bus cannot leak
    into another test. Only genuinely process-wide caches are reset here.
    """
    from src.engine.core.achievements import AchievementSystem
    from src.engine.scenes.demo_layout import clear_demo_font_cache
    from src.engine.utils.asset_loader import AssetLoader
    from src.framework.stage.stage_loader import StageLoader
    AssetLoader.clear_cache()
    AssetLoader._get_instance()._scopes = 0
    StageLoader.clear_tmx_cache()
    clear_demo_font_cache()
    AchievementSystem._reset_instance()


@pytest.fixture
def sample_surface_32x32(_pygame_init) -> pygame.Surface:
    """A 32×32 solid gray surface — canonical input for processing tools."""
    surf = pygame.Surface((32, 32))
    surf.fill((128, 128, 128))
    return surf


@pytest.fixture
def sample_surface_64x64(_pygame_init) -> pygame.Surface:
    """A 64×64 surface with a gradient pattern for filter/vision tests."""
    surf = pygame.Surface((64, 64))
    for x in range(64):
        for y in range(64):
            r = (x * 4) % 256
            g = (y * 4) % 256
            b = ((x + y) * 2) % 256
            surf.set_at((x, y), (r, g, b))
    return surf


@pytest.fixture
def sample_surface_bw_32x32(_pygame_init) -> pygame.Surface:
    """A 32×32 black-and-white checkerboard surface for threshold/morph tests."""
    surf = pygame.Surface((32, 32))
    for x in range(32):
        for y in range(32):
            v = 255 if (x // 4 + y // 4) % 2 == 0 else 0
            surf.set_at((x, y), (v, v, v))
    return surf
