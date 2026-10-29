"""Grade normalization (spec Phase 3, FR-011).

Principles from the spec:
- Always preserve the original value; ``normalized`` is a cleaned form in the
  same system, never a silent conversion.
- Conversions are approximate equivalence tables (YDS <-> French, V <-> Font);
  when there is no exact entry the conversion returns ``None`` instead of
  guessing.
- Unknown or undetectable grades are rejected with :class:`UnknownGradeError`
  so invalid data never reaches the canonical model.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field


class GradeSystem(StrEnum):
    FRENCH = "french"  # sport scale: 3a .. 9c+ (also French bouldering)
    YDS = "yds"  # Yosemite Decimal System: 5.0 .. 5.15d
    FONT = "font"  # Fontainebleau: 1 .. 9c+
    V_SCALE = "v_scale"  # Hueco/V scale: VB .. V17
    UIAA = "uiaa"  # UIAA: I .. XVI with +/-


class UnknownGradeError(ValueError):
    """Raised when a grade cannot be parsed or its system cannot be detected."""


class GradeRecord(BaseModel):
    """A grade as it travels through the pipeline (spec §"Grade System")."""

    value: str = Field(description="Original value exactly as received from the source")
    system: GradeSystem
    normalized: str = Field(description="Cleaned canonical form within the same system")

    def __str__(self) -> str:
        return self.normalized


# Approximate equivalence tables. Pivot for rope grades is French; bouldering
# uses V <-> Font directly. Approximations are intentional (spec: no rigid
# hierarchy between sources; the original value is always preserved).
_YDS_TO_FRENCH: dict[str, str] = {
    "5.0": "3",
    "5.1": "3+",
    "5.2": "4",
    "5.3": "4+",
    "5.4": "5",
    "5.5": "5+",
    "5.6": "6a",
    "5.7": "6a+",
    "5.8": "6b",
    "5.9": "6b+",
    "5.10a": "6c",
    "5.10b": "6c+",
    "5.10c": "7a",
    "5.10d": "7a+",
    "5.11a": "7b",
    "5.11b": "7b+",
    "5.11c": "7c",
    "5.11d": "7c+",
    "5.12a": "8a",
    "5.12b": "8a+",
    "5.12c": "8b",
    "5.12d": "8b+",
    "5.13a": "8c",
    "5.13b": "8c+",
    "5.13c": "9a",
    "5.13d": "9a+",
    "5.14a": "9b",
    "5.14b": "9b+",
    "5.14c": "9c",
    "5.14d": "9c+",
}
_FRENCH_TO_YDS: dict[str, str] = {v: k for k, v in _YDS_TO_FRENCH.items()}

_V_TO_FONT: dict[str, str] = {
    "VB": "3",
    "V0": "4",
    "V1": "5",
    "V2": "5+",
    "V3": "6a",
    "V4": "6b",
    "V5": "6c",
    "V6": "7a",
    "V7": "7b",
    "V8": "7b+",
    "V9": "7c",
    "V10": "7c+",
    "V11": "8a",
    "V12": "8a+",
    "V13": "8b",
    "V14": "8b+",
    "V15": "8c",
    "V16": "8c+",
}
_FONT_TO_V: dict[str, str] = {v: k for k, v in _V_TO_FONT.items()}

_YDS_RE = re.compile(r"^5\.\d{1,2}[a-d]?$", re.IGNORECASE)
_V_RE = re.compile(r"^V\d{1,2}$", re.IGNORECASE)
_FRENCH_RE = re.compile(r"^([3-9])[abc]\+?$", re.IGNORECASE)
_FONT_NUMERIC_RE = re.compile(r"^[1-5]\+?$")
_FONT_LETTER_RE = re.compile(r"^(10|[6-9])[abc]\+?$", re.IGNORECASE)
_ROMAN_RE = re.compile(r"^(?P<roman>[IVXLCDM]+)(?P<mod>[+-]?)$", re.IGNORECASE)
_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _is_valid_roman(text: str) -> bool:
    s = text.upper()
    if not s or any(ch not in _ROMAN_VALUES for ch in s):
        return False
    value = 0
    for i, ch in enumerate(s):
        num = _ROMAN_VALUES[ch]
        if i + 1 < len(s) and num < _ROMAN_VALUES[s[i + 1]]:
            value -= num
        else:
            value += num
    return value > 0


def detect_system(value: str, discipline: str | None = None) -> GradeSystem | None:
    """Best-effort detection of the grade system.

    ``discipline`` ("bouldering" / "sport") disambiguates scales that share
    strings (e.g. ``7a+`` in both French and Fontainebleau).
    """
    raw = value.strip()
    if not raw:
        return None

    if _YDS_RE.match(raw):
        return GradeSystem.YDS
    if _V_RE.match(raw):
        return GradeSystem.V_SCALE

    letter = _FRENCH_RE.match(raw) or _FONT_LETTER_RE.match(raw)
    if letter:
        if discipline == "bouldering":
            return GradeSystem.FONT
        return GradeSystem.FRENCH

    if _FONT_NUMERIC_RE.match(raw):
        return GradeSystem.FONT

    roman = _ROMAN_RE.match(raw)
    if roman and _is_valid_roman(roman.group("roman")):
        # Avoid stealing French "5" style values: roman check runs last.
        return GradeSystem.UIAA

    return None


def _clean(raw: str, system: GradeSystem) -> str:
    text = " ".join(raw.strip().split())
    if system is GradeSystem.YDS:
        match = _YDS_RE.match(text)
        if not match:
            raise UnknownGradeError(f"Not a valid YDS grade: {raw!r}")
        return text.lower()
    if system in (GradeSystem.FRENCH, GradeSystem.FONT):
        return text.lower()
    if system is GradeSystem.V_SCALE:
        return text.upper()
    return text


def normalize_grade(value: str, system: GradeSystem | None = None, discipline: str | None = None) -> GradeRecord:
    """Normalize ``value`` inside its own system, preserving the original.

    Raises :class:`UnknownGradeError` when the system cannot be detected or
    the value is invalid for that system.
    """
    system = system or detect_system(value, discipline)
    if system is None:
        raise UnknownGradeError(f"Cannot detect grade system for: {value!r}")
    cleaned = _clean(value, system)
    return GradeRecord(value=value, system=system, normalized=cleaned)


def convert(
    value: str,
    from_system: GradeSystem,
    to_system: GradeSystem,
) -> GradeRecord | None:
    """Approximate conversion between systems; ``None`` when not tabulated."""
    if from_system is to_system:
        return normalize_grade(value, from_system)

    record = normalize_grade(value, from_system)
    src = record.normalized

    if from_system is GradeSystem.YDS and to_system is GradeSystem.FRENCH:
        target = _YDS_TO_FRENCH.get(src)
    elif from_system is GradeSystem.FRENCH and to_system is GradeSystem.YDS:
        target = _FRENCH_TO_YDS.get(src)
    elif from_system is GradeSystem.V_SCALE and to_system is GradeSystem.FONT:
        target = _V_TO_FONT.get(src)
    elif from_system is GradeSystem.FONT and to_system is GradeSystem.V_SCALE:
        target = _FONT_TO_V.get(src)
    else:
        target = None

    if target is None:
        return None
    return GradeRecord(value=value, system=to_system, normalized=target)
