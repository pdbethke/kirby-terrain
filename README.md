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

## Map Readers

Readers for map-tool exports (FoundryVTT, etc.) arrive in a later change. They translate whatever units an export uses into metres and instantiate these types.

## License

PolyForm Noncommercial License 1.0.0. See `LICENSE` for details.
