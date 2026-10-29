"""Tests de change detection (hash de contenido)."""

from dirtbag_data.pipeline.change_detection import content_hash


def _base(**overrides) -> dict:
    data = {
        "name": "Alien Tufa",
        "grade_value": "5.11c",
        "grade_system": "YDS",
        "length_m": 28.0,
        "latitude": 25.39458320761,
        "longitude": -100.23904078036,
        "status": "unknown",
    }
    data.update(overrides)
    return data


def test_stable_for_same_input():
    assert content_hash(**_base()) == content_hash(**_base())


def test_changes_when_any_field_changes():
    base = content_hash(**_base())
    assert base != content_hash(**_base(name="Alien Tufa 2"))
    assert base != content_hash(**_base(grade_value="5.11d"))
    assert base != content_hash(**_base(length_m=30.0))
    assert base != content_hash(**_base(latitude=25.4))
    assert base != content_hash(**_base(status="removed"))


def test_coordinate_precision_six_decimals():
    """Coords que solo difieren más allá de 6 decimales son el mismo hash."""
    a = content_hash(**_base(latitude=25.3945832, longitude=-100.2390407))
    b = content_hash(**_base(latitude=25.3945834, longitude=-100.2390409))
    assert a == b
