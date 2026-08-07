import os
import tomllib
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parent.parent


class PendenciaDuplicadaError(Exception):
    pass


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


def conectar() -> psycopg.Connection:
    return psycopg.connect(conninfo=obter_url(), autocommit=True)
