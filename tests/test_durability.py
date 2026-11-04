"""The Objects Table, as the book prints it (6E2 p173).

These pin TRANSCRIPTION, not arithmetic. Three places in this platform have
carried a wrong citation for this table and the values in use were invented
ranges, so the transcription is the thing most worth guarding.
"""
import pytest

from kirby_terrain.durability import OBJECT_DURABILITY, ObjectDurability


@pytest.mark.parametrize("kind,pd,ed,body", [
    ("armored wall", 13, 18, 7),
    ("brick wall", 5, 10, 3),
    ("concrete wall", 6, 10, 5),
    ("home inside wall", 3, 3, 3),
    ("home outside wall", 4, 6, 3),
    ("reinforced concrete wall", 8, 10, 5),
    ("spaceship interior wall", 8, 8, 6),
    ("wooden wall", 4, 3, 3),
    ("airlock door", 8, 12, 7),
    ("city gates, small", 5, 8, 10),
    ("exterior wood door", 4, 4, 3),
    ("interior spaceship door", 6, 6, 4),
    ("interior wood door", 2, 2, 3),
    ("large vault door", 16, 24, 9),
    ("metal fire door", 5, 5, 5),
    ("safe door", 10, 15, 9),
    ("glass", 1, 1, 1),
    ("reinforced glass", 2, 2, 1),
    ("automobile", 3, 3, 15),
    ("armored car", 8, 8, 18),
    ("medium tree", 5, 4, 8),
    ("large tree", 5, 4, 11),
    ("furniture, heavy wood", 4, 3, 5),
])
def test_row_matches_the_book(kind, pd, ed, body):
    row = OBJECT_DURABILITY[kind]
    assert (row.pd, row.ed, row.body) == (pd, ed, body)


def test_every_row_is_pinned():
    """Guards the guard. The parametrised list above must cover the WHOLE
    table — a guard that omits rows will not catch a typo in them."""
    assert len(OBJECT_DURABILITY) == 23


def test_cover_objects_carry_the_objects_table_numbers():
    rows = {k: (v.pd, v.ed, v.body, v.resistant) for k, v in OBJECT_DURABILITY.items()}
    assert rows["automobile"] == (3, 3, 15, True)
    assert rows["armored car"] == (8, 8, 18, True)
    assert rows["medium tree"] == (5, 4, 8, True)
    assert rows["large tree"] == (5, 4, 11, True)
    assert rows["furniture, heavy wood"] == (4, 3, 5, True)


def test_pd_and_ed_genuinely_differ_somewhere():
    assert any(r.pd != r.ed for r in OBJECT_DURABILITY.values())


def test_glass_defense_is_not_resistant():
    """6E2 p173 prints glass's defense in parentheses, which the table's
    own footnote defines as Normal Defense: it does not apply against
    Killing damage."""
    assert OBJECT_DURABILITY["glass"].resistant is False
    assert OBJECT_DURABILITY["reinforced glass"].resistant is False


def test_walls_are_resistant_by_default():
    assert OBJECT_DURABILITY["brick wall"].resistant is True


def test_keys_are_lowercase_and_values_are_whole_numbers():
    for kind, row in OBJECT_DURABILITY.items():
        assert kind == kind.lower(), kind
        assert isinstance(row, ObjectDurability)
        for field in (row.pd, row.ed, row.body):
            assert isinstance(field, int) and field >= 0, kind
