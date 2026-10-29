# 07 — Historical Data

El sistema es **temporal**: nada se sobrescribe cuando el cambio proviene de una
fuente observada (spec §24, NFR-006).

## Prohibido

```sql
UPDATE routes SET grade = '6c+';   -- destruye el valor anterior observado
```

## Hacer en su lugar

```
Observation 001 (2024-05) → 6c+
Observation 002 (2025-03) → 6b+     ← hash distinto ⇒ nuevo registro
Canonical (hoy)           → 6b+     ← con razón + confidence
```

- El valor canónico de `routes` es una **proyección del presente**, derivada de
  las observaciones; las observaciones son la verdad histórica.
- Reconstruir el estado de cualquier fecha = filtrar observaciones por
  `observed_at ≤ t`.

## Change detection (§25)

```
content_hash = hash(name + grade + length + coordinates + status)
```

- Igual → sin cambio relevante, no se inserta (idempotencia §28).
- Distinto → nueva observación/version.

## Historiales soportados (Phase 7)

- `crawl_runs` — historial de ejecuciones (qué se corrió, cuándo, resultado).
- `status` — `active → closed → active` trazable vía observaciones (§17).
- Grado, longitud y nombre — vía `source_grade/source_length/source_name` en
  observaciones fechadas.

## Integridad

- Raw y observaciones: **append-only** (a nivel de aplicación; sin `DELETE`/`UPDATE`
  sobre estas tablas en el pipeline).
- Solo la proyección canónica se actualiza, y siempre documentando el porqué.
