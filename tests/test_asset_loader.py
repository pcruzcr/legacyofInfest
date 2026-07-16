"""
Module: test_asset_loader
System: tests
Academic Unit: N/A
Description: Tests for AssetLoader: caching, fallback placeholders,
font loading, clear_cache, and missing asset handling.
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.utils.asset_loader import AssetLoader


@pytest.fixture(autouse=True)
def pygame_init():
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    yield


@pytest.fixture(autouse=True)
def clear_cache():
    AssetLoader.clear_cache()
    yield


def test_load_image_caches() -> None:
    path = "nonexistent_test_image.png"
    s1 = AssetLoader.load_image(path)
    s2 = AssetLoader.load_image(path)
    assert s1 is s2


def test_missing_image_returns_surface() -> None:
    surface = AssetLoader.load_image("completely_missing.png")
    assert isinstance(surface, pygame.Surface)


def test_missing_image_has_white_border() -> None:
    surface = AssetLoader.load_image("missing_tile.png")
    w, h = surface.get_size()
    assert w > 0 and h > 0
    assert surface.get_at((0, 0)) == (255, 255, 255, 255)
    assert surface.get_at((w - 1, h - 1)) == (255, 255, 255, 255)


def test_missing_image_placeholder_size_uses_category() -> None:
    surface = AssetLoader.load_image("enemies/missing.png")
    assert surface.get_size() == (24, 24)


def test_load_font_default() -> None:
    font = AssetLoader.load_font(None, 16)
    assert isinstance(font, pygame.font.Font)


def test_load_font_missing_fallback() -> None:
    font = AssetLoader.load_font("nonexistent_font.ttf", 16)
    assert isinstance(font, pygame.font.Font)


def test_load_font_caches() -> None:
    f1 = AssetLoader.load_font(None, 12)
    f2 = AssetLoader.load_font(None, 12)
    assert f1 is f2


def test_load_font_different_sizes_different_instances() -> None:
    f1 = AssetLoader.load_font(None, 12)
    f2 = AssetLoader.load_font(None, 16)
    assert f1 is not f2


def test_load_missing_sound_returns_none() -> None:
    sound = AssetLoader.load_sound("nonexistent_sound.wav")
    assert sound is None


def test_clear_cache_empties_all_caches() -> None:
    inst = AssetLoader.load_image  # access default instance via closure
    default = AssetLoader._get_instance()
    s1 = AssetLoader.load_image("img_a.png")
    f1 = AssetLoader.load_font(None, 10)
    assert default._images
    assert default._fonts

    AssetLoader.clear_cache()

    assert not default._images
    assert not default._fonts
    assert not default._sounds
    assert not default._missing

    s2 = AssetLoader.load_image("img_a.png")
    assert s1 is not s2


def test_load_image_with_scale() -> None:
    surface = AssetLoader.load_image("missing.png", scale=2.0)
    assert isinstance(surface, pygame.Surface)


def test_load_image_with_size() -> None:
    surface = AssetLoader.load_image("missing.png", size=(64, 64))
    assert surface.get_size() == (64, 64)


def test_instance_isolation() -> None:
    """Verify that separate AssetLoader instances have independent caches."""
    loader_a = AssetLoader()
    loader_b = AssetLoader()
    s1 = loader_a._load_image("img_c.png")  # missing → placeholder
    s2 = loader_b._load_image("img_c.png")
    # Same missing path, different instances → different objects
    assert s1 is not s2
    # Default singleton should remain unaffected
    assert "img_c.png" not in str(list(AssetLoader._get_instance()._images.keys()))


def test_instance_vs_classmethod_independence() -> None:
    """Verify that explicit instance and default singleton have separate caches."""
    loader = AssetLoader()
    img_inst = loader._load_image("missing_instance_test.png")
    img_cls = AssetLoader.load_image("missing_instance_test.png")
    # Different instances → different objects
    assert img_inst is not img_cls
