import logging
import os
import tomllib
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import psycopg
from psycopg_pool import ConnectionPool

RAIZ = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


class PendenciaDuplicadaError(Exception):
    pass


@lru_cache(maxsize=1)
def obter_url() -> str:
    url = os.environ.get("SUPABASE_DB_URL")
    if url:
        return url
    try:
        import streamlit as st

        return st.secrets["SUPABASE_DB_URL"]
    except Exception:
        with open(RAIZ / ".streamlit" / "secrets.toml", "rb") as f:
            return tomllib.load(f)["SUPABASE_DB_URL"]


def _novo_pool() -> ConnectionPool:
    return ConnectionPool(
        conninfo=obter_url(),
        min_size=1,
        max_size=5,
        open=True,
        timeout=10,
        kwargs={"autocommit": True},
    )


try:
    import streamlit as st

    _get_pool = st.cache_resource(_novo_pool, show_spinner=False, max_entries=1)
except Exception:  # pragma: no cover - fora do runtime Streamlit
    def _get_pool() -> ConnectionPool:
        return _novo_pool()


@contextmanager
def conectar() -> psycopg.Connection:
    """Pega uma conexão do pool e a devolve ao final (ou em caso de erro).

    Compatível com o uso existente: `with conectar() as conn:`.
    """
    try:
        conn = _get_pool().connection(timeout=10)
    except Exception:
        logger.exception("Falha ao obter conexão do pool de banco")
        raise
    with conn as conexao:
        yield conexao
