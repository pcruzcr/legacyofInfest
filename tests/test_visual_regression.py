"""
Visual regression tests — detect unintended visual changes.

Each test renders a scene or component to a surface and checks
pixel count / color distribution / known invariants.
"""
from __future__ import annotations

import hashlib

import pygame
import pytest

from src.engine.core import settings
from src.engine.scenes.demo_common import build_default_sources
from src.framework.processing.filter_tools import FilterTools
from src.framework.processing.vision_tools import VisionTools


def _surface_fingerprint(surface: pygame.Surface) -> str:
    """Return SHA-256 of surface pixel data for change detection."""
    raw = pygame.image.tostring(surface, "RGB")
    return hashlib.sha256(raw).hexdigest()


def _all_pixels_black(surface: pygame.Surface) -> bool:
    """Check if all pixels are (0, 0, 0)."""
    w, h = surface.get_size()
    for y in range(h):
        for x in range(w):
            if surface.get_at((x, y))[:3] != (0, 0, 0):
                return False
    return True


SWATCH_32 = (32, 32)


@pytest.fixture(autouse=True)
def _init_pygame():
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()


# === Filter output invariants ===

def test_adjust_brightness_identity():
    """Brightness factor 1.0 should return identical image."""
    surf = pygame.Surface(SWATCH_32)
    surf.fill((100, 100, 100))

    result = FilterTools.adjust_brightness(surf, 1.0)
    fp1 = _surface_fingerprint(surf)
    fp2 = _surface_fingerprint(result)
    assert fp1 == fp2, "Brightness 1.0 changed the image"


def test_adjust_brightness_doubles():
    """Brightness factor 2.0 should double pixel values (clamped)."""
    surf = pygame.Surface((16, 16))
    surf.fill((50, 100, 150))

    result = FilterTools.adjust_brightness(surf, 2.0)
    for y in range(16):
        for x in range(16):
            r, g, b, _ = result.get_at((x, y))
            assert r == 100
            assert g == 200
            assert b == 255  # clamped


def test_sobel_edge_output_not_empty():
    """Sobel edge detection should produce non-black output on non-uniform image."""
    surf = pygame.Surface((64, 64))
    surf.fill((100, 100, 100))
    # Draw a white square
    pygame.draw.rect(surf, (255, 255, 255), (20, 20, 24, 24))

    result = FilterTools.sobel_edge(surf)
    assert not _all_pixels_black(result), "Sobel produced all-black on edge-rich image"


def test_histogram_equalize_preserves_shape():
    """Histogram equalize should preserve image dimensions."""
    surf = pygame.Surface((64, 64))
    surf.fill((50, 100, 150))

    result = FilterTools.histogram_equalize(surf)
    assert result.get_size() == (64, 64)


# === Vision output invariants ===

def test_threshold_binary_output():
    """Threshold binary should produce only 0 or 255 pixels."""
    surf = pygame.Surface((32, 32))
    surf.fill((100, 100, 100))

    result = VisionTools.threshold_binary(surf, 128)
    w, h = result.get_size()
    for y in range(h):
        for x in range(w):
            val = result.get_at((x, y))[0]
            assert val in (0, 255), f"Threshold output has non-binary value {val}"


def test_morph_operations_preserve_shape():
    """Erosion and dilation should preserve image dimensions."""
    surf = pygame.Surface((32, 32))
    surf.fill((200, 200, 200))

    eroded = VisionTools.morphological_erode(surf, 3)
    assert eroded.get_size() == (32, 32)

    dilated = VisionTools.morphological_dilate(surf, 3)
    assert dilated.get_size() == (32, 32)


# === Source surface manager invariants ===

def test_default_sources_have_content():
    """Default sources should produce non-black images."""
    mgr = build_default_sources()
    src = mgr.current_source
    assert src is not None, "No source available"
    w, h = src.get_size()
    non_black = 0
    for y in range(min(h, 16)):
        for x in range(min(w, 16)):
            if src.get_at((x, y))[:3] != (0, 0, 0):
                non_black += 1
    assert non_black > 0, "Source surface is all black (likely missing asset)"


def test_source_surface_freeze_consistency():
    """Frozen source should return same surface on repeated calls."""
    mgr = build_default_sources()
    mgr.freeze()
    a = mgr.current_source
    b = mgr.current_source
    if a is not None and b is not None:
        assert _surface_fingerprint(a) == _surface_fingerprint(b)


# === Drawing invariants (top_bar, bottom_bar) ===

def test_draw_top_bar_does_not_crash():
    """draw_top_bar should render without errors."""
    from src.engine.scenes.demo_common import draw_top_bar
    surf = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    draw_top_bar(surf, "TEST TITLE", "TEST UNIT")
    # Check bar is non-empty
    non_bg = 0
    for y in range(26):
        for x in range(surf.get_width()):
            if surf.get_at((x, y))[:3] != (10, 10, 30):
                non_bg += 1
    assert non_bg > 0, "draw_top_bar produced empty result"


def test_draw_bottom_bar_does_not_crash():
    """draw_bottom_bar should render without errors."""
    from src.engine.scenes.demo_common import draw_bottom_bar
    surf = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    draw_bottom_bar(surf, "TEST CONTROLS: ARROWS SPACE ESC")
