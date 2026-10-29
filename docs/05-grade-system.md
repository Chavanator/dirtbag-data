# 05 — Grade System

Implementación: `src/dirtbag_data/normalization/grades.py` (+ `tests/unit/test_grades.py`).

## Sistemas soportados (FR-011)

| Sistema | Ejemplos | Detección |
|---|---|---|
| French (sport) | `3a … 9c+` | `^[3-9][abc]\+?$` |
| YDS | `5.0 … 5.14d` | `^5\.\d{1,2}[a-d]?$` |
| Fontainebleau | `1 … 5+`, `6a … 9c+` | numérico `1–5(+)` o letra en `6–9` |
| V-scale | `VB, V0 … V16` | `^V\d{1,2}$` |
| UIAA | `I … XVI` con `+/-` | romanos válidos |

Ambigüedad French↔Font (`7a+` existe en ambas): se resuelve con `discipline`
("bouldering" → Font, "sport" → French). Sin contexto, se asume French (el
formato con letra es el más común en nuestras fuentes).

## GradeRecord

```python
GradeRecord(value="6C+", system=FRENCH, normalized="6c+")
```

- `value`: **exactamente** lo que dijo la fuente (spec: mantener valor original).
- `normalized`: limpieza dentro del mismo sistema (case, espacios) — nunca una
  conversión silenciosa.

## Conversiones (aproximadas, tabuladas)

- YDS ↔ French (tabla estándar `5.10d ↔ 7a+`, hasta `5.14d`).
- V ↔ Font (tabla aproximada `V6 ↔ 7a`).
- Sin entrada en tabla → `convert()` devuelve `None` (**no adivinar**).
- Conversión entre familias (YDS↔Font, UIAA↔X) → `None` por ahora.

## Reglas

1. Datos inválidos → `UnknownGradeError` **antes** de entrar al modelo canónico (spec §33).
2. La conversión es solo para comparación/matching; el canónico conserva
   `value`+`system` de la fuente predominante por evidencia (§23).
3. UIAA: detección sí, conversión pendiente (tabla a definir con fuentes revisadas).
