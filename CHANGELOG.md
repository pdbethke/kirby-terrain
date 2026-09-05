# Changelog

All notable changes to `kirby-terrain` are documented in this file.

## 0.2.0

- **`read_uvtt`.** Reads a Universal VTT export (`.dd2vtt` / `.uvtt` /
  `.df2vtt`) into `TerrainObject`s: walls from `line_of_sight` (one object
  per polyline segment, so a polyline of N points becomes N−1 walls), and
  doors/windows from `portals`. Exported from the package root as
  `kirby_terrain.read_uvtt`.
- **Four required keyword arguments, no defaults.** The format carries no
  real-world scale, no materials and no heights, so `metres_per_square`,
  `wall_kind`, `portal_kind` and `wall_height_m` must be supplied by the
  caller — a guessed default would be silently wrong on any map built to
  another convention.

## 0.1.0

Initial release.

- **Geometry in metres.** `Point`, `Segment` and `Polygon` — immutable
  primitives for describing walls, doors, floors and zones in real-world
  units, independent of any map tool's grid or pixel scale.
- **`TerrainObject`.** One type for everything physically present on a map
  — a wall, a door, a window, a floor, a zone — carrying what it blocks
  (sight, movement, sound) and its durability, following the combat
  engine's `Construct` precedent rather than a class per shape.
- **The HERO System 6E2 p173 Objects Table**, transcribed as
  `OBJECT_DURABILITY`/`ObjectDurability`. This package is the platform's
  single home for these PD/ED/BODY values; kirby-combat's own copy
  (`breakables/object_table.py`) is removed in a later change once
  kirby-combat can depend on this package.
- **Zero runtime dependencies.** Nothing here reads a database, calls a
  network, or depends on another Kirby package — it can be unit-tested in
  memory and cannot drift from anything else.

Not included in this release: file-format readers. Universal VTT and
Foundry Scene JSON import, and the kirby-combat adapter that turns a
`TerrainObject` into an engine `Wall`, are later work.
