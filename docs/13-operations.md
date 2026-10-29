# 13 — Operations

## Formato de log por crawl (§44)

```
START · SOURCE · SCOPE · PAGES · ROUTES · NEW · UPDATED · UNCHANGED · ERRORS · DURATION · END

Crawl completed
Source:  The Crag
Scope:   Nuevo León
Pages:   1,284
Routes:  2,184   New: 43   Changed: 128   Unchanged: 2,013
Errors:  4
Duration: 18m 32s
```

El mismo resumen se persiste en `crawl_runs` (consultable con `dirtbag status`).

## Políticas operativas

1. **Rate limiting siempre** (1.5–2 s entre requests, UA identificable).
2. **ToS/robots.txt antes que código**: revisar por fuente antes de habilitarla
   (Mountain Project: evaluar alternativas antes de Phase 8).
3. **Crawl fallido** → `crawl_runs.status=failed`, alerta, **cero** escrituras
   destructivas (FR-016).
4. **Reintentos**: solo con backoff acotado; un alcance completo jamás en bucle.
5. **Scheduler**: manual → semanal → diario (Phase 11).

## Estado del entorno (2026-10-25)

- Docker Desktop: **activo**; `docker compose up -d` → `dirtbag-postgres`
  (postgis/postgis:16-3.4) **healthy** en `localhost:5433`
  (5432 ocupado por el postgres de otro proyecto local).
- `alembic upgrade head` verificado en vivo + roundtrip
  (upgrade → downgrade → upgrade) + smoke espacial `ST_DWithin` ✅.

## Backup / restore (Phase 12)

- `pg_dump` programado + retención + **prueba de restore** (DoD del spec).
- Object storage con versionado si el proveedor lo permite.

## Alertas mínimas

- Crawl `failed` o `partial` > 0 errores.
- Última ejecución con éxito > 2× intervalo programado.
- Espacio de object storage / crecimiento anómalo de observaciones.
