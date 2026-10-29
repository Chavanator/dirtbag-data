# AGENTS.md — dirtbag-data

Reglas vinculantes para agentes trabajando en este módulo.

## Fuente de verdad

1. Spec maestro: `../instructions/Data_acquisition.txt` (v0.1) — ante conflicto
   con `docs/`, manda el spec.
2. `docs/decisions/` — ADRs aceptados; cambiar un ADR requiere nuevo ADR en estado propuesto.
3. Este archivo — reglas operativas.

## Regla de fase (spec §49)

**No avanzar de fase si la anterior no tiene implementation + tests + documentation.**
Orden de fases: ver `docs/10-development.md` (01–20) y `docs/00-overview.md` (estado).

## Principios innegociables (spec §39)

- Cada fuente = un adaptador en `crawlers/<fuente>/`; el core no conoce sus internals.
- RAW y `source_observations` son **append-only**: jamás UPDATE/DELETE desde el pipeline.
- El crawler **nunca** escribe directo sobre `routes` — solo produce observaciones.
- Sin LLM para operaciones deterministas (matching básico = RapidFuzz + PostGIS).
- Sin infraestructura prematura: sin RabbitMQ/K8s/microservicios (ADR-004).
- Crawling siempre con rate limiting, UA identificable y respeto a ToS/robots.txt.
- Grados: conservar siempre el valor original; conversiones solo si están en tabla (jamás adivinar).

## Verificación obligatoria

Antes de dar por terminado cualquier cambio:

```bash
uv run ruff check .                               # lint
uv run pytest                                     # tests
uv run alembic upgrade head --sql                 # valida migraciones sin DB
```

Si el cambio toca la CLI o config, además:

```bash
uv run dirtbag status --config configs/development.yaml
```

## Entorno (2026-10-25)

- Python 3.12 (uv) · Docker Desktop **activo**; PostGIS en `localhost:5433`
  (5432 pertenece a otro proyecto — no tocarlo ni redirigirlo).
- Migraciones ya verificadas en vivo (upgrade/downgrade roundtrip + `ST_DWithin`).
- Infra adoptada: GitHub Actions + Supabase Free (+ R2 en Fase 2), ver
  `docs/12-deployment.md` — no comprar infraestructura sin instrucción explícita.
- No instalar dependencias fuera de `pyproject.toml`; usar `uv add`/`uv sync`.

## Límites de alcance

- No modificar la app web (`../app`, `../components`, `../messages`, …) ni
  `../instructions/` (specs históricas — leer, no editar).
- Datos de demo del frontend (`../lib/mock-data/**`) viven en español y son
  dominio del repo web, no de este módulo.
- Producción y hosting: decisiones en `docs/12-deployment.md`; no comprar
  infraestructura sin instrucción explícita del usuario.
