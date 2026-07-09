"""
Module: filter_tools
System: framework.processing
Academic Unit: Unit VII (Digital Image Processing)
Description: FilterTools class — histogram, brightness, contrast,
convolution, Gaussian blur, Sobel, and Canny edge detection.
"""
from __future__ import annotations

import numpy as np
import pygame
from scipy.ndimage import convolve, gaussian_filter
import cv2

_STANDARD_KERNELS: dict[str, np.ndarray] = {}


def _init_kernels() -> None:
    global _STANDARD_KERNELS
    _STANDARD_KERNELS = {
        "identity": np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=np.float32),
        "sharpen": np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32),
        "box_blur": np.ones((3, 3), dtype=np.float32) / 9.0,
        "box_blur_5": np.ones((5, 5), dtype=np.float32) / 25.0,
        "edge_laplacian": np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32),
        "emboss": np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], dtype=np.float32),
        "ridge": np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], dtype=np.float32),
        "sobel_x": np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32),
        "sobel_y": np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32),
    }


_init_kernels()


class FilterTools:
    """Image filtering operations. All methods are classmethods."""

    @classmethod
    def compute_histogram(cls, surface: pygame.Surface) -> dict:
        cls._validate_surface(surface)
        arr = pygame.surfarray.array3d(surface)
        h, w, _ = arr.shape
        total = h * w
        r, _ = np.histogram(arr[:, :, 0], bins=256, range=(0, 255))
        g, _ = np.histogram(arr[:, :, 1], bins=256, range=(0, 255))
        b, _ = np.histogram(arr[:, :, 2], bins=256, range=(0, 255))
        lum = np.clip(0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2], 0, 255).astype(np.uint8)
        luminance, _ = np.histogram(lum, bins=256, range=(0, 255))
        return {"r": r.astype(np.int64), "g": g.astype(np.int64), "b": b.astype(np.int64),
                "luminance": luminance.astype(np.int64), "total_pixels": total}

    @classmethod
    def histogram_equalize(cls, surface: pygame.Surface) -> pygame.Surface:
        cls._validate_surface(surface)
        arr = pygame.surfarray.array3d(surface)
        result = np.zeros_like(arr)
        for c in range(3):
            channel = arr[:, :, c]
            hist, _ = np.histogram(channel, 256, (0, 255))
            cdf = hist.cumsum()
            cdf_masked = np.ma.masked_equal(cdf, 0)
            cdf_masked = (cdf_masked - cdf_masked.min()) * 255 / (cdf_masked.max() - cdf_masked.min())
            cdf = np.ma.filled(cdf_masked, 0).astype(np.uint8)
            result[:, :, c] = cdf[channel]
        return pygame.surfarray.make_surface(result)

    @classmethod
    def adjust_brightness(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        cls._validate_surface(surface)
        if factor < 0.0 or factor > 4.0:
            raise ValueError(f"FilterTools.adjust_brightness: factor must be in [0.0, 4.0], got {factor}")
        arr = pygame.surfarray.array3d(surface).astype(np.float32)
        arr = (arr * factor).clip(0, 255).astype(np.uint8)
        result = pygame.surfarray.make_surface(arr)
        if surface.get_alpha():
            result.set_alpha(surface.get_alpha())
        return result

    @classmethod
    def adjust_contrast(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        cls._validate_surface(surface)
        if factor < 0.0 or factor > 4.0:
            raise ValueError(f"FilterTools.adjust_contrast: factor must be in [0.0, 4.0], got {factor}")
        arr = pygame.surfarray.array3d(surface).astype(np.float32)
        arr = ((arr - 128.0) * factor + 128.0).clip(0, 255).astype(np.uint8)
        result = pygame.surfarray.make_surface(arr)
        if surface.get_alpha():
            result.set_alpha(surface.get_alpha())
        return result

    @classmethod
    def stretch_contrast(cls, surface: pygame.Surface) -> pygame.Surface:
        cls._validate_surface(surface)
        arr = pygame.surfarray.array3d(surface).astype(np.float32)
        result = np.zeros_like(arr)
        for c in range(3):
            ch = arr[:, :, c]
            mn, mx = ch.min(), ch.max()
            if mx - mn < 1.0:
                result[:, :, c] = ch
            else:
                result[:, :, c] = ((ch - mn) / (mx - mn) * 255.0).clip(0, 255)
        return pygame.surfarray.make_surface(result.astype(np.uint8))

    @classmethod
    def apply_kernel(cls, surface: pygame.Surface, kernel: np.ndarray) -> pygame.Surface:
        cls._validate_surface(surface)
        if kernel.ndim != 2 or kernel.shape[0] != kernel.shape[1]:
            raise ValueError(f"FilterTools.apply_kernel: kernel must be square, got shape {kernel.shape}")
        n = kernel.shape[0]
        if n < 3 or n > 15 or n % 2 != 1:
            raise ValueError(f"FilterTools.apply_kernel: kernel must be odd-sized 3-15, got {n}")
        arr = pygame.surfarray.array3d(surface).astype(np.float32)
        result = np.zeros_like(arr)
        for c in range(3):
            result[:, :, c] = convolve(arr[:, :, c], kernel, mode="reflect")
        return pygame.surfarray.make_surface(result.clip(0, 255).astype(np.uint8))

    @classmethod
    def get_standard_kernel(cls, name: str) -> np.ndarray:
        if name not in _STANDARD_KERNELS:
            valid = ", ".join(sorted(_STANDARD_KERNELS.keys()))
            raise KeyError(f"Unknown kernel '{name}'. Valid names: {valid}")
        return _STANDARD_KERNELS[name].copy()

    @classmethod
    def gaussian_blur(cls, surface: pygame.Surface, sigma: float) -> pygame.Surface:
        cls._validate_surface(surface)
        if sigma <= 0.0 or sigma > 10.0:
            raise ValueError(f"FilterTools.gaussian_blur: sigma must be in (0.0, 10.0], got {sigma}")
        arr = pygame.surfarray.array3d(surface).astype(np.float32)
        result = np.zeros_like(arr)
        for c in range(3):
            result[:, :, c] = gaussian_filter(arr[:, :, c], sigma=sigma, mode="reflect")
        out = pygame.surfarray.make_surface(result.clip(0, 255).astype(np.uint8))
        if surface.get_alpha():
            out.set_alpha(surface.get_alpha())
        return out

    @classmethod
    def sobel_edge(cls, surface: pygame.Surface) -> pygame.Surface:
        cls._validate_surface(surface)
        arr = pygame.surfarray.array3d(surface)
        gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.uint8)
        gray = gray.T
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        mag = cv2.convertScaleAbs(mag)
        mag = np.clip(mag, 0, 255).astype(np.uint8)
        rgb = np.stack([mag, mag, mag], axis=-1)
        return pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))

    @classmethod
    def canny_edge(cls, surface: pygame.Surface, low_threshold: int, high_threshold: int) -> pygame.Surface:
        cls._validate_surface(surface)
        if low_threshold < 1 or high_threshold > 255 or low_threshold >= high_threshold:
            raise ValueError(
                f"FilterTools.canny_edge: thresholds must satisfy 1 <= low < high <= 255, "
                f"got low={low_threshold}, high={high_threshold}"
            )
        arr = pygame.surfarray.array3d(surface)
        gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.uint8)
        gray = gray.T
        edges = cv2.Canny(gray, low_threshold, high_threshold)
        rgb = np.stack([edges, edges, edges], axis=-1)
        return pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))

    @classmethod
    def _validate_surface(cls, surface: pygame.Surface) -> None:
        if surface is None:
            raise TypeError("FilterTools: surface cannot be None")
        if not isinstance(surface, pygame.Surface):
            raise TypeError(f"FilterTools: expected pygame.Surface, got {type(surface)}")
        w, h = surface.get_size()
        if w == 0 or h == 0:
            raise ValueError("FilterTools: surface has zero dimensions")
