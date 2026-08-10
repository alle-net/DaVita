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


def iniciar_pagina(pagina: str) -> int:
    """Registra a página aberta e devolve o contador de visitas.

    Cada vez que a página é (re)aberta o contador muda, permitindo que os
    widgets usem chaves baseadas nele e comecem sempre vazios.
    """
    if st.session_state.get("_pagina_atual") != pagina:
        st.session_state["_pagina_atual"] = pagina
        st.session_state[f"_visita_{pagina}"] = (
            st.session_state.get(f"_visita_{pagina}", 0) + 1
        )
    return st.session_state[f"_visita_{pagina}"]
