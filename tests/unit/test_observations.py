"""Tests de observaciones contra la BD local (skip si no hay BD/esquema).

Verifican idempotencia §28: reinsertar la misma observación no duplica filas.
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine, text

from dirtbag_data.config import load_settings
from dirtbag_data.storage.observations import (
    ObservationInput,
    ensure_source,
    record_observation,
)
from tests.conftest import requires_db

_ENTITY = f"test-obs-{uuid4()}"


@requires_db
def test_ensure_source_idempotent_and_record_dedupes():
    settings = load_settings()
    engine = create_engine(settings.database.url)
    now = datetime.now(UTC)
    obs = ObservationInput(
        source_entity_id=_ENTITY,
        source_url=f"https://www.thecrag.com/en/climbing/mexico/el-salto/route/{_ENTITY}",
        source_name="Ruta de prueba",
        source_grade="5.10a",
        source_length="28m",
        source_status="unknown",
        source_coordinates=(25.394583, -100.239040),
        normalized_data={"name": "Ruta de prueba", "grade_value": "5.10a"},
        content_hash="a" * 64,
        raw_object_key="thecrag/2026-10-27/test.html",
        observed_at=now,
    )
    try:
        with engine.begin() as conn:
            sid1 = ensure_source(conn, name="thecrag", base_url="https://www.thecrag.com")
            sid2 = ensure_source(conn, name="thecrag", base_url="https://www.thecrag.com")
            assert sid1 == sid2

            assert record_observation(conn, sid1, obs) is True  # fila nueva
            assert record_observation(conn, sid1, obs) is False  # duplicado exacto
            count = conn.execute(
                text(
                    "SELECT count(*) FROM source_observations "
                    "WHERE source_id = :sid AND source_entity_id = :eid"
                ),
                {"sid": sid1, "eid": _ENTITY},
            ).scalar_one()
            assert count == 1

            # geometría escrita correctamente (Point, 4326)
            x = conn.execute(
                text(
                    "SELECT ST_X(source_coordinates) FROM source_observations "
                    "WHERE source_id = :sid AND source_entity_id = :eid"
                ),
                {"sid": sid1, "eid": _ENTITY},
            ).scalar_one()
            assert abs(float(x) - (-100.239040)) < 1e-6
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM source_observations WHERE source_entity_id = :eid"),
                {"eid": _ENTITY},
            )
        engine.dispose()


@requires_db
def test_record_without_coordinates():
    settings = load_settings()
    engine = create_engine(settings.database.url)
    eid = f"test-obs-nocoord-{uuid4()}"
    obs = ObservationInput(
        source_entity_id=eid,
        source_url="https://example.test/r/1",
        source_name="Sin coords",
        source_status="unknown",
        source_coordinates=None,
        normalized_data={},
        content_hash="b" * 64,
        observed_at=datetime.now(UTC),
    )
    try:
        with engine.begin() as conn:
            sid = ensure_source(conn, name="thecrag", base_url="https://www.thecrag.com")
            assert record_observation(conn, sid, obs) is True
            coord = conn.execute(
                text(
                    "SELECT source_coordinates IS NULL FROM source_observations "
                    "WHERE source_entity_id = :eid"
                ),
                {"eid": eid},
            ).scalar_one()
            assert coord is True
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM source_observations WHERE source_entity_id = :eid"),
                {"eid": eid},
            )
        engine.dispose()
