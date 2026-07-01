"""
Module: math_utils
System: engine.utils
Academic Unit: N/A
Description: Pure math utility functions: lerp, clamp, ease curves,
and vector operations used across the engine and framework.
"""
from __future__ import annotations
import pygame


def lerp(a: float, b: float, t: float) -> float:
    """Linearly interpolate from a to b by factor t (clamped 0..1)."""
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value between minimum and maximum."""
    return max(minimum, min(value, maximum))


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in: t^2."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out: t * (2 - t)."""
    return t * (2.0 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out."""
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t


def vec2_normalize(v: pygame.Vector2) -> pygame.Vector2:
    """Normalize a Vector2. Returns zero vector if length is ~0."""
    length = v.length()
    if length < 1e-10:
        return pygame.Vector2(0, 0)
    return v / length


def vec2_length(v: pygame.Vector2) -> float:
    """Return the length (magnitude) of a Vector2."""
    return v.length()


def vec2_dot(a: pygame.Vector2, b: pygame.Vector2) -> float:
    """Return the dot product of two Vector2s."""
    return a.x * b.x + a.y * b.y


def vec2_distance(a: pygame.Vector2, b: pygame.Vector2) -> float:
    """Return the Euclidean distance between two Vector2s."""
    return a.distance_to(b)
