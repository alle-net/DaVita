"""Consolida os XLSX da pasta 1033 em um unico CSV.GZ.

Spec (18/09):
- 1 linha por registro, todas as colunas originais +
  ds_modalidade='CRONICO' e atualizacao='<run YYYY-MM-DD HH:MM:SS>'.
- CSV com ';', UTF-8, gzip.
- Nome: CRONICO-yyyyMMdd-hhmm.csv.gz em output/.
- Inclui tudo (xlsx vazios contribuem com 0 linhas, sem quebrar).

Uso: .\\.venv\\Scripts\\python.exe consolidar_ec.py
"""

import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

MODALIDADE = "CRONICO"
SEP = ";"
ENCODING = "utf-8"


def pasta_1033() -> Path:
    return Path.home() / "Downloads" / "1033"


def consolidar() -> Path | None:
    import pandas as pd

    origem = pasta_1033()
    arquivos = sorted(origem.glob("*.xlsx"))
    if not arquivos:
        print(f"[EC] Nada a consolidar — sem *.xlsx em {origem}")
        return None

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
        df["ds_modalidade"] = MODALIDADE
        df["atualizacao"] = carimbo
        frames.append(df)
        print(f"[EC] {f.name}: {len(df)} linha(s)")

    if not frames:
        print("[EC] Nenhum dado legivel — nada gerado")
        return None

    total = pd.concat(frames, ignore_index=True)
    nome = f"CRONICO-{run_dt:%Y%m%d}-{run_dt:%H%M}.csv.gz"
    OUTPUT_DIR.mkdir(exist_ok=True)
    destino = OUTPUT_DIR / nome
    total.to_csv(destino, sep=SEP, encoding=ENCODING, index=False, compression="gzip")
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
