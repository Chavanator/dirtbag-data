# 10 — Development

## Setup

```bash
cp .env.example .env
uv sync
docker compose up -d          # PostgreSQL + PostGIS (requiere Docker Desktop activo)
uv run alembic upgrade head
uv run dirtbag status
uv run pytest && uv run ruff check .
```

## Comandos de verificación (correr siempre antes de dar por cerrada una fase)

```bash
uv run ruff check .      # lint
uv run pytest            # tests
uv run alembic upgrade head --sql   # valida migraciones sin DB (modo offline)
```

## Orden de implementación (§48)

```
01 Repository → 02 Docker → 03 PostgreSQL+PostGIS → 04 DB schema
→ 05 Pydantic models → 06 Source abstraction → 07 CrawlRun → 08 Raw storage
→ 09 The Crag crawler → 10 The Crag parser → 11 Normalization
→ 12 Observations → 13 Change detection → 14 Entity resolution
→ 15 Canonicalization → 16 Historical data → 17 CLI → 18 Tests
→ 19 Documentation → 20 Production deployment
```

## Regla de fase (§49)

**No avanzar si la fase anterior no tiene implementation + tests + documentation.**
Cada cambio estructural queda registrado en `docs/architecture/` y cada decisión
importante en `docs/decisions/` (ADR).

## Convenciones

- Ruff (config en `pyproject.toml`), line-length 100, Python 3.12+.
- Pytest: unit en `tests/unit/`, integración en `tests/integration/`,
  HTML de fixture en `tests/fixtures/` (nunca red en unit tests).
- Contratos Pydantic viven en `models/` y se comparten entre parser y pipeline.
- Sin secretos en config YAML: `${VAR}` o variables `DIRTBAG_*`.

## Entorno del agente

Ver `AGENTS.md` (reglas vinculantes) y el spec maestro
`../instructions/Data_acquisition.txt`.
