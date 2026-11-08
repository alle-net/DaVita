====================================================================================
DOCUMENTACAO DO PROJETO - Extracao EC (Parquet)
====================================================================================
Data: 08/11/2026
Descricao: Script de extracao de dados do MySQL para arquivo Parquet (compressao
           Zstandard), com agendamento semanal no Windows Task Scheduler.

====================================================================================
1. ESTRUTURA DO DIRETORIO
====================================================================================

Extracao EC/
├── Config.json                  # Configuracao do banco MySQL e pasta de saida
├── Intus.py                     # Script principal (Python)
├── gerenciar_tarefa.bat         # Menu para gerenciar tarefa agendada no Windows
├── requirements.txt             # Dependencias Python
├── Querys/
│   ├── EC.sql                   # Query completa (36 colunas, todos estabelecimentos)
│   ├── ECC.sql                  # Query simplificada (SELECT *)
│   └── EC_RJ.sql                # Query filtrada para 8 unidades do RJ
└── venv/                        # Ambiente virtual Python

====================================================================================
2. ARQUIVOS E CONTEUDO ATUAL
====================================================================================

2.1 Intus.py
───────────────────────────────────────────────────────────────────────────────────
- Conexao MySQL via SQLAlchemy + PyMySQL, charset utf8mb4 / use_unicode.
- Carrega query do diretorio Querys/.
- 3 tentativas de conexao com intervalo de 2s (MAX_TENTATIVAS / INTERVALO).
- Corrige mojibake (double-encoding UTF-8 lido como cp1252/latin1) em todas as
  colunas de texto. Marcadores tratados: "Ã", "Â" e "â" (cobre travessoes,
  aspas e simbolo de euro). Preserva maiusculas legitimas (SAO, INTERCAMBIO).
- Converte vl_conta para numerico (float) para armazenamento tipado.
- Adiciona as colunas finais "ds_modalidade" (AGUDO) e "gravacao"
  (YYYY-MM-DD HH:MM) com o horario da extracao.
- Salva como Parquet (engine pyarrow, compression zstd, index=False).
- Nome do arquivo: EC-YYYYMMDD-HHMM.parquet
- Type hints, logging estruturado, context manager para conexao.

Funcoes principais:
  carregar_config / _validar_config  -> le e valida o Config.json
  carregar_query                     -> le o .sql em Querys/
  conectar                           -> context manager da Engine SQLAlchemy
  corrigir_mojibake / _tem_marca...  -> desfaz double-encoding
  tratar_textos_df                   -> aplica correcao em colunas de texto
  normalizar_vl_conta                -> garante vl_conta numerica
  extrair_dados                      -> leitura com retry + tratamentos
  salvar_parquet                     -> grava .parquet (zstd)
  main                               -> orquestra o fluxo

2.2 Config.json (Senha em texto puro - PENDENTE DE CORRECAO)
───────────────────────────────────────────────────────────────────────────────────
{
  "servidor": "...",
  "banco": "...",
  "usuario": "...",
  "senha": "<definida no Config.json>",
  "query": "ECC.sql",
  "data_inicial": "01/01/2026",
  "data_final": "08/11/2026",
  "pasta_saida": "~/Downloads"
}

OBS: data_inicial/data_final usam o formato dd/mm/aaaa e sao obrigatorias.
     Elas sao convertidas para yyyy-mm-dd e injetadas na query como binds
     :data_inicio / :data_fim.

OBS: A senha esta em texto puro no Config.json. Sugestao pendente: usar variavel
     de ambiente (DB_PASSWORD) ou .env para remover a senha do JSON.
     (Decisao de 08/11/2026: manter como esta por enquanto.)

2.3 requirements.txt
───────────────────────────────────────────────────────────────────────────────────
pandas>=3.0.5
pyarrow>=24.0.0
PyMySQL>=1.2.0
SQLAlchemy>=2.0.51

2.4 Querys/ECC.sql (Query em uso atualmente)
───────────────────────────────────────────────────────────────────────────────────
SELECT * FROM status_conta
WHERE dt_periodo_inicial >= :data_inicio
  AND dt_periodo_inicial <= :data_fim
  AND ds_etapa <> 'Contas Canceladas'
  AND cd_estabelecimento NOT IN (264,265)

Os valores de :data_inicio e :data_fim vem do Config.json (data_inicial e
data_final, em dd/mm/aaaa) e sao convertidos para yyyy-mm-dd pelo Intus.py.

O Tasy_1033.py tambem le o MESMO periodo do Config.json (data_inicial e
data_final), garantindo que Intus e Tasy_1033 rodem com o mesmo range de datas.
Se Config.json nao tiver as chaves, usa o fallback parametros.json >
extracao.periodo.

2.5 gerenciar_tarefa.bat
───────────────────────────────────────────────────────────────────────────────────
Menu interativo para gerenciar a tarefa agendada "ExtracaoEC" no Windows:
  [1] Criar tarefa    - pergunta dia da semana e horario
  [2] Alterar dia e horario
  [3] Deletar tarefa
  [0] Sair
Executa: venv\Scripts\python.exe "C:\Alexandre\Repositorios\DaVita\Extracao EC\Intus.py"

====================================================================================
3. FORMATO DE SAIDA (Parquet)
====================================================================================

Arquivo: EC-YYYYMMDD-HHMM.parquet
Engine: pyarrow | Compressao: zstd | index=False

Vantagens sobre CSV.gz:
  - Dados tipados: texto (UTF-8), vl_conta numerico (double), datas nativas.
  - Arquivo menor e leitura muito mais rapida (ideal para Power BI / pandas).
  - Sem BOM, sem delimitador, sem problemas de encoding na gravacao.

Ponto de atencao:
  - Excel/VBA/Access NAO abrem .parquet com duplo clique. Para Excel, use
    Dados > Obter Dados > Do Arquivo > Parquet (Power Query) ou o projeto
    "Conversor Parquet". O CSV.gz antigo continua legivel diretamente no Excel.

Tasy_1033 (consolidar_ec.py):
  - Le os XLSX de ~/Downloads/1033 e grava CRONICO-YYYYMMDD-HHMM.parquet.
  - Filtra pela coluna "Dt periodo inicial": mantem apenas linhas com data
    entre extracao.periodo.data_inicio e data_fim (parametros.json). Linhas
    com data vazia/invalida ou fora do range sao descartadas.
  - Colunas finais "ds_modalidade" (CRONICO) e "gravacao"
    (YYYY-MM-DD HH:MM:SS), no mesmo padrao do Intus.

====================================================================================
4. TAREFA AGENDADA (Windows Task Scheduler)
====================================================================================

Nome: ExtracaoEC
Executar: py -3 "C:\Alexandre\Repositorios\DaVita\Extracao EC\Intus.py"
Agendamento: Semanal - Quarta-feira as 12:30
Estado: Ready (Pronto)
Descricao: Extracao EC (Parquet)

Para ver no PowerShell:
  Get-ScheduledTask -TaskName "ExtracaoEC" | Format-List *

Para abrir o Agendador de Tarefas:
  Win + R > taskschd.msc > Biblioteca > ExtracaoEC

====================================================================================
5. MELHORIAS APLICADAS
====================================================================================

[29/07/2026]
  - Type hints em todas as funcoes.
  - print() substituido por logging estruturado.
  - Validacao de chaves obrigatorias no Config.json.
  - Conexao com banco via @contextmanager (dispose automatico).
  - Delimitador CSV alterado para ";" (ponto e virgula).

[08/11/2026]
  - Saida migrada de CSV.gz para Parquet (pyarrow + zstd).
  - vl_conta gravada como numero (formatacao pt-BR fica para a importacao/exibicao).
  - Correcao de mojibake ampliada para sequencias iniciadas por "â"
    (travessoes, aspas e euro), mantendo maiusculas legitimas.
  - Contagem de colunas de texto no log corrigida (nao conta vl_conta).
  - requirements.txt inclui pyarrow.
  - Periodo configuravel no Config.json (data_inicial/data_final em dd/mm/aaaa),
    injetado nas queries como binds :data_inicio / :data_fim.
  - gerenciar_tarefa.bat e README atualizados (pasta "Extracao EC" e Intus.py).

====================================================================================
6. PENDENCIAS
====================================================================================

[ ] Remover senha do Config.json (usar variavel de ambiente ou .env).
[ ] Opcional: unificar "Extracao EC/" (Parquet) e "Extracao EC - CSV gz/" (CSV.gz).

====================================================================================
7. COMANDOS UTEIS
====================================================================================

Executar manualmente:
  cd "C:\Alexandre\Repositorios\DaVita\Extracao EC"
  venv\Scripts\python Importacao.py   (Intus.py e depois Tasy_1033.py)
  venv\Scripts\python Intus.py        (apenas MySQL)
  venv\Scripts\python Tasy_1033.py    (apenas Tasy 1033)

Gerenciar tarefa agendada:
  .\gerenciar_tarefa.bat

Verificar tarefa:
  Get-ScheduledTask -TaskName "ExtracaoEC" | Format-List *

Verificar pasta de saida dos arquivos:
  C:/Users/<usuario>/Downloads/

  - Intus: EC-YYYYMMDD-HHMM.parquet
  - Tasy:  CRONICO-YYYYMMDD-HHMM.parquet

====================================================================================
FIM DO DOCUMENTO
====================================================================================
