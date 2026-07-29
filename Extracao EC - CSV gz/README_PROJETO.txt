====================================================================================
DOCUMENTACAO DO PROJETO - Extracao EC (CSV.gz)
====================================================================================
Data: 29/07/2026
Descricao: Script de extracao de dados do MySQL para CSV compactado (GZip),
           com agendamento semanal no Windows Task Scheduler.

====================================================================================
1. ESTRUTURA DO DIRETORIO
====================================================================================

Extracao EC - CSV gz/
├── Config.json                  # Configuracao do banco MySQL e pasta de saida
├── extracao.py                  # Script principal (Python)
├── gerenciar_tarefa.bat         # Menu para gerenciar tarefa agendada no Windows
├── Progresso.txt                # Instrucoes basicas
├── requirements.txt             # Dependencias Python
├── Querys/
│   ├── EC.sql                   # Query completa (36 colunas, todos estabelecimentos)
│   ├── ECC.sql                  # Query simplificada (SELECT *)
│   └── EC_RJ.sql                # Query filtrada para 8 unidades do RJ
└── venv/                        # Ambiente virtual Python

====================================================================================
2. ARQUIVOS E CONTEUDO ATUAL
====================================================================================

2.1 extracao.py (101 linhas)
───────────────────────────────────────────────────────────────────────────────────
- Conexao MySQL via SQLAlchemy + PyMySQL
- Carrega query do diretorio Querys/
- 3 tentativas de conexao com intervalo de 2s
- Adiciona coluna "gravacao" com timestamp da extracao
- Salva como CSV.gz com delimitador ";" (ponto e virgula)
- Nome do arquivo: EC-YYYYMMDD-HHMM.csv.gz
- Type hints, logging estruturado, context manager para conexao
- Se liga: Config{"senha"} pode retornar "" se a chave nao existir (config.get)

2.2 Config.json (Senha em texto puro - PENDENTE DE CORRECAO)
───────────────────────────────────────────────────────────────────────────────────
{
  "servidor": "149.28.212.92",
  "banco": "nefrolco_davita_panel",
  "usuario": "nefrolcoud_ciclodereceita",
  "senha": "#pwzx1rfS%cnF@MC",
  "query": "ECC.sql",
  "pasta_saida": "C:/Users/alexandresilva3/DaVita/..."
}

OBS: A senha esta em texto puro. Sugestao pendente: usar variavel de ambiente
     (DB_PASSWORD) ou .env para remover a senha do JSON.

2.3 requirements.txt
───────────────────────────────────────────────────────────────────────────────────
pandas>=3.0.5
PyMySQL>=1.2.0
SQLAlchemy>=2.0.51

2.4 Querys/ECC.sql (Query em uso atualmente)
───────────────────────────────────────────────────────────────────────────────────
SELECT * FROM status_conta
WHERE dt_periodo_final >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
  AND dt_periodo_final <= CURDATE()
  AND ds_etapa <> 'Contas Canceladas'
  AND cd_estabelecimento NOT IN (264,265)

2.5 gerenciar_tarefa.bat
───────────────────────────────────────────────────────────────────────────────────
Menu interativo para gerenciar tarefa agendada "ExtracaoEC" no Windows:
  [1] Criar tarefa - pergunta dia da semana e horario
  [2] Alterar dia e horario
  [3] Deletar tarefa
  [0] Sair

====================================================================================
3. TAREFA AGENDADA (Windows Task Scheduler)
====================================================================================

Nome: ExtracaoEC
Executar: py -3 "C:\Alexandre\Repositorios\DaVita\Extracao EC - CSV gz\extracao.py"
Agendamento: Semanal - Quarta-feira as 12:30
Estado: Ready (Pronto)
Descricao: Extracao EC (CSV.gz)

Para ver no PowerShell:
  Get-ScheduledTask -TaskName "ExtracaoEC" | Format-List *

Para abrir o Agendador de Tarefas:
  Win + R > taskschd.msc > Biblioteca > ExtracaoEC

====================================================================================
4. MELHORIAS APLICADAS EM 29/07/2026
====================================================================================

[✓] extracao.py:
    - Adicionados type hints em todas as funcoes
    - Substituido print() por logging estruturado
    - Adicionada validacao de chaves obrigatorias no Config.json
    - Conexao com banco usa @contextmanager (dispose automatico)
    - Delimitador CSV alterado para ";" (ponto e virgula)

[✓] gerenciar_tarefa.bat:
    - Corrigido caminho do script (apontava para Extracao EC/ versao Parquet)
    - Codificacao ajustada para ANSI com CRLF (Windows)

[✓] Progresso.txt:
    - Atualizado para refletir formato CSV.gz (estava descrevendo Parquet)

[✓] requirements.txt:
    - Versoes alteradas de == para >= (flexibilidade)

====================================================================================
5. PENDENCIAS
====================================================================================

[ ] Remover senha do Config.json (usar variavel de ambiente ou .env)
[ ] Opcional: unificar Extracao EC/ (Parquet) e Extracao EC - CSV gz/ (CSV.gz)

====================================================================================
6. COMANDOS UTEIS
====================================================================================

Executar manualmente:
  cd "C:\Alexandre\Repositorios\DaVita\Extracao EC - CSV gz"
  venv\Scripts\python extracao.py

Gerenciar tarefa agendada:
  .\gerenciar_tarefa.bat

Verificar tarefa:
  Get-ScheduledTask -TaskName "ExtracaoEC" | Format-List *

Verificar pasta de saida dos arquivos:
  C:/Users/alexandresilva3/DaVita/Ciclo da Receita - HOSPITAL/
  Analise_De_Dados/Relatorios/0002 - Etapa Conta/Dados/

====================================================================================
FIM DO DOCUMENTO
====================================================================================
