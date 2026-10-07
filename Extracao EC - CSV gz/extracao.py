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
    return caminho_completo.read_text(encoding="utf-8")


@contextmanager
def conectar(config: dict[str, Any]) -> Iterator[Engine]:
    senha_encoded = quote_plus(config.get("senha", ""))
    string_conexao = (
        f"mysql+pymysql://{config['usuario']}:{senha_encoded}"
        f"@{config['servidor']}/{config['banco']}?charset=utf8mb4"
    )
    engine = create_engine(
        string_conexao,
        pool_pre_ping=True,
        connect_args={"charset": "utf8mb4", "use_unicode": True},
    )
    try:
        yield engine
    finally:
        engine.dispose()


def corrigir_mojibake(valor: Any) -> Any:
    """Corrige texto com double-encoding tipo 'GoiÃ¢nia' -> 'Goiânia'.

    Retorna o valor inalterado se não for str ou se não houver marca de mojibake.
    """
    if not isinstance(valor, str):
        return valor
    if "Ã" not in valor and "Â" not in valor:
        return valor
    texto = valor
    # até 2 níveis (cobre double-encoding)
    for _ in range(2):
        if "Ã" not in texto and "Â" not in texto:
            break
        corrigido = None
        for enc in ("cp1252", "latin1"):
            try:
                corrigido = texto.encode(enc).decode("utf-8")
                break
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
        if corrigido is None or corrigido == texto:
            break
        texto = corrigido
    return texto


def tratar_textos_df(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica correção de acentos em TODAS as colunas de texto do DataFrame."""
    cols_texto = df.select_dtypes(include=["object", "string"]).columns
    for col in cols_texto:
        # pula vl_conta: ela será formatada como moeda BR em formatar_vl_conta()
        if col == "vl_conta":
            continue
        df[col] = df[col].map(corrigir_mojibake)
    if len(cols_texto):
        logger.info("Tratamento de acentos aplicado em %d coluna(s) texto.", len(cols_texto))
    return df


def formatar_moeda_br(valor: Any) -> str:
    """Converte 1234.56 (americano) -> '1.234,56' (brasileiro).

    Aceita Decimal/float/int/str. NaN/None/vazio -> ''.
    Se já vier em formato BR ('1.234,56'), preserva.
    """
    if valor is None:
        return ""
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    if isinstance(valor, str):
        s = valor.strip().replace("R$", "").strip()
        if not s:
            return ""
        if "," in s:
            # já está em formato BR — normaliza espaços
            return s
        try:
            num = float(s.replace(" ", ""))
        except ValueError:
            return valor
    else:
        try:
            if pd.isna(valor):
                return ""
        except (TypeError, ValueError):
            pass
        try:
            num = float(valor)
        except (TypeError, ValueError):
            return valor
    us = f"{num:,.2f}"  # ex: '1,234.56' / '-1,234.56'
    br = us.replace(",", "X").replace(".", ",").replace("X", ".")
    return br


def formatar_vl_conta(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica formato brasileiro na coluna vl_conta, se existir."""
    if "vl_conta" not in df.columns:
        return df
    df["vl_conta"] = df["vl_conta"].map(formatar_moeda_br)
    logger.info("Coluna vl_conta formatada para padrão BR (ex: 1.234,56).")
    return df


def extrair_dados(config: dict[str, Any]) -> pd.DataFrame:
    query = carregar_query(config["query"])

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            with conectar(config) as engine:
                df = pd.read_sql(query, engine, coerce_float=False)
            df = tratar_textos_df(df)
            df = formatar_vl_conta(df)
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
    df.to_csv(
        caminho_completo,
        index=False,
        sep=";",
        compression="gzip",
        encoding="utf-8-sig",
    )
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
