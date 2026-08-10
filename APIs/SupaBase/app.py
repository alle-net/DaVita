import streamlit as st

from utils import db, sessao

st.set_page_config(page_title="Justificativas de Pendências", layout="wide")

sessao.iniciar_pagina("login")

st.title("Justificativas de Pendências")
st.caption("Registro de pendências por usuário — Supabase")

if st.session_state.get("logado"):
    st.switch_page("pages/meus_registros.py")
else:
    st.subheader("Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if not email or not senha:
            st.error("Informe email e senha.")
        else:
            usuario = db.buscar_usuario_por_email(email.strip().lower())
            if (
                usuario is None
                or not usuario.get("Ativo")
                or senha != usuario["SenhaUsuario"]
            ):
                st.error("Credenciais inválidas ou usuário inativo.")
            else:
                sessao.fazer_login(usuario["IdUsuario"], usuario["EmailUsuario"])
                st.switch_page("pages/meus_registros.py")
