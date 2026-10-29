# 11 — Testing

Tres niveles (spec §45). Estado actual: **36 tests unitarios verdes**.

## Unit (`tests/unit/`) — sin red, sin DB

Ejemplos del spec y los ya implementados:

| Área | Tests |
|---|---|
| Parser | HTML fixture → `RouteRecord` (Phase 4) |
| Normalizer | `90 ft → 27.432 m` (Phase 3, pendiente) |
| Grades | ✅ `detect_system`, `normalize_grade`, `convert` (`5.10d↔7a+`, `V6↔7a`, desconocidos → `UnknownGradeError`) |
| Matcher | `Pleciosaurus ↔ Plesiosaurus` (Phase 6, pendiente) |
| Config | ✅ YAML + overrides `DIRTBAG_*` + expansión `${VAR:-default}` |
| CLI | ✅ `status`, `crawl` (exit 2), enmascaramiento de credenciales |

## Integration (`tests/integration/`) — DB real via Docker

```
Crawler → Parser → Normalizer → Database
```
Requiere `docker compose up` + PostGIS; migraciones al inicio del suite.
**Pendiente**: el entorno actual no tiene Docker activo (symlink WSL roto —
iniciar Docker Desktop).

## End-to-end

```
Source → Crawler → RAW → Observation → Matching → Canonical Route
```

Fixture principle: los HTML de test viven en `tests/fixtures/` (capturas
inmutables de fuentes reales) — nunca hacer red en CI (reproducibilidad NFR-002).

## Gates

- Toda fase nueva: tests + lint antes de documentarla como completa (§49).
- CI futuro: `ruff check` + `pytest` en cada push.
