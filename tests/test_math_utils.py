"""
Module: test_math_utils
System: tests
Description: Tests for math utility functions (lerp, clamp, ease, vector ops).
"""
from __future__ import annotations
import pygame
import pytest
from src.engine.utils.math_utils import (
    lerp, clamp, ease_in_quad, ease_out_quad, ease_in_out_quad,
    ease_in_cubic, ease_out_cubic, ease_out_bounce, ease_out_elastic,
    ease_in_sine, ease_out_sine,
    vec2_normalize, vec2_length, vec2_dot, vec2_distance,
)


class TestLerp:
    def test_lerp_zero(self) -> None:
        assert lerp(10, 20, 0.0) == 10.0

    def test_lerp_one(self) -> None:
        assert lerp(10, 20, 1.0) == 20.0

    def test_lerp_half(self) -> None:
        assert lerp(10, 20, 0.5) == 15.0

    def test_lerp_clamped_below(self) -> None:
        assert lerp(10, 20, -0.5) == 10.0

    def test_lerp_clamped_above(self) -> None:
        assert lerp(10, 20, 1.5) == 20.0


class TestClamp:
    def test_clamp_within(self) -> None:
        assert clamp(5, 0, 10) == 5

    def test_clamp_below(self) -> None:
        assert clamp(-5, 0, 10) == 0

    def test_clamp_above(self) -> None:
        assert clamp(15, 0, 10) == 10

    def test_clamp_edge_low(self) -> None:
        assert clamp(0, 0, 10) == 0

    def test_clamp_edge_high(self) -> None:
        assert clamp(10, 0, 10) == 10


class TestEaseFunctions:
    def test_ease_in_quad(self) -> None:
        assert ease_in_quad(0.0) == 0.0
        assert ease_in_quad(1.0) == 1.0
        assert ease_in_quad(0.5) == 0.25

    def test_ease_out_quad(self) -> None:
        assert ease_out_quad(0.0) == 0.0
        assert ease_out_quad(1.0) == 1.0
        assert ease_out_quad(0.5) == 0.75

    def test_ease_in_out_quad(self) -> None:
        assert ease_in_out_quad(0.0) == 0.0
        assert ease_in_out_quad(1.0) == 1.0
        assert ease_in_out_quad(0.5) == 0.5
        assert ease_in_out_quad(0.25) == pytest.approx(0.125)

    def test_ease_in_cubic(self) -> None:
        assert ease_in_cubic(0.0) == 0.0
        assert ease_in_cubic(1.0) == 1.0
        assert ease_in_cubic(0.5) == 0.125

    def test_ease_out_cubic(self) -> None:
        assert ease_out_cubic(0.0) == 0.0
        assert ease_out_cubic(1.0) == 1.0
        assert ease_out_cubic(0.5) == pytest.approx(0.875)

    def test_ease_out_bounce(self) -> None:
        assert ease_out_bounce(0.0) == 0.0
        assert ease_out_bounce(1.0) == 1.0

    def test_ease_out_elastic(self) -> None:
        assert ease_out_elastic(0.0) == 0.0
        assert ease_out_elastic(1.0) == 1.0

    def test_ease_in_sine(self) -> None:
        assert ease_in_sine(0.0) == 0.0
        assert ease_in_sine(1.0) == pytest.approx(1.0)

    def test_ease_out_sine(self) -> None:
        assert ease_out_sine(0.0) == 0.0
        assert ease_out_sine(1.0) == pytest.approx(1.0)


class TestVectorFunctions:
    def test_vec2_normalize(self) -> None:
        v = vec2_normalize(pygame.Vector2(3, 4))
        assert abs(v.length() - 1.0) < 1e-6

    def test_vec2_normalize_zero(self) -> None:
        v = vec2_normalize(pygame.Vector2(0, 0))
        assert v == pygame.Vector2(0, 0)

    def test_vec2_length(self) -> None:
        assert vec2_length(pygame.Vector2(3, 4)) == 5.0

    def test_vec2_length_zero(self) -> None:
        assert vec2_length(pygame.Vector2(0, 0)) == 0.0

    def test_vec2_dot(self) -> None:
        result = vec2_dot(pygame.Vector2(1, 0), pygame.Vector2(0, 1))
        assert result == 0.0

    def test_vec2_dot_parallel(self) -> None:
        result = vec2_dot(pygame.Vector2(3, 4), pygame.Vector2(6, 8))
        assert result == pytest.approx(50.0)

    def test_vec2_distance(self) -> None:
        d = vec2_distance(pygame.Vector2(0, 0), pygame.Vector2(3, 4))
        assert d == 5.0
