"""Consolida os XLSX da pasta 1033 em um unico Parquet.

Spec:
- 1 linha por registro, todas as colunas originais +
  ds_modalidade='CRONICO' e gravacao='<run YYYY-MM-DD HH:MM:SS>'.
- Filtra pela coluna "Dt periodo inicial" mantendo apenas datas dentro de
  extracao.periodo (data_inicio/data_fim) de parametros.json.
- Parquet (pyarrow + compression zstd).
- Nome: <prefixo>-yyyyMMdd-hhmm.parquet no diretorio de saida.
- Destino e prefixo configuraveis em parametros.json > saida
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
PARAMS_PATH = BASE_DIR / "parametros.json"
CONFIG_PATH = BASE_DIR / "Config.json"

MODALIDADE = "CRONICO"
COLUNA_PERIODO = "Dt periodo inicial"


def load_params() -> dict:
    try:
        with open(PARAMS_PATH, encoding="utf-8") as f:
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
    periodo = (load_params().get("extracao", {}) or {}).get("periodo", {}) or {}
    inicio = _parse_data(periodo.get("data_inicio"))
    fim = _parse_data(periodo.get("data_fim"))
    if inicio is None or fim is None:
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
        inicio = inicio or _parse_data(cfg.get("data_inicial"))
        fim = fim or _parse_data(cfg.get("data_final"))
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


def filtrar_periodo(df, inicio: datetime | None, fim: datetime | None):
    import pandas as pd

    if inicio is None or fim is None:
        return df, 0, False

    coluna = resolver_coluna(df, COLUNA_PERIODO)
    if coluna is None:
        return df, 0, False

    datas = pd.to_datetime(
        df[coluna].astype(str).str.strip(), format="%d/%m/%Y", errors="coerce"
    )
    dentro = datas.between(inicio, fim)
    removidas = int((~dentro).sum())
    return df.loc[dentro].copy(), removidas, True


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
    if inicio and fim:
        print(f"[EC] Periodo: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} "
              f"(coluna '{COLUNA_PERIODO}')")
    else:
        print("[EC-AVISO] Periodo nao configurado — filtro desativado")

    run_dt = datetime.now()
    carimbo = run_dt.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[EC] {len(arquivos)} arquivo(s), atualizacao={carimbo}")

    frames = []
    vazios = []
    t0 = time.time()
    for f in arquivos:
        try:
            df = pd.read_excel(f, dtype=str)
        except Exception as e:
            print(f"[EC-AVISO] {f.name}: leitura falhou ({e}) — pulado")
            continue
        if len(df) == 0:
            vazios.append(f.stem)
        df, removidas, filtrado = filtrar_periodo(df, inicio, fim)
        if not filtrado:
            print(f"[EC-AVISO] {f.name}: coluna '{COLUNA_PERIODO}' ausente "
                  "— periodo nao filtrado")
        df["ds_modalidade"] = MODALIDADE
        df["gravacao"] = carimbo
        frames.append(df)
        sufixo = f" (removidas {removidas} fora do periodo)" if filtrado else ""
        print(f"[EC] {f.name}: {len(df)} linha(s){sufixo}")

    if not frames:
        print("[EC] Nenhum dado legivel — nada gerado")
        return None

    total = pd.concat(frames, ignore_index=True)
    dest_dir, prefixo = destino_config()
    nome = f"{prefixo}-{run_dt:%Y%m%d}-{run_dt:%H%M}.parquet"
    dest_dir.mkdir(parents=True, exist_ok=True)
    destino = dest_dir / nome
    total.to_parquet(destino, engine="pyarrow", compression="zstd", index=False)
    dt = time.time() - t0
    print(f"[EC] {destino.name}: {len(total)} linhas x {len(total.columns)} cols, "
          f"{destino.stat().st_size / 1024:.0f} KB em {dt:.1f}s")
    if vazios:
        print(f"[EC] Vazios (0 linhas, incluidos sem registros): {', '.join(vazios)}")
    return destino


def main() -> int:
    out = consolidar()
    return 0 if out else 1


if __name__ == "__main__":
    raise SystemExit(main())
