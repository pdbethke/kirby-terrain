# kirby-terrain

Terrain objects, geometry and durability for the Kirby HERO System platform.

## Overview

This package provides geometric primitives — points, segments and polygons — all measured in metres. It has **zero dependencies** and holds **no game rules**. It describes only what is physically present.

### Key Properties

- **All units are metres.** Scale conversion belongs at a source boundary (e.g. a map-tool reader) and does not leak inward.
- **No rules.** A `Segment` does not know whether it blocks sight. A `Polygon` does not know how much damage breaks it. These types describe shape and space; rules live in other repositories.
- **Immutable.** All types are frozen dataclasses, safe to share and reason about.

## Geometry

### Point
A position in three dimensions, with `x`, `y`, and optional `z` (height above ground, defaulting to 0.0).

### Segment
A straight line between two points. Provides a `length_m` property (accounting for elevation) and an `is_degenerate` check.

### Polygon
A closed region defined by a list of points. Provides:
- `is_degenerate`: True if fewer than three points, or if points are collinear (no area).
- `centroid`: The average of the vertices, suitable for labels or spawns.

## Durability

Durability data (how hard materials are to break) comes from HERO System 6E2, p173. This package holds no durability logic; that belongs in other layers.

## TerrainObject

`TerrainObject` is one primitive for everything physically present — a wall, a door, a window, a floor, a zone. It carries a `shape` (`Segment` or `Polygon`), a `height_m`, and an optional `kind` naming what it IS.

When `kind` is a row of `OBJECT_DURABILITY` (a wall, door or pane of glass from the 6E2 p173 Objects Table), `pd`, `ed` and `body` come from that table, overridable per object. When `kind` is `None` — "not identified": a floor, a tree, a vehicle, anything the table has no row for — the caller must supply `pd_override`, `ed_override` and `body_override` directly.

```python
from kirby_terrain import OBJECT_DURABILITY, Point, Segment, TerrainObject

wall = TerrainObject(
    id="w1", name="north wall", kind="brick wall",
    shape=Segment(Point(0.0, 0.0), Point(5.0, 0.0)),
    height_m=3.0,
)
wall.pd, wall.ed, wall.body  # (5, 10, 3), from the table
```

## Map Readers

Readers for map-tool exports (FoundryVTT, etc.) arrive in a later change. They translate whatever units an export uses into metres and instantiate these types.

## License

PolyForm Noncommercial License 1.0.0. See `LICENSE` for details.
