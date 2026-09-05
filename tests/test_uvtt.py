"""Reading a Universal VTT export.

The fixture is a real Dungeon Alchemist export of a warehouse, with its 8 MB
embedded base64 image stripped — the reader never looks at the image, and an
8 MB fixture in a repository is its own problem.

UVTT is the interchange format created for Dungeondraft; other tools emit it
too, which is why this reader exists before any tool-specific one.
"""
import json
import pathlib

import pytest

from kirby_terrain.sources.uvtt import read_uvtt

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "warehouse.dd2vtt"

#: The sample map was built at 5 ft to the square.
FIVE_FEET_M = 1.524


def _read(**kw):
    base = {
        "metres_per_square": FIVE_FEET_M,
        "wall_kind": "brick wall",
        "portal_kind": "interior wood door",
        "wall_height_m": 4.0,
    }
    base.update(kw)
    return read_uvtt(FIXTURE, **base)


def test_metres_per_square_has_no_default():
    """UVTT states pixels_per_grid and map_size and NOTHING about how long a
    square is. A default here would be a convention-shaped guess, silently
    wrong on any map built to another scale."""
    with pytest.raises(TypeError):
        read_uvtt(FIXTURE, wall_kind="brick wall",  # type: ignore[call-arg]
                  portal_kind="interior wood door", wall_height_m=4.0)


def test_a_missing_file_says_so():
    with pytest.raises(FileNotFoundError):
        _read_path = pathlib.Path("/nonexistent/nope.dd2vtt")
        read_uvtt(_read_path, metres_per_square=FIVE_FEET_M,
                  wall_kind="brick wall", portal_kind="interior wood door",
                  wall_height_m=4.0)


def test_a_file_that_is_not_uvtt_is_rejected_by_name(tmp_path):
    """A Foundry Scene export parses as JSON perfectly well and has none of
    the fields this reader needs. Failing on a missing key three functions
    later is a worse message than failing here."""
    bad = tmp_path / "notuvtt.json"
    bad.write_text(json.dumps({"name": "map", "walls": [], "grid": 150}))
    with pytest.raises(ValueError, match="does not look like a Universal VTT"):
        read_uvtt(bad, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                  portal_kind="interior wood door", wall_height_m=4.0)


def test_wall_kind_has_no_default():
    with pytest.raises(TypeError):
        read_uvtt(FIXTURE, metres_per_square=FIVE_FEET_M,  # type: ignore[call-arg]
                  portal_kind="interior wood door", wall_height_m=4.0)


def test_portal_kind_has_no_default():
    with pytest.raises(TypeError):
        read_uvtt(FIXTURE, metres_per_square=FIVE_FEET_M,  # type: ignore[call-arg]
                  wall_kind="brick wall", wall_height_m=4.0)


def test_wall_height_m_has_no_default():
    with pytest.raises(TypeError):
        read_uvtt(FIXTURE, metres_per_square=FIVE_FEET_M,  # type: ignore[call-arg]
                  wall_kind="brick wall", portal_kind="interior wood door")


def test_scale_converts_grid_units_to_metres():
    """One square across, at 5 ft to the square, is 1.524 m — not 150 of
    anything. The reader is where units stop being the file's and start
    being this platform's."""
    from kirby_terrain.sources.uvtt import _to_metres

    assert _to_metres(1.0, FIVE_FEET_M) == pytest.approx(1.524)
    assert _to_metres(0.0, FIVE_FEET_M) == 0.0
    assert _to_metres(58.0, FIVE_FEET_M) == pytest.approx(88.392)


def test_reading_the_real_fixture_returns_a_list():
    result = _read()
    assert isinstance(result, list)
    assert result


def test_every_polyline_segment_becomes_an_object():
    """line_of_sight holds POLYLINES. One with N points is N-1 walls; a
    reader treating a polyline as a single object loses every corner."""
    document = json.loads(FIXTURE.read_text())
    expected = sum(len(line) - 1 for line in document["line_of_sight"])
    walls = [o for o in _read() if o.kind == "brick wall"]
    assert len(walls) == expected


def test_walls_carry_the_kind_they_were_told():
    walls = [o for o in _read() if o.kind == "brick wall"]
    assert walls
    for wall in walls:
        assert (wall.pd, wall.ed, wall.body) == (5, 10, 3)


def test_a_wall_blocks_sight_and_movement():
    """These came out of line_of_sight, so sight-blocking is what the file
    actually said. Movement is the caller's assumption, stated here."""
    wall = next(o for o in _read() if o.kind == "brick wall")
    assert wall.blocks_los is True
    assert wall.blocks_movement is True


def test_wall_geometry_is_in_metres_and_matches_the_file():
    """Pin the conversion against the fixture's own first segment rather
    than a number typed from memory."""
    from kirby_terrain.geometry import Segment

    document = json.loads(FIXTURE.read_text())
    a, b = document["line_of_sight"][0][0], document["line_of_sight"][0][1]
    wall = next(o for o in _read() if o.kind == "brick wall")
    assert isinstance(wall.shape, Segment)
    assert wall.shape.start.x == pytest.approx(a["x"] * FIVE_FEET_M)
    assert wall.shape.start.y == pytest.approx(a["y"] * FIVE_FEET_M)
    assert wall.shape.end.x == pytest.approx(b["x"] * FIVE_FEET_M)
    assert wall.shape.end.y == pytest.approx(b["y"] * FIVE_FEET_M)


def test_walls_take_the_height_they_were_given():
    assert next(o for o in _read(wall_height_m=6.5)
                if o.kind == "brick wall").height_m == 6.5


def test_ids_are_unique():
    """Two objects sharing an id is how a later consumer silently drops one."""
    objects = _read()
    assert len({o.id for o in objects}) == len(objects)


def test_a_degenerate_segment_is_skipped(tmp_path):
    """A malformed export can repeat a point. A zero-length wall is not a
    wall, and passing it downstream makes every consumer handle it."""
    document = json.loads(FIXTURE.read_text())
    document["line_of_sight"] = [[{"x": 1.0, "y": 1.0}, {"x": 1.0, "y": 1.0}]]
    document["portals"] = []
    bad = tmp_path / "degenerate.dd2vtt"
    bad.write_text(json.dumps(document))
    assert read_uvtt(bad, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                     portal_kind="interior wood door", wall_height_m=4.0) == []


def test_a_multi_point_polyline_becomes_one_wall_per_SEGMENT(tmp_path):
    """The fixture's polylines all have exactly two points, so the count
    check against it passes either way. This one cannot: a four-point
    polyline is THREE walls, and an implementation that treats a polyline
    as a single object returns one."""
    document = json.loads(FIXTURE.read_text())
    document["line_of_sight"] = [[
        {"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0},
        {"x": 1.0, "y": 1.0}, {"x": 2.0, "y": 1.0},
    ]]
    document["portals"] = []
    path = tmp_path / "corners.dd2vtt"
    path.write_text(json.dumps(document))
    walls = read_uvtt(path, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                      portal_kind="interior wood door", wall_height_m=4.0)
    assert len(walls) == 3


def test_a_non_positive_scale_is_rejected():
    """A zero or negative scale collapses an entire map to a point. Task 1
    added this guard; nothing exercised it."""
    with pytest.raises(ValueError, match="metres_per_square"):
        _read(metres_per_square=0.0)


def test_every_portal_becomes_an_object():
    document = json.loads(FIXTURE.read_text())
    portals = [o for o in _read() if o.kind == "interior wood door"]
    assert len(portals) == len(document["portals"])


def test_a_portal_spans_its_bounds_in_metres():
    from kirby_terrain.geometry import Segment

    document = json.loads(FIXTURE.read_text())
    a, b = document["portals"][0]["bounds"]
    portal = next(o for o in _read() if o.kind == "interior wood door")
    assert isinstance(portal.shape, Segment)
    assert portal.shape.start.x == pytest.approx(a["x"] * FIVE_FEET_M)
    assert portal.shape.start.y == pytest.approx(a["y"] * FIVE_FEET_M)
    assert portal.shape.end.x == pytest.approx(b["x"] * FIVE_FEET_M)
    assert portal.shape.end.y == pytest.approx(b["y"] * FIVE_FEET_M)


def test_an_open_portal_can_be_seen_through_but_not_walked_through():
    """The sample map's one portal is `closed: false` — the same object the
    Foundry export calls a wall that does not block sight. A window."""
    document = json.loads(FIXTURE.read_text())
    assert document["portals"][0]["closed"] is False
    portal = next(o for o in _read() if o.kind == "interior wood door")
    assert portal.blocks_los is False
    assert portal.blocks_movement is True


def test_a_closed_portal_blocks_sight(tmp_path):
    document = json.loads(FIXTURE.read_text())
    document["portals"][0]["closed"] = True
    shut = tmp_path / "shut.dd2vtt"
    shut.write_text(json.dumps(document))
    portal = next(o for o in read_uvtt(
        shut, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
        portal_kind="interior wood door", wall_height_m=4.0)
        if o.kind == "interior wood door")
    assert portal.blocks_los is True


def test_portals_carry_their_own_kind_not_the_wall_kind():
    portal = next(o for o in _read() if o.kind == "interior wood door")
    assert (portal.pd, portal.ed, portal.body) == (2, 2, 3)


def test_a_document_with_no_portals_key_still_reads(tmp_path):
    """`portals` is optional in the format; a map with no doors omits it."""
    document = json.loads(FIXTURE.read_text())
    document.pop("portals", None)
    nodoors = tmp_path / "nodoors.dd2vtt"
    nodoors.write_text(json.dumps(document))
    objects = read_uvtt(nodoors, metres_per_square=FIVE_FEET_M,
                        wall_kind="brick wall", portal_kind="interior wood door",
                        wall_height_m=4.0)
    walls = [o for o in objects if o.kind == "brick wall"]
    portals = [o for o in objects if o.kind == "interior wood door"]
    assert len(walls) == 33
    assert len(portals) == 0


def test_a_string_closed_is_rejected_not_coerced(tmp_path):
    """`bool("false")` is `True` — coercing `closed` with `bool()` would make
    a wide-open door read as sight-blocking, silently. A non-bool `closed`
    must be an error, not a value the reader guesses at."""
    document = json.loads(FIXTURE.read_text())
    document["portals"][0]["closed"] = "false"
    bad = tmp_path / "stringclosed.dd2vtt"
    bad.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="non-boolean"):
        read_uvtt(bad, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                  portal_kind="interior wood door", wall_height_m=4.0)


def _write(tmp_path, document, name="bad.dd2vtt"):
    path = tmp_path / name
    path.write_text(json.dumps(document))
    return path


class TestMalformedGeometryNamesTheFileAndLocation:
    """Every row of the review's table: today these raise KeyError/TypeError
    naming neither the file nor the point. They must raise ValueError naming
    both."""

    def _base_document(self):
        return json.loads(FIXTURE.read_text())

    def _read(self, path):
        return read_uvtt(path, metres_per_square=FIVE_FEET_M,
                         wall_kind="brick wall",
                         portal_kind="interior wood door", wall_height_m=4.0)

    def test_point_missing_y(self, tmp_path):
        document = self._base_document()
        document["line_of_sight"] = [[{"x": 1.0}, {"x": 2.0, "y": 2.0}]]
        document["portals"] = []
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*line_of_sight\[0\]"):
            self._read(path)

    def test_coordinate_is_a_string(self, tmp_path):
        document = self._base_document()
        document["line_of_sight"] = [[{"x": "12", "y": 1.0}, {"x": 2.0, "y": 2.0}]]
        document["portals"] = []
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*line_of_sight\[0\]"):
            self._read(path)

    def test_coordinate_is_null(self, tmp_path):
        document = self._base_document()
        document["line_of_sight"] = [[{"x": None, "y": 1.0}, {"x": 2.0, "y": 2.0}]]
        document["portals"] = []
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*line_of_sight\[0\]"):
            self._read(path)

    def test_coordinate_is_a_bool(self, tmp_path):
        """`True` is an `int` in Python; a coordinate of `True` is still a
        malformed file, not a valid `1`."""
        document = self._base_document()
        document["line_of_sight"] = [[{"x": True, "y": 1.0}, {"x": 2.0, "y": 2.0}]]
        document["portals"] = []
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*line_of_sight\[0\]"):
            self._read(path)

    def test_point_is_not_a_mapping(self, tmp_path):
        document = self._base_document()
        document["line_of_sight"] = [[[1.0, 1.0], {"x": 2.0, "y": 2.0}]]
        document["portals"] = []
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*line_of_sight\[0\]"):
            self._read(path)

    def test_portal_bounds_has_three_points(self, tmp_path):
        document = self._base_document()
        document["portals"][0]["bounds"] = [
            {"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}, {"x": 1.0, "y": 1.0},
        ]
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*portals\[0\]"):
            self._read(path)

    def test_portal_missing_bounds(self, tmp_path):
        document = self._base_document()
        del document["portals"][0]["bounds"]
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*portals\[0\]"):
            self._read(path)

    def test_portal_missing_closed(self, tmp_path):
        document = self._base_document()
        del document["portals"][0]["closed"]
        path = _write(tmp_path, document)
        with pytest.raises(ValueError, match=r"bad\.dd2vtt.*portals\[0\]"):
            self._read(path)


def test_line_of_sight_that_is_a_dict_is_rejected(tmp_path):
    """A dict iterates as its keys and `pairwise` over a one-character
    string yields nothing — today this silently returns 0 walls instead of
    raising. Only wrong TYPES should raise; an empty list is legal."""
    document = json.loads(FIXTURE.read_text())
    document["line_of_sight"] = {"a": 1}
    path = tmp_path / "dictlos.dd2vtt"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match=r"dictlos\.dd2vtt.*line_of_sight"):
        read_uvtt(path, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                  portal_kind="interior wood door", wall_height_m=4.0)


def test_a_polyline_that_is_not_a_list_is_rejected(tmp_path):
    document = json.loads(FIXTURE.read_text())
    document["line_of_sight"] = ["not a polyline"]
    document["portals"] = []
    path = tmp_path / "badpolyline.dd2vtt"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match=r"badpolyline\.dd2vtt.*line_of_sight\[0\]"):
        read_uvtt(path, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                  portal_kind="interior wood door", wall_height_m=4.0)


def test_an_empty_line_of_sight_is_legal(tmp_path):
    """A map may genuinely have no walls. Empty is not malformed."""
    document = json.loads(FIXTURE.read_text())
    document["line_of_sight"] = []
    document["portals"] = []
    path = tmp_path / "nowalls.dd2vtt"
    path.write_text(json.dumps(document))
    assert read_uvtt(path, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                     portal_kind="interior wood door", wall_height_m=4.0) == []


def test_a_single_point_polyline_is_legal(tmp_path):
    """One point makes zero segments via pairwise — odd, but not an error."""
    document = json.loads(FIXTURE.read_text())
    document["line_of_sight"] = [[{"x": 1.0, "y": 1.0}]]
    document["portals"] = []
    path = tmp_path / "onepoint.dd2vtt"
    path.write_text(json.dumps(document))
    assert read_uvtt(path, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                     portal_kind="interior wood door", wall_height_m=4.0) == []


def test_a_non_ascii_value_reads_correctly(tmp_path):
    """json.loads(path.read_text()) decodes with the machine's default
    encoding; JSON is UTF-8 by specification. Use read_bytes() and let json
    detect it, so this doesn't silently mangle on a non-UTF-8-default
    machine (notably Windows)."""
    document = json.loads(FIXTURE.read_text())
    document["format_note"] = "Kürbis-Lagerhaus — a warehouse, in German"
    path = tmp_path / "nonascii.dd2vtt"
    path.write_bytes(json.dumps(document, ensure_ascii=False).encode("utf-8"))
    result = read_uvtt(path, metres_per_square=FIVE_FEET_M, wall_kind="brick wall",
                       portal_kind="interior wood door", wall_height_m=4.0)
    assert result


def test_the_reader_is_on_the_import_surface():
    """A consumer should not reach two levels deep for the thing the
    package exists to do."""
    import kirby_terrain

    assert kirby_terrain.read_uvtt is read_uvtt
    assert "read_uvtt" in kirby_terrain.__all__
