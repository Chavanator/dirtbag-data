# ADR-002 — RAW → Normalized → Canonical (tres capas inmutables)

- **Estado:** Aceptado
- **Fecha:** 2026-08-18 (spec v0.1) · documentado 2026-10-25

## Contexto

Scraping multi-fuente con errores, cambios y conflictos: si el crawler escribe
directo sobre `routes`, se pierde la procedencia, el histórico y la capacidad
de auditar o reproducir (NFR-003, NFR-006).

## Decisión

Tres capas estrictas:

1. **RAW** (object storage): la respuesta exacta de la fuente. Inmutable,
   `raw_object_key` referenciado desde la observación.
2. **NORMALIZED** (Pydantic, en `source_observations.normalized_data`): contrato
   validado — longitudes en metros, grados con `value/system/normalized`,
   nombres limpios, coordenadas EPSG:4326.
3. **CANONICAL** (`routes` + `pitches`): identidad única derivada por
   reconciliación, con confidence y razón.

La DB representa lo que entendimos; el RAW representa lo que recibimos.

## Consecuencias

- ✅ Debugging: reproducir cualquier observación desde su snapshot.
- ✅ Reprocesar todo el pipeline con parsers corregidos sin volver a crawlear.
- ✅ Auditoría completa ("¿de dónde vino este dato?").
- ⚠️ Costo de almacenamiento del HTML crudo — aceptable (MBs por crawl,
  gratis en free tiers).
- ⚠️ Disciplina de append-only que el pipeline debe respetar por código.
