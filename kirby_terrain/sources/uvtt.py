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
    document = json.loads(path.read_text())
    missing = [k for k in _REQUIRED_KEYS if k not in document]
    if missing:
        raise ValueError(
            f"{path.name} does not look like a Universal VTT export: "
            f"missing {', '.join(missing)}"
        )
    if metres_per_square <= 0:
        raise ValueError(f"metres_per_square must be positive, got {metres_per_square}")

    objects: list[TerrainObject] = []
    for line_index, line in enumerate(document["line_of_sight"]):
        for segment_index, (a, b) in enumerate(pairwise(line)):
            shape = Segment(
                start=Point(
                    _to_metres(a["x"], metres_per_square),
                    _to_metres(a["y"], metres_per_square),
                ),
                end=Point(
                    _to_metres(b["x"], metres_per_square),
                    _to_metres(b["y"], metres_per_square),
                ),
            )
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
        a, b = portal["bounds"]
        shape = Segment(
            start=Point(
                _to_metres(a["x"], metres_per_square),
                _to_metres(a["y"], metres_per_square),
            ),
            end=Point(
                _to_metres(b["x"], metres_per_square),
                _to_metres(b["y"], metres_per_square),
            ),
        )
        if shape.is_degenerate:
            continue
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
                blocks_los=portal["closed"],
                blocks_movement=True,
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
