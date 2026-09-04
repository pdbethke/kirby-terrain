"""One primitive for everything physically present.

Walls, doors, windows and zones are one type carrying different values,
following the combat engine's own Construct precedent — a class per shape
multiplies the places a new source has to touch.
"""
import pytest

from kirby_terrain import OBJECT_DURABILITY, Point, Polygon, Segment, TerrainObject


def _wall(**kw) -> TerrainObject:
    base = dict(
        id="w1", name="north wall", kind="brick wall",
        shape=Segment(Point(0.0, 0.0), Point(5.0, 0.0)),
        height_m=4.0,
    )
    base.update(kw)
    return TerrainObject(**base)


def test_durability_comes_from_the_kind():
    """The point of keying on the book's object kind: a caller names what
    the thing IS and the numbers follow, with no chance to invent one."""
    w = _wall()
    assert (w.pd, w.ed, w.body) == (5, 10, 3)
    assert w.resistant is True


def test_an_unknown_kind_is_rejected_loudly():
    """A typo'd kind must not silently become an indestructible wall."""
    with pytest.raises(ValueError, match="unknown terrain kind"):
        _wall(kind="briick wall")


def test_durability_can_be_overridden_per_object():
    """The book calls its table a baseline the GM should change to fit the
    adventure (6E2 p172), so a specific wall may state its own numbers."""
    w = _wall(pd_override=9, ed_override=12, body_override=8)
    assert (w.pd, w.ed, w.body) == (9, 12, 8)


def test_an_override_of_one_value_leaves_the_others_from_the_table():
    w = _wall(body_override=8)
    assert (w.pd, w.ed, w.body) == (5, 10, 8)


def test_glass_is_not_resistant_through_the_object():
    assert _wall(kind="glass", name="window").resistant is False


def test_blocking_defaults_suit_a_wall():
    w = _wall()
    assert (w.blocks_los, w.blocks_movement, w.blocks_sound) == (True, True, True)


def test_a_window_sees_through_but_does_not_pass_through():
    """The object DA and UVTT described differently: sight-transparent,
    movement-blocking."""
    w = _wall(kind="glass", blocks_los=False)
    assert w.blocks_los is False
    assert w.blocks_movement is True


def test_sound_blocking_is_carried_separately():
    """Kirby's perception model is per-Sense-Group and one map format
    states this per wall. Nothing else can supply it later."""
    assert _wall(blocks_sound=False).blocks_sound is False


def test_a_zone_is_a_polygon():
    z = TerrainObject(
        id="z1", name="floor", kind="concrete wall",
        shape=Polygon([Point(0.0, 0.0), Point(2.0, 0.0), Point(2.0, 2.0)]),
        height_m=0.0,
    )
    assert isinstance(z.shape, Polygon)


def test_every_table_kind_can_build_an_object():
    """Guards the seam between the table and the objects: a key the table
    holds but an object rejects would be found only at import time."""
    for kind in OBJECT_DURABILITY:
        assert _wall(kind=kind).kind == kind
