# Fuente: The Crag (thecrag.com)

Estado: **adaptador implementado (Phase 4)** · `src/dirtbag_data/crawlers/thecrag/`
Crawl en vivo: pendiente de autorización explícita del usuario (slice verificado
con fixtures + `httpx.MockTransport`, sin red).

## Permisos

- `robots.txt`: **sin `Disallow`** (solo reglas `Noindex` de SEO) → crawling permitido.
- Sitemap: `/sitemap-index.xml` → meses `sitemap-YYYY-MM.xml` + `sitemap-older-c01..c03`.
  Los "older" contienen URLs de **áreas**; los meses solo URLs cambiadas en el mes.
- ToS: requieren revisión antes de producción (ver `docs/12-deployment.md`).
- Cortesía: UA `DirtBagBot/0.1 (+https://dirtbag.vercel.app)` y rate ≥ 1.5 s
  (config `http.rate_limit_seconds`), manejado por `crawlers/http.py`.

## Descubrimiento (por qué BFS de áreas)

| Vía | Resultado |
|---|---|
| Páginas de área | rutas **destacadas** + enlaces a sub-áreas (grafo completo) |
| `/routes/at/...`, `with-grade/...` | 302 → `/home` (listado completo requiere login) |
| `/directory` | 403/503 |
| Sitemaps | sin cobertura de rutas de El Salto en meses recientes |

Estrategia adoptada: **BFS por el árbol de áreas** desde un seed
(`configs/*.yaml → crawlers.sources.thecrag.seeds`). Cada página de área aporta
sus filas destacadas y sus hijos; las fichas de ruta se bajan por separado.
Cobertura: lo que el árbol expone sin sesión (parcial pero educado y sin cuenta).

## URLs

- Seed: `https://www.thecrag.com/en/climbing/mexico/el-salto`
- Sub-área: `…/el-salto/area/<nid>` (el enlace de nombre NO lleva `/locate`)
- Ruta: `…/el-salto/route/<id>` → id extraído de la URL

## Selectores (confirmados con fixtures en `tests/fixtures/thecrag/`)

Página de área:

- Fila: `<tr title=" N ascents - path">` + `<td class="g">5.9</td>` +
  `<td class="rt"><span class="route"><a href="…/route/<id>">★… nombre</a>` +
  `<td class="s sport"></td>`.
- El `title` trae entidades **dobles** (`&amp;nbsp;`, `&amp;#8250;`) → desescapar
  dos veces, partir por `›` (U+203A) → `area_path`.
- Hijos: `<div class="area" data-nid="<id>">` → nombre en
  `span.primary-node-name`, conteo en `div.routes`.

Página de ruta:

- Nombre: `span[itemprop=name]` dentro de `h1` (fallback: `<title>`).
- Grado: `span.grade[title="Set using US grade config"]` → hint de sistema
  (US→YDS); el valor se conserva **tal cual** (spec).
- Largo: `<strong>Length:</strong> 28m` → `normalization/lengths.py` (m/ft).
- Coords: `meta place:location:latitude|longitude`.
- Disciplina: `title="Filter to N sport routes"` o `<title>… Sport climb in …`.
- Breadcrumb: `span.crumb__long` (último crumb = la ruta → se descarta).

## Limitaciones conocidas

- Las páginas de área listan solo destacados (ej.: Nebulosidad declara 18 rutas
  y lista 3) → sin login no hay inventario completo.
- Errores por página (404/5xx) **no abortan** el crawl: se cuentan y se sigue
  (`crawl_runs.status = 'partial'` si hubo errores).
- Idempotencia: `ON CONFLICT (source_id, source_entity_id, content_hash) DO
  NOTHING` — re-crawlear sin cambios escribe 0 filas.
