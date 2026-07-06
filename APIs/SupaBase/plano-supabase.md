# Plano de Implementação — API de Justificativas com Supabase + Python

## Sumário

1. [Esclarecimento: O que é Supabase? Onde fica a interface?](#1)
2. [Arquitetura com Supabase](#2)
3. [Comparação: Antes (Azure) vs Depois (Supabase)](#3)
4. [Estrutura do Banco (PostgreSQL)](#4)
5. [Row Level Security (RLS) — Segurança na própria base](#5)
6. [Cronograma Detalhado](#6)
7. [Dúvidas Comuns](#7)

---

<a id="1"></a>
## 1. Esclarecimento: O que é Supabase? Onde fica a interface?

### Supabase NÃO é só um banco de dados

Supabase é uma **plataforma backend completa** que fornece:

| Componente | O que faz | Você precisa implementar? |
|------------|-----------|:---:|
| **PostgreSQL** | Armazena os dados (tabelas) | ❌ Só criar as tabelas |
| **REST API automática** | Expõe cada tabela como endpoint HTTP (`GET /registros`, `POST /registros`, etc.) | ❌ Já vem pronta |
| **Auth** | Cadastro, login, tokens JWT, recovery | ❌ Já vem pronto |
| **Realtime** | Websockets para dados ao vivo | ❌ Opcional |
| **Row Level Security** | Regras de segurança diretamente no banco | ✅ Só configurar (SQL simples) |

**Resumo:** Supabase substitui **Azure Functions + Azure SQL Database** juntos.

### Onde fica a interface (Streamlit)?

| Camada | Onde fica | Exemplo |
|--------|-----------|---------|
| **Banco + API + Auth** | **Supabase Cloud** (nuvem) | `https://xyz.supabase.co` |
| **Interface (Streamlit App)** | **Serviço de hospedagem separado** | Streamlit Cloud, Render, Railway, Azure |

A **interface (Streamlit)** é um aplicativo Python separado que:
- Importa `supabase-py` (SDK)
- Chama a API do Supabase para fazer login, buscar dados, salvar registros
- É deployado separadamente (Streamlit Community Cloud é grátis)

**Fluxo de dados:**
```
[Streamlit App] ──supabase-py──► [Supabase REST API] ──► [PostgreSQL]
[Interface]                       [Backend automático]     [Dados]
```

---

<a id="2"></a>
## 2. Arquitetura com Supabase

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         SUPABASE CLOUD                                   │
│                                                                          │
│  ┌─────────────────────┐    ┌─────────────────────────────────────────┐  │
│  │  PostgreSQL          │    │  Auth Service                          │  │
│  │  - registros         │    │  - Email/senha                         │  │
│  │  - regionais         │◄──►│  - JWT automático                      │  │
│  │  - profiles          │    │  - Gerenciamento de usuários           │  │
│  └─────────────────────┘    └─────────────────────────────────────────┘  │
│          │                                                               │
│          ▼                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Auto-generated REST API                                          │  │
│  │                                                                   │  │
│  │  POST /auth/v1/signup           — Criar conta                     │  │
│  │  POST /auth/v1/token?grant_type=password  — Login (email+senha)   │  │
│  │  GET /rest/v1/registros        — Listar registros                 │  │
│  │  POST /rest/v1/registros       — Criar registro                   │  │
│  │  GET /rest/v1/registros?id=eq.123  — Buscar por ID                │  │
│  │  GET /rest/v1/regionais        — Listar regionais (dropdown)      │  │
│  │  GET /rest/v1/profiles         — Listar perfis (admin)            │  │
│  │  DELETE /rest/v1/profiles?id=eq.XXX  — Remover usuário (admin)    │  │
│  │                                                                   │  │
│  │  TODOS protegidos por RLS (Row Level Security)                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
           │
           │  HTTPS + JWT Token
           │
┌──────────────────────────────────────────────────────────────────────────┐
│  STREAMLIT APP (Interface do Usuário) — "projeto-justificativas"         │
│                                                                          │
│  ├── app.py                → App principal com navegação                 │
│  ├── pages/                                                             │
│  │   ├── login.py           → Tela de login (email + senha)             │
│  │   ├── novo_registro.py   → Formulário: dropdown regional + texto     │
│  │   ├── consultar.py       → Tabela com filtros + exportar CSV         │
│  │   └── admin.py           → Gerenciar usuários (só admin)             │
│  ├── .streamlit/secrets.toml  → URL + chaves do Supabase                │
│  └── requirements.txt      → streamlit, supabase, pandas               │
│                                                                          │
│  Hospedado em: Streamlit Community Cloud (free) / Render / Railway      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

<a id="3"></a>
## 3. Comparação: Antes (Azure) vs Depois (Supabase)

| Item | Plano Original (Azure) | Novo Plano (Supabase) | Impacto |
|------|----------------------|-----------------------|---------|
| **Banco** | Azure SQL (SQL Server) | PostgreSQL | Sintaxe SQL diferente |
| **API** | Azure Functions (7 endpoints escritos à mão) | REST API gerada automaticamente | **~50% menos código** |
| **Auth** | JWT manual + hash de senha | Supabase Auth (pronto) | **Não implementa nada** |
| **Endpoints a codificar** | 7 endpoints | 0 endpoints | Economia de ~3 dias |
| **SDK Python** | `pyodbc` (driver nativo, problemático) | `supabase-py` (puro Python) | Sem dor de cabeça |
| **Libs necessárias** | azure-functions, pyjwt, pyodbc, python-multipart | **só supabase-py** | Mais leve |
| **Complexidade deploy** | 3 serviços (SQL + Functions + App Service) | 1 serviço (Streamlit) + Supabase (SaaS) | **Muito mais simples** |
| **Cold start** | Sim (Consumption Plan 5-10s) | Não (Supabase sempre ativo) | Melhor UX |
| **Limite free DB** | 10 GB SQL Server | 500 MB PostgreSQL | Menor, mas suficiente (~50 registros/dia) |
| **Dashboard admin** | Azure Portal (pesado) | Supabase Dashboard (leve/visual) | Mais produtivo |

---

<a id="4"></a>
## 4. Estrutura do Banco (PostgreSQL)

```sql
-- ============================================================
-- 1. Tabela de regionais (lookup — evita erro de digitação)
-- ============================================================
CREATE TABLE regionais (
    id BIGSERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL
);

-- Inserir regionais padrão (ajuste conforme necessário)
INSERT INTO regionais (nome) VALUES
    ('Norte'),
    ('Nordeste'),
    ('Centro-Oeste'),
    ('Sudeste'),
    ('Sul');

-- ============================================================
-- 2. Tabela de registros (justificativas dos usuários)
-- ============================================================
CREATE TABLE registros (
    id BIGSERIAL PRIMARY KEY,
    justificativa TEXT NOT NULL,
    regional_id BIGINT NOT NULL REFERENCES regionais(id),
    usuario_email TEXT NOT NULL,
    usuario_nome TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice para consultas por data e regional
CREATE INDEX idx_registros_created_at ON registros(created_at);
CREATE INDEX idx_registros_regional ON registros(regional_id);

-- ============================================================
-- 3. Tabela de perfis (vinculada ao auth.users do Supabase)
-- ============================================================
-- O Supabase já cria a tabela auth.users automaticamente.
-- Precisamos de uma tabela profiles com dados extras.

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    papel TEXT NOT NULL DEFAULT 'usuario' CHECK (papel IN ('admin', 'usuario')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger: criar profile automaticamente quando usuário se cadastrar
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, nome, papel)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'nome', NEW.email),
        'usuario'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- 4. Row Level Security (RLS) — regras de acesso
-- ============================================================

-- Habilitar RLS nas tabelas
ALTER TABLE registros ENABLE ROW LEVEL SECURITY;
ALTER TABLE regionais ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Regionais: todos podem ver
CREATE POLICY "Todos podem ver regionais"
    ON regionais FOR SELECT
    USING (true);

-- Registros: todos podem ver todos (consulta geral)
CREATE POLICY "Todos podem ver registros"
    ON registros FOR SELECT
    USING (true);

-- Registros: qualquer usuário autenticado pode criar
CREATE POLICY "Usuários autenticados podem criar registros"
    ON registros FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- Profiles: cada um vê seu próprio perfil; admins veem todos
CREATE POLICY "Usuários veem próprio profile; admins veem todos"
    ON profiles FOR SELECT
    USING (
        auth.uid() = id
        OR EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid() AND papel = 'admin'
        )
    );

-- Profiles: só admin pode modificar
CREATE POLICY "Só admin altera profiles"
    ON profiles FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid() AND papel = 'admin'
        )
    );
```

---

<a id="5"></a>
## 5. Row Level Security (RLS) — Segurança na própria base

Uma das maiores vantagens do Supabase:

- **Regras de segurança no banco**, não no código
- Mesmo que alguém chame a API diretamente (curl, Postman), as regras se aplicam
- O JWT do usuário é verificado automaticamente pelo Supabase

Exemplo prático:
```python
# No código do Streamlit, você só faz:
supabase.table("registros").select("*").execute()
# O Supabase automaticamente:
# 1. Verifica o JWT do usuário
# 2. Aplica as regras RLS
# 3. Retorna só os dados permitidos
```

---

<a id="6"></a>
## 6. Cronograma Detalhado

### Fase 0 — Setup do Ambiente (1 dia)

**Dia 1 — Contas + Ferramentas**

| Passo | Descrição | Tempo |
|-------|-----------|:-----:|
| 1.1 | Criar conta no **Supabase** (github.com/supabase/supabase) | 10 min |
| 1.2 | Criar um **novo projeto** no Supabase (escolher região próxima) | 5 min |
| 1.3 | Anotar `Project URL` e `anon public key` (vamos usar depois) | 2 min |
| 1.4 | Instalar **Python 3.11+** (se não tiver) | 10 min |
| 1.5 | Instalar VS Code + extensão Python | 10 min |
| 1.6 | Criar ambiente virtual: `python -m venv venv` | 2 min |
| 1.7 | Instalar dependências: `pip install streamlit supabase pandas` | 5 min |
| 1.8 | Criar estrutura de pastas do projeto | 5 min |

**Checkpoint D1:** Projeto criado no Supabase, Python pronto, dependências instaladas ✅

---

### Fase 1 — Banco de Dados + Segurança (1 dia)

**Dia 2 — Tabelas + RLS**

| Passo | Descrição | Tempo |
|-------|-----------|:-----:|
| 2.1 | Abrir **SQL Editor** no Supabase Dashboard | 2 min |
| 2.2 | Executar script de criação das tabelas: `regionais`, `registros`, `profiles` | 5 min |
| 2.3 | Executar script do **trigger** (criar profile automático no cadastro) | 3 min |
| 2.4 | Habilitar RLS e criar as **policies** de segurança | 10 min |
| 2.5 | Inserir regionais na tabela (`INSERT INTO regionais ...`) | 2 min |
| 2.6 | Configurar **Authentication > Settings** no dashboard | 5 min |
| 2.7 | Desabilitar "Confirm email" (para teste) | 2 min |
| 2.8 | **Testar:** criar usuário via dashboard e verificar se profile foi criado | 5 min |

**Checkpoint D2:** Banco pronto com 3 tabelas, RLS funcionando ✅

---

### Fase 2 — Interface Streamlit (3 dias)

**Dia 3 — Autenticação + Estrutura**

| Passo | Descrição | Tempo |
|-------|-----------|:-----:|
| 3.1 | Criar `.streamlit/secrets.toml` com credenciais do Supabase | 5 min |
| 3.2 | Criar `app.py` com navegação entre páginas | 30 min |
| 3.3 | Criar `pages/login.py` — formulário de email + senha | 1h |
| 3.4 | Implementar login via `supabase.auth.sign_in_with_password()` | 30 min |
| 3.5 | Implementar logout e exibição do usuário logado | 15 min |
| 3.6 | Proteger páginas (redirecionar para login se não autenticado) | 20 min |
| 3.7 | **Testar:** login, logout, sessão persistente | 15 min |

**Checkpoint D3:** Login funcionando, sessão persistindo ✅

**Dia 4 — Novo Registro + Consulta**

| Passo | Descrição | Tempo |
|-------|-----------|:-----:|
| 4.1 | Criar `pages/novo_registro.py` | 30 min |
| 4.2 | Carregar dropdown de regionais da tabela `regionais` via API | 15 min |
| 4.3 | Implementar formulário (regional + justificativa) | 30 min |
| 4.4 | Implementar `INSERT` via `supabase.table("registros").insert()` | 15 min |
| 4.5 | Validar campos e mostrar mensagens de sucesso/erro | 15 min |
| 4.6 | **Testar:** criar 3 registros com diferentes regionais | 10 min |
| 4.7 | Criar `pages/consultar.py` — buscar registros | 30 min |
| 4.8 | Adicionar filtros: por regional (dropdown) e data (date picker) | 30 min |
| 4.9 | Exibir resultados em tabela (st.dataframe) | 15 min |
| 4.10 | Adicionar botão **Exportar CSV** | 20 min |
| 4.11 | **Testar:** consultar com filtros, exportar CSV | 15 min |

**Checkpoint D4:** Cadastro + consulta funcionando ✅

**Dia 5 — Admin + Ajustes Finais**

| Passo | Descrição | Tempo |
|-------|-----------|:-----:|
| 5.1 | Criar `pages/admin.py` — rota protegida (só admin) | 15 min |
| 5.2 | Listar usuários da tabela `profiles` | 20 min |
| 5.3 | Adicionar funcionalidade: **convidar novo usuário** | 45 min |
| 5.4 | Adicionar funcionalidade: **remover usuário** | 20 min |
| 5.5 | Melhorar tratamento de erros (try/except em todas as chamadas) | 30 min |
| 5.6 | Adicionar loading spinners (st.spinner) nas operações | 15 min |
| 5.7 | Testar **fluxo completo**: login → cadastrar → consultar → admin | 30 min |
| 5.8 | Testar com **múltiplos usuários** (criar 2 contas de teste) | 20 min |
| 5.9 | Revisar código e organizar imports | 15 min |

**Checkpoint D5:** Aplicação completa, todos os fluxos testados ✅

---

### Fase 3 — Deploy (1 dia)

**Dia 6 — Publicar na Internet**

| Passo | Descrição | Tempo |
|-------|-----------|:-----:|
| 6.1 | Criar conta no **Streamlit Community Cloud** (streamlit.io) | 10 min |
| 6.2 | Criar repositório no **GitHub** com o código | 15 min |
| 6.3 | Conectar GitHub ao Streamlit Cloud | 5 min |
| 6.4 | Configurar **Secrets** no Streamlit Cloud (URL + chave Supabase) | 5 min |
| 6.5 | Fazer deploy (clicar em "Deploy") | 5 min |
| 6.6 | **Testar aplicação online** pelo navegador | 15 min |
| 6.7 | Configurar domínio personalizado (opcional) | - |
| 6.8 | **Celebrar!** A aplicação está no ar 24/7 | 🎉 |

**Checkpoint D6:** App online, acessível de qualquer lugar ✅

---

### Fase 4 — Pós-Deploy (contínuo)

| Passo | Descrição | Quando |
|-------|-----------|:------:|
| 7.1 | Testar com usuários reais | Semana 1 |
| 7.2 | Ajustar baseado em feedback | Contínuo |
| 7.3 | Adicionar novas regionais (se necessário) | Conforme demanda |
| 7.4 | Configurar backup automático do banco | Após deploy |
| 7.5 | Adicionar dashboard com gráficos (Plotly) | Versão 2.0 |

---

## 7. Dúvidas Comuns

### O código da interface (Streamlit) fica onde?

O código Streamlit fica no **seu computador** (desenvolvimento) e depois é **enviado para o GitHub** e **deployado no Streamlit Community Cloud**. É um app separado do Supabase.

### Supabase é só o banco? E a API?

Supabase fornece **banco + API + auth** automaticamente. A API REST é gerada pelas tabelas que você cria. Você **não precisa codificar** os endpoints.

### Preciso de servidor para rodar o Streamlit?

O Streamlit Community Cloud hospeda **gratuitamente** apps públicos/privados. O app fica online 24/7.

### E se o limite de 500 MB do Supabase Free for pouco?

Para ~50 registros/dia com texto curto, 500 MB dura **anos**. Cada registro ocupa ~1 KB. 50 registros/dia × 365 dias × 1 KB = ~18 MB/ano.

### E se eu quiser migrar do Supabase depois?

PostgreSQL é padrão aberto. Você pode migrar para qualquer hospedagem PostgreSQL (RDS, DigitalOcean, self-hosted). O código Python muda pouco.

---

**Documento atualizado em:** Julho 2026
**Autor:** Desenvolvimento Python
