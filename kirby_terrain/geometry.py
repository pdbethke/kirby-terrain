"""Shapes, in metres.

Every coordinate and every length in this package is metres. Scale
conversion happens at a source boundary — a reader turns whatever units an
export uses into these — and never leaks inward. Nothing below a reader has
to know what a pixel was.

These types describe what is physically present. They carry no rules: a
Segment does not know whether it blocks sight, and must not learn.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """A position in metres. `z` is height above the ground plane."""
    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class Segment:
    """A straight run between two points — a wall, a door, a railing."""
    start: Point
    end: Point

    @property
    def length_m(self) -> float:
        return math.dist(
            (self.start.x, self.start.y, self.start.z),
            (self.end.x, self.end.y, self.end.z),
        )

    @property
    def is_degenerate(self) -> bool:
        """A segment going nowhere. Readers produce these from malformed
        exports; callers should skip rather than reason about them.

        This is an exact-equality check (`length_m == 0.0`), not a
        tolerance. A segment that is merely very short is not degenerate;
        filtering near-zero-length segments is the caller's job."""
        return self.length_m == 0.0


@dataclass(frozen=True)
class Polygon:
    """A closed region — a floor, a hazard zone, a room."""
    points: tuple[Point, ...] | list[Point]

    def __post_init__(self) -> None:
        """Coerce the points list to a tuple for true immutability."""
        object.__setattr__(self, "points", tuple(self.points))

    @property
    def is_degenerate(self) -> bool:
        """Fewer than three points, or three-plus points enclosing no area.
        The area test matters: collinear points pass a count check and
        enclose nothing.

        This is an exact-equality check (`_twice_signed_area() == 0.0`), not
        a tolerance; filtering near-degenerate shapes is the caller's job.
        The area is computed in the XY plan view only, so a vertical
        polygon — an upright pane standing in the XZ or YZ plane — reports
        as degenerate here even though it encloses real area in 3D."""
        if len(self.points) < 3:
            return True
        return self._twice_signed_area() == 0.0

    @property
    def centroid(self) -> Point:
        """The average of the vertices. Adequate for placing a label or a
        spawn; this is not the area centroid of a concave shape."""
        n = len(self.points)
        if n == 0:
            return Point(0.0, 0.0)
        return Point(
            sum(p.x for p in self.points) / n,
            sum(p.y for p in self.points) / n,
            sum(p.z for p in self.points) / n,
        )

    def _twice_signed_area(self) -> float:
        total = 0.0
        for i, a in enumerate(self.points):
            b = self.points[(i + 1) % len(self.points)]
            total += a.x * b.y - b.x * a.y
        return total
