"""Shared fixtures/helpers for dirtbag-data tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "thecrag"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


_db_state: dict[str, bool] = {}


def db_ready() -> bool:
    """True si la BD local responde Y tiene el esquema aplicado."""
    if "ready" in _db_state:
        return _db_state["ready"]
    try:
        from sqlalchemy import create_engine, text

        from dirtbag_data.config import load_settings

        engine = create_engine(load_settings().database.url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT postgis_version()"))
            has_table = conn.execute(
                text(
                    "SELECT to_regclass('public.source_observations') IS NOT NULL"
                )
            ).scalar()
        engine.dispose()
        _db_state["ready"] = bool(has_table)
    except Exception:  # cualquier fallo -> tests de BD se saltan
        _db_state["ready"] = False
    return _db_state["ready"]


requires_db = pytest.mark.skipif(
    not db_ready(),
    reason="BD local no disponible o esquema sin aplicar (alembic upgrade head)",
)
