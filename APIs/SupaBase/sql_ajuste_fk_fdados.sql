-- ============================================================
-- Migração — fDados: FKs de BIGINT para INTEGER
--
-- Motivo: as PKs das dimensões são SERIAL (= INTEGER). O
-- PostgreSQL rejeita FK bigint -> integer (tipos incompatíveis).
-- Este script ajusta as colunas de FK de fDados para INTEGER,
-- tornando as constraints válidas (recriadas automaticamente).
--
-- Executar no Supabase Dashboard (SQL Editor).
-- Seguro para repetir (idempotente).
-- ============================================================

ALTER TABLE "fDados"
    ALTER COLUMN "IdUsuario" TYPE INTEGER USING "IdUsuario"::INTEGER;

ALTER TABLE "fDados"
    ALTER COLUMN "IdJustificativa" TYPE INTEGER USING "IdJustificativa"::INTEGER;

ALTER TABLE "fDados"
    ALTER COLUMN "IdAreaResponsavel" TYPE INTEGER USING "IdAreaResponsavel"::INTEGER;

-- ============================================================
-- Verificação (opcional): deve retornar fDados com os tipos
-- integer nas 3 colunas de FK.
-- ============================================================
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'fDados'
-- ORDER BY ordinal_position;
