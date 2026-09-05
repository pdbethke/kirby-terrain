"""One primitive for everything physically present.

Walls, doors, windows and zones are one type carrying different values,
following the combat engine's own Construct precedent — a class per shape
multiplies the places a new source has to touch.
"""
import pytest

from kirby_terrain import OBJECT_DURABILITY, Point, Polygon, Segment, TerrainObject


def _wall(**kw) -> TerrainObject:
    base = {
        "id": "w1", "name": "north wall", "kind": "brick wall",
        "shape": Segment(Point(0.0, 0.0), Point(5.0, 0.0)),
        "height_m": 4.0,
    }
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
    """A floor has no honest row in the Objects Table (it holds only walls,
    doors and glass), so an unidentified object states its own numbers."""
    z = TerrainObject(
        id="z1", name="floor", kind=None,
        shape=Polygon([Point(0.0, 0.0), Point(2.0, 0.0), Point(2.0, 2.0)]),
        height_m=0.0,
        pd_override=0, ed_override=0, body_override=0,
    )
    assert isinstance(z.shape, Polygon)


def test_an_unidentified_object_with_full_overrides_works():
    z = _wall(kind=None, pd_override=1, ed_override=2, body_override=3)
    assert (z.pd, z.ed, z.body) == (1, 2, 3)
    assert z.resistant is True


def test_an_unidentified_object_missing_an_override_raises():
    with pytest.raises(ValueError, match="pd_override"):
        _wall(kind=None, ed_override=2, body_override=3)


def test_every_table_kind_can_build_an_object():
    """Guards the seam between the table and the objects: a key the table
    holds but an object rejects would be found only at import time."""
    for kind in OBJECT_DURABILITY:
        assert _wall(kind=kind).kind == kind


# ---------------------------------------------------------------------------
# Zones: a slab of space, and things that cannot be broken
# ---------------------------------------------------------------------------

def _pool(**kw) -> TerrainObject:
    """A rooftop pool: a polygon of water two metres deep.

    Not a hole in the floor. The combat engine models a region of space as a
    polygon plus an elevation BAND, and a band is more expressive than a
    signed height — it describes a pool, a pit, a gas cloud at head height,
    or the underside of a catwalk with one field.
    """
    base = {
        "id": "pool", "name": "deep pool", "kind": None,
        "shape": Polygon([Point(0.0, 0.0), Point(4.0, 0.0),
                          Point(4.0, 4.0), Point(0.0, 4.0)]),
        "height_m": 0.0,
        "elevation_range_m": (-2.0, 0.0),
    }
    base.update(kw)
    return TerrainObject(**base)


def test_a_zone_occupies_an_elevation_band():
    """Two metres below ground up to the surface."""
    assert _pool().elevation_range_m == (-2.0, 0.0)


def test_the_band_may_be_entirely_below_ground():
    """The whole point of a band over a signed height: a submerged pipe
    occupies space that neither starts nor ends at ground level."""
    assert _pool(elevation_range_m=(-5.0, -3.0)).elevation_range_m == (-5.0, -3.0)


def test_a_band_given_backwards_is_rejected():
    """(0, -2) is not a band, it is a mistake. Accepting it silently gives
    every consumer a range whose 'within' test can never be true."""
    with pytest.raises(ValueError, match="elevation_range_m"):
        _pool(elevation_range_m=(0.0, -2.0))


def test_a_band_is_stored_as_a_tuple():
    """A list would leave the frozen dataclass mutable in place, the same
    trap Polygon.points had."""
    assert isinstance(_pool(elevation_range_m=[-2.0, 0.0]).elevation_range_m, tuple)


def test_most_terrain_has_no_band():
    """A wall stands on the ground and height_m says how tall. None means
    'ordinary', not 'zero-thickness'."""
    w = TerrainObject(id="w", name="brick wall", kind="brick wall",
                      shape=Segment(Point(0.0, 0.0), Point(5.0, 0.0)),
                      height_m=4.0)
    assert w.elevation_range_m is None


def test_water_cannot_be_broken():
    """A pool has no DEF and no BODY. Before this change TerrainObject
    REQUIRED durability, so a pool could not be described at all."""
    p = _pool()
    assert (p.pd, p.ed, p.body) == (None, None, None)
    assert p.destructible is False


def test_a_wall_is_destructible():
    """Guards the guard: if `destructible` were hardcoded False, the test
    above would pass while every wall became unbreakable."""
    w = TerrainObject(id="w", name="brick wall", kind="brick wall",
                      shape=Segment(Point(0.0, 0.0), Point(5.0, 0.0)),
                      height_m=4.0)
    assert w.destructible is True
    assert (w.pd, w.ed, w.body) == (5, 10, 3)


def test_an_unidentified_object_with_full_overrides_is_still_destructible():
    """kind=None means 'not identified', which is NOT the same as 'not
    breakable'. A crate of unknown make still has BODY."""
    crate = TerrainObject(id="c", name="crate", kind=None,
                          shape=Segment(Point(0.0, 0.0), Point(1.0, 0.0)),
                          height_m=1.0, pd_override=3, ed_override=2,
                          body_override=4)
    assert crate.destructible is True
    assert (crate.pd, crate.ed, crate.body) == (3, 2, 4)


def test_stating_some_durability_but_not_all_is_still_an_error():
    """The ambiguous case stays an error. Nothing states pd but means 'and
    no ED' — that is a half-finished thought, unlike stating none at all."""
    with pytest.raises(ValueError, match="ed_override"):
        _pool(pd_override=3)
