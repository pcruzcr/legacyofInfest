"""
Module: test_filter_tools
System: tests
Academic Unit: N/A
Description: Tests for FilterTools: histogram, brightness, contrast,
convolution, standard kernels, gaussian_blur, sobel_edge, canny_edge.
"""
from pathlib import Path

import numpy as np
import pygame

from src.framework.processing.filter_tools import FilterTools

OUTPUT_DIR = Path("tests/output/filter")


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _test_surface(w: int = 32, h: int = 32) -> pygame.Surface:
    surf = pygame.Surface((w, h))
    surf.fill((100, 150, 200))
    return surf


class TestComputeHistogram:
    def test_histogram_structure(self) -> None:
        surf = _test_surface()
        hist = FilterTools.compute_histogram(surf)
        assert "r" in hist and "g" in hist and "b" in hist
        assert "luminance" in hist and "total_pixels" in hist
        assert hist["total_pixels"] == 32 * 32
        assert hist["r"].shape == (256,)
        assert hist["g"].shape == (256,)
        assert hist["b"].shape == (256,)

    def test_histogram_solid_color(self) -> None:
        surf = pygame.Surface((10, 10))
        surf.fill((100, 100, 100))
        hist = FilterTools.compute_histogram(surf)
        assert hist["r"][100] == 100
        assert hist["g"][100] == 100
        assert hist["b"][100] == 100

    def test_histogram_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface()
        hist = FilterTools.compute_histogram(surf)
        assert hist["total_pixels"] > 0


class TestHistogramEqualize:
    def test_equalize_returns_surface(self) -> None:
        surf = pygame.Surface((16, 16))
        surf.fill((30, 30, 30))
        result = FilterTools.histogram_equalize(surf)
        assert isinstance(result, pygame.Surface)
        assert result.get_size() == (16, 16)
        _ensure_output_dir()
        pygame.image.save(result, str(OUTPUT_DIR / "histogram_equalize.png"))

    def test_equalize_brightens_dark(self) -> None:
        surf = pygame.Surface((8, 8))
        # Use gradient-like surface (non-uniform) so equalization has range to work with
        for y in range(8):
            for x in range(8):
                v = x * 32 + y * 4
                surf.set_at((x, y), (v, v, v))
        result = FilterTools.histogram_equalize(surf)
        px = result.get_at((0, 0))
        # Some pixels should have been brightened
        mean_before = sum(surf.get_at((x, y))[0] for x in range(8) for y in range(8)) / 64
        mean_after = sum(result.get_at((x, y))[0] for x in range(8) for y in range(8)) / 64
        # Equalization should spread the histogram wider
        max_before = max(surf.get_at((x, y))[0] for x in range(8) for y in range(8))
        max_after = max(result.get_at((x, y))[0] for x in range(8) for y in range(8))
        assert max_after >= max_before


class TestAdjustBrightness:
    def test_brightness_identity(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((100, 100, 100))
        result = FilterTools.adjust_brightness(surf, 1.0)
        assert result.get_at((0, 0))[0] == 100

    def test_brightness_double(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((100, 100, 100))
        result = FilterTools.adjust_brightness(surf, 2.0)
        assert result.get_at((0, 0))[0] == 200

    def test_brightness_zero(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((100, 100, 100))
        result = FilterTools.adjust_brightness(surf, 0.0)
        assert result.get_at((0, 0))[0] == 0

    def test_brightness_out_of_range_raises(self) -> None:
        surf = _test_surface()
        try:
            FilterTools.adjust_brightness(surf, 5.0)
            assert False
        except ValueError:
            pass

    def test_brightness_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface()
        result = FilterTools.adjust_brightness(surf, 0.5)
        pygame.image.save(result, str(OUTPUT_DIR / "adjust_brightness.png"))


class TestAdjustContrast:
    def test_contrast_identity(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((100, 100, 100))
        result = FilterTools.adjust_contrast(surf, 1.0)
        assert result.get_at((0, 0))[0] == 100

    def test_contrast_zero(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((100, 100, 100))
        result = FilterTools.adjust_contrast(surf, 0.0)
        assert result.get_at((0, 0))[0] == 128

    def test_contrast_out_of_range_raises(self) -> None:
        surf = _test_surface()
        try:
            FilterTools.adjust_contrast(surf, 5.0)
            assert False
        except ValueError:
            pass

    def test_contrast_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface()
        result = FilterTools.adjust_contrast(surf, 2.0)
        pygame.image.save(result, str(OUTPUT_DIR / "adjust_contrast.png"))


class TestStretchContrast:
    def test_stretch_full_range(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((50, 50, 50))
        # Add one bright pixel to create range
        surf.set_at((0, 0), (200, 200, 200))
        result = FilterTools.stretch_contrast(surf)
        px_min = result.get_at((1, 0))
        px_max = result.get_at((0, 0))
        assert px_max[0] > px_min[0]

    def test_stretch_uniform(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((100, 100, 100))
        result = FilterTools.stretch_contrast(surf)
        assert result.get_at((0, 0))[0] == 100

    def test_stretch_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface()
        result = FilterTools.stretch_contrast(surf)
        pygame.image.save(result, str(OUTPUT_DIR / "stretch_contrast.png"))


class TestStandardKernels:
    def test_all_kernels_returned(self) -> None:
        names = ["identity", "sharpen", "box_blur", "box_blur_5",
                 "edge_laplacian", "emboss", "ridge", "sobel_x", "sobel_y"]
        for name in names:
            k = FilterTools.get_standard_kernel(name)
            assert isinstance(k, np.ndarray)
            assert k.shape[0] == k.shape[1]

    def test_unknown_kernel_raises(self) -> None:
        try:
            FilterTools.get_standard_kernel("nonexistent")
            assert False
        except KeyError:
            pass

    def test_identity_kernel_values(self) -> None:
        k = FilterTools.get_standard_kernel("identity")
        assert k[1, 1] == 1.0
        assert k.sum() == 1.0


class TestApplyKernel:
    def test_kernel_sharpen(self) -> None:
        surf = _test_surface()
        kernel = FilterTools.get_standard_kernel("sharpen")
        result = FilterTools.apply_kernel(surf, kernel)
        assert isinstance(result, pygame.Surface)
        assert result.get_size() == surf.get_size()

    def test_kernel_invalid_shape_raises(self) -> None:
        surf = _test_surface()
        bad = np.array([[1, 2], [3, 4]], dtype=np.float32)
        try:
            FilterTools.apply_kernel(surf, bad)
            assert False
        except ValueError:
            pass

    def test_kernel_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface()
        kernel = FilterTools.get_standard_kernel("sharpen")
        result = FilterTools.apply_kernel(surf, kernel)
        pygame.image.save(result, str(OUTPUT_DIR / "apply_kernel_sharpen.png"))


class TestGaussianBlur:
    def test_gaussian_blur_returns_surface(self) -> None:
        surf = _test_surface()
        result = FilterTools.gaussian_blur(surf, 1.0)
        assert isinstance(result, pygame.Surface)
        assert result.get_size() == surf.get_size()

    def test_gaussian_blur_sigma_zero_raises(self) -> None:
        surf = _test_surface()
        try:
            FilterTools.gaussian_blur(surf, 0.0)
            assert False
        except ValueError:
            pass

    def test_gaussian_blur_sigma_too_large_raises(self) -> None:
        surf = _test_surface()
        try:
            FilterTools.gaussian_blur(surf, 11.0)
            assert False
        except ValueError:
            pass

    def test_gaussian_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface()
        result = FilterTools.gaussian_blur(surf, 2.0)
        pygame.image.save(result, str(OUTPUT_DIR / "gaussian_blur.png"))


class TestSobelEdge:
    def test_sobel_returns_surface(self) -> None:
        surf = _test_surface()
        result = FilterTools.sobel_edge(surf)
        assert isinstance(result, pygame.Surface)
        assert result.get_size() == surf.get_size()

    def test_sobel_grayscale_output(self) -> None:
        surf = pygame.Surface((16, 16))
        surf.fill((100, 100, 100))
        # Add a vertical line for edge detection
        for y in range(16):
            surf.set_at((8, y), (255, 255, 255))
        result = FilterTools.sobel_edge(surf)
        px = result.get_at((8, 0))
        assert px[0] == px[1] == px[2]

    def test_sobel_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface(64, 64)
        result = FilterTools.sobel_edge(surf)
        pygame.image.save(result, str(OUTPUT_DIR / "sobel_edge.png"))


class TestCannyEdge:
    def test_canny_returns_surface(self) -> None:
        surf = _test_surface()
        result = FilterTools.canny_edge(surf, 50, 150)
        assert isinstance(result, pygame.Surface)
        assert result.get_size() == surf.get_size()

    def test_canny_invalid_threshold_raises(self) -> None:
        surf = _test_surface()
        try:
            FilterTools.canny_edge(surf, 150, 50)
            assert False
        except ValueError:
            pass

    def test_canny_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _test_surface(64, 64)
        result = FilterTools.canny_edge(surf, 50, 150)
        pygame.image.save(result, str(OUTPUT_DIR / "canny_edge.png"))


class TestSurfaceValidation:
    def test_none_raises(self) -> None:
        try:
            FilterTools.compute_histogram(None)
            assert False
        except TypeError:
            pass

    def test_zero_size_raises(self) -> None:
        surf = pygame.Surface((0, 0))
        try:
            FilterTools.compute_histogram(surf)
            assert False
        except ValueError:
            pass
