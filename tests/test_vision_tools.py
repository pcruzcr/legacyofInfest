"""
Module: test_vision_tools
System: tests
Academic Unit: N/A
Description: Tests for VisionTools: threshold, morphology, connected
components, region analysis, watershed, feature extraction, contours,
bounding boxes.
"""
from pathlib import Path

import numpy as np
import pygame

from src.framework.processing.vision_tools import VisionTools, ComponentResult, RegionInfo

OUTPUT_DIR = Path("tests/output/vision")


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _mask_surface(w: int = 32, h: int = 32) -> pygame.Surface:
    """Create a binary mask with two distinct white squares."""
    surf = pygame.Surface((w, h))
    surf.fill((0, 0, 0))
    pygame.draw.rect(surf, (255, 255, 255), (2, 2, 8, 8))
    pygame.draw.rect(surf, (255, 255, 255), (20, 10, 8, 8))
    return surf


class TestThresholdBinary:
    def test_threshold_binary_returns_surface(self) -> None:
        surf = pygame.Surface((16, 16))
        surf.fill((100, 100, 100))
        result = VisionTools.threshold_binary(surf, 128)
        assert isinstance(result, pygame.Surface)
        assert result.get_size() == (16, 16)

    def test_threshold_all_white(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((200, 200, 200))
        result = VisionTools.threshold_binary(surf, 100)
        px = result.get_at((0, 0))
        assert px[0] == 255

    def test_threshold_all_black(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((50, 50, 50))
        result = VisionTools.threshold_binary(surf, 100)
        px = result.get_at((0, 0))
        assert px[0] == 0

    def test_threshold_invalid_raises(self) -> None:
        surf = pygame.Surface((8, 8))
        try:
            VisionTools.threshold_binary(surf, 300)
            assert False
        except ValueError:
            pass

    def test_threshold_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _mask_surface()
        result = VisionTools.threshold_binary(surf, 50)
        pygame.image.save(result, str(OUTPUT_DIR / "threshold_binary.png"))


class TestThresholdOtsu:
    def test_otsu_returns_tuple(self) -> None:
        surf = _mask_surface()
        mask, t = VisionTools.threshold_otsu(surf)
        assert isinstance(mask, pygame.Surface)
        assert isinstance(t, int)
        assert 0 <= t <= 255

    def test_otsu_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _mask_surface()
        mask, t = VisionTools.threshold_otsu(surf)
        pygame.image.save(mask, str(OUTPUT_DIR / "threshold_otsu.png"))


class TestMorphology:
    def test_erode_reduces_white(self) -> None:
        mask = _mask_surface(32, 32)
        eroded = VisionTools.morphological_erode(mask, 3)
        white_before = np.sum(pygame.surfarray.array3d(mask) > 0)
        white_after = np.sum(pygame.surfarray.array3d(eroded) > 0)
        assert white_after <= white_before

    def test_dilate_increases_white(self) -> None:
        mask = _mask_surface(32, 32)
        dilated = VisionTools.morphological_dilate(mask, 3)
        white_before = np.sum(pygame.surfarray.array3d(mask) > 0)
        white_after = np.sum(pygame.surfarray.array3d(dilated) > 0)
        assert white_after >= white_before

    def test_open_returns_surface(self) -> None:
        mask = _mask_surface()
        result = VisionTools.morphological_open(mask, 3)
        assert isinstance(result, pygame.Surface)

    def test_close_returns_surface(self) -> None:
        mask = _mask_surface()
        result = VisionTools.morphological_close(mask, 3)
        assert isinstance(result, pygame.Surface)

    def test_morphology_saves_png(self) -> None:
        _ensure_output_dir()
        mask = _mask_surface()
        for name, op in [("erode", VisionTools.morphological_erode),
                         ("dilate", VisionTools.morphological_dilate),
                         ("open", VisionTools.morphological_open),
                         ("close", VisionTools.morphological_close)]:
            result = op(mask, 3)
            pygame.image.save(result, str(OUTPUT_DIR / f"morphological_{name}.png"))


class TestConnectedComponents:
    def test_components_finds_two_regions(self) -> None:
        mask = _mask_surface(32, 32)
        result = VisionTools.connected_components(mask)
        assert isinstance(result, ComponentResult)
        assert result.num_components >= 2
        assert isinstance(result.component_sizes, dict)
        assert result.label_array.shape == (32, 32)

    def test_components_saves_png(self) -> None:
        _ensure_output_dir()
        mask = _mask_surface()
        result = VisionTools.connected_components(mask)
        pygame.image.save(result.label_surface, str(OUTPUT_DIR / "connected_components.png"))


class TestFilterComponentsByArea:
    def test_filter_keeps_large_only(self) -> None:
        mask = _mask_surface()
        result = VisionTools.connected_components(mask)
        filtered = VisionTools.filter_components_by_area(result, 100, 99999)
        assert filtered.num_components <= result.num_components

    def test_filter_invalid_area_raises(self) -> None:
        mask = _mask_surface()
        result = VisionTools.connected_components(mask)
        try:
            VisionTools.filter_components_by_area(result, -1, 100)
            assert False
        except ValueError:
            pass


class TestAnalyzeRegions:
    def test_analyze_returns_list(self) -> None:
        mask = _mask_surface()
        regions = VisionTools.analyze_regions(mask)
        assert isinstance(regions, list)
        if regions:
            r = regions[0]
            assert isinstance(r, RegionInfo)
            assert r.area > 0
            assert len(r.centroid) == 2
            assert isinstance(r.bounding_rect, pygame.Rect)

    def test_sorted_by_area(self) -> None:
        mask = _mask_surface()
        regions = VisionTools.analyze_regions(mask)
        for i in range(len(regions) - 1):
            assert regions[i].area >= regions[i + 1].area

    def test_analyze_saves_png(self) -> None:
        _ensure_output_dir()
        mask = _mask_surface()
        regions = VisionTools.analyze_regions(mask)
        assert isinstance(regions, list)


class TestLargestRegion:
    def test_largest_region_exists(self) -> None:
        mask = _mask_surface()
        region = VisionTools.largest_region(mask)
        if region:
            assert isinstance(region, RegionInfo)
            assert region.area > 0

    def test_largest_region_none(self) -> None:
        surf = pygame.Surface((8, 8))
        surf.fill((0, 0, 0))
        region = VisionTools.largest_region(surf)
        assert region is None


class TestWatershed:
    def test_watershed_returns_tuple(self) -> None:
        surf = _mask_surface(32, 32)
        label_surf, label_arr = VisionTools.watershed_segment(surf)
        assert isinstance(label_surf, pygame.Surface)
        assert isinstance(label_arr, np.ndarray)
        assert label_surf.get_size() == (32, 32)

    def test_watershed_saves_png(self) -> None:
        _ensure_output_dir()
        surf = _mask_surface(32, 32)
        label_surf, _ = VisionTools.watershed_segment(surf)
        pygame.image.save(label_surf, str(OUTPUT_DIR / "watershed.png"))


class TestFeatureExtraction:
    def test_extract_hog(self) -> None:
        surf = pygame.Surface((32, 32))
        surf.fill((100, 100, 100))
        features = VisionTools.extract_hog(surf)
        assert isinstance(features, np.ndarray)
        # HOG: 4*4*2*2*8 = 512
        assert len(features) > 0

    def test_extract_lbp(self) -> None:
        surf = pygame.Surface((32, 32))
        surf.fill((100, 100, 100))
        features = VisionTools.extract_lbp(surf)
        assert isinstance(features, np.ndarray)
        assert len(features) == 256

    def test_extract_color_histogram(self) -> None:
        surf = pygame.Surface((32, 32))
        surf.fill((100, 150, 200))
        features = VisionTools.extract_color_histogram(surf, bins=32)
        assert isinstance(features, np.ndarray)
        assert len(features) == 32 * 3

    def test_extract_features_hog(self) -> None:
        surf = pygame.Surface((32, 32))
        surf.fill((100, 100, 100))
        features = VisionTools.extract_features(surf, method="hog")
        assert len(features) > 0

    def test_extract_features_combined(self) -> None:
        surf = pygame.Surface((32, 32))
        surf.fill((100, 100, 100))
        features = VisionTools.extract_features(surf, method="combined")
        assert len(features) > 512 + 256

    def test_extract_features_invalid_method(self) -> None:
        surf = pygame.Surface((32, 32))
        try:
            VisionTools.extract_features(surf, method="invalid")
            assert False
        except ValueError:
            pass


class TestContours:
    def test_find_contours_returns_list(self) -> None:
        mask = _mask_surface()
        contours = VisionTools.find_contours(mask)
        assert isinstance(contours, list)

    def test_contours_saves_png(self) -> None:
        _ensure_output_dir()
        mask = _mask_surface()
        contours = VisionTools.find_contours(mask)
        assert isinstance(contours, list)


class TestBoundingBoxes:
    def test_bounding_boxes_finds_regions(self) -> None:
        mask = _mask_surface(32, 32)
        rects = VisionTools.bounding_boxes_from_mask(mask)
        assert isinstance(rects, list)
        assert len(rects) >= 2

    def test_bounding_boxes_are_rects(self) -> None:
        mask = _mask_surface()
        rects = VisionTools.bounding_boxes_from_mask(mask)
        for r in rects:
            assert isinstance(r, pygame.Rect)

    def test_bounding_boxes_saves_png(self) -> None:
        _ensure_output_dir()
        mask = _mask_surface()
        rects = VisionTools.bounding_boxes_from_mask(mask)
        assert len(rects) >= 0


class TestSurfaceValidation:
    def test_none_raises(self) -> None:
        try:
            VisionTools.threshold_binary(None, 100)
            assert False
        except TypeError:
            pass

    def test_zero_size_raises(self) -> None:
        surf = pygame.Surface((0, 0))
        try:
            VisionTools.threshold_otsu(surf)
            assert False
        except ValueError:
            pass
