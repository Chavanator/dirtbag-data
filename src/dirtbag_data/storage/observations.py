"""Escritura de observaciones de fuente (spec §25) — jamás escribe `routes`.

Idempotencia §28: ``ON CONFLICT (source_id, source_entity_id, content_hash) DO
NOTHING`` → re-crawlear lo mismo no duplica filas.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Connection


class ObservationInput(BaseModel):
    source_entity_id: str
    source_url: str
    source_name: str | None = None
    source_grade: str | None = None
    source_length: str | None = None
    source_status: str | None = None
    source_coordinates: tuple[float, float] | None = None  # (lat, lng)
    normalized_data: dict[str, Any] = {}
    content_hash: str
    raw_object_key: str | None = None
    observed_at: datetime


def ensure_source(conn: Connection, *, name: str, base_url: str, type_: str = "website") -> str:
    row = conn.execute(
        text("SELECT id FROM sources WHERE name = :name"), {"name": name}
    ).first()
    if row is not None:
        return str(row[0])
    return str(
        conn.execute(
            text(
                "INSERT INTO sources (name, base_url, type) "
                "VALUES (:name, :base_url, :type) "
                "ON CONFLICT (name) DO UPDATE SET name = sources.name "
                "RETURNING id"
            ),
            {"name": name, "base_url": base_url, "type": type_},
        ).scalar_one()
    )


_INSERT_WITH_COORDS = """
    INSERT INTO source_observations (
        source_id, source_entity_id, source_url, observed_at,
        source_name, source_grade, source_length, source_status,
        source_coordinates, normalized_data, content_hash, raw_object_key
    ) VALUES (
        :source_id, :entity_id, :source_url, :observed_at,
        :source_name, :source_grade, :source_length, :source_status,
        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
        CAST(:normalized_data AS jsonb), :content_hash, :raw_object_key
    )
    ON CONFLICT (source_id, source_entity_id, content_hash) DO NOTHING
"""

_INSERT_NO_COORDS = """
    INSERT INTO source_observations (
        source_id, source_entity_id, source_url, observed_at,
        source_name, source_grade, source_length, source_status,
        source_coordinates, normalized_data, content_hash, raw_object_key
    ) VALUES (
        :source_id, :entity_id, :source_url, :observed_at,
        :source_name, :source_grade, :source_length, :source_status,
        NULL, CAST(:normalized_data AS jsonb), :content_hash, :raw_object_key
    )
    ON CONFLICT (source_id, source_entity_id, content_hash) DO NOTHING
"""


def record_observation(conn: Connection, source_id: str, obs: ObservationInput) -> bool:
    """Inserta una observación. ``True`` = fila nueva; ``False`` = ya existía."""
    params: dict[str, Any] = {
        "source_id": source_id,
        "entity_id": obs.source_entity_id,
        "source_url": obs.source_url,
        "observed_at": obs.observed_at,
        "source_name": obs.source_name,
        "source_grade": obs.source_grade,
        "source_length": obs.source_length,
        "source_status": obs.source_status,
        "normalized_data": json.dumps(obs.normalized_data, ensure_ascii=False),
        "content_hash": obs.content_hash,
        "raw_object_key": obs.raw_object_key,
    }
    if obs.source_coordinates is not None:
        lat, lng = obs.source_coordinates
        params["lat"] = lat
        params["lng"] = lng
        sql = _INSERT_WITH_COORDS
    else:
        sql = _INSERT_NO_COORDS
    result = conn.execute(text(sql), params)
    return result.rowcount == 1


_INSERT_CRAWL_RUN = """
    INSERT INTO crawl_runs (
        source_id, geographic_scope, started_at, finished_at, status,
        pages_processed, routes_found, routes_changed, routes_new, errors, logs
    ) VALUES (
        :source_id, :scope, :started_at, :finished_at, :status,
        :pages, :found, :changed, :new, :errors, :logs
    )
"""


def record_crawl_run(
    conn: Connection,
    *,
    source_id: str,
    scope: str,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    pages_processed: int,
    routes_found: int,
    routes_changed: int,
    routes_new: int,
    errors: int,
    logs: str | None = None,
) -> None:
    conn.execute(
        text(_INSERT_CRAWL_RUN),
        {
            "source_id": source_id,
            "scope": scope,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "pages": pages_processed,
            "found": routes_found,
            "changed": routes_changed,
            "new": routes_new,
            "errors": errors,
            "logs": logs,
        },
    )
