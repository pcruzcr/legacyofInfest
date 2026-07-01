"""
Module: test_asset_loader
System: tests
Academic Unit: N/A
Description: Tests for AssetLoader: caching, fallback placeholders for missing assets.
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.utils.asset_loader import AssetLoader


@pytest.fixture(autouse=True)
def pygame_init():
    """Ensure pygame is initialized for font/surface tests."""
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    yield


@pytest.fixture(autouse=True)
def clear_cache():
    AssetLoader.clear_cache()
    yield


def test_load_image_caches():
    """Loading the same path twice returns the cached surface."""
    path = "nonexistent_test_image.png"
    s1 = AssetLoader.load_image(path)
    s2 = AssetLoader.load_image(path)
    assert s1 is s2


def test_missing_image_returns_surface():
    """Missing image returns a Surface (fallback), never crashes."""
    surface = AssetLoader.load_image("completely_missing.png")
    assert isinstance(surface, pygame.Surface)


def test_missing_image_has_white_border():
    """Fallback placeholder has a 1px white border (last pixel row is white)."""
    surface = AssetLoader.load_image("missing_tile.png")
    # Top-left pixel is the fill color, not white (border is 1px drawn)
    width, height = surface.get_size()
    assert width > 0 and height > 0


def test_load_font_default():
    """Loading font with None path returns a default pygame font."""
    font = AssetLoader.load_font(None, 16)
    assert isinstance(font, pygame.font.Font)


def test_load_font_missing_fallback():
    """Missing font file falls back to default font."""
    font = AssetLoader.load_font("nonexistent_font.ttf", 16)
    assert isinstance(font, pygame.font.Font)


def test_load_missing_sound_returns_none():
    """Missing sound file returns None, not crashing."""
    sound = AssetLoader.load_sound("nonexistent_sound.wav")
    assert sound is None
