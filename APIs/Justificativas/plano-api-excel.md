# Plano de Execução — API Corporativa com Python + Azure

## 1. Visão Geral

### O que vamos construir

Um sistema **100% online** composto por **API REST + Interface Web** onde usuários autorizados acessam pelo navegador para cadastrar e consultar justificativas por regional. Tudo hospedado na nuvem Azure — **sem planilha Excel, sem script local, sem rede da empresa**.

### Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                     MICROSOFT AZURE (nuvem)                      │
│                                                                  │
│  ┌─────────────────────┐       ┌──────────────────────────────┐ │
│  │  Azure Functions     │       │  Streamlit (App Service)     │ │
│  │  (API REST)          │◄────►│  (Interface do usuário)      │ │
│  │                      │       │                              │ │
│  │  Endpoints:          │       │  - Login                     │ │
│  │  POST /auth          │       │  - Novo registro (formulário)│ │
│  │  GET /registros      │       │  - Consulta com filtros      │ │
│  │  POST /registros     │       │  - Exportar CSV              │ │
│  │  GET /registros/{id} │       │  - Admin (gerenciar usuários)│ │
│  │  POST /usuarios      │       │                              │ │
│  │  GET /usuarios       │       │                              │ │
│  │  DELETE /usuarios/{id}│      │                              │ │
│  └─────────┬────────────┘       └──────────────────────────────┘ │
│            │                                                     │
│  ┌─────────▼────────────┐                                       │
│  │  Azure SQL Database   │                                       │
│  │  Free Tier (10 GB)    │  ← dados persistidos                 │
│  │  SQL completo         │                                       │
│  │  R$ 0 permanente      │                                       │
│  └──────────────────────┘                                       │
└──────────────────────────────────────────────────────────────────┘
           │
           │
    Usuários acessam pelo navegador
    (escritório, casa, celular — qualquer lugar)
```

---

## 2. Componentes do Sistema

### 2.1 API (Azure Functions)

| Aspecto | Descrição |
|---|---|
| **Linguagem** | Python 3.11 |
| **Hospedagem** | Azure Functions (Consumption Plan — grátis) |
| **URL** | `https://sua-api.azurewebsites.net` |
| **Disponibilidade** | 24 horas por dia, 7 dias por semana |

Endpoints:

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth` | Login: email + senha → retorna token JWT |
| `GET` | `/registros` | Listar registros (com filtros: regional, data) |
| `POST` | `/registros` | Criar novo registro |
| `GET` | `/registros/{id}` | Buscar um registro específico |
| `POST` | `/usuarios` | Adicionar novo usuário (admin) |
| `GET` | `/usuarios` | Listar usuários (admin) |
| `DELETE` | `/usuarios/{id}` | Remover usuário (admin) |

### 2.2 Interface (Streamlit)

| Aspecto | Descrição |
|---|---|
| **Linguagem** | Python (Streamlit) |
| **Hospedagem** | Azure App Service (plano F1 grátis) |
| **URL** | `https://sua-interface.azurewebsites.net` |
| **Funcionalidades** | Login, formulário de registro, consulta com filtros, exportar CSV, admin |

Telas planejadas:

1. **Login** — usuário digita email + senha (validado contra a API)
2. **Novo Registro** — formulário: selecionar regional (dropdown) + digitar justificativa
3. **Consultar** — tabela com filtros por regional e data, exportar CSV
4. **Admin** — gerenciar usuários autorizados (só para você)

### 2.3 Banco de Dados (Azure SQL Database — Free Tier)

| Aspecto | Descrição |
|---|---|
| **Tipo** | Relacional (SQL Server) |
| **Plano** | Free Tier — **permanente** (não expira) |
| **Armazenamento** | Até 10 GB |
| **Limite** | 100.000 vCore segundos/mês |
| **SQL** | Completo (SELECT, JOIN, GROUP BY, SUM) |
| **Custo** | **R$ 0** |

### 2.4 Autenticação (JWT + Tabela de Usuários)

- Você mantém uma tabela `usuarios` no Azure SQL
- Cada usuário tem: nome, email, senha (hash), papel (admin ou usuario)
- Login retorna token JWT válido por 24h
- **Só você** pode adicionar/remover usuários

---

## 3. Estrutura do Banco de Dados

```sql
-- Tabela de registros (justificativas)
CREATE TABLE registros (
    id INT IDENTITY(1,1) PRIMARY KEY,
    justificativa NVARCHAR(500) NOT NULL,
    regional NVARCHAR(100) NOT NULL,
    usuario_email NVARCHAR(200) NOT NULL,
    usuario_nome NVARCHAR(200) NOT NULL,
    data_hora DATETIME2 DEFAULT GETDATE()
);

-- Tabela de usuários (controlada por você)
CREATE TABLE usuarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nome NVARCHAR(100) NOT NULL,
    email NVARCHAR(200) NOT NULL UNIQUE,
    senha_hash NVARCHAR(500) NOT NULL,
    papel NVARCHAR(50) DEFAULT 'usuario'  -- 'admin' ou 'usuario'
);
```

---

## 4. Fluxo de Funcionamento

### 4.1 Usuário cadastra um registro

```
[Usuário]                    [Streamlit]                  [Azure Functions]
  Navegador                   Interface                    API
     │                           │                            │
     │── Login ────────────────►│                            │
     │                          │── POST /auth ────────────►│
     │                          │◀── token JWT ─────────────│
     │                          │                            │
     │── Abre "Novo Registro" ─►│                            │
     │                          │                            │
     │── Seleciona regional ───►│                            │
     │── Digita justificativa ─►│                            │
     │                          │── POST /registros ───────►│
     │                          │   (com token + dados)      │── Insere no
     │                          │                            │   Azure SQL
     │                          │◀── 201 Created ───────────│
     │◀── "Salvo com sucesso" ──│                            │
```

### 4.2 Usuário consulta registros

```
[Usuário]                    [Streamlit]                  [Azure Functions]
     │                           │                            │
     │── Abre "Consultar" ─────►│                            │
     │                          │── GET /registros ─────────►│
     │                          │   ?regional=Sul            │── SELECT no
     │                          │   &data_inicio=2026-07-01  │   Azure SQL
     │                          │◀── JSON com registros ─────│
     │◀── Tabela com dados ─────│                            │
     │    e botão "Exportar CSV"│                            │
```

---

## 5. Custos

| Item | Incluso no grátis | Custo mensal |
|---|---|---|
| Azure Functions (Consumption Plan) | 1 milhão execuções/mês | **R$ 0** |
| Azure SQL Database (Free Tier) | 10 GB, 100K vCore seg/mês **(permanente)** | **R$ 0** |
| Azure App Service (Streamlit) — F1 | 60 min CPU/dia | **R$ 0** |
| Domínio (`*.azurewebsites.net`) | Incluso | **R$ 0** |
| Certificado SSL/HTTPS | Incluso | **R$ 0** |
| Python (bibliotecas) | Open source | **R$ 0** |
| **Total** | | **R$ 0** |

### Estimativa de uso mensal

| Métrica | Cálculo | Consumo estimado |
|---|---|---|
| Registros/dia | 50 linhas | ~1.100 registros/mês |
| Consultas/dia | 30 usuários × 5 consultas | ~3.300 consultas/mês |
| Execuções API | registros + consultas + auth | ~5.000/mês |
| Limite Azure Functions | 1 milhão/mês | **0,5% do limite** |
| Limite SQL (vCore seg) | 100.000/mês | Muito abaixo |

> **Conclusão:** o projeto funciona **indefinidamente com custo zero** no Azure Free Tier. Mesmo crescendo 10x, ainda estará dentro dos limites gratuitos.

---

## 6. Cronograma de Desenvolvimento

### Fase 1 — Setup + API (3 dias)

- [ ] Criar conta gratuita na Azure (cartão para verificação, não cobra)
- [ ] Provisionar Azure SQL Database (Free Tier)
- [ ] Criar tabelas `registros` e `usuarios`
- [ ] Criar Azure Function App (Consumption Plan)
- [ ] Implementar endpoint `POST /auth` (login + JWT)
- [ ] Implementar CRUD de registros (`GET`, `POST`, `GET /{id}`)
- [ ] Implementar CRUD de usuários (só admin)
- [ ] Testar com `curl` ou Postman

### Fase 2 — Interface Streamlit (4 dias)

- [ ] Criar tela de login (email + senha → token JWT)
- [ ] Criar formulário "Novo Registro" (dropdown regional + justificativa)
- [ ] Criar tela "Consultar" (tabela com filtros regional/data)
- [ ] Adicionar exportação para CSV
- [ ] Criar tela "Admin" (listar, adicionar, remover usuários)
- [ ] Fazer deploy no Azure App Service (plano F1 grátis)
- [ ] Testar fluxo completo (login → cadastrar → consultar)

### Fase 3 — Refinamentos (2 dias)

- [ ] Testar com usuários reais
- [ ] Ajustar baseado em feedback
- [ ] Melhorar tratamento de erros e mensagens
- [ ] Documentar instruções de uso

---

## 7. Tecnologias e Bibliotecas

### API (Azure Functions)

```
azure-functions
pyjwt
python-multipart
pyodbc
```

### Interface (Streamlit)

```
streamlit
requests
pandas
plotly
```

---

## 8. Estrutura de Pastas do Projeto

```
projeto-api-justificativas/
│
├── api/                          # Azure Functions
│   ├── function_app.py           # Endpoints da API
│   ├── db.py                     # Conexão com Azure SQL
│   ├── auth.py                   # JWT (gerar/validar token)
│   ├── host.json                 # Config Azure Functions
│   ├── local.settings.json       # Config local (desenvolvimento)
│   └── requirements.txt          # Dependências
│
├── interface/                    # Streamlit
│   ├── app.py                    # App principal (login + navegação)
│   ├── pages/
│   │   ├── novo_registro.py      # Formulário de cadastro
│   │   ├── consultar.py          # Tabela com filtros
│   │   └── admin.py              # Gerenciar usuários
│   ├── config.toml               # URL da API
│   └── requirements.txt          # Dependências
│
└── docs/
    └── instrucoes.md             # Manual do usuário
```

---

## 9. Próximos Passos

1. ✅ Revisar este documento
2. ✅ Decisões definidas:
   - Estrutura: id + regional (lista) + justificativa + usuário + data/hora
   - Volume: ~50 registros/dia
   - Usuários: até 30
   - Atualização: direto pela interface (não tem planilha)
   - Autenticação: senha fixa definida por você
   - Banco: Azure SQL Database Free Tier
   - 100% online, sem Excel, sem script local
3. 📅 Agendar início da implementação
4. ▶️ Criar conta Azure
5. 💻 Implementar Fase 1

---

## 10. Glossário

| Termo | Significado |
|---|---|
| **API** | Interface de programação — conjunto de endpoints que permitem comunicação entre sistemas |
| **REST** | Estilo arquitetural de APIs que usa HTTP (GET, POST, etc.) |
| **Endpoint** | URL específica da API (ex: `/auth`, `/registros`) |
| **JSON** | Formato de dados leve e legível, usado para trocar informações |
| **JWT** | Token de autenticação — um "crachá digital" que o usuário recebe ao logar |
| **Azure Functions** | Serviço serverless da Microsoft — executa código sem gerenciar servidor |
| **Consumption Plan** | Plano onde você paga só pelo que usar (no grátis: R$ 0) |
| **Streamlit** | Biblioteca Python para criar interfaces web sem HTML/JS |
| **Azure SQL Free Tier** | Banco relacional gratuito permanente (10 GB, SQL completo) |
| **Serverless** | Modelo onde a nuvem gerencia o servidor — você só sobe o código |

---

**Documento atualizado em:** Julho 2026
**Autor:** Consultoria Técnica — Python + Azure
