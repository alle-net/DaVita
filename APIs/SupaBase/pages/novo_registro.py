import streamlit as st

from utils import db, sessao

st.set_page_config(page_title="Novo Registro", layout="wide")

sessao.exigir_login()
sessao.botao_logout()
visita = sessao.iniciar_pagina("novo_registro")

st.title("Novo Registro")

justificativas = db.listar_justificativas()
areas = db.listar_areas()

opcoes_just = {j["DescJustificativa"]: j["IdJustificativa"] for j in justificativas}
opcoes_area = {a["NomeAreaResponsavel"]: a["IdAreaResponsavel"] for a in areas}

numero_pendencia = st.text_input(
    "Número da Pendência",
    key=f"novo_pendencia_{visita}",
    placeholder="Digite o número da pendência",
)
justificativa = st.selectbox(
    "Justificativa",
    list(opcoes_just),
    index=None,
    placeholder="Selecione a justificativa",
    key=f"novo_just_{visita}",
)
area_responsavel = st.selectbox(
    "Área Responsável",
    list(opcoes_area),
    index=None,
    placeholder="Selecione a área responsável",
    key=f"novo_area_{visita}",
)

if st.button("Salvar", type="primary"):
    erros = []
    if not numero_pendencia.strip():
        erros.append("O número da pendência é obrigatório.")
    if justificativa is None:
        erros.append("Selecione a justificativa.")
    if area_responsavel is None:
        erros.append("Selecione a área responsável.")
    if erros:
        for erro in erros:
            st.error(erro)
    else:
        try:
            numero = int(numero_pendencia.strip())
        except ValueError:
            st.error("O número da pendência deve ser um inteiro.")
        else:
            try:
                db.inserir_registro(
                    numero_pendencia=numero,
                    id_usuario=st.session_state["usuario_id"],
                    id_justificativa=opcoes_just[justificativa],
                    id_area_responsavel=opcoes_area[area_responsavel],
                )
                st.session_state.pop(f"novo_pendencia_{visita}", None)
                st.session_state.pop(f"novo_just_{visita}", None)
                st.session_state.pop(f"novo_area_{visita}", None)
                st.rerun()
            except db.PendenciaDuplicadaError as err:
                st.error(str(err))
            except Exception as err:
                st.error(f"Erro ao salvar: {err}")
