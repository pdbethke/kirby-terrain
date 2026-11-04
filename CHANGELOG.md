# Changelog

## 0.4.0 — 2026-11-02

**Terrain can describe cover.**

### Added

Five rows in `OBJECT_DURABILITY`, from the 6E2 p.173 Objects Table: Automobile
(PD 3, ED 3, BODY 15), Armored car (8, 8, 18), Medium tree (5, 4, 8), Large
tree (5, 4, 11) and Furniture, heavy wood (4, 3, 5). All five are resistant.

These are the cover an arena places, so a generated map can stand a squad
behind a car or a tree. Each has a single BODY value in the book, so none is
omitted under the rule that leaves out ranged or open-ended rows.

## 0.3.0 — 2026-09-05

**Terrain can describe a pool.**

### Added

`TerrainObject.elevation_range_m` — the band of space a zone occupies, as
`(lowest, highest)` in metres relative to the ground plane. `None`, the
default, means ordinary terrain standing on the ground and described by
`height_m`.

A band rather than a signed height, matching the combat engine's own
`Construct.elevation_range_m`. It describes a pool two metres deep as
`(-2.0, 0.0)`, a submerged pipe as `(-5.0, -3.0)`, or a gas cloud at head
height as `(1.5, 3.0)`. **A pool is not a hole in the floor**, and a band
says things a signed height cannot.

A band given backwards is rejected rather than accepted silently — `(0.0,
-2.0)` is not a range, it is a mistake, and every consumer's "is this
inside?" test would simply never be true.

`TerrainObject.destructible`, mirroring the engine's predicate.

### Changed

**Terrain may now have no durability at all.** `pd`, `ed` and `body` return
`int | None`, and an object with `kind=None` that states no overrides is not
destructible — water has no BODY, and hitting it does nothing.

Previously an object with `kind=None` had to state all three, so a pool
could not be expressed at all. Stating SOME but not all is still an error:
nothing means "pd 3 and deliberately no ED", so that case is a
half-finished thought rather than a statement about water.

This closes a gap the module design named and the first implementation
dropped: the spec said extent was "`height_m`, and an elevation range for
zones", and only `height_m` was built.

### Note

No map format carries this. Neither Foundry Scene JSON nor Universal VTT
has any notion of water, terrain type, or a region of space — they describe
walls, portals and lights. A pool must be authored, or inferred from the
rendered image. The object model can now hold one either way.

All notable changes to `kirby-terrain` are documented in this file.

## 0.2.0

- **`read_uvtt`.** Reads a Universal VTT export (`.dd2vtt` / `.uvtt` /
  `.df2vtt`) into `TerrainObject`s: walls from `line_of_sight` (one object
  per polyline segment, so a polyline of N points becomes N−1 walls, though
  degenerate segments are dropped so the count can be lower), and
  doors/windows from `portals`. Exported from the package root as
  `kirby_terrain.read_uvtt`.
- **Four required keyword arguments, no defaults.** The format carries no
  real-world scale, no materials and no heights, so `metres_per_square`,
  `wall_kind`, `portal_kind` and `wall_height_m` must be supplied by the
  caller — a guessed default would be silently wrong on any map built to
  another convention.
- **Malformed geometry and a non-boolean `closed` now raise `ValueError`**
  naming the file and the location, instead of a bare `KeyError`/`TypeError`
  from somewhere inside the reader. A portal's `closed` value that is not an
  actual `bool` (e.g. the string `"false"`, which is truthy) is rejected
  rather than coerced. `line_of_sight` must be a list of lists; an empty
  list or a one-point polyline is still legal. The document is now read as
  bytes so JSON's UTF-8 is honoured regardless of the machine's locale.

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
