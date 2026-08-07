import streamlit as st

from utils import db, sessao

st.set_page_config(page_title="Novo Registro", layout="wide")

sessao.exigir_login()
sessao.botao_logout()

st.title("Novo Registro")

justificativas = db.listar_justificativas()
areas = db.listar_areas()

opcoes_just = {j["DescJustificativa"]: j["IdJustificativa"] for j in justificativas}
opcoes_area = {a["NomeAreaResponsavel"]: a["IdAreaResponsavel"] for a in areas}

numero_pendencia = st.number_input(
    "Número da Pendência", min_value=1, step=1, format="%d", value=1
)
justificativa = st.selectbox("Justificativa", list(opcoes_just))
area_responsavel = st.selectbox("Área Responsável", list(opcoes_area))

if st.button("Salvar", type="primary"):
    try:
        db.inserir_registro(
            numero_pendencia=numero_pendencia,
            id_usuario=st.session_state["usuario_id"],
            id_justificativa=opcoes_just[justificativa],
            id_area_responsavel=opcoes_area[area_responsavel],
        )
        st.success(f"Pendência {numero_pendencia} registrada com sucesso.")
    except db.PendenciaDuplicadaError:
        st.error(
            "Este número de pendência já foi justificado. "
            "Números de pendência não podem se repetir no banco."
        )
    except Exception as err:
        st.error(f"Erro ao salvar: {err}")
