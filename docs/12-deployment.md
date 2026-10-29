# 12 — Deployment

## Tabla decisión (export §15)

| Componente | Desarrollo | Producción |
|---|---|---|
| Web | local (`next dev`) | Vercel / Cloudflare |
| DNS | — | Cloudflare |
| Crawler | WSL2 | Docker (worker) |
| Python | WSL2 + uv | Docker image |
| PostgreSQL+PostGIS | Docker Compose | Managed (sin dependencia de proveedor) |
| RAW / media | disco local | Object Storage (R2/B2) |
| Scheduler | CLI / cron | Scheduled job (cron / GitHub Actions) |
| Secrets | `.env` local | env vars del runner/host |

**Regla del spec**: no comprar ni configurar servidor hasta que el pipeline
local funcione de punta a punta (`dirtbag crawl el-salto --source thecrag`).

## Opciones evaluadas (cuando llegue Phase 12)

| Pieza | Opción gratis | Opción de pago |
|---|---|---|
| Web Next.js | Vercel free (default: `dirtbag.vercel.app`) | — |
| Postgres+PostGIS | Supabase free (PostGIS habilitado) | Hetzner VPS auto-hospedado (~€4/mes) |
| Object storage | Cloudflare R2 10 GB / Backblaze B2 | idem |
| Worker/crawl | GitHub Actions cron (2000 min/mes) | misma VPS |
| DNS/CDN | Cloudflare free | — |

Arquitectura híbrida gratis = Vercel + Supabase + GitHub Actions + R2.
Si el crawl crece → una VPS con `docker compose` (DB + worker + API juntos).

## Checklist Phase 12 (spec)

Docker image · deploy worker · deploy PostgreSQL · object storage ·
secrets · scheduler · logging · monitoring · alerts · backup ·
**restore test** (probar que el backup sirve).

## Decisión de infraestructura adoptada (2026-10-25)

Stack **US$0/mes** para el MVP, tres necesidades separadas:

| Necesidad | Elección | Alternativa reservada |
|---|---|---|
| Ejecución (Python/crawlers) | **GitHub Actions** (cron semanal + CI) | OCI Always Free / VPS → Fase 3 |
| Base de datos | **Supabase Free** (PostgreSQL + PostGIS, 500 MB) | Neon (validar PostGIS), VPS |
| Objetos RAW | Fase 1: **GitHub artifacts** (dev) / **Supabase Storage** 1 GB (automatizado); Fase 2: **Cloudflare R2** (10 GB, 0 egress) | idem |
| Web/app | **Supabase PostgREST + SDK** con vistas de solo lectura y RLS | API propia si crece |

**Web ↔ datos — decisión resuelta:** la web y la app consultan Supabase con la
**anon key** + políticas RLS / vistas (`routes_public`, `sectors_public`…);
`source_observations`, histórico y RAW **no** se exponen (spec: la web necesita
lo canónico, no todas las capturas). La **service role key** vive solo en el
crawler/CI — jamás en el cliente. Ver `docs/02-data-model.md`.

### Fases

1. **Fase 1 ($0):** Supabase + GitHub Actions + Docker local. Una zona (El Salto),
   crawls manuales → semanal. CI: ruff + pytest (`.github/workflows/ci.yml`).
2. **Fase 2:** R2 para RAW con volumen, `pg_dump` semanal a R2/artifacts
   (Supabase Free **no** tiene backups automáticos), vistas RLS + integración
   real de la web, health-check diario anti-pausa.
3. **Fase 3:** solo si hace falta → OCI/VPS (crawls > 6 h, Playwright continuo).

### Riesgos a validar en Fase 1 (orden de prueba)

1. **IPv6 ↔ GitHub Actions**: el endpoint de DB de Supabase Free es IPv6-only
   (IPv4 es add-on de US$4) y los runners estándar de Actions son IPv4 →
   **probar con un workflow de conexión de 5 líneas antes de escribir el
   crawler**. Fallbacks: connection pooler de Supabase, add-on IPv4 (+US$4,
   rompe el $0), o ejecutar el crawl en Oracle free.
2. **Pausa por inactividad** (7 días sin API usage): el crawl semanal puede no
   bastar → cron diario de 1 consulta (~1 min/mo) o aceptar unpause manual.
3. **ToS de las fuentes** antes de automatizar (The Crag, MP, 8a.nu) — ver `13-operations.md`.
4. **Minutos de Actions**: repo privado 2.000 min/mes; crawl de El Salto
   estimado 15–30 min + CI ≈ 5 min/run → holgado. Repo público = ilimitado.

### Coste estimado Fase 1

Actions $0 · Supabase Free $0 · R2/Storage $0 · VPS $0 → **US$0/mes**.
