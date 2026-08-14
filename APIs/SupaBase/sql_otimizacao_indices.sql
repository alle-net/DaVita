-- ============================================================
-- Migração — otimização de índices de fDados
--
-- 1) idx_fdados_datapendencia é REDUNDANTE: o UNIQUE em
--    "NumeroPendencia" já cria o índice (fDados_NumeroPendencia_key).
-- 2) idx_fdados_usuario (coluna única) é substituído pelo COMPOSTO
--    (IdUsuario, DataHora DESC), que cobre a query principal do app
--    (WHERE IdUsuario = ? ORDER BY DataHora DESC) com index scan
--    ordenado, sem arquivo de ordenação extra.
--
-- Mantidos: idx_fdados_datahora (consultas externas Excel/PowerQuery
-- ordenadas por DataHora), idx_fdados_justificativa e idx_fdados_area.
--
-- Executar no Supabase Dashboard (SQL Editor).
-- Seguro para repetir (idempotente). Não bloqueia escrita (SHARE lock).
-- ============================================================

DROP INDEX IF EXISTS "idx_fdados_datapendencia";

DROP INDEX IF EXISTS "idx_fdados_usuario";

CREATE INDEX IF NOT EXISTS "idx_fdados_usuario_datahora"
    ON "fDados" ("IdUsuario", "DataHora" DESC);

-- ============================================================
-- Migração 14/08/2026 — app agora lista por NumeroPendencia DESC
--
-- A listagem principal (WHERE IdUsuario = ? ORDER BY
-- "NumeroPendencia" DESC LIMIT/OFFSET) passa a ser coberta por este
-- índice composto, sem arquivo de ordenação. O índice por DataHora
-- acima continua válido para consultas externas.
-- ============================================================

CREATE INDEX IF NOT EXISTS "idx_fdados_usuario_pendencia"
    ON "fDados" ("IdUsuario", "NumeroPendencia" DESC);

-- ============================================================
-- Verificação (opcional)
-- ============================================================
-- SELECT indexname FROM pg_indexes WHERE tablename = 'fDados' ORDER BY 1;