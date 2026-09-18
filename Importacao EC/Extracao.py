"""Etapa 4 — Orquestrador: Intus_SC e depois Tasy_1033 em um unico fluxo.

1. Intus_SC (MySQL -> AGUDO-yyyyMMdd-hhmm.csv.gz).
2. Tasy_1033 (Tasy UI -> 1033/*.xlsx -> CRONICO-yyyyMMdd-hhmm.csv.gz [5/5]).

Cada etapa roda independente: se a 1a falhar, a 2a executa mesmo assim.
Placar final no console + exit code 1 se alguma falhar.

Uso: .\\.venv\\Scripts\\python.exe Extracao.py
"""

import time
from datetime import datetime

import Intus_SC
import Tasy_1033


def etapa_intus() -> bool:
    print("=" * 70)
    print("[ETAPA 1/2] Intus_SC — MySQL -> CSV.GZ")
    print("=" * 70)
    t0 = time.time()
    try:
        params = Intus_SC.load_params()
        db = Intus_SC.carregar_db(params)
        binds = Intus_SC.periodo_mysql(params)
        Intus_SC.logger.info("Periodo MySQL: %s a %s", binds["data_inicio"], binds["data_fim"])
        df = Intus_SC.extrair_dados(db, binds)
        Intus_SC.logger.info("Registros extraidos: %d", len(df))
        caminho = Intus_SC.salvar_csv_gz(df, params, db)
        Intus_SC.logger.info("Arquivo salvo em: %s", caminho)
        print(f"[ETAPA 1/2] OK em {time.time()-t0:.0f}s -> {caminho}")
        return True
    except Exception as e:
        print(f"[ETAPA 1/2] FALHOU em {time.time()-t0:.0f}s: {e}")
        return False


def etapa_tasy() -> bool:
    print("=" * 70)
    print("[ETAPA 2/2] Tasy_1033 — UI Tasy -> 1033 -> CRONICO CSV.GZ")
    print("=" * 70)
    t0 = time.time()
    try:
        Tasy_1033.main()
        print(f"[ETAPA 2/2] OK em {time.time()-t0:.0f}s")
        return True
    except SystemExit as e:
        # main() pode propagar SystemExit em erro fatal de config
        ok = (e.code in (0, None))
        print(f"[ETAPA 2/2] {'OK' if ok else 'FALHOU'} em {time.time()-t0:.0f}s (exit={e.code})")
        return ok
    except Exception as e:
        print(f"[ETAPA 2/2] FALHOU em {time.time()-t0:.0f}s: {e}")
        return False


def main() -> int:
    ini = datetime.now()
    print(f"EXTRACAO COMPLETA iniciada em {ini:%Y-%m-%d %H:%M:%S}")
    ok_intus = etapa_intus()
    ok_tasy = etapa_tasy()
    print("=" * 70)
    print(f"PLACAR FINAL — Intus: {'OK' if ok_intus else 'FALHA'} | "
          f"Tasy: {'OK' if ok_tasy else 'FALHA'} | "
          f"duracao total {(datetime.now()-ini)}")
    print("=" * 70)
    return 0 if (ok_intus and ok_tasy) else 1


if __name__ == "__main__":
    raise SystemExit(main())
