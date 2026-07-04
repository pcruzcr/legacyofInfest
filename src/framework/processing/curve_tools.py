"""
Module: curve_tools
System: framework.processing
Academic Unit: Phase 8 (Curve Mathematics)
Description: CurveTools class with Bézier, B-spline, NURBS, Catmull-Rom
spline evaluation utilities.
"""
from __future__ import annotations

import math

import pygame


class CurveTools:
    """Curve evaluation utilities. All methods are classmethods."""

    @classmethod
    def bezier(
        cls,
        control_points: list[tuple[float, float]],
        n_samples: int,
    ) -> list[tuple[float, float]]:
        """Evaluate a Bézier curve of degree = len(control_points) - 1."""
        n = len(control_points)
        if n < 2:
            return control_points
        pts = [pygame.Vector2(p) for p in control_points]
        result: list[tuple[float, float]] = []
        for i in range(n_samples):
            t = i / max(n_samples - 1, 1)
            result.append(cls._eval_bernstein(pts, t))
        return result

    @classmethod
    def b_spline(
        cls,
        control_points: list[tuple[float, float]],
        degree: int,
        n_samples: int,
    ) -> list[tuple[float, float]]:
        """Evaluate a uniform B-spline curve."""
        n = len(control_points)
        if n < degree + 1 or n < 2:
            return control_points
        pts = [pygame.Vector2(p) for p in control_points]
        knots = cls._uniform_knots(n, degree)
        result: list[tuple[float, float]] = []
        t_min = knots[degree]
        t_max = knots[n]
        for i in range(n_samples):
            t = t_min + (t_max - t_min) * (i / max(n_samples - 1, 1))
            result.append(cls._eval_bspline(pts, knots, degree, t))
        return result

    @classmethod
    def nurbs(
        cls,
        control_points: list[tuple[float, float]],
        weights: list[float],
        knots: list[float],
        degree: int,
        n_samples: int,
    ) -> list[tuple[float, float]]:
        """Evaluate a NURBS curve with given weights and knot vector."""
        n = len(control_points)
        if n < degree + 1 or n < 2:
            return control_points
        pts = [pygame.Vector2(p) for p in control_points]
        result: list[tuple[float, float]] = []
        t_min = knots[degree]
        t_max = knots[len(knots) - degree - 1]
        for i in range(n_samples):
            t = t_min + (t_max - t_min) * (i / max(n_samples - 1, 1))
            result.append(cls._eval_nurbs(pts, weights, knots, degree, t))
        return result

    @classmethod
    def catmull_rom(
        cls,
        control_points: list[tuple[float, float]],
        n_samples: int,
    ) -> list[tuple[float, float]]:
        """Evaluate a Catmull-Rom spline passing through control_points."""
        n = len(control_points)
        if n < 2:
            return control_points
        if n == 2:
            return cls.bezier(control_points, n_samples)
        pts = [pygame.Vector2(p) for p in control_points]
        result: list[tuple[float, float]] = []
        for i in range(n_samples):
            t = i / max(n_samples - 1, 1)
            result.append(cls._eval_catmull_path(pts, t))
        return result

    @classmethod
    def sample_path(
        cls,
        points: list[tuple[float, float]],
        t: float,
    ) -> tuple[float, float]:
        """Interpolate along a pre-sampled path. t in [0, 1]."""
        n = len(points)
        if n < 2:
            return points[0] if n == 1 else (0.0, 0.0)
        clamped_t = max(0.0, min(1.0, t))
        index = clamped_t * (n - 1)
        i0 = min(int(index), n - 2)
        frac = index - i0
        x0, y0 = points[i0]
        x1, y1 = points[i0 + 1]
        return (x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)

    @classmethod
    def build_bezier_path(
        cls,
        waypoints: list[pygame.Vector2],
        t: float,
    ) -> pygame.Vector2:
        """Smooth Catmull-Rom interpolation through waypoints, t in [0, 1]."""
        n = len(waypoints)
        if n < 2:
            return waypoints[0] if n == 1 else pygame.Vector2(0, 0)
        if n == 2:
            return waypoints[0].lerp(waypoints[1], max(0.0, min(1.0, t)))
        clamped_t = max(0.0, min(1.0, t))
        total_segments = n - 1
        raw_index = clamped_t * total_segments
        seg_index = min(int(raw_index), total_segments - 1)
        local_t = max(0.0, raw_index - seg_index)
        i0 = max(0, seg_index - 1)
        i1 = seg_index
        i2 = min(n - 1, seg_index + 1)
        i3 = min(n - 1, seg_index + 2)
        return cls._eval_catmull(waypoints[i0], waypoints[i1], waypoints[i2], waypoints[i3], local_t)

    @classmethod
    def _eval_bernstein(cls, pts: list[pygame.Vector2], t: float) -> tuple[float, float]:
        """Evaluate Bézier via Bernstein basis (De Casteljau)."""
        n = len(pts) - 1
        result = pygame.Vector2(0, 0)
        for i, p in enumerate(pts):
            coeff = math.comb(n, i) * (t ** i) * ((1.0 - t) ** (n - i))
            result += p * coeff
        return (result.x, result.y)

    @classmethod
    def _uniform_knots(cls, n: int, degree: int) -> list[float]:
        knots: list[float] = []
        m = n + degree + 1
        for i in range(m):
            if i < degree:
                knots.append(0.0)
            elif i > n:
                knots.append(float(m - 2 * degree))
            else:
                knots.append(float(i - degree))
        return knots

    @classmethod
    def _basis_spline(cls, knots: list[float], degree: int, i: int, t: float) -> float:
        if degree == 0:
            return 1.0 if knots[i] <= t < knots[i + 1] else 0.0
        d1 = knots[i + degree] - knots[i]
        d2 = knots[i + degree + 1] - knots[i + 1]
        c1 = ((t - knots[i]) / d1 * cls._basis_spline(knots, degree - 1, i, t)) if d1 != 0 else 0.0
        c2 = ((knots[i + degree + 1] - t) / d2 * cls._basis_spline(knots, degree - 1, i + 1, t)) if d2 != 0 else 0.0
        return c1 + c2

    @classmethod
    def _eval_bspline(cls, pts: list[pygame.Vector2], knots: list[float], degree: int, t: float) -> tuple[float, float]:
        result = pygame.Vector2(0, 0)
        for i, p in enumerate(pts):
            b = cls._basis_spline(knots, degree, i, t)
            result += p * b
        return (result.x, result.y)

    @classmethod
    def _eval_nurbs(cls, pts: list[pygame.Vector2], weights: list[float], knots: list[float], degree: int, t: float) -> tuple[float, float]:
        numerator = pygame.Vector2(0, 0)
        denominator = 0.0
        for i, p in enumerate(pts):
            b = cls._basis_spline(knots, degree, i, t)
            numerator += p * weights[i] * b
            denominator += weights[i] * b
        if denominator == 0:
            return (0.0, 0.0)
        return (numerator.x / denominator, numerator.y / denominator)

    @classmethod
    def _eval_catmull(cls, p0: pygame.Vector2, p1: pygame.Vector2, p2: pygame.Vector2, p3: pygame.Vector2, t: float) -> pygame.Vector2:
        return (
            0.5 * (
                (2.0 * p1)
                + (-p0 + p2) * t
                + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * (t * t)
                + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * (t * t * t)
            )
        )

    @classmethod
    def _eval_catmull_path(cls, pts: list[pygame.Vector2], t: float) -> tuple[float, float]:
        n = len(pts)
        if n < 2:
            return (pts[0].x, pts[0].y) if n == 1 else (0.0, 0.0)
        if n == 2:
            p = pts[0].lerp(pts[1], max(0.0, min(1.0, t)))
            return (p.x, p.y)
        clamped_t = max(0.0, min(1.0, t))
        total = n - 1
        raw = clamped_t * total
        seg = min(int(raw), total - 1)
        lt = max(0.0, raw - seg)
        i0 = max(0, seg - 1)
        i1 = seg
        i2 = min(n - 1, seg + 1)
        i3 = min(n - 1, seg + 2)
        pos = cls._eval_catmull(pts[i0], pts[i1], pts[i2], pts[i3], lt)
        return (pos.x, pos.y)
