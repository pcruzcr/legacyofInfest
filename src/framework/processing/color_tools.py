"""
Module: color_tools
System: framework.processing
Academic Unit: Phase 8 (Color Mathematics)
Description: ColorTools class with RGB/HSV/HSL/CMYK conversions,
alpha blending, tinting, and surface-array bridging.
"""
from __future__ import annotations

import numpy as np
import pygame


class ColorTools:
    """Color space conversion and manipulation utilities."""

    @classmethod
    def rgb_to_hsv(cls, r: int, g: int, b: int) -> tuple[float, float, float]:
        rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
        mx = max(rn, gn, bn)
        mn = min(rn, gn, bn)
        diff = mx - mn
        h = 0.0
        if diff > 1e-10:
            if mx == rn:
                h = 60.0 * (((gn - bn) / diff) % 6.0)
            elif mx == gn:
                h = 60.0 * (((bn - rn) / diff) + 2.0)
            else:
                h = 60.0 * (((rn - gn) / diff) + 4.0)
        if h < 0:
            h += 360.0
        s = diff / mx if mx > 1e-10 else 0.0
        v = mx
        return (h, s, v)

    @classmethod
    def hsv_to_rgb(cls, h: float, s: float, v: float) -> tuple[int, int, int]:
        c = v * s
        hp = h / 60.0
        x = c * (1.0 - abs(hp % 2.0 - 1.0))
        m = v - c
        if hp < 1.0:
            rn, gn, bn = c, x, 0.0
        elif hp < 2.0:
            rn, gn, bn = x, c, 0.0
        elif hp < 3.0:
            rn, gn, bn = 0.0, c, x
        elif hp < 4.0:
            rn, gn, bn = 0.0, x, c
        elif hp < 5.0:
            rn, gn, bn = x, 0.0, c
        else:
            rn, gn, bn = c, 0.0, x
        return (round((rn + m) * 255), round((gn + m) * 255), round((bn + m) * 255))

    @classmethod
    def rgb_to_hsl(cls, r: int, g: int, b: int) -> tuple[float, float, float]:
        rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
        mx = max(rn, gn, bn)
        mn = min(rn, gn, bn)
        diff = mx - mn
        lightness = (mx + mn) / 2.0
        if diff < 1e-10:
            return (0.0, 0.0, lightness)
        s = diff / (1.0 - abs(2.0 * lightness - 1.0))
        if mx == rn:
            h = 60.0 * (((gn - bn) / diff) % 6.0)
        elif mx == gn:
            h = 60.0 * (((bn - rn) / diff) + 2.0)
        else:
            h = 60.0 * (((rn - gn) / diff) + 4.0)
        if h < 0:
            h += 360.0
        return (h, s, lightness)

    @classmethod
    def hsl_to_rgb(cls, h: float, s: float, lightness: float) -> tuple[int, int, int]:
        c = (1.0 - abs(2.0 * lightness - 1.0)) * s
        hp = h / 60.0
        x = c * (1.0 - abs(hp % 2.0 - 1.0))
        m = lightness - c / 2.0
        if hp < 1.0:
            rn, gn, bn = c, x, 0.0
        elif hp < 2.0:
            rn, gn, bn = x, c, 0.0
        elif hp < 3.0:
            rn, gn, bn = 0.0, c, x
        elif hp < 4.0:
            rn, gn, bn = 0.0, x, c
        elif hp < 5.0:
            rn, gn, bn = x, 0.0, c
        else:
            rn, gn, bn = c, 0.0, x
        return (round((rn + m) * 255), round((gn + m) * 255), round((bn + m) * 255))

    @classmethod
    def rgb_to_cmyk(cls, r: int, g: int, b: int) -> tuple[float, float, float, float]:
        rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
        k = 1.0 - max(rn, gn, bn)
        if k > 0.9999:
            return (0.0, 0.0, 0.0, 1.0)
        c = (1.0 - rn - k) / (1.0 - k)
        m = (1.0 - gn - k) / (1.0 - k)
        y = (1.0 - bn - k) / (1.0 - k)
        return (c, m, y, k)

    @classmethod
    def cmyk_to_rgb(cls, c: float, m: float, y: float, k: float) -> tuple[int, int, int]:
        rn = (1.0 - c) * (1.0 - k)
        gn = (1.0 - m) * (1.0 - k)
        bn = (1.0 - y) * (1.0 - k)
        r = round(max(0.0, min(1.0, rn)) * 255)
        g = round(max(0.0, min(1.0, gn)) * 255)
        b = round(max(0.0, min(1.0, bn)) * 255)
        return (r, g, b)

    @classmethod
    def alpha_blend(cls, src: pygame.Surface, dst: pygame.Surface, alpha: float) -> pygame.Surface:
        if src.get_size() != dst.get_size():
            raise ValueError(
                f"ColorTools.alpha_blend: surfaces must be same size,"
                f" got {src.get_size()} and {dst.get_size()}")
        alpha = max(0.0, min(1.0, alpha))
        src_arr: np.ndarray = pygame.surfarray.array3d(src).astype(np.float32)
        dst_arr: np.ndarray = pygame.surfarray.array3d(dst).astype(np.float32)
        result = (src_arr * alpha + dst_arr * (1.0 - alpha)).astype(np.uint8)
        out = pygame.surfarray.make_surface(result)
        src_alpha = src.get_alpha()
        if src_alpha is not None:
            out.set_alpha(src_alpha)
        return out

    @classmethod
    def apply_tint(cls, surface: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
        w, h = surface.get_size()
        r, g, b = color
        has_alpha = bool(surface.get_flags() & pygame.SRCALPHA) or surface.get_colorkey() is not None
        alpha_arr: np.ndarray | None = None
        try:
            alpha_arr = pygame.surfarray.array_alpha(surface)
            if np.all(alpha_arr == 255) and not (surface.get_flags() & pygame.SRCALPHA):
                has_alpha = False
                alpha_arr = None
            elif np.any(alpha_arr != 255):
                has_alpha = True
        except Exception:
            alpha_arr = None
        arr: np.ndarray = pygame.surfarray.array3d(surface).astype(np.float32)
        arr[:, :, 0] = (arr[:, :, 0] * r / 255.0).clip(0, 255)
        arr[:, :, 1] = (arr[:, :, 1] * g / 255.0).clip(0, 255)
        arr[:, :, 2] = (arr[:, :, 2] * b / 255.0).clip(0, 255)
        rgb_uint8 = arr.astype(np.uint8)
        if has_alpha and alpha_arr is not None:
            rgba = np.zeros((h, w, 4), dtype=np.uint8)
            rgba[:, :, 0:3] = __import__('numpy').transpose(rgb_uint8, (1, 0, 2))
            rgba[:, :, 3] = alpha_arr.T
            try:
                out = pygame.image.frombuffer(rgba.tobytes(), (w, h), "RGBA").convert_alpha()
            except pygame.error:
                out = pygame.image.frombuffer(rgba.tobytes(), (w, h), "RGBA")
            return out
        result = pygame.surfarray.make_surface(rgb_uint8)
        if surface.get_alpha() is not None:
            result.set_alpha(surface.get_alpha())
        if surface.get_colorkey() is not None:
            result.set_colorkey(surface.get_colorkey())
        return result

    @classmethod
    def surface_to_array(cls, surface: pygame.Surface) -> np.ndarray:
        return pygame.surfarray.array3d(surface)

    @classmethod
    def array_to_surface(cls, array: np.ndarray) -> pygame.Surface:
        return pygame.surfarray.make_surface(array)
