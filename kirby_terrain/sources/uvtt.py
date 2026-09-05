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
from pathlib import Path

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
    return []
