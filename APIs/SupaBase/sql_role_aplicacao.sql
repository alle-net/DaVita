-- ============================================================
-- MIGRAÇÃO OPCIONAL — Role dedicada para o app (defesa em
-- profundidade). Hoje o app conecta como superuser "postgres"
-- (RLS ignora). Esta role limita o acesso ao mínimo necessário.
--
-- ATENÇÃO: aplicar SOMENTE quando puder testar o deploy.
-- Depois de rodar este script, troque o valor de
-- SUPABASE_DB_URL em .streamlit/secrets.toml para o
-- "Connection string" da nova role (CONTRIBUIÇÃO: a mesma URL,
-- apenas usuário/senha diferentes) e REINICIE o Streamlit.
--
-- Executar no Supabase Dashboard (SQL Editor), como postgres.
-- ============================================================

DO $$
DECLARE
    _senha TEXT := 'TROQUE_ESTA_SENHA_LONGA_ALEATORIA';
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_justificativas') THEN
        CREATE ROLE app_justificativas LOGIN PASSWORD _senha;
    END IF;
END
$$;

-- Acesso apenas às tabelas do app
GRANT CONNECT ON DATABASE postgres TO app_justificativas;
GRANT USAGE ON SCHEMA public TO app_justificativas;

GRANT SELECT, INSERT, UPDATE, DELETE ON "dUsuarios", "dJustificativas",
    "dAreasResponsaveis", "fDados" TO app_justificativas;

-- Sequences usadas pelos SERIAL (INSERT precisa de USAGE)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_justificativas;

-- Revogar tabelas de sistema/infra não necessárias (defesa extra)
REVOKE ALL ON pg_catalog.pg_index, pg_catalog.pg_sequence FROM app_justificativas;

-- ============================================================
-- Verificação (opcional)
-- SELECT rolname FROM pg_roles WHERE rolname = 'app_justificativas';
-- ============================================================