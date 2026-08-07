import streamlit as st


def exigir_login() -> None:
    if not st.session_state.get("logado"):
        st.switch_page("app.py")


def fazer_login(usuario_id: int, email: str) -> None:
    st.session_state["logado"] = True
    st.session_state["usuario_id"] = usuario_id
    st.session_state["usuario_email"] = email


def fazer_logout() -> None:
    st.session_state.clear()


def botao_logout() -> None:
    with st.sidebar:
        st.write(f"Usuário: **{st.session_state.get('usuario_email', '')}**")
        if st.button("Sair"):
            fazer_logout()
            st.rerun()
