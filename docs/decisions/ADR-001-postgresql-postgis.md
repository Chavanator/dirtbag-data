# ADR-001 — PostgreSQL + PostGIS

- **Estado:** Aceptado
- **Fecha:** 2026-08-18 (spec v0.1) · documentado 2026-10-25

## Contexto

DirtBag necesita: consultas geoespaciales (`ST_DWithin`, "rutas a 10 km",
"rutas dentro de zona"), modelo relacional jerárquico, histórico temporal y
crecimiento de México → Latinoamérica → global sin rediseño (NFR-004).

## Decisión

Usar **PostgreSQL + PostGIS** como única base:

- Geografía nativa con índices GIST (NFR-007).
- SQL estándar + PostGIS ⇒ migrar de proveedor (Neon → AWS, etc.) sin rediseñar.
- JSONB para `normalized_data` (contratos Pydantic) sin colapsar en columnas.
- La geometría se manipula con SQL crudo + Shapely (sin geoalchemy2, según el
  stack del spec §38).

## Consecuencias

- ✅ Una sola DB para canónico + histórico + espacial.
- ✅ Proveedor intercambiable; docker-compose local idéntico a prod.
- ⚠️ Requiere PostGIS en cualquier entorno (incluida la DB managed elegida:
  verificar que lo ofrece antes de contratar).
- ⚠️ Sin Redis/caché por ahora — se añade solo si hay evidencia de necesidad.
