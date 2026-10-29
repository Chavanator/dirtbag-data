"""Change detection (spec §25): hash de contenido por observación.

Si ``old_hash == new_hash`` no hay cambio relevante → no se inserta nada
(idempotencia §28). Si difiere → nueva observación/version.

Se hashean SIEMPRE valores normalizados (no el texto crudo) para que un cambio
de formato (``5.11A`` vs ``5.11a``) no genere observaciones falsas.
"""

from __future__ import annotations

import hashlib
import json


def content_hash(
    *,
    name: str,
    grade_value: str,
    grade_system: str,
    length_m: float | None,
    latitude: float | None,
    longitude: float | None,
    status: str,
) -> str:
    payload = {
        "name": " ".join(name.split()),
        "grade": f"{grade_system}:{grade_value}",
        "length_m": round(length_m, 1) if length_m is not None else None,
        "coordinates": (
            [round(latitude, 6), round(longitude, 6)]
            if latitude is not None and longitude is not None
            else None
        ),
        "status": status,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
