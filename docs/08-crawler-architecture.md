# 08 — Crawler Architecture

## Estructura por fuente (§29)

```
src/dirtbag_data/crawlers/
├── thecrag/{crawler.py, parser.py, models.py}
├── mountain_project/{...}
└── eighta/{...}
```

El core jamás importa detalles internos de un adaptador; solo su contrato.

## HTTP (§30)

- Cliente principal: **HTTPX** (async, connection pooling).
- Obligatorio: timeouts, retrasos controlados, retries limitados, **rate
  limiting** (default `DIRTBAG_HTTP_RATE_LIMIT_SECONDS=1.5`), headers
  configurables (UA `DirtBagBot`), logging.
- **Nunca crawling agresivo.**

## Parsing (§31)

- BeautifulSoup + lxml/XPath según la fuente.
- Playwright (§32) **solo** cuando el contenido real dependa de JavaScript;
  no para todas las páginas.

## Validación (§33)

- Pydantic como contrato: HTML → `RouteRecord` validado.
- Datos inválidos se rechazan **antes** del modelo canónico (con log, sin
  romper el crawl completo — NFR-001).

## CrawlRun (§26–28)

Cada ejecución registra: `source, geographic_scope, started_at, finished_at,
status(pending|running|completed|failed|partial), pages_processed,
routes_found, routes_new, routes_changed, errors, logs`.

- **Falsos deletes**: 0 rutas encontradas + `status=failed` **no** significa
  "0 rutas existen" — se conserva el estado anterior (§27).
- **Idempotencia**: dos crawls sin cambios ⇒ mismas 100 rutas, no 200 (§28).

## Scheduling (Phase 11)

manual → semanal → diario, según actividad de la fuente. Sin message queue:
CLI + cron/GitHub Actions (§39, ADR-004).
