-- Bootstrap de DirtBag Data en Supabase (Fase 1)
-- Ejecutar en el SQL Editor de Supabase ANTES de `alembic upgrade head`.
-- Idempotente: se puede correr más de una vez.

-- 1. PostGIS (requerido: NFR-007, índices GIST, ST_DWithin)
create extension if not exists postgis;

-- 2. Verificaciones que deben devolver filas:
--    select extname from pg_extension where extname = 'postgis';
--    select postgis_version();

-- 3. Tras esto, desde tu máquina local:
--    DIRTBAG_DATABASE_URL='<URL de conexión de Supabase>' \
--    uv run alembic upgrade head
--
--    Notas:
--    * Usar la "Connection string (postgresql)" del panel, NO la URI de la
--      palette de Next.js; incluye el usuario `postgres.<ref>` y el pooler.
--    * El endpoint de DB de Supabase Free es IPv6-only: si tu red/runner no
--      tiene IPv6, fallará aquí — es exactamente lo que valida el workflow
--      `.github/workflows/supabase-connectivity.yml`.
--    * Migraciones: el módulo usa SQL estándar + PostGIS; compatible con
--      Supabase sin cambios (gen_random_uuid, JSONB, ARRAY, GIST).

-- 4. Roles de seguridad (Fase 2, vista pública — se documenta aquí y se
--    implementa en una migración posterior):
--    - anon key  → solo vistas de solo lectura (routes_public, ...) vía RLS
--    - service role key → SOLO el crawler/CI, nunca en el navegador
