"""
Module: test_color_tools
System: tests
Academic Unit: N/A
Description: Tests for ColorTools: RGB↔HSV↔HSL↔CMYK round-trips,
alpha_blend, apply_tint, surface_to_array.
"""
import numpy as np
import pygame

from src.framework.processing.color_tools import ColorTools


class TestColorConversions:
    """Verify all color conversions round-trip within ±1 unit."""

    TEST_COLORS = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (0, 0, 0),
        (255, 255, 255),
        (128, 128, 128),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
        (42, 99, 187),
        (200, 100, 50),
        (10, 200, 180),
    ]

    def test_rgb_to_hsv_and_back(self) -> None:
        for r, g, b in self.TEST_COLORS:
            h, s, v = ColorTools.rgb_to_hsv(r, g, b)
            r2, g2, b2 = ColorTools.hsv_to_rgb(h, s, v)
            assert abs(r - r2) <= 1, f"R diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"
            assert abs(g - g2) <= 1, f"G diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"
            assert abs(b - b2) <= 1, f"B diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"

    def test_rgb_to_hsl_and_back(self) -> None:
        for r, g, b in self.TEST_COLORS:
            h, s, lightness = ColorTools.rgb_to_hsl(r, g, b)
            r2, g2, b2 = ColorTools.hsl_to_rgb(h, s, lightness)
            assert abs(r - r2) <= 1, f"R diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"
            assert abs(g - g2) <= 1, f"G diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"
            assert abs(b - b2) <= 1, f"B diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"

    def test_rgb_to_cmyk_and_back(self) -> None:
        for r, g, b in self.TEST_COLORS:
            c, m, y, k = ColorTools.rgb_to_cmyk(r, g, b)
            r2, g2, b2 = ColorTools.cmyk_to_rgb(c, m, y, k)
            assert abs(r - r2) <= 1, f"R diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"
            assert abs(g - g2) <= 1, f"G diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"
            assert abs(b - b2) <= 1, f"B diff too large for ({r},{g},{b}): got ({r2},{g2},{b2})"

    def test_black_cmyk(self) -> None:
        c, m, y, k = ColorTools.rgb_to_cmyk(0, 0, 0)
        assert k == 1.0, f"Black CMYK k should be 1.0, got {k}"
        assert c == 0.0 and m == 0.0 and y == 0.0

    def test_hsv_black_and_white(self) -> None:
        h, s, v = ColorTools.rgb_to_hsv(0, 0, 0)
        assert v == 0.0
        h, s, v = ColorTools.rgb_to_hsv(255, 255, 255)
        assert s == 0.0 and v == 1.0

    def test_hsl_black_and_white(self) -> None:
        h, s, lightness = ColorTools.rgb_to_hsl(0, 0, 0)
        assert lightness == 0.0
        h, s, lightness = ColorTools.rgb_to_hsl(255, 255, 255)
        assert lightness == 1.0 and s == 0.0


class TestAlphaBlend:
    def test_alpha_blend_half(self) -> None:
        src = pygame.Surface((4, 4))
        src.fill((255, 0, 0))
        dst = pygame.Surface((4, 4))
        dst.fill((0, 0, 255))
        result = ColorTools.alpha_blend(src, dst, 0.5)
        px = result.get_at((0, 0))
        assert px[0] == 127 or px[0] == 128, f"Expected ~127, got {px}"
        assert px[2] == 127 or px[2] == 128

    def test_alpha_blend_full_src(self) -> None:
        src = pygame.Surface((4, 4))
        src.fill((255, 0, 0))
        dst = pygame.Surface((4, 4))
        dst.fill((0, 0, 255))
        result = ColorTools.alpha_blend(src, dst, 1.0)
        px = result.get_at((0, 0))
        assert px[0] == 255 and px[2] == 0

    def test_alpha_blend_full_dst(self) -> None:
        src = pygame.Surface((4, 4))
        src.fill((255, 0, 0))
        dst = pygame.Surface((4, 4))
        dst.fill((0, 0, 255))
        result = ColorTools.alpha_blend(src, dst, 0.0)
        px = result.get_at((0, 0))
        assert px[0] == 0 and px[2] == 255

    def test_alpha_blend_size_mismatch_raises(self) -> None:
        src = pygame.Surface((4, 4))
        dst = pygame.Surface((8, 8))
        try:
            ColorTools.alpha_blend(src, dst, 0.5)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestApplyTint:
    def test_apply_tint_red(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((255, 255, 255))
        tinted = ColorTools.apply_tint(surf, (255, 0, 0))
        px = tinted.get_at((0, 0))
        assert px[0] == 255
        assert px[1] == 0
        assert px[2] == 0


class TestSurfaceArrayBridge:
    def test_surface_to_array_shape(self) -> None:
        surf = pygame.Surface((10, 5))
        arr = ColorTools.surface_to_array(surf)
        assert arr.shape == (10, 5, 3)

    def test_array_to_surface(self) -> None:
        arr = np.zeros((10, 5, 3), dtype=np.uint8)
        arr[:, :, 0] = 255
        surf = ColorTools.array_to_surface(arr)
        assert surf.get_size() == (10, 5)
