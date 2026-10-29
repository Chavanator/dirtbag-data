"""Normalización de longitudes (spec Phase 3): fuentes en m / ft → metros."""

from __future__ import annotations

import re

_FT_TO_M = 0.3048

_LENGTH_RE = re.compile(
    r"^\s*(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>m|metros?|meters?|mt|ft|feet|foot|')\s*$",
    re.IGNORECASE,
)


def parse_length(raw: str | None) -> float | None:
    """Convierte ``"28m"`` / ``"90 ft"`` / ``"90'"`` a metros (3 decimales).

    ``None`` cuando falta o no es interpretable — jamás adivina unidades.
    """
    if not raw:
        return None
    match = _LENGTH_RE.match(raw)
    if not match:
        return None
    value = float(match.group("value").replace(",", "."))
    unit = match.group("unit").lower().replace("'", "ft")
    if unit in {"ft", "feet", "foot"}:
        return round(value * _FT_TO_M, 3)
    return value
