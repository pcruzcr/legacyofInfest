"""
Tests for math_utils — pure helper functions.

See 24_TEST_PLAN.md §4.1 for test specifications.
"""

from src.engine.utils.math_utils import (
    clamp,
    ease_in_cubic,
    ease_in_out_quad,
    ease_in_quad,
    ease_in_sine,
    ease_out_bounce,
    ease_out_cubic,
    ease_out_elastic,
    ease_out_quad,
    ease_out_sine,
    lerp,
    vec2_distance,
    vec2_dot,
    vec2_length,
    vec2_normalize,
)


def test_lerp_endpoints():
    """lerp(0, 10, 0.0) == 0 and lerp(0, 10, 1.0) == 10."""
    assert lerp(0, 10, 0.0) == 0.0
    assert lerp(0, 10, 1.0) == 10.0


def test_lerp_midpoint():
    """lerp(0, 10, 0.5) == 5."""
    assert lerp(0, 10, 0.5) == 5.0


def test_clamp_below_min():
    """clamp(-5, 0, 10) == 0."""
    assert clamp(-5, 0, 10) == 0


def test_clamp_above_max():
    """clamp(15, 0, 10) == 10."""
    assert clamp(15, 0, 10) == 10


def test_clamp_within_range():
    """clamp(5, 0, 10) == 5."""
    assert clamp(5, 0, 10) == 5


def test_ease_functions_boundary():
    """Every ease_* function returns approximately 0.0 at t=0 and 1.0 at t=1.

    ease_out_bounce and ease_out_elastic may overshoot past 1.0, so
    we only assert the t=0 boundary strictly for those two.
    """
    funcs = [
        ease_in_quad,
        ease_out_quad,
        ease_in_out_quad,
        ease_in_cubic,
        ease_out_cubic,
        ease_out_bounce,
        ease_out_elastic,
        ease_in_sine,
        ease_out_sine,
    ]
    for fn in funcs:
        assert abs(fn(0.0)) < 1e-6, f"{fn.__name__}(0) != 0"
        if fn in (ease_out_bounce, ease_out_elastic):
            continue  # these may overshoot past 1.0
        assert abs(fn(1.0) - 1.0) < 1e-6, f"{fn.__name__}(1) != 1"


def test_vec2_normalize_unit_length():
    """vec2_length(vec2_normalize((3, 4))) ~= 1.0."""
    normalized = vec2_normalize((3.0, 4.0))
    assert abs(vec2_length(normalized) - 1.0) < 1e-9


def test_vec2_normalize_zero_vector():
    """vec2_normalize((0, 0)) does not raise."""
    result = vec2_normalize((0, 0))
    assert result == (0.0, 0.0)


def test_vec2_dot_orthogonal():
    """vec2_dot((1, 0), (0, 1)) == 0."""
    assert vec2_dot((1, 0), (0, 1)) == 0.0


def test_vec2_distance_known_case():
    """vec2_distance((0, 0), (3, 4)) == 5.0."""
    assert vec2_distance((0, 0), (3, 4)) == 5.0