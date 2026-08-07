import pandas as pd
import streamlit as st

from utils import db, sessao

st.set_page_config(page_title="Meus Registros", layout="wide")

sessao.exigir_login()
sessao.botao_logout()

st.title("Meus Registros")

id_usuario = st.session_state["usuario_id"]
registros = db.listar_meus_registros(id_usuario)

if not registros:
    st.info("Nenhum registro encontrado. Use a página Novo Registro para incluir.")
    st.stop()

justificativas = db.listar_justificativas()
areas = db.listar_areas()
id_para_just = {j["IdJustificativa"]: j["DescJustificativa"] for j in justificativas}
id_para_area = {a["IdAreaResponsavel"]: a["NomeAreaResponsavel"] for a in areas}

df = pd.DataFrame(registros)
df["Justificativa"] = df["IdJustificativa"].map(id_para_just)
df["Área Responsável"] = df["IdAreaResponsavel"].map(id_para_area)
df = df[
    ["Id", "NumeroPendencia", "Justificativa", "Área Responsável", "DataHora"]
]

st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Editar ou Excluir Registro")

opcoes = {
    f"Pendência {r['NumeroPendencia']} — {id_para_just.get(r['IdJustificativa'], '?')}": r
    for r in registros
}
escolha = st.selectbox("Selecione o registro", list(opcoes))
registro = opcoes[escolha]

opcoes_just = {j["DescJustificativa"]: j["IdJustificativa"] for j in justificativas}
opcoes_area = {a["NomeAreaResponsavel"]: a["IdAreaResponsavel"] for a in areas}

acao = st.radio("Ação", ["Editar", "Excluir"], horizontal=True)

if acao == "Editar":
    with st.form("form_edicao"):
        numero_pendencia = st.number_input(
            "Número da Pendência",
            min_value=1,
            step=1,
            format="%d",
            value=int(registro["NumeroPendencia"]),
        )
        justificativa = st.selectbox(
            "Justificativa",
            list(opcoes_just),
            index=list(opcoes_just).index(
                id_para_just[registro["IdJustificativa"]]
            ),
        )
        area_responsavel = st.selectbox(
            "Área Responsável",
            list(opcoes_area),
            index=list(opcoes_area).index(
                id_para_area[registro["IdAreaResponsavel"]]
            ),
        )
        salvar = st.form_submit_button("Salvar alterações", type="primary")

    if salvar:
        try:
            db.atualizar_registro(
                id_registro=registro["Id"],
                id_usuario=id_usuario,
                numero_pendencia=numero_pendencia,
                id_justificativa=opcoes_just[justificativa],
                id_area_responsavel=opcoes_area[area_responsavel],
            )
            st.success("Registro atualizado.")
            st.rerun()
        except db.PendenciaDuplicadaError:
            st.error(
                "Este número de pendência já foi justificado. "
                "Números de pendência não podem se repetir no banco."
            )
        except Exception as err:
            st.error(f"Erro ao atualizar: {err}")
else:
    confirmar = st.checkbox(
        f"Confirmo que desejo excluir a pendência {registro['NumeroPendencia']}."
    )
    if st.button("Excluir definitivamente", type="primary", disabled=not confirmar):
        db.excluir_registro(registro["Id"], id_usuario)
        st.success("Registro excluído.")
        st.rerun()
