"""Grade normalization tests (spec Phase 3)."""

import pytest

from dirtbag_data.normalization.grades import (
    GradeSystem,
    UnknownGradeError,
    convert,
    detect_system,
    normalize_grade,
)


class TestDetectSystem:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("5.11a", GradeSystem.YDS),
            ("5.10D", GradeSystem.YDS),
            ("5.6", GradeSystem.YDS),
            ("6c+", GradeSystem.FRENCH),
            ("8a", GradeSystem.FRENCH),
            ("V5", GradeSystem.V_SCALE),
            ("v12", GradeSystem.V_SCALE),
            ("VII+", GradeSystem.UIAA),
            ("IV", GradeSystem.UIAA),
            ("5+", GradeSystem.FONT),
            ("3", GradeSystem.FONT),
            ("gibberish", None),
            ("", None),
        ],
    )
    def test_detection(self, value, expected):
        assert detect_system(value) == expected

    def test_bouldering_context_prefers_font(self):
        assert detect_system("7a+", discipline="bouldering") == GradeSystem.FONT

    def test_sport_context_prefers_french(self):
        assert detect_system("7a+", discipline="sport") == GradeSystem.FRENCH


class TestNormalize:
    def test_preserves_original_value(self):
        record = normalize_grade(" 6C+ ", GradeSystem.FRENCH)
        assert record.value == " 6C+ "
        assert record.normalized == "6c+"
        assert record.system is GradeSystem.FRENCH

    def test_yds_lowercased(self):
        assert normalize_grade("5.10D").normalized == "5.10d"

    def test_v_scale_uppercased(self):
        assert normalize_grade("v7").normalized == "V7"

    def test_unknown_raises(self):
        with pytest.raises(UnknownGradeError):
            normalize_grade("banana")

    def test_invalid_for_system_raises(self):
        with pytest.raises(UnknownGradeError):
            normalize_grade("banana", GradeSystem.YDS)


class TestConvert:
    @pytest.mark.parametrize(
        ("value", "from_sys", "to_sys", "expected"),
        [
            ("5.10d", GradeSystem.YDS, GradeSystem.FRENCH, "7a+"),
            ("5.12a", GradeSystem.YDS, GradeSystem.FRENCH, "8a"),
            ("7a+", GradeSystem.FRENCH, GradeSystem.YDS, "5.10d"),
            ("V6", GradeSystem.V_SCALE, GradeSystem.FONT, "7a"),
            ("4", GradeSystem.FONT, GradeSystem.V_SCALE, "V0"),
        ],
    )
    def test_known_conversions(self, value, from_sys, to_sys, expected):
        result = convert(value, from_sys, to_sys)
        assert result is not None
        assert result.normalized == expected
        assert result.system is to_sys
        assert result.value == value

    def test_same_system_passthrough(self):
        result = convert("6b+", GradeSystem.FRENCH, GradeSystem.FRENCH)
        assert result is not None and result.normalized == "6b+"

    def test_untabulated_returns_none(self):
        assert convert("5.15d", GradeSystem.YDS, GradeSystem.FRENCH) is None

    def test_cross_family_returns_none(self):
        assert convert("5.11a", GradeSystem.YDS, GradeSystem.FONT) is None
