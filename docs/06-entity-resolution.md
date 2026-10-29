# 06 — Entity Resolution

Determinar cuándo dos registros describen **la misma ruta** (spec §21).
Implementación prevista en `src/dirtbag_data/matching/`.

## Señales (en orden, todas combinables)

1. **Nombre normalizado** — case, espacios, acentos, puntuación (`Pleciosaurus` ≡ `plesiosaurus`).
2. **Ubicación** — sector, zona, coordenadas.
3. **Distancia geográfica** — PostGIS (`ST_DWithin`): misma ruta ⇒ dentro de umbral (p.ej. 50–200 m según densidad).
4. **Longitud** — tolerancia (p.ej. ±10% o ±3 m); `90 ft` ya normalizado a `27.4 m` antes de comparar.
5. **Grado** — comparar en sistema común vía tablas (`05-grade-system.md`) con tolerancia ±1 gradación.
6. **Disciplina** — boulder nunca matchea con deporte.
7. **Otros atributos** — first ascent, año, nombre del sector…

## Fuzzy matching

- **RapidFuzz** para nombres similares (`Pleciosaurus` ↔ `Plesiosaurus`, score alto).
- Candidatos se generan por proximidad geográfica primero (barato) y luego se
  puntúan con todas las señales.
- Score → `confidence` (§23): sin jerarquía rígida de fuentes; manda la evidencia
  (nº de fuentes que coinciden, consistencia, recencia, evidencia geográfica).

## LLM

**Prohibido** para el matching básico (regla §39). Solo, en fase posterior y de
forma opt-in, para la **cola de revisión manual** de casos ambiguos — nunca para
operaciones deterministas ni para decidir en soledad.

## Salida

- Match aceptado → `source_observations.route_id` + candidato canónico consolidado.
- Ambiguo → **manual review queue** (Phase 6): fila pendiente con evidencia
  para decidir un humano; jamás auto-fusionar con score bajo.

## Reconciliación (Phase 10)

Observaciones matcheadas → valores canónicos: se elige `canonical value`
conservando **todos** los valores fuente + razón + confidence (§22).
