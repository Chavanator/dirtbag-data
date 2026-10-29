# 02 — Data Model

Migración canónica: `migrations/versions/0001_initial_schema.py` (fuente de verdad ejecutable).
Resumen: UUIDs server-side (`gen_random_uuid()`), timestamps `created_at/updated_at` (tz), FKs sin `ON DELETE CASCADE` (NFR-006: nunca destruir histórico).

## Jerarquía geográfica

```
countries └── states └── zones └── sectors └── routes └── pitches
```

- `zones (state_id, slug)` únicos; `sectors (zone_id, slug)`; `routes (sector_id, slug)`.
- `pitches (route_id, number)` — la multipitch es **una** Route con pitches hijos (spec §16); jamás rutas independientes por pitch.

## Ruta canónica (`routes`)

| Columna | Notas |
|---|---|
| `discipline` | FR-009: múltiples disciplinas (sport, boulder, trad…) |
| `is_multipitch` | FR-010 |
| `grade_value / grade_system / grade_normalized` | spec: `{value, system, normalized}` — el valor original siempre se conserva |
| `status` | CHECK: `active, closed, removed, unknown` (FR-013), histórico vía observaciones |
| `alternative_names` | FR-012 |
| `confidence` | 0–1, calculada por evidencia (spec §23, sin jerarquía rígida de fuentes) |
| `location` | `geometry(Point,4326)` + índice GIST (NFR-007) |

## Observaciones (`source_observations`)

`route_id` **nullable**: una observación existe antes de que entity resolution asigne identidad canónica.
Única constraint `(source_id, source_entity_id, content_hash)` → **idempotencia** (spec §28).
`normalized_data JSONB` conserva el contrato Pydantic validado; `raw_object_key` apunta al snapshot RAW.

## Fuentes y crawls

- `sources`: entidad independiente por fuente (`thecrag`, `mountain_project`, `eighta`, `guidebook`) — FR-018.
- `crawl_runs`: estadísticas e historial de cada ejecución (`pending/running/completed/failed/partial`).

## Geometría sin geoalchemy2

El stack (spec §38) usa **Shapely**, no geoalchemy2: las columnas geometry se crean con SQL crudo
en la migración; para consultas se usa SQL estándar PostGIS (`ST_DWithin`, `ST_X/ST_Y`).
