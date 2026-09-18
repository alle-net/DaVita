"""Etapa 3 — Extracao Intus_SC (MySQL -> CSV.GZ).

Adaptado de 'Extracao EC - CSV gz/extracao.py'. Diferencas:
- Config vem de parametros.json > intus_db (credenciais ex-Config.json).
- Periodo vem de parametros.json > extracao.periodo (dd/mm/yyyy),
  injetado na query via bind params :data_inicio/:data_fim (yyyy-mm-dd).
- Colunas extras: ds_modalidade (default 'AGUDO') e atualizacao
  (ex-gravacao, run YYYY-MM-DD HH:MM:SS).
- Saida: <prefixo>-yyyyMMdd-hhmm.csv.gz (default prefixo 'AGUDO'),
  CSV ';', UTF-8, gzip.

Uso: .\\.venv\\Scripts\\python.exe Intus_SC.py
"""

import json
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

BASE_DIR = Path(__file__).resolve().parent
PARAMS_PATH = BASE_DIR / "parametros.json"
QUERYS_DIR = BASE_DIR / "Querys"

MAX_TENTATIVAS = 3
INTERVALO = 2
CHAVES_DB_OBRIGATORIAS = {"servidor", "banco", "usuario", "query"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_params() -> dict[str, Any]:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        return json.load(f)


def periodo_mysql(params: dict[str, Any]) -> dict[str, str]:
    """Converte extracao.periodo (dd/mm/yyyy) p/ binds yyyy-mm-dd."""
    periodo = params.get("extracao", {}).get("periodo", {}) or {}
    try:
        ini = datetime.strptime(str(periodo["data_inicio"]).strip(), "%d/%m/%Y")
        fim = datetime.strptime(str(periodo["data_fim"]).strip(), "%d/%m/%Y")
    except (KeyError, ValueError) as e:
        raise SystemExit(
            "Preencha extracao.periodo (data_inicio/data_fim dd/mm/yyyy) "
            f"em parametros.json: {e}"
        )
    if ini > fim:
        raise SystemExit("extracao.periodo: data_inicio apos data_fim")
    return {"data_inicio": ini.strftime("%Y-%m-%d"), "data_fim": fim.strftime("%Y-%m-%d")}


def carregar_db(params: dict[str, Any]) -> dict[str, Any]:
    db = params.get("intus_db", {}) or {}
    faltando = CHAVES_DB_OBRIGATORIAS - db.keys()
    if faltando:
        raise KeyError(
            "parametros.json > intus_db faltando chaves: "
            + ", ".join(sorted(faltando))
        )
    return db


def carregar_query(nome_query: str) -> str:
    return (QUERYS_DIR / nome_query).read_text(encoding="utf-8")


@contextmanager
def conectar(db: dict[str, Any]) -> Iterator[Engine]:
    senha_encoded = quote_plus(db.get("senha", ""))
    string_conexao = (
        f"mysql+pymysql://{db['usuario']}:{senha_encoded}"
        f"@{db['servidor']}/{db['banco']}?charset=utf8mb4"
    )
    # Timeouts longos: a transferencia de ~150k linhas leva minutos.
    engine = create_engine(
        string_conexao,
        connect_args={
            "connect_timeout": 15,
            "read_timeout": 600,
            "write_timeout": 600,
        },
    )
    try:
        yield engine
    finally:
        engine.dispose()


CHUNK_SIZE = 20000  # streaming por lotes: progresso visivel + pico de RAM menor


def extrair_dados(db: dict[str, Any], binds: dict[str, str]) -> pd.DataFrame:
    query = text(carregar_query(db["query"]))
    modalidade = str(db.get("ds_modalidade", "AGUDO") or "AGUDO")
    carimbo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            with conectar(db) as engine:
                partes = []
                total = 0
                t0 = time.time()
                for chunk in pd.read_sql(
                    query, engine, params=binds, coerce_float=False,
                    chunksize=CHUNK_SIZE,
                ):
                    total += len(chunk)
                    partes.append(chunk)
                    logger.info("... %d linhas em %ds", total, int(time.time() - t0))
            df = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
            df["ds_modalidade"] = modalidade
            df["atualizacao"] = carimbo
            return df
        except Exception as e:
            if tentativa < MAX_TENTATIVAS:
                logger.warning("Tentativa %d falhou: %s", tentativa, e)
                logger.info("Tentando novamente em %ds...", INTERVALO)
                time.sleep(INTERVALO)
            else:
                logger.error("Falha apos %d tentativas", MAX_TENTATIVAS)
                raise


def salvar_csv_gz(df: pd.DataFrame, params: dict[str, Any], db: dict[str, Any]) -> Path:
    # Mesmo destino do Tasy: parametros.json > saida.consolidado_diretorio.
    saida = params.get("saida", {}) or {}
    raw = str(saida.get("consolidado_diretorio", "") or "").strip()
    pasta_saida = Path(raw).expanduser() if raw else Path.home() / "Downloads"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    prefixo = str(db.get("prefixo", "AGUDO") or "AGUDO")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    caminho_completo = pasta_saida / f"{prefixo}-{timestamp}.csv.gz"
    df.to_csv(
        caminho_completo,
        index=False,
        sep=";",
        compression="gzip",
        # UTF-8 COM BOM: sem ele o Excel BR abre como Windows-1252 e exibe
        # 'VitÃ³ria' (o arquivo estava byte-correto; o problema era a deteccao).
        encoding="utf-8-sig",
    )
    return caminho_completo


def main() -> None:
    params = load_params()
    db = carregar_db(params)
    binds = periodo_mysql(params)
    logger.info("Periodo MySQL: %s a %s", binds["data_inicio"], binds["data_fim"])
    logger.info("Query: %s | banco: %s@%s/%s",
                db["query"], db["usuario"], db["servidor"], db["banco"])
    logger.info("Conectando ao banco de dados...")
    df = extrair_dados(db, binds)
    logger.info("Registros extraidos: %d", len(df))
    caminho = salvar_csv_gz(df, params, db)
    logger.info("Arquivo salvo em: %s", caminho)


if __name__ == "__main__":
    main()
