"""
Module: vision_tools
System: framework.processing
Academic Unit: Unit VIII (Image Segmentation and Analysis)
Description: VisionTools class — thresholding, morphology, connected
components, region analysis, watershed, feature extraction (HOG, LBP,
color histogram), contours, and bounding boxes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

import cv2
import numpy as np
import pygame
from skimage.feature import hog, local_binary_pattern
from skimage.measure import regionprops


@dataclass
class ComponentResult:
    label_array: np.ndarray
    num_components: int
    component_sizes: dict[int, int]
    label_surface: pygame.Surface


@dataclass
class RegionInfo:
    label: int
    area: int
    centroid: tuple[float, float]
    bounding_rect: pygame.Rect
    eccentricity: float
    solidity: float
    perimeter: float


class VisionTools:
    """Image segmentation and analysis operations."""

    @classmethod
    def threshold_binary(cls, surface: pygame.Surface, threshold: int) -> pygame.Surface:
        cls._validate_surface(surface)
        if threshold < 0 or threshold > 255:
            raise ValueError(f"VisionTools.threshold_binary: threshold must be in [0, 255], got {threshold}")
        arr = cls._to_gray_array(surface)
        _, binary = cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY)
        rgb = np.stack([binary, binary, binary], axis=-1)
        return pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))

    @classmethod
    def threshold_otsu(cls, surface: pygame.Surface) -> tuple[pygame.Surface, int]:
        cls._validate_surface(surface)
        arr = cls._to_gray_array(surface)
        _, binary, = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        threshold_val = int(_)
        rgb = np.stack([binary, binary, binary], axis=-1)
        result = pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))
        return (result, threshold_val)

    @classmethod
    def morphological_erode(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface:
        return cls._morph_op(surface, kernel_size, cv2.MORPH_ERODE)

    @classmethod
    def morphological_dilate(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface:
        return cls._morph_op(surface, kernel_size, cv2.MORPH_DILATE)

    @classmethod
    def morphological_open(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface:
        return cls._morph_op(surface, kernel_size, cv2.MORPH_OPEN)

    @classmethod
    def morphological_close(cls, surface: pygame.Surface, kernel_size: int) -> pygame.Surface:
        return cls._morph_op(surface, kernel_size, cv2.MORPH_CLOSE)

    @classmethod
    def connected_components(cls, mask_surface: pygame.Surface) -> ComponentResult:
        cls._validate_surface(mask_surface)
        binary = cls._to_binary_array(mask_surface)
        num_labels, label_array, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        component_sizes: dict[int, int] = {}
        for i in range(1, num_labels):
            component_sizes[i] = int(stats[i, cv2.CC_STAT_AREA])
        label_surface = cls._label_array_to_color_surface(label_array, num_labels)
        return ComponentResult(
            label_array=label_array,
            num_components=num_labels - 1,
            component_sizes=component_sizes,
            label_surface=label_surface,
        )

    @classmethod
    def filter_components_by_area(cls, result: ComponentResult, min_area: int, max_area: int) -> ComponentResult:
        if min_area < 0:
            raise ValueError(f"VisionTools.filter_components_by_area: min_area must be >= 0, got {min_area}")
        if max_area <= min_area:
            raise ValueError(
                f"VisionTools.filter_components_by_area: "
                f"max_area must be > min_area, got max={max_area}, min={min_area}")
        filtered = np.zeros_like(result.label_array)
        sizes: dict[int, int] = {}
        for label_id, area in result.component_sizes.items():
            if min_area <= area <= max_area:
                filtered[result.label_array == label_id] = label_id
                sizes[label_id] = area
        num = len(sizes)
        label_surface = cls._label_array_to_color_surface(filtered, num + 1)
        return ComponentResult(
            label_array=filtered, num_components=num,
            component_sizes=sizes, label_surface=label_surface)

    @classmethod
    def analyze_regions(cls, mask_surface: pygame.Surface) -> list[RegionInfo]:
        cls._validate_surface(mask_surface)
        binary = cls._to_binary_array(mask_surface)
        num_labels, label_array = cv2.connectedComponents(binary, connectivity=8)
        regions: list[RegionInfo] = []
        props = regionprops(label_array)
        for prop in props:
            y1, x1, y2, x2 = prop.bbox
            regions.append(RegionInfo(
                label=int(prop.label),
                area=int(prop.area),
                centroid=(float(prop.centroid[1]), float(prop.centroid[0])),
                bounding_rect=pygame.Rect(int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                eccentricity=float(prop.eccentricity),
                solidity=float(prop.solidity),
                perimeter=float(prop.perimeter),
            ))
        regions.sort(key=lambda r: r.area, reverse=True)
        return regions

    @classmethod
    def largest_region(cls, mask_surface: pygame.Surface) -> RegionInfo | None:
        regions = cls.analyze_regions(mask_surface)
        return regions[0] if regions else None

    @classmethod
    def watershed_segment(cls, surface: pygame.Surface) -> tuple[pygame.Surface, np.ndarray]:
        cls._validate_surface(surface)
        arr = cls._to_gray_array(surface)
        blurred = cv2.GaussianBlur(arr, (5, 5), 1.0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist, 0.7 * dist.max(), 255, cv2.THRESH_BINARY)
        sure_fg = sure_fg.astype(np.uint8)
        unknown = cv2.subtract(cv2.dilate(blurred, np.ones((3, 3), np.uint8), iterations=2), sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        bgr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        markers = cv2.watershed(bgr, markers)
        label_surface = cls._label_array_to_color_surface(markers, markers.max() + 1)
        return (label_surface, markers)

    @classmethod
    def extract_features(
        cls, surface: pygame.Surface,
        method: Literal["hog", "lbp", "color_hist", "combined"] = "hog"
    ) -> np.ndarray:
        cls._validate_surface(surface)
        if method == "hog":
            return cls.extract_hog(surface)
        elif method == "lbp":
            return cls.extract_lbp(surface)
        elif method == "color_hist":
            return cls.extract_color_histogram(surface)
        elif method == "combined":
            hog_feat = cls.extract_hog(surface)
            lbp_feat = cls.extract_lbp(surface)
            hist_feat = cls.extract_color_histogram(surface)
            return cast(np.ndarray, np.concatenate([hog_feat, lbp_feat, hist_feat]))
        else:
            raise ValueError(
                f"VisionTools.extract_features: unknown method '{method}'. "
                f"Use 'hog', 'lbp', 'color_hist', or 'combined'.")

    @classmethod
    def extract_hog(cls, surface: pygame.Surface) -> np.ndarray:
        cls._validate_surface(surface)
        resized = cls._resize_canonical(surface)
        gray = cls._to_gray_array(resized)
        features = hog(
            gray,
            orientations=8,
            pixels_per_cell=(8, 8),
            cells_per_block=(2, 2),
            block_norm="L2-Hys",
        )
        return np.asarray(features) if isinstance(features, np.ndarray) else np.array(features)

    @classmethod
    def extract_lbp(cls, surface: pygame.Surface) -> np.ndarray:
        cls._validate_surface(surface)
        resized = cls._resize_canonical(surface)
        gray = cls._to_gray_array(resized)
        lbp = local_binary_pattern(gray, 8, 1, method="uniform")
        hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256), density=True)
        return np.asarray(hist) if isinstance(hist, np.ndarray) else np.array(hist)

    @classmethod
    def extract_color_histogram(cls, surface: pygame.Surface, bins: int = 256) -> np.ndarray:
        cls._validate_surface(surface)
        if bins < 4 or bins > 256:
            raise ValueError(f"VisionTools.extract_color_histogram: bins must be in [4, 256], got {bins}")
        arr = pygame.surfarray.array3d(surface)
        result: list[np.ndarray] = []
        for c in range(3):
            hist, _ = np.histogram(arr[:, :, c].ravel(), bins=bins, range=(0, 255), density=True)
            result.append(hist)
        return cast(np.ndarray, np.concatenate(result))

    @classmethod
    def find_contours(cls, mask_surface: pygame.Surface) -> list[np.ndarray]:
        cls._validate_surface(mask_surface)
        binary = cls._to_binary_array(mask_surface)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return list(contours)

    @classmethod
    def bounding_boxes_from_mask(cls, mask_surface: pygame.Surface) -> list[pygame.Rect]:
        cls._validate_surface(mask_surface)
        binary = cls._to_binary_array(mask_surface)
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        rects: list[pygame.Rect] = []
        for i in range(1, num_labels):
            x = int(stats[i, cv2.CC_STAT_LEFT])
            y = int(stats[i, cv2.CC_STAT_TOP])
            w = int(stats[i, cv2.CC_STAT_WIDTH])
            h = int(stats[i, cv2.CC_STAT_HEIGHT])
            rects.append(pygame.Rect(x, y, w, h))
        return rects

    @classmethod
    def _validate_surface(cls, surface: pygame.Surface) -> None:
        if surface is None:
            raise TypeError("VisionTools: surface cannot be None")
        if not isinstance(surface, pygame.Surface):
            raise TypeError(f"VisionTools: expected pygame.Surface, got {type(surface)}")
        w, h = surface.get_size()
        if w == 0 or h == 0:
            raise ValueError("VisionTools: surface has zero dimensions")

    @classmethod
    def _to_gray_array(cls, surface: pygame.Surface) -> np.ndarray:
        arr = pygame.surfarray.array3d(surface)
        gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.uint8)
        return np.asarray(gray.T) if isinstance(gray, np.ndarray) else np.array(gray.T)

    @classmethod
    def _to_binary_array(cls, mask_surface: pygame.Surface) -> np.ndarray:
        arr = pygame.surfarray.array3d(mask_surface)
        gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.uint8)
        _, binary = cv2.threshold(gray.T, 127, 255, cv2.THRESH_BINARY)
        return np.asarray(binary)

    @classmethod
    def _label_array_to_color_surface(cls, label_array: np.ndarray, num_labels: int) -> pygame.Surface:
        h, w = label_array.shape
        colors = [
            (0, 0, 0),
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (128, 255, 0), (255, 128, 0), (0, 128, 255),
        ]
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(1, num_labels):
            color = colors[i % len(colors)]
            mask = label_array == i
            rgb[mask] = color
        return pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))

    @classmethod
    def _resize_canonical(cls, surface: pygame.Surface) -> pygame.Surface:
        w, h = surface.get_size()
        if w == 32 and h == 32:
            return surface
        arr = pygame.surfarray.array3d(surface)
        arr = arr.transpose(1, 0, 2)
        resized = cv2.resize(arr, (32, 32), interpolation=cv2.INTER_AREA)
        resized = resized.transpose(1, 0, 2)
        return pygame.surfarray.make_surface(resized)

    @classmethod
    def _morph_op(cls, surface: pygame.Surface, kernel_size: int, op: int) -> pygame.Surface:
        cls._validate_surface(surface)
        if kernel_size < 1:
            raise ValueError(f"VisionTools: kernel_size must be >= 1, got {kernel_size}")
        binary = cls._to_binary_array(surface)
        kernel: np.ndarray = np.ones((kernel_size, kernel_size), np.uint8)
        result = cv2.morphologyEx(binary, op, kernel)
        rgb = np.stack([result, result, result], axis=-1)
        return pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))
