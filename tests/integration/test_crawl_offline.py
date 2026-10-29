"""E2E offline del crawler BFS: fixtures servidos por httpx.MockTransport.

Sin red. La variante con BD (skip si no hay BD) verifica idempotencia real:
segundo crawl con el mismo HTML → 0 escrituras, N sin cambios.
"""

import httpx
from sqlalchemy import create_engine, text

from dirtbag_data.config import load_settings
from dirtbag_data.crawlers.thecrag.crawler import crawl_area_tree
from tests.conftest import load_fixture, requires_db

SEED = "https://www.thecrag.com/en/climbing/mexico/el-salto"

_FIXTURES = {
    SEED: "el_salto_area.html",
    "/en/climbing/mexico/el-salto/area/9288277437": "area_9288277437.html",
    "/en/climbing/mexico/el-salto/area/9288353292": "area_9288353292.html",
    "/en/climbing/mexico/el-salto/route/11939401": "route_11939401.html",
}


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/en/climbing/mexico/el-salto":
        return httpx.Response(200, text=load_fixture(_FIXTURES[SEED]))
    for suffix, name in _FIXTURES.items():
        if suffix != SEED and path == suffix:
            return httpx.Response(200, text=load_fixture(name))
    if "/route/" in path:
        # cualquier otra ruta sirve la misma ficha (id distinto por URL)
        return httpx.Response(200, text=load_fixture("route_11939401.html"))
    return httpx.Response(404)  # áreas desconocidas → error no fatal


_TRANSPORT = httpx.MockTransport(_handler)


async def test_dry_run_walks_root_and_collects_links():
    settings = load_settings()
    summary = await crawl_area_tree(
        settings,
        SEED,
        limit=3,
        dry_run=True,
        transport=_TRANSPORT,
        rate_limit_seconds=0.0,
    )
    assert summary.areas == 1
    assert summary.route_links == 18  # destacadas del root
    assert summary.route_pages == 3  # limit respetado
    assert summary.written is None  # dry-run no toca BD
    assert summary.errors == 0


async def test_bfs_counts_missing_children_as_errors_not_failures():
    """Las 12 áreas hijas sin fixture devuelven 404 → errores, no aborto."""
    settings = load_settings()
    summary = await crawl_area_tree(
        settings,
        SEED,
        limit=None,
        dry_run=True,
        transport=_TRANSPORT,
        rate_limit_seconds=0.0,
    )
    # root + Los Delirios + Nebulosidad tienen fixture; el resto del árbol → 404
    assert summary.areas == 3
    assert summary.errors == 13  # 10 hijos root sin fixture + 3 de Los Delirios
    assert summary.route_pages == summary.route_links  # todo lo posible, sin aborto
    assert summary.route_links == 21  # 18 root + 1 Los Delirios + 3 Nebulosidad (dedupe)
    assert len(summary.error_messages) == summary.errors


@requires_db
async def test_crawl_with_db_is_idempotent():
    settings = load_settings()
    engine = create_engine(settings.database.url)
    scope_key = f"%{SEED}%"
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM source_observations WHERE source_url LIKE :u"
                ),
                {"u": scope_key},
            )
            conn.execute(
                text(
                    "DELETE FROM crawl_runs WHERE geographic_scope = :s"
                ),
                {"s": SEED},
            )

        first = await crawl_area_tree(
            settings,
            SEED,
            limit=3,
            dry_run=False,
            transport=_TRANSPORT,
            rate_limit_seconds=0.0,
        )
        assert first.written == 3
        assert first.unchanged == 0

        second = await crawl_area_tree(
            settings,
            SEED,
            limit=3,
            dry_run=False,
            transport=_TRANSPORT,
            rate_limit_seconds=0.0,
        )
        assert second.written == 0
        assert second.unchanged == 3  # misma fuente + mismo hash → sin cambio

        with engine.connect() as conn:
            n = conn.execute(
                text(
                    "SELECT count(*) FROM source_observations WHERE source_url LIKE :u"
                ),
                {"u": scope_key},
            ).scalar_one()
            assert n == 3  # ninguna fila duplicada
            runs = conn.execute(
                text(
                    "SELECT count(*) FROM crawl_runs WHERE geographic_scope = :s"
                ),
                {"s": SEED},
            ).scalar_one()
            assert runs == 2
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM source_observations WHERE source_url LIKE :u"),
                {"u": scope_key},
            )
            conn.execute(
                text("DELETE FROM crawl_runs WHERE geographic_scope = :s"),
                {"s": SEED},
            )
        engine.dispose()
