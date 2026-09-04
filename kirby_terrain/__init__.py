"""Terrain for the Kirby HERO System platform: what is here, and how hard
it is to break.

Zero dependencies and no rules. Geometry is metres throughout; durability
comes from the HERO System 6E2 p173 Objects Table. What a wall DOES in a
fight belongs to kirby-combat, not here.

Readers for map-tool exports (Universal VTT, Foundry Scene JSON) arrive in
a later change and are the only code that will know a file format.
"""
from kirby_terrain.durability import OBJECT_DURABILITY, ObjectDurability
from kirby_terrain.geometry import Point, Polygon, Segment
from kirby_terrain.objects import TerrainObject

__all__ = [
    "Point", "Segment", "Polygon",
    "TerrainObject",
    "ObjectDurability", "OBJECT_DURABILITY",
]
