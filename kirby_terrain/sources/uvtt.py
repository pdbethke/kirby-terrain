"""Universal VTT (`.dd2vtt` / `.uvtt` / `.df2vtt`).

The interchange format created for Dungeondraft — the extension is literally
"dungeondraft to vtt" — and emitted by other map tools including Dungeon
Alchemist. One reader therefore serves several sources.

WHAT THIS FORMAT DOES NOT TELL YOU, measured against a real export:

  * **No real-world scale.** It carries `pixels_per_grid`, `map_size` and
    `map_origin`, all in grid squares, and nothing saying how long a square
    is. `metres_per_square` is required for that reason and must never gain
    a default: a convention-shaped guess is silently wrong on any map built
    to another scale, and every distance in this platform is metres.
  * **No materials.** Nothing says what a wall is made of, so `wall_kind`
    and `portal_kind` are required too.
  * **No heights.** A plan view has none, so `wall_height_m` is required.
  * **`map_origin` is assumed zero.** `resolution.map_origin` exists in the
    format but this reader never reads it — `line_of_sight` and `portals`
    coordinates are treated as already absolute. The fixture happens to
    carry `map_origin: {0, 0}`, so a nonzero origin has never been
    exercised against this reader; if one turns up, this assumption is the
    first place to look.

Every one of those is an assumption the caller makes, and requiring them
puts all four on one visible line at the call site.
"""
from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path

from kirby_terrain.geometry import Point, Segment
from kirby_terrain.objects import TerrainObject

#: Keys a Universal VTT document must have. A Foundry Scene export is also
#: valid JSON and has none of them; failing here beats a KeyError later.
_REQUIRED_KEYS = ("resolution", "line_of_sight")


def _to_metres(grid_units: float, metres_per_square: float) -> float:
    """Grid units to metres. The one place units change in this package."""
    return grid_units * metres_per_square


def _point(raw: object, metres_per_square: float, where: str) -> Point:
    """One point, in metres. `where` names the location for error messages."""
    if not isinstance(raw, dict):
        # ValueError, not TypeError: every other malformed-document error in
        # this reader (missing keys, bad bounds shape, non-bool `closed`) is
        # a ValueError naming the file and location, and this is one more
        # row of the same table, not a distinct category of failure.
        raise ValueError(f"{where}: expected a point object, got {raw!r}")  # noqa: TRY004
    missing = [k for k in ("x", "y") if k not in raw]
    if missing:
        raise ValueError(f"{where}: point is missing {', '.join(missing)}: {raw!r}")
    coords = {}
    for axis in ("x", "y"):
        value = raw[axis]
        # bool is a subclass of int in Python, and a coordinate of True/False
        # is a malformed file, not a 1.0/0.0 one — reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(  # noqa: TRY004 -- ValueError by design, see above
                f"{where}: point has a non-numeric '{axis}': {value!r}"
            )
        coords[axis] = value
    return Point(
        _to_metres(coords["x"], metres_per_square),
        _to_metres(coords["y"], metres_per_square),
    )


def _segment(a: object, b: object, metres_per_square: float, where: str) -> Segment:
    """Two points, in metres, as a Segment."""
    return Segment(
        start=_point(a, metres_per_square, f"{where} 0"),
        end=_point(b, metres_per_square, f"{where} 1"),
    )


def read_uvtt(
    path: str | Path,
    *,
    metres_per_square: float,
    wall_kind: str,
    portal_kind: str,
    wall_height_m: float,
) -> list[TerrainObject]:
    """Read a Universal VTT export into terrain objects.

    Every keyword argument names something the file does not state. See the
    module docstring for why none of them has a default.
    """
    path = Path(path)
    # UTF-8 is what JSON is by specification; read_text() would decode with
    # the machine's default encoding instead, which is wrong on Windows and
    # this is a published package that will meet Windows machines.
    document = json.loads(path.read_bytes())
    missing = [k for k in _REQUIRED_KEYS if k not in document]
    if missing:
        raise ValueError(
            f"{path.name} does not look like a Universal VTT export: "
            f"missing {', '.join(missing)}"
        )
    if metres_per_square <= 0:
        raise ValueError(f"metres_per_square must be positive, got {metres_per_square}")

    line_of_sight = document["line_of_sight"]
    if not isinstance(line_of_sight, list):
        raise ValueError(  # noqa: TRY004 -- ValueError by design, see above
            f"{path.name}: line_of_sight must be a list, got "
            f"{type(line_of_sight).__name__}"
        )

    objects: list[TerrainObject] = []
    for line_index, line in enumerate(line_of_sight):
        if not isinstance(line, list):
            raise ValueError(  # noqa: TRY004 -- ValueError by design, see above
                f"{path.name}: line_of_sight[{line_index}] must be a list "
                f"of points, got {type(line).__name__}"
            )
        for segment_index, (a, b) in enumerate(pairwise(line)):
            where = f"{path.name}: line_of_sight[{line_index}] point"
            shape = _segment(a, b, metres_per_square, where)
            if shape.is_degenerate:
                continue
            object_id = f"uvtt-los-{line_index}-{segment_index}"
            objects.append(
                TerrainObject(
                    id=object_id,
                    name=wall_kind,
                    kind=wall_kind,
                    shape=shape,
                    height_m=wall_height_m,
                    blocks_los=True,
                    blocks_movement=True,
                    # UVTT does not carry sound-blocking per wall, unlike
                    # the Foundry Scene format — blocks_sound is left at
                    # TerrainObject's default.
                )
            )

    # `portals` is optional in the format — a map with no doors omits the
    # key entirely, so absent must read as empty, not as an error.
    for portal_index, portal in enumerate(document.get("portals", [])):
        if "bounds" not in portal:
            raise ValueError(f"{path.name}: portals[{portal_index}] is missing 'bounds'")
        bounds = portal["bounds"]
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError(
                f"{path.name}: portals[{portal_index}] bounds must be exactly "
                f"two points, got {bounds!r}"
            )
        a, b = bounds
        where = f"{path.name}: portals[{portal_index}] bounds point"
        shape = _segment(a, b, metres_per_square, where)
        if shape.is_degenerate:
            continue
        if "closed" not in portal:
            raise ValueError(f"{path.name}: portals[{portal_index}] is missing 'closed'")
        closed = portal["closed"]
        # `bool(closed)` does NOT belong here: bool("false") is True. A
        # document with "closed": "false" (the string) must be rejected,
        # not silently read as a shut door.
        if not isinstance(closed, bool):
            raise ValueError(  # noqa: TRY004 -- ValueError by design, see above
                f"{path.name}: portals[{portal_index}] has a non-boolean "
                f"'closed': {closed!r}"
            )
        object_id = f"uvtt-portal-{portal_index}"
        objects.append(
            TerrainObject(
                id=object_id,
                name=portal_kind,
                kind=portal_kind,
                shape=shape,
                height_m=wall_height_m,
                # An open portal is a hole you can see through; it still
                # occupies a doorway you must path through rather than
                # over, so blocks_movement is always True regardless of
                # `closed`.
                blocks_los=closed,
                blocks_movement=True,
                # `closed` drives blocks_los above, is deliberately
                # overridden for blocks_movement (always True), and is
                # simply ignored for blocks_sound, which is left at
                # TerrainObject's default — so an open window reads as
                # sound-blocking. UVTT does not state sound-blocking at
                # all, for walls or portals alike.
                #
                # NOTE cross-check: on the sample map, this single portal
                # is `closed: false` — and it is the very same physical
                # object that this map's Foundry Scene export encodes as
                # a wall with `sense: 0` (does not block sight). A window:
                # see-through, not walk-through. Two independent formats
                # describing one object differently is a fidelity
                # cross-check the design relies on; it is recorded here,
                # not smoothed away.
            )
        )
    return objects
