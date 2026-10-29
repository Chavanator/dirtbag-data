# 00 — Overview

**Módulo:** DirtBag Data Acquisition & Route Intelligence
**Spec maestro:** `instructions/Data_acquisition.txt` (repo web, v0.1) — este documento es su resumen operativo; ante conflicto, manda el spec.
**Stack:** Python 3.12+ · uv · PostgreSQL + PostGIS · Docker · HTTPX · BeautifulSoup/lxml · Playwright · Pydantic · RapidFuzz · Shapely · Polars · Alembic

## Objetivo

No es "un scraper de The Crag": es construir el **Data Layer** propio de DirtBag.
Cada ruta tiene identidad canónica, ubicación, disciplina, grado, longitud, historial
y procedencia. DirtBag es dueño de su modelo y su histórico; ninguna fuente externa
define la estructura.

## Pipeline (inmutable → canónico)

```
SOURCE → RAW → PARSE → NORMALIZE → MATCH → RECONCILE → CANONICAL
                                     │
                                     └─ Source Observations (inmutables)
```

## Fuentes

| Fuente | Fase | Estado |
|---|---|---|
| The Crag | 4–5 | adaptador Phase 4 ✅ (BFS + observaciones) · crawl en vivo pendiente de autorización |
| Mountain Project | 8 | pendiente (ToS restrictivas — revisar legalmente) |
| 8a.nu | 9 | pendiente |
| Guías / PDF | — | flujo manual actual (repo web: `docs/pitumarca_demo/`) |

## Primer vertical slice (reducción de riesgo)

The Crag → México → Nuevo León → El Salto → Las Ánimas → Routes.
Después: expandir alcance y añadir fuentes.

## Estado actual

| Fase | Contenido | Estado |
|---|---|---|
| 0 | repositorio, uv, lint, tests, CLI, config | ✅ |
| 1 | Docker Compose (PostGIS) | ✅ `dirtbag-postgres` healthy en :5433 |
| 2 | esquema PostgreSQL (migración 0001) | ✅ upgrade + roundtrip + smoke `ST_DWithin` en vivo |
| 3 | grade system + normalizador | ✅ |
| 4 | crawler The Crag (BFS áreas, RAW, observaciones idempotentes) | ✅ offline: parser+e2e con fixtures y MockTransport · en vivo pendiente |
| 5+ | matching, reconciliación, producción | ⬜ pendiente |

**Infra adoptada (2026-10-25):** GitHub Actions + Supabase Free + R2 en Fase 2 — US$0/mes;
detalles y riesgos en `12-deployment.md`.

Ver `10-development.md` para el orden de fases 01–20.
