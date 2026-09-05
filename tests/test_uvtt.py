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


def test_scale_converts_grid_units_to_metres(tmp_path):
    """One square across, at 5 ft to the square, is 1.524 m — not 150 of
    anything. The reader is where units stop being the file's and start
    being this platform's."""
    from kirby_terrain.sources.uvtt import _to_metres

    assert _to_metres(1.0, FIVE_FEET_M) == pytest.approx(1.524)
    assert _to_metres(0.0, FIVE_FEET_M) == 0.0
    assert _to_metres(58.0, FIVE_FEET_M) == pytest.approx(88.392)


def test_reading_the_real_fixture_returns_a_list():
    assert isinstance(_read(), list)
