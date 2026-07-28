import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine
import pandas as pd

MAX_TENTATIVAS = 3
INTERVALO = 2


def carregar_config(caminho_config: str = "Config.json") -> dict:
    with open(caminho_config, "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_query(caminho_query: str) -> str:
    caminho_completo = Path("Querys") / caminho_query
    with open(caminho_completo, "r", encoding="utf-8") as f:
        return f.read()


def criar_conexao(config: dict):
    senha_encoded = quote_plus(config["senha"])
    string_conexao = (
        f"mysql+pymysql://{config['usuario']}:{senha_encoded}"
        f"@{config['servidor']}/{config['banco']}"
    )
    return create_engine(string_conexao)


def extrair_dados(config: dict) -> pd.DataFrame:
    query = carregar_query(config["query"])

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            engine = criar_conexao(config)
            df = pd.read_sql(query, engine)
            engine.dispose()
            df["gravacao"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            return df
        except Exception as e:
            if tentativa < MAX_TENTATIVAS:
                print(f"Tentativa {tentativa} falhou: {e}")
                print(f"Tentando novamente em {INTERVALO}s...")
                time.sleep(INTERVALO)
            else:
                raise Exception(f"Falha apos {MAX_TENTATIVAS} tentativas: {e}")


def salvar_csv_gz(df: pd.DataFrame, config: dict):
    pasta_saida = Path(config["pasta_saida"])
    pasta_saida.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    nome_arquivo = f"EC-{timestamp}.csv.gz"
    caminho_completo = pasta_saida / nome_arquivo
    df.to_csv(caminho_completo, index=False, compression="gzip")
    return caminho_completo


def main():
    config = carregar_config()
    print("Conectando ao banco de dados...")
    df = extrair_dados(config)
    print(f"Registros extraidos: {len(df)}")
    caminho = salvar_csv_gz(df, config)
    print(f"Arquivo salvo em: {caminho}")


if __name__ == "__main__":
    main()
