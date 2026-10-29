# 04 — Observation Model

`source_observations` es la entidad más importante del sistema (spec §19).

## Qué es

El registro **inmutable** de "lo que una fuente dijo, una vez, en un momento":

```
SourceObservation
├── source_id · route_id (nullable hasta entity resolution)
├── source_entity_id · source_url
├── observed_at · source_updated_at
├── source_name · source_grade · source_length · source_status · source_coordinates
├── normalized_data (JSONB, contrato Pydantic validado)
├── content_hash
└── raw_object_key → snapshot RAW original
```

## Reglas

1. **Inmutable**: jamás se edita ni se borra una observación (NFR-006).
2. **Una observación por cambio relevante**: `hash(name + grade + length + coordinates + status)`
   — si `old_hash == new_hash`, no se inserta nada (idempotencia §28);
   si cambia, se crea la nueva observación (change detection §25).
3. **Procedencia completa** (NFR-003): ¿de dónde vino? ¿cuándo? ¿qué decía?
   ¿cuándo cambió? — respondible con una sola fila + `raw_object_key`.
4. **Crawl fallido ≠ 0 rutas**: un crawl `failed` jamás borra observaciones ni
   rutas existentes (FR-016); se registra el fallo en `crawl_runs` y se conserva
   el estado anterior (§27).

## Ejemplo de reconciliación

| Fuente | Nombre | Grado | Longitud |
|---|---|---|---|
| The Crag | Pleciosaurus | 6c+ | 27 m |
| Mountain Project | Plesiosaurus | 5.11a | 90 ft |
| 8a.nu | Pleciosaurus | 6c+ | — |
| Guía | Pleciosaurus | 6c+ | 27 m |

→ Canonical: `Pleciosaurus · 6c+ · 27.4 m` + conserva **todas** las observaciones
originales + `confidence` + razón (§20, §22).

## RAW asociado

`raw_object_key` apunta al snapshot en object storage (`9-storage.md`):
la DB guarda lo que entendimos; el RAW guarda lo que realmente recibimos.
