# 09 — Storage

Dos almacenes, responsabilidades separadas (spec §35):

## 1. PostgreSQL + PostGIS — "lo que entendimos"

- Datos canónicos, observaciones, histórico, índices espaciales.
- **Nunca** archivos grandes en PG.

## 2. Object Storage — "lo que realmente recibimos"

```
raw/
├── thecrag/2026/08/17/<scope>/<hash-or-id>.html
├── mountain-project/...
├── 8a/...
└── guidebooks/...          # PDFs escaneados
snapshots/                  # exportaciones por fecha
exports/                    # consumos (JSON para la web, reportes)
```

- Cada fila guarda solo la **referencia** `raw_object_key`.
- Indispensable para debugging y auditoría (§5 del export): permite reproducir
  exactamente qué respuesta generó una observación (NFR-002).

## Configuración

| Entorno | Ubicación |
|---|---|
| Desarrollo | `DIRTBAG_RAW_STORAGE_PATH=./data/local/raw` (gitignored) |
| Producción | Object storage (p.ej. Cloudflare R2 / Backblaze B2) |

Volumen estimado: pequeño (México ≈ 10–20k rutas; HTML crudo de unas pocas
decenas de MB por crawl completo). Gratis en cualquier free tier de objetos.

## Export hacia la web

El frontend Next.js **no** consulta la DB directamente: consumirá `exports/`
(JSON canónico generado por `dirtbag validate/export`, decisión pendiente:
SSG en build vs API) — ver `01-architecture.md`.
