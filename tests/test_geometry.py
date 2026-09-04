"""Geometry, in metres, and nothing else.

There is no pixel below a reader. A source states its own scale, the
reader resolves it, and everything from here down speaks one unit.
"""
import math

import pytest

from kirby_terrain.geometry import Point, Polygon, Segment


def test_a_point_defaults_to_ground_level():
    assert Point(1.0, 2.0).z == 0.0


def test_a_segment_knows_its_length_in_metres():
    s = Segment(Point(0.0, 0.0), Point(3.0, 4.0))
    assert s.length_m == pytest.approx(5.0)


def test_length_accounts_for_elevation():
    """A wall running up a slope is longer than its footprint."""
    s = Segment(Point(0.0, 0.0, 0.0), Point(3.0, 4.0, 12.0))
    assert s.length_m == pytest.approx(13.0)


def test_a_zero_length_segment_is_degenerate():
    p = Point(1.0, 1.0)
    assert Segment(p, p).is_degenerate is True
    assert Segment(Point(0.0, 0.0), Point(1.0, 0.0)).is_degenerate is False


def test_a_polygon_with_fewer_than_three_points_is_degenerate():
    assert Polygon([Point(0.0, 0.0), Point(1.0, 0.0)]).is_degenerate is True


def test_a_polygon_with_no_area_is_degenerate():
    """Three collinear points enclose nothing. Guards the guard: a count
    check alone would call this a valid polygon."""
    collinear = Polygon([Point(0.0, 0.0), Point(1.0, 0.0), Point(2.0, 0.0)])
    assert collinear.is_degenerate is True


def test_a_real_polygon_is_not_degenerate():
    square = Polygon([Point(0.0, 0.0), Point(2.0, 0.0), Point(2.0, 2.0), Point(0.0, 2.0)])
    assert square.is_degenerate is False


def test_a_polygon_knows_its_centroid():
    square = Polygon([Point(0.0, 0.0), Point(2.0, 0.0), Point(2.0, 2.0), Point(0.0, 2.0)])
    c = square.centroid
    assert (c.x, c.y) == pytest.approx((1.0, 1.0))


def test_geometry_is_immutable():
    """These describe what is physically there. Nothing mutates them; a
    frozen dataclass says so and makes them safe to share."""
    p = Point(1.0, 2.0)
    with pytest.raises(Exception):
        p.x = 5.0  # type: ignore[misc]
