# ADR-003 — Source Observations como verdad histórica

- **Estado:** Aceptado
- **Fecha:** 2026-08-18 (spec v0.1) · documentado 2026-10-25

## Contexto

Las fuentes cambian grados, nombres y estados; un crawl fallido puede reportar
"0 rutas"; queremos saber qué dijo cada fuente y cuándo.

## Decisión

- **Una fila por (fuente, entidad, hash)** — `source_observations` con unique
  `(source_id, source_entity_id, content_hash)` ⇒ idempotencia natural (§28).
- `route_id` nullable: la observación existe antes que la identidad canónica.
- El canónico (`routes`) es una **proyección del presente**, actualizable; las
  observaciones son **append-only** (jamás UPDATE/DELETE desde el pipeline).
- Cambio de contenido ⇒ hash distinto ⇒ nueva observación (change detection §25).
- `crawl_runs.status=failed` ⇒ cero escrituras destructivas (FR-016, §27).

## Consecuencias

- ✅ Histórico de grados/estados/nombres gratis, reconstruible en cualquier fecha.
- ✅ Re-crawls repetidos no duplican datos (idempotencia).
- ✅ Falsos deletes imposibles por diseño.
- ⚠️ Tabla que crece con cada cambio — indexada por `observed_at`/`route_id`;
  poda de RAW solo bajo política explícita (nunca de observaciones).
