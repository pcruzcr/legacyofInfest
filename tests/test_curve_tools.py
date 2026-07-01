"""
Module: test_curve_tools
System: tests
Academic Unit: N/A
Description: Tests for CurveTools: bezier, b_spline, nurbs, catmull_rom,
sample_path, build_bezier_path.
"""
import math

import pygame

from src.framework.processing.curve_tools import CurveTools


class TestBezier:
    def test_bezier_linear(self) -> None:
        pts = [(0.0, 0.0), (100.0, 0.0)]
        samples = CurveTools.bezier(pts, 5)
        assert len(samples) == 5
        assert samples[0] == (0.0, 0.0)
        assert abs(samples[-1][0] - 100.0) < 0.1

    def test_bezier_quadratic_midpoint(self) -> None:
        pts = [(0.0, 0.0), (50.0, 100.0), (100.0, 0.0)]
        samples = CurveTools.bezier(pts, 3)
        assert len(samples) == 3
        # At t=0.5: (0*0.25 + 50*0.5 + 100*0.25 = 50, 0*0.25 + 100*0.5 + 0*0.25 = 50)
        assert abs(samples[1][0] - 50.0) < 0.1
        assert abs(samples[1][1] - 50.0) < 0.1


class TestCatmullRom:
    def test_catmull_rom_two_points(self) -> None:
        pts = [(0.0, 0.0), (100.0, 0.0)]
        samples = CurveTools.catmull_rom(pts, 5)
        assert len(samples) == 5
        assert samples[0] == (0.0, 0.0)
        assert abs(samples[-1][0] - 100.0) < 0.1

    def test_catmull_rom_three_points(self) -> None:
        pts = [(0.0, 0.0), (50.0, 100.0), (100.0, 0.0)]
        samples = CurveTools.catmull_rom(pts, 11)
        assert len(samples) == 11
        # t=0 should be start, t=1 should be end
        assert abs(samples[0][0]) < 0.1
        assert abs(samples[-1][0] - 100.0) < 0.1


class TestBSpline:
    def test_bspline_basic(self) -> None:
        pts = [(0.0, 0.0), (50.0, 100.0), (100.0, 0.0)]
        samples = CurveTools.b_spline(pts, degree=2, n_samples=10)
        assert len(samples) == 10

    def test_bspline_too_few_points(self) -> None:
        pts = [(0.0, 0.0)]
        samples = CurveTools.b_spline(pts, degree=2, n_samples=5)
        assert len(samples) == 1


class TestNURBS:
    def test_nurbs_basic(self) -> None:
        pts = [(0.0, 0.0), (50.0, 100.0), (100.0, 0.0)]
        weights = [1.0, 1.0, 1.0]
        knots = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        samples = CurveTools.nurbs(pts, weights, knots, degree=2, n_samples=10)
        assert len(samples) == 10

    def test_nurbs_too_few_points(self) -> None:
        samples = CurveTools.nurbs([(0.0, 0.0)], [1.0], [0.0, 0.0, 0.0, 1.0, 1.0, 1.0], degree=2, n_samples=5)
        assert len(samples) == 1


class TestSamplePath:
    def test_sample_path_linear(self) -> None:
        pts = [(0.0, 0.0), (100.0, 0.0)]
        p = CurveTools.sample_path(pts, 0.5)
        assert abs(p[0] - 50.0) < 0.1

    def test_sample_path_ends(self) -> None:
        pts = [(0.0, 0.0), (100.0, 100.0)]
        p0 = CurveTools.sample_path(pts, 0.0)
        p1 = CurveTools.sample_path(pts, 1.0)
        assert abs(p0[0]) < 0.1 and abs(p0[1]) < 0.1
        assert abs(p1[0] - 100.0) < 0.1 and abs(p1[1] - 100.0) < 0.1

    def test_sample_path_single_point(self) -> None:
        p = CurveTools.sample_path([(42.0, 99.0)], 0.5)
        assert p == (42.0, 99.0)


class TestBuildBezierPath:
    def test_two_points(self) -> None:
        pts = [pygame.Vector2(0, 0), pygame.Vector2(100, 0)]
        pos = CurveTools.build_bezier_path(pts, 0.5)
        assert abs(pos.x - 50.0) < 0.1

    def test_three_points(self) -> None:
        pts = [pygame.Vector2(0, 0), pygame.Vector2(50, 100), pygame.Vector2(100, 0)]
        pos = CurveTools.build_bezier_path(pts, 0.5)
        assert not math.isnan(pos.x)
        assert not math.isnan(pos.y)

    def test_single_point(self) -> None:
        pts = [pygame.Vector2(42, 99)]
        pos = CurveTools.build_bezier_path(pts, 0.5)
        assert pos.x == 42 and pos.y == 99
