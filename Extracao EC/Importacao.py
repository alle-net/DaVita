"""Executa as extracoes em sequencia: Intus.py e depois Tasy_1033.py."""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ETAPAS = ("Intus.py", "Tasy_1033.py")


def python_executavel() -> str:
    for pasta in ("venv", ".venv"):
        candidato = BASE_DIR / pasta / "Scripts" / "python.exe"
        if candidato.is_file():
            return str(candidato)
    return sys.executable


def executar(script: str, env: dict[str, str]) -> int:
    caminho = BASE_DIR / script
    if not caminho.is_file():
        print(f"[IMPORTACAO][ERRO] nao encontrado: {caminho}")
        return 1
    print(f"\n[IMPORTACAO] ===== {script} =====")
    inicio = time.time()
    try:
        resultado = subprocess.run(
            [python_executavel(), str(caminho)],
            cwd=str(BASE_DIR),
            env=env,
        )
        codigo = resultado.returncode
    except KeyboardInterrupt:
        print(f"[IMPORTACAO] {script} interrompido pelo usuario")
        return 130
    except Exception as e:
        print(f"[IMPORTACAO][ERRO] {script}: {e}")
        return 1
    duracao = time.time() - inicio
    status = "OK" if codigo == 0 else f"FALHA (codigo {codigo})"
    print(f"[IMPORTACAO] {script}: {status} em {duracao:.1f}s")
    return codigo


def main() -> int:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    print(f"[IMPORTACAO] inicio {datetime.now():%Y-%m-%d %H:%M:%S}")
    inicio = time.time()
    for script in ETAPAS:
        codigo = executar(script, env)
        if codigo != 0:
            print(f"[IMPORTACAO] parando: {script} falhou")
            return codigo
    print(f"[IMPORTACAO] concluido em {time.time() - inicio:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
