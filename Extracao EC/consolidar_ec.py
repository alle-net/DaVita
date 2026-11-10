"""Consolida os XLSX da pasta 1033 em um unico Parquet.

Spec:
- 1 linha por registro, todas as colunas originais +
  ds_modalidade='CRONICO' e gravacao='<run YYYY-MM-DD HH:MM:SS>'.
- Filtra pela coluna "Dt periodo inicial" mantendo apenas datas dentro do
  periodo global (data_inicial/data_final) de configui.json.
- Tipa datas (date32) e "Vl conta" (float64); identificadores permanecem texto.
  Se algum valor nao seguir o formato, a coluna fica texto e gera aviso.
- Parquet (pyarrow + compression zstd).
- Nome: <prefixo>-yyyyMMdd-hhmm.parquet no diretorio de saida.
- Destino e prefixo configuraveis em configui.json > saida
  (consolidado_diretorio, consolidado_prefixo). Default: ~/Downloads.
- Inclui tudo (xlsx vazios contribuem com 0 linhas, sem quebrar).

Uso: venv\\Scripts\\python.exe consolidar_ec.py
"""

import json
import time
import unicodedata
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "configui.json"

MODALIDADE = "CRONICO"
COLUNA_PERIODO = "Dt periodo inicial"

COLUNAS_DATA = (
    "Dt mesano referencia",
    "Dt periodo inicial",
    "Dt periodo final",
    "Dt etapa",
    "dt_emissao_titulo",
    "Último Pré-Faturamento",
)
COLUNA_VALOR = "Vl conta"


def load_params() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def _parse_data(valor: object) -> datetime | None:
    texto = str(valor or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    return None


def carregar_periodo() -> tuple[datetime | None, datetime | None]:
    """Periodo global (topo de configui.json), o mesmo usado por Intus e Tasy."""
    cfg = load_params()
    inicio = _parse_data(cfg.get("data_inicial"))
    fim = _parse_data(cfg.get("data_final"))
    return inicio, fim


def _norm(texto: object) -> str:
    sem_acento = (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    return " ".join(sem_acento.split())


def resolver_coluna(df, alvo: str) -> str | None:
    alvo_norm = _norm(alvo)
    for coluna in df.columns:
        if _norm(coluna) == alvo_norm:
            return coluna
    return None


def _texto_limpo(serie):
    """Espacos/strings vazias viram nulo; o restante e preservado."""
    import pandas as pd

    texto = serie.astype("string").str.strip()
    return texto.mask(texto == "", pd.NA)


def _tipar_data(df, coluna: str) -> bool:
    import pandas as pd

    origem = _texto_limpo(df[coluna])
    datas = pd.to_datetime(origem, format="%d/%m/%Y", errors="coerce")
    invalidos = int(origem.notna().sum() - datas.notna().sum())
    if invalidos:
        exemplos = origem[origem.notna() & datas.isna()].head(3).tolist()
        print(f"[EC-AVISO] '{coluna}': {invalidos} valor(es) fora de "
              f"dd/mm/aaaa — mantida como texto (ex: {exemplos})")
        return False
    df[coluna] = datas.dt.date
    return True


def _tipar_valor(df, coluna: str) -> bool:
    import pandas as pd

    origem = _texto_limpo(df[coluna])
    if origem.str.contains(",", na=False).any():
        candidato = origem.str.replace(".", "", regex=False)
        candidato = candidato.str.replace(",", ".", regex=False)
    else:
        candidato = origem
    numeros = pd.to_numeric(candidato, errors="coerce")
    invalidos = int(origem.notna().sum() - numeros.notna().sum())
    if invalidos:
        exemplos = origem[origem.notna() & numeros.isna()].head(3).tolist()
        print(f"[EC-AVISO] '{coluna}': {invalidos} valor(es) nao numerico(s) "
              f"— mantida como texto (ex: {exemplos})")
        return False
    df[coluna] = numeros.astype("float64")
    return True


def tipar_colunas(df):
    """Tipa datas e Vl conta; identificadores permanecem texto.

    So converte quando 100% dos valores nao vazios estao no formato esperado;
    caso contrario a coluna permanece texto e um aviso e emitido.
    """
    import pandas as pd

    convertidas = []
    for alvo in COLUNAS_DATA:
        coluna = resolver_coluna(df, alvo)
        if coluna is None or not pd.api.types.is_string_dtype(df[coluna]):
            continue
        if _tipar_data(df, coluna):
            convertidas.append(f"{coluna} (data)")

    coluna_valor = resolver_coluna(df, COLUNA_VALOR)
    if coluna_valor is not None and pd.api.types.is_string_dtype(df[coluna_valor]):
        if _tipar_valor(df, coluna_valor):
            convertidas.append(f"{coluna_valor} (num)")

    if convertidas:
        print(f"[EC] Colunas tipadas: {', '.join(convertidas)}")
    return df


def filtrar_periodo(df, inicio: datetime | None, fim: datetime | None):
    """Mantem so linhas com 'Dt periodo inicial' dentro de [inicio, fim].

    Retorna (df_filtrado, removidas_fora, sem_data_valida, filtrado).
    filtrado=False quando nao ha periodo ou a coluna nao existe.
    """
    import pandas as pd

    if inicio is None or fim is None:
        return df, 0, 0, False

    coluna = resolver_coluna(df, COLUNA_PERIODO)
    if coluna is None:
        return df, 0, 0, False

    datas = pd.to_datetime(
        df[coluna].astype(str).str.strip(), format="%d/%m/%Y", errors="coerce"
    )
    dentro = datas.between(inicio, fim)
    sem_data_valida = int(datas.isna().sum())
    fora = int((~dentro).sum()) - sem_data_valida
    return df.loc[dentro].copy(), fora, sem_data_valida, True


def destino_config() -> tuple[Path, str]:
    saida = load_params().get("saida", {}) or {}
    raw = str(saida.get("consolidado_diretorio", "") or "").strip()
    base = Path(raw).expanduser() if raw else Path.home() / "Downloads"
    prefixo = str(saida.get("consolidado_prefixo", "") or "").strip() or "CRONICO"
    return base, prefixo


def pasta_1033() -> Path:
    return Path.home() / "Downloads" / "1033"


def consolidar() -> Path | None:
    import pandas as pd

    origem = pasta_1033()
    arquivos = sorted(
        f for f in origem.glob("*.xlsx") if not f.name.startswith("~$")
    )
    if not arquivos:
        print(f"[EC] Nada a consolidar — sem *.xlsx em {origem}")
        return None

    inicio, fim = carregar_periodo()
    if inicio is None or fim is None:
        print("[EC-ERRO] Periodo invalido/ausente em configui.json "
              "(data_inicial/data_final) — consolidacao abortada")
        return None
    print(f"[EC] Periodo: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} "
          f"(coluna '{COLUNA_PERIODO}')")

    run_dt = datetime.now()
    carimbo = run_dt.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[EC] {len(arquivos)} arquivo(s), atualizacao={carimbo}")

    frames = []
    vazios = []
    total_fora = 0
    total_sem_data = 0
    t0 = time.time()
    for f in arquivos:
        try:
            df = pd.read_excel(f, dtype=str)
        except Exception as e:
            print(f"[EC-AVISO] {f.name}: leitura falhou ({e}) — pulado")
            continue
        if len(df) == 0:
            vazios.append(f.stem)
        df, fora, sem_data, filtrado = filtrar_periodo(df, inicio, fim)
        if not filtrado:
            print(f"[EC-ERRO] {f.name}: coluna '{COLUNA_PERIODO}' ausente "
                  "— consolidacao abortada para nao gravar dado fora do periodo")
            return None
        total_fora += fora
        total_sem_data += sem_data
        df["ds_modalidade"] = MODALIDADE
        df["gravacao"] = carimbo
        frames.append(df)
        print(f"[EC] {f.name}: {len(df)} linha(s) "
              f"(removidas {fora} fora do periodo, {sem_data} sem data valida)")

    if not frames:
        print("[EC] Nenhum dado legivel — nada gerado")
        return None

    total = pd.concat(frames, ignore_index=True)
    total = tipar_colunas(total)
    dest_dir, prefixo = destino_config()
    nome = f"{prefixo}-{run_dt:%Y%m%d}-{run_dt:%H%M}.parquet"
    dest_dir.mkdir(parents=True, exist_ok=True)
    destino = dest_dir / nome
    total.to_parquet(destino, engine="pyarrow", compression="zstd", index=False)
    dt = time.time() - t0
    print(f"[EC] {destino.name}: {len(total)} linhas x {len(total.columns)} cols, "
          f"{destino.stat().st_size / 1024:.0f} KB em {dt:.1f}s")
    print(f"[EC] Filtro '{COLUNA_PERIODO}': {total_fora} removida(s) fora do "
          f"periodo + {total_sem_data} sem data valida")
    if vazios:
        print(f"[EC] Vazios (0 linhas, incluidos sem registros): {', '.join(vazios)}")
    return destino


def main() -> int:
    out = consolidar()
    return 0 if out else 1


if __name__ == "__main__":
    raise SystemExit(main())
