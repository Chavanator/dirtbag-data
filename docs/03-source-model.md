# 03 — Source Model

## Entidad `Source`

```
Source: id · name · base_url · type · enabled
```

- `name` es el identificador estable usado por la CLI (`--source thecrag`).
- `enabled` gobierna qué adaptadores corre el scheduler; añadir una fuente nueva
  **no** requiere tocar el core (FR-018).

## Contrato de adaptador

Cada fuente vive en `src/dirtbag_data/crawlers/<fuente>/` con tres piezas:

```
crawler.py   # discovery + traversing geográfico (usa HTTP client compartido)
parser.py    # HTML/JSON → registros crudos (Pydantic)
models.py    # contratos específicos de la fuente
```

Reglas:

- El adaptador **solo** produce *source observations* crudas; jamás escribe en `routes` (spec §10 del export: "el scraper no debe escribir directamente sobre routes").
- El adaptador expone: `source_name`, `source_entity_id`, `source_url`, `observed_at`, `source_updated_at` (si existe) y los atributos vistos en la fuente (`source_name/grade/length/status/coordinates`).
- El parser devuelve datos inválidos como rechazo explícito (Pydantic) antes de tocar el modelo canónico.

## Fuente inicial: The Crag

- Habilitada en `configs/*.yaml`.
- Traversing por bbox geográfico (México → Nuevo León → El Salto → Las Ánimas).
- Bounding box de La Huasteca: **pendiente** (repo web: `docs/Plantilla de Datos Reales — Módulo Mapa.md`).

## Advertencia legal

Respetar ToS, `robots.txt` y rate limits de cada fuente (ver `13-operations.md`).
Mountain Project es notoriamente restrictiva con scraping: evaluar alternativas
(API oficial, datos cedidos por la comunidad, importación manual) antes del Phase 8.
