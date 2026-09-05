"""Terrain for the Kirby HERO System platform: what is here, and how hard
it is to break.

Zero dependencies and no rules. Geometry is metres throughout; durability
comes from the HERO System 6E2 p173 Objects Table. What a wall DOES in a
fight belongs to kirby-combat, not here.

`read_uvtt` reads Universal VTT exports; it and any reader that follows are
the only code here that will know a file format. Foundry Scene JSON is
later work.
"""
from kirby_terrain.durability import OBJECT_DURABILITY, ObjectDurability
from kirby_terrain.geometry import Point, Polygon, Segment
from kirby_terrain.objects import TerrainObject
from kirby_terrain.sources.uvtt import read_uvtt

__all__ = [
    "OBJECT_DURABILITY",
    "ObjectDurability",
    "Point",
    "Polygon",
    "Segment",
    "TerrainObject",
    "read_uvtt",
]
