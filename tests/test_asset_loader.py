"""
Tests for AssetLoader and SpriteSheet caching behaviour.

See 24_TEST_PLAN.md §4.2 for test specifications.
"""

from pathlib import Path

import pygame
import pytest

from src.engine.utils.asset_loader import AssetLoader


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure AssetLoader cache is empty before and after each test."""
    AssetLoader._cache.clear()
    yield
    AssetLoader._cache.clear()


def _make_png(path: Path, size: tuple[int, int] = (16, 16)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(pygame.Surface(size), str(path))


def test_load_image_caches():
    """Calling load_image(same_path) twice returns the same object (is)."""
    test_image = Path("assets") / "_test_asset_loader_cache.png"
    _make_png(test_image)
    try:
        img1 = AssetLoader.load_image(test_image)
        img2 = AssetLoader.load_image(test_image)
        assert img1 is img2, (
            "Cache miss: load_image did not return the same object"
        )
    finally:
        if test_image.exists():
            test_image.unlink()


def test_load_image_different_paths_different_objects():
    """Two different paths return different cached objects."""
    path_a = Path("assets") / "_test_asset_a.png"
    path_b = Path("assets") / "_test_asset_b.png"
    _make_png(path_a, (8, 8))
    _make_png(path_b, (8, 8))
    try:
        img_a = AssetLoader.load_image(path_a)
        img_b = AssetLoader.load_image(path_b)
        assert img_a is not img_b, (
            "Different paths returned the same cached object"
        )
    finally:
        if path_a.exists():
            path_a.unlink()
        if path_b.exists():
            path_b.unlink()


def test_load_spritesheet_frame_count():
    """A sheet of known width/frame_w produces the expected frame_count."""
    sheet_path = Path("assets") / "_test_spritesheet.png"
    frame_w, frame_h = 16, 16
    _make_png(sheet_path, (48, 16))  # 3 cols × 1 row
    try:
        sheet = AssetLoader.load_spritesheet(
            sheet_path, frame_w, frame_h
        )
        assert sheet.frame_count == 3, (
            f"Expected 3 frames, got {sheet.frame_count}"
        )
    finally:
        if sheet_path.exists():
            sheet_path.unlink()


def test_load_missing_file_raises():
    """Loading a nonexistent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        AssetLoader.load_image(
            "assets/definitely_missing_file_9999.png"
        )