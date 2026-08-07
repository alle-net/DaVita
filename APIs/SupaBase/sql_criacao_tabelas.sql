-- ============================================================
-- Script de Criação — Justificativas de Pendências (Supabase)
-- Modelo: 1 fato (fDados) + 3 dimensões (dUsuarios,
--         dJustificativas, dAreasResponsaveis)
-- Escopo aprovado em 05/08/2026 — CRUD por usuário
--
-- IMPORTANTE: identificadores entre aspas duplas preservam o
-- nome exato (fDados, dUsuarios...). O app Python e o Power
-- Query devem usar exatamente estes nomes.
-- ============================================================

-- ============================================================
-- 1. Dimensão: Usuários
-- SenhaUsuario em TEXTO PURO (decisão da gestão: sistema
-- interno, sem dados sensíveis, controle simples de acesso).
-- ============================================================
CREATE TABLE "dUsuarios" (
    "IdUsuario" SERIAL PRIMARY KEY,
    "EmailUsuario" TEXT NOT NULL UNIQUE,
    "SenhaUsuario" TEXT NOT NULL,
    "Ativo" BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- 2. Dimensão: Justificativas (18 valores fixos)
-- ============================================================
CREATE TABLE "dJustificativas" (
    "IdJustificativa" SERIAL PRIMARY KEY,
    "DescJustificativa" TEXT NOT NULL UNIQUE
);

INSERT INTO "dJustificativas" ("DescJustificativa") VALUES
    ('AGUARDANDO AUDITORIA/SINTESE'),
    ('COBRANCA INDEVIDA'),
    ('CRITICA NO XML'),
    ('ENTREGA NO MES'),
    ('ENTREGA NO PROXIMO MES'),
    ('FALTA DE GUIA/AUTORIZACAO'),
    ('PERDA DE PRAZO'),
    ('PROBLEMA NO CADASTRO'),
    ('PROBLEMA NO PORTAL DA OPERADORA'),
    ('TRATATIVA COMERCIAL'),
    ('TRATATIVA JURIDICA'),
    ('TRATATIVA OPERACIONAL'),
    ('DUPLICIDADE'),
    ('GLOSA PREVIA'),
    ('FALTA GERAR TITULO'),
    ('CONTA FATURADA'),
    ('CONTA NAO FATURADA'),
    ('NAO AUTORIZADO PELA OPERADORA')
ON CONFLICT ("DescJustificativa") DO NOTHING;

-- ============================================================
-- 3. Dimensão: Áreas Responsáveis (6 valores fixos)
-- ============================================================
CREATE TABLE "dAreasResponsaveis" (
    "IdAreaResponsavel" SERIAL PRIMARY KEY,
    "NomeAreaResponsavel" TEXT NOT NULL UNIQUE
);

INSERT INTO "dAreasResponsaveis" ("NomeAreaResponsavel") VALUES
    ('COMERCIAL'),
    ('OPERACAO'),
    ('FATURAMENTO'),
    ('COMITE JURIDICO'),
    ('CENTRAL DE AUTORIZACAO'),
    ('CADASTRO')
ON CONFLICT ("NomeAreaResponsavel") DO NOTHING;

-- ============================================================
-- 4. Tabela Fato: fDados (justificativas registradas)
-- ============================================================
CREATE TABLE "fDados" (
    "Id" BIGSERIAL PRIMARY KEY,
    "NumeroPendencia" INTEGER NOT NULL UNIQUE,
    "IdUsuario" BIGINT NOT NULL REFERENCES "dUsuarios"("IdUsuario"),
    "IdJustificativa" BIGINT NOT NULL REFERENCES "dJustificativas"("IdJustificativa"),
    "IdAreaResponsavel" BIGINT NOT NULL REFERENCES "dAreasResponsaveis"("IdAreaResponsavel"),
    "DataHora" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para performance nas consultas (Excel/Power Query)
CREATE INDEX idx_fdados_datapendencia ON "fDados"("NumeroPendencia");
CREATE INDEX idx_fdados_datahora ON "fDados"("DataHora");
CREATE INDEX idx_fdados_usuario ON "fDados"("IdUsuario");
CREATE INDEX idx_fdados_justificativa ON "fDados"("IdJustificativa");
CREATE INDEX idx_fdados_area ON "fDados"("IdAreaResponsavel");

-- ============================================================
-- 5. Row Level Security (RLS) — defesa em profundidade
--
-- Nota: o app Streamlit conecta DIRETO ao PostgreSQL (usuário
-- postgres, porta 5432), que ignora o RLS. O isolamento
-- "cada usuário vê só o que gravou" é aplicado no CÓDIGO
-- Python (utils/db.py filtra por IdUsuario).
-- As policies abaixo são defesa extra caso o cliente adote
-- Supabase Auth (JWT) no futuro; elas não limitam o postgres.
-- ============================================================
ALTER TABLE "dUsuarios" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "dJustificativas" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "dAreasResponsaveis" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fDados" ENABLE ROW LEVEL SECURITY;

-- Justificativas e áreas: leitura para autenticados (dropdowns)
CREATE POLICY "Autenticados podem ler dJustificativas"
    ON "dJustificativas" FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem ler dAreasResponsaveis"
    ON "dAreasResponsaveis" FOR SELECT USING (auth.role() = 'authenticated');

-- fDados: leitura/inserção/edição/exclusão para autenticados.
-- O controle por usuário é feito no app (filtro IdUsuario).
CREATE POLICY "Autenticados podem ler fDados"
    ON "fDados" FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem inserir fDados"
    ON "fDados" FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem atualizar fDados"
    ON "fDados" FOR UPDATE USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem excluir fDados"
    ON "fDados" FOR DELETE USING (auth.role() = 'authenticated');

-- dUsuarios: RLS habilitado e SEM policies -> anon/authenticated
-- NÃO têm acesso algum. Usuários só podem ser criados/alterados/
-- desativados pelo PAINEL do Supabase (Table Editor / postgres).
