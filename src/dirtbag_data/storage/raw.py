"""Almacenamiento RAW append-only (spec §24, NFR-006): nada se sobreescribe.

Clave canónica: ``<source>/<YYYY-MM-DD>/<slug-url>-<sha1>.html``
dentro de ``raw_dir`` (Fase 1: disco local; Fase 2: R2 con misma clave).
"""

from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path


class LocalRawStorage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def save(self, source: str, url: str, content: str, fetched_at: date | None = None) -> str:
        day = (fetched_at or date.today()).isoformat()
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        tail = url.split("//", 1)[-1].strip("/")
        slug = re.sub(r"[^a-z0-9]+", "-", tail.lower()).strip("-")[-80:] or "page"
        key = f"{source}/{day}/{slug}-{digest}.html"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():  # append-only: jamás sobreescribe
            path.write_text(content, encoding="utf-8")
        return key
