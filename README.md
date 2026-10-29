# dirtbag-data

**DirtBag Data Acquisition & Route Intelligence** — módulo de datos de DirtBag:
crawling de fuentes de escalada, normalización, entity resolution, reconciliación
y modelo canónico de rutas con histórico temporal.

Spec maestro: [`instructions/Data_acquisition.txt`](../instructions/Data_acquisition.txt)
(en el repo web) — este módulo es su implementación (fases 0–12 del spec).

> El sistema **no es un scraper simple**: construye la base de conocimiento propia
> de DirtBag. RAW e insumos son inmutables; el modelo canónico se deriva de
> *source observations* y nunca destruye histórico (NFR-006).

## Fuentes iniciales

| Fuente | Estado |
|---|---|
| The Crag | adaptador Phase 4 ✅ (crawl en vivo pendiente de autorización) |
| Mountain Project | deshabilitada (Phase 8) |
| 8a.nu | deshabilitada (Phase 9) |
| Guías impresas / PDF | futuro (flujo manual actual en `docs/pitumarca_demo/` del repo web) |

## Requisitos

- Python ≥ 3.12 ([uv](https://docs.astral.sh/uv/))
- Docker + Docker Compose (PostgreSQL + PostGIS) para la base de datos
- Playwright solo donde el contenido real dependa de JavaScript (spec §32)

## Puesta en marcha

```bash
cp .env.example .env
uv sync                       # instala dependencias + grupos dev
docker compose up -d          # PostgreSQL + PostGIS en :5433
uv run alembic upgrade head   # esquema (Phase 2)
uv run dirtbag status         # smoke de la CLI
uv run pytest                 # tests
uv run ruff check .           # lint
```

## CLI (spec §36)

```bash
uv run dirtbag crawl el-salto --dry-run --limit 5   # fetch+parse sin tocar BD
uv run dirtbag crawl el-salto --limit 20            # escribe observaciones (idempotente)
uv run dirtbag crawl <url-completa> --source thecrag
uv run dirtbag status
uv run dirtbag validate    # pendiente
uv run dirtbag reconcile   # pendiente
```

## Estructura

```
dirtbag-data/
├── configs/            # development.yaml / production.yaml
├── migrations/         # Alembic (esquema PostgreSQL + PostGIS)
├── src/dirtbag_data/
│   ├── cli/            # CLI `dirtbag`
│   ├── crawlers/       # adaptadores por fuente (thecrag, mountain_project, eighta)
│   ├── parsers/        # HTML → registros crudos
│   ├── models/         # modelos Pydantic (contratos)
│   ├── normalization/  # grados, longitudes, nombres
│   ├── matching/       # entity resolution (RapidFuzz + PostGIS)
│   ├── reconciliation/ # observaciones → valores canónicos
│   ├── validation/     # contratos de datos
│   ├── storage/        # RAW object storage
│   ├── pipeline/       # orquestación fetch→parse→normalize→match→reconcile→persist
│   └── config/         # settings
├── tests/{unit,integration,fixtures}/
├── data/local/         # RAW snapshots en desarrollo (gitignored)
└── docs/               # 00–13 + decisions/ADR
```

## Documentación

- `docs/00-overview.md` … `docs/13-operations.md`
- `docs/decisions/` — ADR-001…004
- `AGENTS.md` — reglas que el agente debe respetar en este módulo

## Estado

Phases 0–4 completas: scaffold + CLI + config, PostGIS local (:5433,
migración 0001 con roundtrip y smoke espacial), grade normalization y
**crawler The Crag** (parser contra fixtures reales, BFS por áreas, RAW
append-only, observaciones idempotentes, `crawl_runs`) — 60 tests, ruff limpio.
El crawl en vivo queda pendiente de autorización (los tests no usan red).
Ver `docs/10-development.md` (fases 01–20) y la regla de no avanzar sin
implementation + tests + documentation.
Infra adoptada (Actions + Supabase, US$0): `docs/12-deployment.md`.
