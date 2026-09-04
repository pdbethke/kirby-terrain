"""What is physically present, as one primitive.

Walls, doors, windows, floors and zones are ONE type carrying different
values, following the combat engine's `Construct` precedent. A class per
shape multiplies the places every new reader has to touch.

An object names what it IS (`kind`, keyed to the Objects Table) and its
durability follows from that, so a caller cannot invent numbers. 6E2 p172
calls the table a baseline the GM should change to fit the adventure, so a
specific object may override any of the three values.

This type carries no rules. It records that a wall blocks sight; what
blocking sight MEANS in a fight belongs to kirby-combat.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_terrain.durability import OBJECT_DURABILITY
from kirby_terrain.geometry import Polygon, Segment


@dataclass(frozen=True)
class TerrainObject:
    """One piece of terrain: a wall, a door, a window, a floor, a zone."""

    id: str
    name: str
    #: What this IS, keyed to `OBJECT_DURABILITY` (6E2 p173).
    kind: str
    shape: Segment | Polygon
    height_m: float

    blocks_los: bool = True
    blocks_movement: bool = True
    #: Carried because one map format states it per wall and Kirby's
    #: perception model is per-Sense-Group. Nothing else can supply it.
    blocks_sound: bool = True

    #: Per-object durability, overriding the table (6E2 p172: the table is a
    #: baseline the GM should change to fit the adventure). None = use it.
    pd_override: int | None = None
    ed_override: int | None = None
    body_override: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in OBJECT_DURABILITY:
            raise ValueError(
                f"unknown terrain kind: {self.kind!r}. "
                f"Known kinds are the rows of the 6E2 p173 Objects Table."
            )

    @property
    def _row(self):
        return OBJECT_DURABILITY[self.kind]

    @property
    def pd(self) -> int:
        return self._row.pd if self.pd_override is None else self.pd_override

    @property
    def ed(self) -> int:
        return self._row.ed if self.ed_override is None else self.ed_override

    @property
    def body(self) -> int:
        return self._row.body if self.body_override is None else self.body_override

    @property
    def resistant(self) -> bool:
        """Whether the defense applies against Killing damage. A property of
        the material, so it is never overridden per object."""
        return self._row.resistant
