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
    def compute_histogram(cls, surface: pygame.Surface) -> dict[str, int]:
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
            cdf_min = cdf_masked.min()
            cdf_max = cdf_masked.max()
            if cdf_max - cdf_min < 1:
                result[:, :, c] = channel
            else:
                cdf_masked = (cdf_masked - cdf_min) * 255 / (cdf_max - cdf_min)
                cdf = np.ma.filled(cdf_masked, 0).astype(np.uint8)
                result[:, :, c] = cdf[channel]
        return pygame.surfarray.make_surface(result)

    @classmethod
    def adjust_brightness(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        cls._validate_surface(surface)
        if factor < 0.0 or factor > 4.0:
            raise ValueError(f"FilterTools.adjust_brightness: factor must be in [0.0, 4.0], got {factor}")
        arr: np.ndarray = pygame.surfarray.array3d(surface).astype(np.float32)
        arr = (arr * factor).clip(0, 255).astype(np.uint8)
        result = pygame.surfarray.make_surface(arr)
        src_alpha = surface.get_alpha()
        if src_alpha is not None:
            result.set_alpha(src_alpha)
        return result

    @classmethod
    def adjust_contrast(cls, surface: pygame.Surface, factor: float) -> pygame.Surface:
        cls._validate_surface(surface)
        if factor < 0.0 or factor > 4.0:
            raise ValueError(f"FilterTools.adjust_contrast: factor must be in [0.0, 4.0], got {factor}")
        arr: np.ndarray = pygame.surfarray.array3d(surface).astype(np.float32)
        arr = ((arr - 128.0) * factor + 128.0).clip(0, 255).astype(np.uint8)
        result = pygame.surfarray.make_surface(arr)
        src_alpha = surface.get_alpha()
        if src_alpha is not None:
            result.set_alpha(src_alpha)
        return result

    @classmethod
    def stretch_contrast(cls, surface: pygame.Surface) -> pygame.Surface:
        cls._validate_surface(surface)
        arr: np.ndarray = pygame.surfarray.array3d(surface).astype(np.float32)
        result = np.zeros_like(arr)
        for c in range(3):
            ch = arr[:, :, c]
            mn: np.ndarray = ch.min()
            mx: np.ndarray = ch.max()
            if mx - mn < 1.0:
                result[:, :, c] = ch
            else:
                result[:, :, c] = ((ch - mn) / (mx - mn) * 255.0).clip(0, 255)
        return pygame.surfarray.make_surface(result.astype(np.uint8))

    @classmethod
    def apply_kernel(cls, surface: pygame.Surface, kernel: np.ndarray) -> pygame.Surface:
        from scipy.ndimage import convolve
        cls._validate_surface(surface)
        if kernel.ndim != 2 or kernel.shape[0] != kernel.shape[1]:
            raise ValueError(f"FilterTools.apply_kernel: kernel must be square, got shape {kernel.shape}")
        n = kernel.shape[0]
        if n < 3 or n > 15 or n % 2 != 1:
            raise ValueError(f"FilterTools.apply_kernel: kernel must be odd-sized 3-15, got {n}")
        arr: np.ndarray = pygame.surfarray.array3d(surface).astype(np.float32)
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
        from scipy.ndimage import gaussian_filter
        cls._validate_surface(surface)
        if sigma <= 0.0 or sigma > 10.0:
            raise ValueError(f"FilterTools.gaussian_blur: sigma must be in (0.0, 10.0], got {sigma}")
        arr: np.ndarray = pygame.surfarray.array3d(surface).astype(np.float32)
        result = np.zeros_like(arr)
        for c in range(3):
            result[:, :, c] = gaussian_filter(arr[:, :, c], sigma=sigma, mode="reflect")
        out = pygame.surfarray.make_surface(result.clip(0, 255).astype(np.uint8))
        src_alpha = surface.get_alpha()
        if src_alpha is not None:
            out.set_alpha(src_alpha)
        return out

    @classmethod
    def sobel_edge(cls, surface: pygame.Surface) -> pygame.Surface:
        """Sobel con soporte SRCALPHA (fix B-048).

        Antes creaba la imagen sin canal alfa → rectángulo opaco negro que tapaba
        al jefe y, al recalcularse 1 de cada 5 frames, parpadeaba ~12 Hz.
        Ahora: si la superficie tiene transparencia, el fondo queda transparente
        y el contorno se compone con blending; si es opaca (foto de laboratorio)
        se conserva el fondo negro para no romper el uso académico.
        """
        import cv2
        cls._validate_surface(surface)
        w, h = surface.get_size()
        arr = pygame.surfarray.array3d(surface)  # (w,h,3)
        # Detectar si hay transparencia útil (SRCALPHA o colorkey)
        has_alpha = bool(surface.get_flags() & pygame.SRCALPHA) or surface.get_colorkey() is not None
        alpha_arr = None
        # Intentar leer alpha aunque no tenga flag SRCALPHA (colorkey o surface sin flag pero con alpha)
        try:
            alpha_arr = pygame.surfarray.array_alpha(surface)  # (w,h)
            if np.all(alpha_arr == 255):
                # Todo opaco → foto opaca, no sprite
                has_alpha = False
                alpha_arr = None
            else:
                has_alpha = True
        except Exception:
            # Sin canal alfa legible
            alpha_arr = None
            # Mantener has_alpha basado en flag/colorkey
            if not has_alpha:
                alpha_arr = None
            else:
                # Flag decía que hay alpha pero no se pudo leer → asumir sprite
                pass

        gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]).astype(np.uint8)
        gray = gray.T  # (h,w) para cv2
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        mag = cv2.convertScaleAbs(mag)
        mag = np.clip(mag, 0, 255).astype(np.uint8)  # (h,w)

        if has_alpha:
            # Sprite con transparencia → fondo transparente, contorno blanco con alpha
            rgba: np.ndarray = np.zeros((h, w, 4), dtype=np.uint8)
            # Umbral para evitar ruido: mag>30 es borde
            mask = mag > 30
            rgba[mask, 0] = 255
            rgba[mask, 1] = 255
            rgba[mask, 2] = 255
            # Alpha del borde: usar mag como intensidad (más fuerte = más opaco)
            rgba[mask, 3] = np.clip(mag[mask], 80, 255)
            # Crear surf con alpha y devolver solo el contorno (no el fondo negro)
            # El caller (BossBase) compondrá este contorno encima del sprite original
            # y cacheará el resultado. Para no romper tests que esperan superficie
            # con fondo, devolvemos el contorno transparente aquí.
            try:
                edge_surf = pygame.image.frombuffer(rgba.tobytes(), (w, h), "RGBA").convert_alpha()
            except pygame.error:
                edge_surf = pygame.image.frombuffer(rgba.tobytes(), (w, h), "RGBA")
            return edge_surf

        # Foto opaca / laboratorio → comportamiento clásico (fondo negro, borde blanco)
        rgb = np.stack([mag, mag, mag], axis=-1)  # (h,w,3)
        return pygame.surfarray.make_surface(rgb.transpose(1, 0, 2))

    @classmethod
    def canny_edge(cls, surface: pygame.Surface, low_threshold: int, high_threshold: int) -> pygame.Surface:
        import cv2
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

    # ── Versiones propias, paso a paso (F2.3) ────────────────────────
    #
    # `sobel_edge` y `canny_edge`, arriba, llaman a OpenCV. Están bien: es lo
    # que se usa en la industria y son entre 17 y 50 veces más rápidas. Pero en
    # las Unidades VII y VIII **Sobel y Canny son el contenido**, y quien sólo
    # ve `cv2.Canny(gray, 50, 150)` aprende una API, no un algoritmo.
    #
    # Las dos versiones conviven a propósito, y el laboratorio muestra ambas
    # con sus tiempos: comparar tu implementación con la de referencia es parte
    # de aprender, y descubrir que la tuya es cincuenta veces más lenta
    # también. Ver `framework.processing.edge_detection`.

    @classmethod
    def sobel_edge_propio(cls, surface: pygame.Surface) -> pygame.Surface:
        """Sobel implementado a mano. Ver `edge_detection.sobel`."""
        from src.framework.processing import edge_detection

        cls._validate_surface(surface)
        rgb = pygame.surfarray.array3d(surface).transpose(1, 0, 2)
        bordes = edge_detection.sobel(rgb)
        return cls._gris_a_superficie(bordes)

    @classmethod
    def canny_edge_propio(
        cls, surface: pygame.Surface, low_threshold: int, high_threshold: int,
        sigma: float = 1.4,
    ) -> pygame.Surface:
        """Canny implementado a mano, en sus cinco pasos.

        Ver `edge_detection.canny`. Los umbrales se validan igual que en la
        versión de OpenCV para que las dos se puedan intercambiar sin sorpresas.
        """
        from src.framework.processing import edge_detection

        cls._validate_surface(surface)
        if low_threshold < 1 or high_threshold > 255 or low_threshold >= high_threshold:
            raise ValueError(
                f"FilterTools.canny_edge_propio: thresholds must satisfy "
                f"1 <= low < high <= 255, got low={low_threshold}, "
                f"high={high_threshold}"
            )
        rgb = pygame.surfarray.array3d(surface).transpose(1, 0, 2)
        bordes = edge_detection.canny(
            rgb, float(low_threshold), float(high_threshold), sigma)
        return cls._gris_a_superficie(bordes)

    @staticmethod
    def _gris_a_superficie(gris: np.ndarray) -> pygame.Surface:
        """Convierte una imagen de un canal (alto, ancho) en una superficie.

        La transposición no es decorativa: numpy indexa (fila, columna) y
        pygame.surfarray indexa (x, y). Confundirlas produce una imagen girada
        90 grados, que es un fallo silencioso muy fácil de cometer.
        """
        rgb = np.stack([gris, gris, gris], axis=-1)
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
