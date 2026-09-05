"""Readers: the only code in this package that knows a file format.

A reader takes one export and returns `TerrainObject`s. Readers are
interchangeable, and adding one must not touch geometry, objects or
durability — if it does, the boundary is in the wrong place.
"""
