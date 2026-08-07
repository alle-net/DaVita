import streamlit as st

from utils import db, sessao

st.set_page_config(page_title="Justificativas de Pendências", layout="wide")

st.title("Justificativas de Pendências")
st.caption("Registro de pendências por usuário — Supabase")

if st.session_state.get("logado"):
    st.success(f"Logado como {st.session_state.get('usuario_email')}")
    st.page_link("pages/novo_registro.py", label="Novo Registro", icon=":material/add_circle:")
    st.page_link("pages/meus_registros.py", label="Meus Registros", icon=":material/list_alt:")
    if st.button("Sair"):
        sessao.fazer_logout()
        st.rerun()
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
                st.rerun()
