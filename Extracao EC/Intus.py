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
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql import sqltypes

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "configui.json"

MAX_TENTATIVAS = 3
INTERVALO = 2
MODALIDADE = "AGUDO"
TABELA_ORIGEM = "status_conta"
CHAVES_OBRIGATORIAS = {
    "servidor",
    "banco",
    "usuario",
    "query",
    "pasta_saida",
    "data_inicial",
    "data_final",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def carregar_config(caminho_config: str | Path | None = None) -> dict[str, Any]:
    if caminho_config is None:
        caminho_config = CONFIG_PATH
    with open(caminho_config, "r", encoding="utf-8-sig") as f:
        config = json.load(f)

    _validar_config(config)
    return config


def _validar_config(config: dict[str, Any]) -> None:
    faltando = CHAVES_OBRIGATORIAS - config.keys()
    if faltando:
        raise KeyError(
            f"configui.json faltando chaves obrigatorias: {', '.join(sorted(faltando))}"
        )


def carregar_query(caminho_query: str) -> str:
    caminho_completo = BASE_DIR / "Querys" / caminho_query
    return caminho_completo.read_text(encoding="utf-8")


def periodo_mysql(config: dict[str, Any]) -> dict[str, str]:
    """Converte data_inicial/data_final (dd/mm/aaaa) para binds yyyy-mm-dd."""
    try:
        inicio = datetime.strptime(str(config["data_inicial"]).strip(), "%d/%m/%Y")
        fim = datetime.strptime(str(config["data_final"]).strip(), "%d/%m/%Y")
    except ValueError as e:
        raise ValueError(
            "configui.json: data_inicial e data_final devem estar no formato dd/mm/aaaa"
        ) from e
    if inicio > fim:
        raise ValueError("configui.json: data_inicial nao pode ser posterior a data_final")
    return {
        "data_inicio": inicio.strftime("%Y-%m-%d"),
        "data_fim": fim.strftime("%Y-%m-%d"),
    }


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


# Marcadores de double-encoding UTF-8 lido como cp1252/latin1.
# Inclui "â", que cobre travessões, aspas e € (ex: 'â€“' -> '–').
MARCAS_MOJIBAKE = ("Ã", "Â", "â")


def _tem_marca_mojibake(texto: str) -> bool:
    return any(marca in texto for marca in MARCAS_MOJIBAKE)


def corrigir_mojibake(valor: Any) -> Any:
    """Corrige texto com double-encoding tipo 'GoiÃ¢nia' -> 'Goiânia'.

    Retorna o valor inalterado se não for str ou se não houver marca de mojibake.
    """
    if not isinstance(valor, str):
        return valor
    if not _tem_marca_mojibake(valor):
        return valor
    texto = valor
    # até 2 níveis (cobre double-encoding)
    for _ in range(2):
        if not _tem_marca_mojibake(texto):
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
    cols_texto = [
        col
        for col in df.select_dtypes(include=["object", "string"]).columns
        if col != "vl_conta"  # tratada como numérica em normalizar_vl_conta()
    ]
    for col in cols_texto:
        df[col] = df[col].map(corrigir_mojibake)
    if cols_texto:
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


def normalizar_vl_conta(df: pd.DataFrame) -> pd.DataFrame:
    """Garante vl_conta numérica (float) para armazenamento tipado em Parquet."""
    if "vl_conta" not in df.columns:
        return df
    df["vl_conta"] = pd.to_numeric(df["vl_conta"], errors="coerce")
    logger.info("Coluna vl_conta convertida para numérico.")
    return df


def obter_tipos_colunas(engine: Engine, tabela: str = TABELA_ORIGEM) -> dict[str, Any]:
    """Le os tipos reais das colunas na origem (INFORMATION_SCHEMA)."""
    try:
        return {c["name"]: c["type"] for c in inspect(engine).get_columns(tabela)}
    except Exception as e:
        logger.warning("Nao foi possivel ler tipos de '%s': %s", tabela, e)
        return {}


def _codigo_tipo_sql(sql_type: Any) -> str:
    """Resume o tipo SQL em um codigo serializavel para o Parquet."""
    if isinstance(sql_type, sqltypes.Boolean):
        return "bool"
    if isinstance(sql_type, sqltypes.Integer):
        return "int"
    if isinstance(sql_type, sqltypes.Numeric):
        return "float"
    if isinstance(sql_type, sqltypes.DateTime):
        return "timestamp"
    if isinstance(sql_type, sqltypes.Date):
        return "date"
    return "string"


def _arrow_type_por_codigo(codigo: str) -> pa.DataType:
    """Mapeia o codigo do tipo SQL para o tipo Arrow estavel no Parquet."""
    return {
        "bool": pa.bool_(),
        "int": pa.int64(),
        "float": pa.float64(),
        "timestamp": pa.timestamp("us"),
        "date": pa.date32(),
    }.get(codigo, pa.large_string())


def corrigir_colunas_nulas(tabela: pa.Table, tipos_db: dict[str, str]) -> pa.Table:
    """Troca o tipo Arrow 'null' (coluna 100% nula) por um tipo concreto.

    O Power BI nao abre Parquet com coluna de tipo 'null' (erro
    "Argumento 'dataType' nao pode ser nulo"). Os valores NAO mudam: apenas
    o tipo da coluna passa a ser int64/string/date32 conforme o banco, mantendo
    o schema estavel entre execucoes.
    """
    campos: list[pa.Field] = []
    ajustadas = 0
    for field in tabela.schema:
        if pa.types.is_null(field.type):
            novo_tipo = _arrow_type_por_codigo(tipos_db.get(field.name, "string"))
            campos.append(field.with_type(novo_tipo))
            ajustadas += 1
            logger.info(
                "Coluna '%s' 100%% nula: tipo Parquet ajustado para %s",
                field.name,
                novo_tipo,
            )
        else:
            campos.append(field)
    if not ajustadas:
        return tabela
    novo_schema = pa.schema(campos, metadata=tabela.schema.metadata)
    return tabela.cast(novo_schema)


def extrair_dados(config: dict[str, Any]) -> pd.DataFrame:
    query = text(carregar_query(config["query"]))
    binds = periodo_mysql(config)

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            with conectar(config) as engine:
                tipos_db = obter_tipos_colunas(engine)
                df = pd.read_sql(query, engine, params=binds, coerce_float=False)
            df = tratar_textos_df(df)
            df = normalizar_vl_conta(df)
            df["ds_modalidade"] = MODALIDADE
            df["gravacao"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            df.attrs["tipos_db"] = {
                nome: _codigo_tipo_sql(tipo) for nome, tipo in tipos_db.items()
            }
            return df
        except Exception as e:
            if tentativa < MAX_TENTATIVAS:
                logger.warning("Tentativa %d falhou: %s", tentativa, e)
                logger.info("Tentando novamente em %ds...", INTERVALO)
                time.sleep(INTERVALO)
            else:
                logger.error("Falha apos %d tentativas", MAX_TENTATIVAS)
                raise


def salvar_parquet(df: pd.DataFrame, config: dict[str, Any]) -> Path:
    pasta_saida = Path(config["pasta_saida"]).expanduser()
    pasta_saida.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    nome_arquivo = f"AGUDO-{timestamp}.parquet"
    caminho_completo = pasta_saida / nome_arquivo
    tabela = pa.Table.from_pandas(df, preserve_index=False)
    tabela = corrigir_colunas_nulas(tabela, df.attrs.get("tipos_db", {}))
    pq.write_table(tabela, caminho_completo, compression="zstd")
    return caminho_completo


def main() -> None:
    config = carregar_config()
    logger.info(
        "Periodo: %s a %s", config["data_inicial"], config["data_final"]
    )
    logger.info("Conectando ao banco de dados...")
    df = extrair_dados(config)
    logger.info("Registros extraidos: %d", len(df))
    caminho = salvar_parquet(df, config)
    logger.info("Arquivo salvo em: %s", caminho)


if __name__ == "__main__":
    main()
