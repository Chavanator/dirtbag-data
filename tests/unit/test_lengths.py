"""Tests de normalización de longitudes."""

from dirtbag_data.normalization.lengths import parse_length


def test_meters():
    assert parse_length("28m") == 28.0
    assert parse_length("12 metros") == 12.0
    assert parse_length("1,5m") == 1.5


def test_feet_to_meters():
    assert parse_length("90 ft") == 27.432
    assert parse_length("90'") == 27.432


def test_invalid_returns_none():
    assert parse_length(None) is None
    assert parse_length("") is None
    assert parse_length("chirrlo") is None
    assert parse_length("28") is None  # sin unidad no se adivina
