"""
Module: math_utils
System: engine
Academic Unit: Framework scaffold
Description: Pure math helpers used throughout the engine and framework.
Easing functions wrap ``pytweening``; vector helpers are thin wrappers
around the standard ``math`` module.  All ``t`` parameters for easing
functions are expected to be in ``[0, 1]``; behaviour outside that range
is undefined.
"""

from __future__ import annotations

import math
from typing import Tuple

import pytweening


# ---------------------------------------------------------------------------
# Interpolation helpers
# ---------------------------------------------------------------------------


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between *a* and *b* at parameter *t*."""
    return a + (b - a) * t


def clamp(value: float, min_v: float, max_v: float) -> float:
    """Clamp *value* to the closed interval ``[min_v, max_v]``."""
    return max(min_v, min(max_v, value))


# ---------------------------------------------------------------------------
# Easing functions (thin pytweening wrappers)
# ---------------------------------------------------------------------------


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in. ``t`` in ``[0, 1]``."""
    return pytweening.easeInQuad(t)


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out. ``t`` in ``[0, 1]``."""
    return pytweening.easeOutQuad(t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out. ``t`` in ``[0, 1]``."""
    return pytweening.easeInOutQuad(t)


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in. ``t`` in ``[0, 1]``."""
    return pytweening.easeInCubic(t)


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out. ``t`` in ``[0, 1]``."""
    return pytweening.easeOutCubic(t)


def ease_out_bounce(t: float) -> float:
    """Bounce ease-out. ``t`` in ``[0, 1]``."""
    return pytweening.easeOutBounce(t)


def ease_out_elastic(t: float) -> float:
    """Elastic ease-out. ``t`` in ``[0, 1]``."""
    return pytweening.easeOutElastic(t)


def ease_in_sine(t: float) -> float:
    """Sine ease-in. ``t`` in ``[0, 1]``."""
    return pytweening.easeInSine(t)


def ease_out_sine(t: float) -> float:
    """Sine ease-out. ``t`` in ``[0, 1]``."""
    return pytweening.easeOutSine(t)


# ---------------------------------------------------------------------------
# 2-D vector helpers (operate on ``(x, y)`` tuples)
# ---------------------------------------------------------------------------


def vec2_normalize(v: Tuple[float, float]) -> Tuple[float, float]:
    """Return a unit vector in the same direction as *v*.

    The zero vector is returned unchanged (length 0 — no exception).
    """
    x, y = v
    length = math.hypot(x, y)
    if length == 0.0:
        return (0.0, 0.0)
    return (x / length, y / length)


def vec2_length(v: Tuple[float, float]) -> float:
    """Euclidean length of the 2-D vector *v*."""
    x, y = v
    return math.hypot(x, y)


def vec2_dot(
    a: Tuple[float, float], b: Tuple[float, float]
) -> float:
    """Dot product of two 2-D vectors."""
    ax, ay = a
    bx, by = b
    return ax * bx + ay * by


def vec2_distance(
    a: Tuple[float, float], b: Tuple[float, float]
) -> float:
    """Euclidean distance between two 2-D points."""
    return math.hypot(a[0] - b[0], a[1] - b[1])
