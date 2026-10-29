# 01 — Architecture

## Principios (spec §39)

1. **Cada fuente es un adapter** — el core no conoce la estructura interna de ninguna fuente.
2. **No destruir datos** — RAW y observaciones son inmutables.
3. **Separar etapas** — `fetch → parse → normalize → match → reconcile → persist` nunca se mezclan.
4. **Sin LLM para operaciones deterministas** — RapidFuzz + PostGIS primero; LLM solo para casos ambiguos y en fase posterior.
5. **Sin infraestructura prematura** — sin RabbitMQ, microservicios, Kubernetes ni arquitectura distribuida en el MVP.

## Componentes

```
┌─────────────────────────────────────────────────────┐
│ CLI `dirtbag` (crawl/status/validate/reconcile)     │
└───────────────┬─────────────────────────────────────┘
                ▼
┌───────────────────────────┐   ┌──────────────────────┐
│ Pipeline                  │   │ Scheduler            │
│ fetch→parse→normalize→…   │   │ manual → cron        │
└───────┬───────────────────┘   └──────────────────────┘
        ▼
┌────────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ crawlers/      │   │ normalization/  │   │ matching/        │
│ adapters       │   │ grades,lengths  │   │ RapidFuzz+PostGIS│
└───────┬────────┘   └────────┬────────┘   └────────┬─────────┘
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│ storage: RAW (object storage, inmutable)                    │
│ PostgreSQL+PostGIS: observations + canonical + histórico     │
└─────────────────────────────────────────────────────────────┘
```

## Topología de producción (decisión del spec, export §9–15)

- **Cloudflare**: DNS + CDN + Pages/Workers (entrada).
- **Web Next.js**: separada — si falla el scraper, el sitio sigue vivo; y viceversa.
- **DirtBag API** (futura, §43): `GET /routes`, `/routes/nearby`, `/search`…
- **PostgreSQL + PostGIS** managed (Neon/Supabase/Railway/Render/RDS/VPS — sin dependencia de proveedor).
- **Object storage**: RAW/snapshots/PDFs/media.
- **Pipeline**: worker Python en Docker con jobs programados.

## Fallos aislados (NFR-001)

Un error de una fuente no detiene el pipeline; cada fuente se ejecuta y registra por separado (`crawl_runs`).
