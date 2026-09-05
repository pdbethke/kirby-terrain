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

from kirby_terrain.durability import OBJECT_DURABILITY, ObjectDurability
from kirby_terrain.geometry import Polygon, Segment


@dataclass(frozen=True, kw_only=True)
class TerrainObject:
    """One piece of terrain: a wall, a door, a window, a floor, a zone."""

    id: str
    name: str
    #: What this IS, keyed to `OBJECT_DURABILITY` (6E2 p173). None means
    #: "not identified" — a floor, a tree, a vehicle, a hazard zone, anything
    #: the table has no row for. When `kind` is None the caller must supply
    #: all three of `pd_override`, `ed_override` and `body_override`.
    kind: str | None = None
    shape: Segment | Polygon
    height_m: float

    #: The band of space a ZONE occupies, as (lowest, highest) in metres,
    #: relative to the ground plane. None means ordinary terrain that stands
    #: on the ground and is described by `height_m`.
    #:
    #: A band rather than a signed height, matching the combat engine's own
    #: `Construct.elevation_range_m`: it describes a pool two metres deep as
    #: (-2.0, 0.0), a submerged pipe as (-5.0, -3.0), or a gas cloud at head
    #: height as (1.5, 3.0). A pool is NOT a hole in the floor.
    elevation_range_m: tuple[float, float] | None = None

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
        if self.elevation_range_m is not None:
            band = tuple(self.elevation_range_m)
            if len(band) != 2:
                raise ValueError(
                    f"elevation_range_m must be (lowest, highest); got {band!r}"
                )
            if band[0] > band[1]:
                raise ValueError(
                    f"elevation_range_m is backwards: {band!r}. It reads "
                    "(lowest, highest), so a pool two metres deep is "
                    "(-2.0, 0.0)."
                )
            object.__setattr__(self, "elevation_range_m", band)

        if self.kind is None:
            stated = [
                name
                for name, value in (
                    ("pd_override", self.pd_override),
                    ("ed_override", self.ed_override),
                    ("body_override", self.body_override),
                )
                if value is not None
            ]
            missing = [
                name
                for name, value in (
                    ("pd_override", self.pd_override),
                    ("ed_override", self.ed_override),
                    ("body_override", self.body_override),
                )
                if value is None
            ]
            # Three cases, and the middle one is the mistake:
            #   none stated  -> not destructible at all. Water has no BODY.
            #   some stated  -> a half-finished thought. Nothing means "pd 3
            #                   and deliberately no ED".
            #   all stated   -> unidentified but breakable, e.g. a crate.
            if stated and missing:
                raise ValueError(
                    "an object stating some of its own durability must state "
                    f"all of it; missing: {', '.join(missing)}. State none at "
                    "all for terrain that cannot be broken, such as water."
                )
        elif self.kind not in OBJECT_DURABILITY:
            raise ValueError(
                f"unknown terrain kind: {self.kind!r}. "
                f"Known kinds are the rows of the 6E2 p173 Objects Table."
            )

    @property
    def _row(self) -> ObjectDurability | None:
        return None if self.kind is None else OBJECT_DURABILITY[self.kind]

    @property
    def pd(self) -> int | None:
        if self.pd_override is not None:
            return self.pd_override
        return None if self._row is None else self._row.pd

    @property
    def ed(self) -> int | None:
        if self.ed_override is not None:
            return self.ed_override
        return None if self._row is None else self._row.ed

    @property
    def body(self) -> int | None:
        if self.body_override is not None:
            return self.body_override
        return None if self._row is None else self._row.body

    @property
    def destructible(self) -> bool:
        """Whether this can be broken at all.

        Mirrors the combat engine's `Construct.destructible`: no DEF and no
        BODY means indestructible. Water, and open space, are not damaged by
        hitting them.
        """
        return self.pd is not None

    @property
    def resistant(self) -> bool:
        """Whether the defense applies against Killing damage. A property of
        the material, so it is never overridden per object. An unidentified
        object (kind=None) defaults to True — a plain solid object."""
        return True if self._row is None else self._row.resistant
