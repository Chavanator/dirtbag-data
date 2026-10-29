"""Crawler de The Crag — recorrido BFS del árbol de áreas (spec §24-§26).

Estrategia de descubrimiento (ver docs/sources/thecrag.md): las vistas de
listado completo requieren login; sin sesión solo hay (a) las rutas destacadas
en cada página de área y (b) el grafo de sub-áreas. Se recorre el árbol de
áreas y, de cada página, se toman sus filas de ruta y sus hijos.

Flujo por página: fetch → RAW (append-only) → parse → hash → observación.
Errores por página no abortan el crawl (NFR-001): se cuentan y se continúa.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx

from dirtbag_data.config.loader import Settings
from dirtbag_data.crawlers.http import PoliteClient, PoliteHttpError
from dirtbag_data.crawlers.thecrag.parser import parse_area_page, parse_route_page
from dirtbag_data.models.records import ParsedRoute, RouteLink
from dirtbag_data.pipeline.change_detection import content_hash
from dirtbag_data.storage.observations import (
    ObservationInput,
    ensure_source,
    record_crawl_run,
    record_observation,
)
from dirtbag_data.storage.raw import LocalRawStorage

logger = logging.getLogger(__name__)

SOURCE_NAME = "thecrag"


@dataclass
class CrawlSummary:
    scope: str
    areas: int = 0
    route_links: int = 0
    route_pages: int = 0
    written: int | None = None  # None en dry-run
    unchanged: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "areas": self.areas,
            "route_links": self.route_links,
            "route_pages": self.route_pages,
            "written": self.written,
            "unchanged": self.unchanged,
            "errors": self.errors,
        }


def _observation_from(route: ParsedRoute, raw_key: str, observed_at: datetime) -> ObservationInput:
    grade = route.grade_value
    return ObservationInput(
        source_entity_id=route.source_entity_id,
        source_url=route.source_url,
        source_name=route.name,
        source_grade=route.grade_value,
        source_length=route.length_raw,
        source_status=route.status,
        source_coordinates=(
            (route.latitude, route.longitude)
            if route.latitude is not None and route.longitude is not None
            else None
        ),
        normalized_data=route.model_dump(),
        content_hash=content_hash(
            name=route.name,
            grade_value=grade,
            grade_system=route.grade_system.value,
            length_m=route.length_m,
            latitude=route.latitude,
            longitude=route.longitude,
            status=route.status,
        ),
        raw_object_key=raw_key,
        observed_at=observed_at,
    )


async def crawl_area_tree(
    settings: Settings,
    seed_url: str,
    *,
    limit: int | None = None,
    dry_run: bool = False,
    transport: httpx.AsyncBaseTransport | None = None,
    rate_limit_seconds: float | None = None,
) -> CrawlSummary:
    """BFS por el árbol de áreas; para cuando ``limit`` rutas candidatas están
    recolectadas y luego baja sus fichas hasta escribir ``limit`` observaciones."""
    summary = CrawlSummary(scope=seed_url)
    storage = LocalRawStorage(settings.storage.raw_path)
    client = PoliteClient.from_settings(
        settings.http,
        transport=transport,
    )
    if rate_limit_seconds is not None:
        client.rate_limit_seconds = rate_limit_seconds

    engine = None
    started_at = datetime.now(UTC)
    try:
        conn_cm = None
        if not dry_run:
            from sqlalchemy import create_engine

            engine = create_engine(settings.database.url)
            conn_cm = engine.begin()

        with conn_cm if conn_cm is not None else _NullContext() as conn:
            source_id = None
            if conn is not None:
                source_id = ensure_source(
                    conn,
                    name=SOURCE_NAME,
                    base_url=settings.crawlers.sources.get(
                        SOURCE_NAME
                    ).base_url
                    if SOURCE_NAME in settings.crawlers.sources
                    else "https://www.thecrag.com",
                )

            # --- fase 1: BFS del árbol de áreas ---
            area_queue: deque[str] = deque([seed_url])
            visited_areas: set[str] = set()
            route_links: dict[str, RouteLink] = {}
            while area_queue:
                area_url = area_queue.popleft()
                if area_url in visited_areas:
                    continue
                visited_areas.add(area_url)
                try:
                    html = await client.get_text(area_url)
                except PoliteHttpError as exc:
                    summary.errors += 1
                    summary.error_messages.append(str(exc))
                    logger.warning("area failed: %s", exc)
                    continue
                storage.save(SOURCE_NAME, area_url, html)
                page = parse_area_page(html, area_url)
                summary.areas += 1
                for child in page.child_areas:
                    if child.url not in visited_areas:
                        area_queue.append(child.url)
                for link in page.routes:
                    route_links.setdefault(link.source_entity_id, link)
                if limit is not None and len(route_links) >= limit:
                    break

            summary.route_links = len(route_links)

            # --- fase 2: fichas de ruta ---
            written = 0
            for link in route_links.values():
                if limit is not None and summary.route_pages >= limit:
                    break
                try:
                    html = await client.get_text(link.url)
                except PoliteHttpError as exc:
                    summary.errors += 1
                    summary.error_messages.append(str(exc))
                    logger.warning("route failed: %s", exc)
                    continue
                raw_key = storage.save(SOURCE_NAME, link.url, html)
                route = parse_route_page(html, link.url)
                route.fill_missing(link)
                summary.route_pages += 1
                if conn is None:
                    continue  # dry-run: no toca BD
                obs = _observation_from(route, raw_key, observed_at=started_at)
                if record_observation(conn, source_id, obs):
                    written += 1
                else:
                    summary.unchanged += 1

            summary.written = written if conn is not None else None
            if conn is not None and source_id is not None:
                record_crawl_run(
                    conn,
                    source_id=source_id,
                    scope=seed_url,
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    status="completed" if summary.errors == 0 else "partial",
                    pages_processed=summary.areas + summary.route_pages,
                    routes_found=summary.route_links,
                    routes_changed=summary.unchanged,
                    routes_new=written,
                    errors=summary.errors,
                    logs="; ".join(summary.error_messages[:20]) or None,
                )
    finally:
        await client.aclose()
        if engine is not None:
            engine.dispose()

    return summary


class _NullContext:
    """Context manager vacío para dry-run (sin conexión)."""

    def __enter__(self) -> None:
        return None

    def __exit__(self, *exc: object) -> None:
        return None
