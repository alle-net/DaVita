-- ============================================================
-- Script de Criação — Modelo Estrela (Justificativas)
-- Supabase SQL Editor
-- ============================================================

-- 1. Dimensão: Usuários
CREATE TABLE dUsuarios (
    IdUsuario SERIAL PRIMARY KEY,
    Email TEXT NOT NULL UNIQUE,
    Senha TEXT NOT NULL,
    Ativo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. Dimensão: Regionais
CREATE TABLE dRegional (
    IdRegional SERIAL PRIMARY KEY,
    Regional TEXT NOT NULL UNIQUE,
    Ativo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 3. Dimensão: Pendências
CREATE TABLE dPendencias (
    idPendencia SERIAL PRIMARY KEY,
    Pendencia TEXT NOT NULL UNIQUE,
    Ativo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. Dimensão: Responsáveis
CREATE TABLE dResponsavel (
    IdResponsavel SERIAL PRIMARY KEY,
    Responsavel TEXT NOT NULL UNIQUE,
    Ativo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 5. Tabela Fato: Dados
CREATE TABLE fDados (
    Id INT PRIMARY KEY,
    Email INT NOT NULL REFERENCES dUsuarios(IdUsuario),
    Regional INT NOT NULL REFERENCES dRegional(IdRegional),
    Pendencia INT NOT NULL REFERENCES dPendencias(idPendencia),
    Motivo INT NOT NULL,
    Acao INT NOT NULL,
    Responsavel INT NOT NULL REFERENCES dResponsavel(IdResponsavel),
    Ativo BOOLEAN NOT NULL DEFAULT TRUE,
    Data TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para performance nas consultas
CREATE INDEX idx_fdados_data ON fDados(Data);
CREATE INDEX idx_fdados_regional ON fDados(Regional);
CREATE INDEX idx_fdados_email ON fDados(Email);
CREATE INDEX idx_fdados_pendencia ON fDados(Pendencia);
CREATE INDEX idx_fdados_responsavel ON fDados(Responsavel);

-- ============================================================
-- Inserir dados iniciais nas dimensões
-- ============================================================

-- Regionais
INSERT INTO dRegional (Regional) VALUES
    ('Norte'),
    ('Nordeste'),
    ('Centro-Oeste'),
    ('Sudeste'),
    ('Sul')
ON CONFLICT (Regional) DO NOTHING;

-- Pendências
INSERT INTO dPendencias (Pendencia) VALUES
    ('Em aberto'),
    ('Em andamento'),
    ('Concluída'),
    ('Cancelada')
ON CONFLICT (Pendencia) DO NOTHING;

-- Responsáveis
INSERT INTO dResponsavel (Responsavel) VALUES
    ('Não atribuído')
ON CONFLICT (Responsavel) DO NOTHING;

-- ============================================================
-- Configuração de segurança (RLS)
-- ============================================================
ALTER TABLE fDados ENABLE ROW LEVEL SECURITY;
ALTER TABLE dUsuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE dRegional ENABLE ROW LEVEL SECURITY;
ALTER TABLE dPendencias ENABLE ROW LEVEL SECURITY;
ALTER TABLE dResponsavel ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Autenticados podem ler fDados"
    ON fDados FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Autenticados podem inserir fDados"
    ON fDados FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem ler dUsuarios"
    ON dUsuarios FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem ler dRegional"
    ON dRegional FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem ler dPendencias"
    ON dPendencias FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Autenticados podem ler dResponsavel"
    ON dResponsavel FOR SELECT USING (auth.role() = 'authenticated');
