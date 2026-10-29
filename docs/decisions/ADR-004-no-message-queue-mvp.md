# ADR-004 — Sin message queue en el MVP

- **Estado:** Aceptado (revisar en Phase 11/12)
- **Fecha:** 2026-08-18 (spec v0.1) · documentado 2026-10-25

## Contexto

El MVP es un pipeline de crawls programados por fuente/alcance. RabbitMQ,
Kafka, Celery o microservicios añaden operación, vigilancia y fallos sin
beneficio mientras el volumen sea "México, unos miles de rutas, crawl semanal".

## Decisión

- Orquestación con **CLI + cron** (local: shell; prod: GitHub Actions cron o
  cron de la VPS). Un proceso asyncio por crawl (HTTPX async + asyncio).
- **No** RabbitMQ, **no** Kubernetes, **no** microservicios, **no** arquitectura
  distribuida en el MVP (spec §39).
- Fallos aislados por fuente via `crawl_runs`, no por broker.

## Consecuencias

- ✅ `docker compose up` + un cron = sistema completo operable por una persona.
- ✅ Menos piezas móviles = menos modos de falla (NFR-001/005).
- ⚠️ Re-evaluar si aparece: >1 fuente con crawl diario pesado, colas de
  trabajo > tiempo de ejecución, o múltiples workers. La migración sería
  añadir un queue **detrás** de la misma CLI/pipeline sin tocar el dominio.
