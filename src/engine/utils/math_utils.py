"""
Module: math_utils
System: engine.utils
Academic Unit: Unit II — Vectors and interpolation

Scalar easing curves and 2D vector helpers.

PERFORMANCE NOTE (AUD-006). Every function here was previously a thin Python
wrapper around a ``@numba.njit`` kernel. That was measured and reverted:

    ease_in_quad     numba 296.8 ns/call vs pure Python 139.8 ns/call  (2.12x SLOWER)
    ease_out_bounce  numba 291.8 ns/call vs pure Python 287.3 ns/call  (1.02x SLOWER)

These bodies are one to five floating-point operations. The cost of crossing
the Python -> nopython boundary (unboxing the float, dispatching on the
signature, boxing the result) is larger than the arithmetic itself, so JIT
compilation made every call slower, not faster. numba additionally cost 419 ms
of the module's 450 ms import time (93%), pulled in ~60 MB of numba+llvmlite,
and — because it was absent from requirements.txt — made the game fail to
start for anyone who installed via the documented path.

numba earns its keep on tight loops over large arrays, not on scalar helpers
called a few hundred times a frame. If a genuine array-level hotspot appears
(a per-pixel filter kernel, a particle integrator over 10k particles), JIT
*that*, and benchmark it before and after.
"""
from __future__ import annotations

import math

import pygame

__all__ = [
    "clamp",
    "ease_in_cubic",
    "ease_in_out_quad",
    "ease_in_quad",
    "ease_in_sine",
    "ease_out_bounce",
    "ease_out_cubic",
    "ease_out_elastic",
    "ease_out_quad",
    "ease_out_sine",
    "lerp",
    "vec2_distance",
    "vec2_dot",
    "vec2_length",
    "vec2_normalize",
]


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation from ``a`` to ``b``; ``t`` is clamped to [0, 1]."""
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Constrain ``value`` to the inclusive range [``minimum``, ``maximum``]."""
    return max(minimum, min(value, maximum))


# ── Easing curves ──────────────────────────────────────────────
# All take normalised time t in [0, 1] and return an eased position.


def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_quad(t: float) -> float:
    return t * (2.0 - t)


def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t


def ease_in_cubic(t: float) -> float:
    return t * t * t


def ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def ease_out_bounce(t: float) -> float:
    if t < 1.0 / 2.75:
        return 7.5625 * t * t
    if t < 2.0 / 2.75:
        t2 = t - 1.5 / 2.75
        return 7.5625 * t2 * t2 + 0.75
    if t < 2.5 / 2.75:
        t2 = t - 2.25 / 2.75
        return 7.5625 * t2 * t2 + 0.9375
    t2 = t - 2.625 / 2.75
    return 7.5625 * t2 * t2 + 0.984375


def ease_out_elastic(t: float) -> float:
    if t < 1e-10:
        return 0.0
    if t > 1.0 - 1e-10:
        return 1.0
    return 2.0 ** (-10.0 * t) * math.sin((t * 10.0 - 0.75) * 2.094) + 1.0


def ease_in_sine(t: float) -> float:
    return 1.0 - math.cos(t * math.pi / 2.0)


def ease_out_sine(t: float) -> float:
    return math.sin(t * math.pi / 2.0)


# ── 2D vector helpers ──────────────────────────────────────────


def vec2_normalize(v: pygame.Vector2) -> pygame.Vector2:
    """Unit vector in the direction of ``v``; zero vector if ``v`` is ~zero."""
    length = math.sqrt(v.x * v.x + v.y * v.y)
    if length < 1e-10:
        return pygame.Vector2(0.0, 0.0)
    return pygame.Vector2(v.x / length, v.y / length)


def vec2_length(v: pygame.Vector2) -> float:
    return math.sqrt(v.x * v.x + v.y * v.y)


def vec2_dot(a: pygame.Vector2, b: pygame.Vector2) -> float:
    return a.x * b.x + a.y * b.y


def vec2_distance(a: pygame.Vector2, b: pygame.Vector2) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)
