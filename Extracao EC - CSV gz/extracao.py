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
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

MAX_TENTATIVAS = 3
INTERVALO = 2
CHAVES_OBRIGATORIAS = {"servidor", "banco", "usuario", "query", "pasta_saida"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def carregar_config(caminho_config: str = "Config.json") -> dict[str, Any]:
    with open(caminho_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    _validar_config(config)
    return config


def _validar_config(config: dict[str, Any]) -> None:
    faltando = CHAVES_OBRIGATORIAS - config.keys()
    if faltando:
        raise KeyError(
            f"Config.json faltando chaves obrigatorias: {', '.join(sorted(faltando))}"
        )


def carregar_query(caminho_query: str) -> str:
    caminho_completo = Path("Querys") / caminho_query
    return caminho_completo.read_text("utf-8")


@contextmanager
def conectar(config: dict[str, Any]) -> Iterator[Engine]:
    senha_encoded = quote_plus(config.get("senha", ""))
    string_conexao = (
        f"mysql+pymysql://{config['usuario']}:{senha_encoded}"
        f"@{config['servidor']}/{config['banco']}"
    )
    engine = create_engine(string_conexao)
    try:
        yield engine
    finally:
        engine.dispose()


def extrair_dados(config: dict[str, Any]) -> pd.DataFrame:
    query = carregar_query(config["query"])

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            with conectar(config) as engine:
                df = pd.read_sql(query, engine)
            df["gravacao"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            return df
        except Exception as e:
            if tentativa < MAX_TENTATIVAS:
                logger.warning("Tentativa %d falhou: %s", tentativa, e)
                logger.info("Tentando novamente em %ds...", INTERVALO)
                time.sleep(INTERVALO)
            else:
                logger.error("Falha apos %d tentativas", MAX_TENTATIVAS)
                raise


def salvar_csv_gz(df: pd.DataFrame, config: dict[str, Any]) -> Path:
    pasta_saida = Path(config["pasta_saida"])
    pasta_saida.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    nome_arquivo = f"EC-{timestamp}.csv.gz"
    caminho_completo = pasta_saida / nome_arquivo
    df.to_csv(caminho_completo, index=False, sep=";", compression="gzip")
    return caminho_completo


def main() -> None:
    config = carregar_config()
    logger.info("Conectando ao banco de dados...")
    df = extrair_dados(config)
    logger.info("Registros extraidos: %d", len(df))
    caminho = salvar_csv_gz(df, config)
    logger.info("Arquivo salvo em: %s", caminho)


if __name__ == "__main__":
    main()
