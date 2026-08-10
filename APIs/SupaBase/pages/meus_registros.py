import streamlit as st

from utils import db, sessao

PAGE_SIZE = 25

st.set_page_config(page_title="Meus Registros", layout="wide")

sessao.exigir_login()
sessao.botao_logout()
sessao.iniciar_pagina("meus_registros")

st.title("Justificativas")

col_add, _ = st.columns([1, 11])
with col_add:
    if st.button("＋ Adicionar", type="primary"):
        st.switch_page("pages/novo_registro.py")

id_usuario = st.session_state["usuario_id"]
registros = db.listar_meus_registros(id_usuario)

if not registros:
    st.info("Nenhum registro encontrado. Use o botão Adicionar para incluir.")
    st.stop()

justificativas = db.listar_justificativas()
areas = db.listar_areas()
id_para_just = {j["IdJustificativa"]: j["DescJustificativa"] for j in justificativas}
id_para_area = {a["IdAreaResponsavel"]: a["NomeAreaResponsavel"] for a in areas}


def fmt_datahora(valor) -> str:
    return valor.strftime("%d/%m/%Y %H:%M")


total_paginas = max(1, -(-len(registros) // PAGE_SIZE))
pagina = st.session_state.get("pagina_registros", 0)
if pagina >= total_paginas:
    pagina = total_paginas - 1
    st.session_state["pagina_registros"] = pagina

inicio = pagina * PAGE_SIZE
pagina_registros = registros[inicio : inicio + PAGE_SIZE]

col1, col2, col3 = st.columns([2, 2, 8])
with col1:
    if pagina > 0 and st.button("◀ Anterior"):
        st.session_state["pagina_registros"] = pagina - 1
        st.rerun()
with col2:
    if pagina < total_paginas - 1 and st.button("Próxima ▶"):
        st.session_state["pagina_registros"] = pagina + 1
        st.rerun()
with col3:
    st.caption(f"Página {pagina + 1} de {total_paginas} — {len(registros)} registros")

header = st.columns([2, 3.5, 2.5, 2, 1, 1])
for col, texto in zip(
    header,
    ["Pendência", "Justificativa", "Área Responsável", "Data/Hora", "", ""],
):
    col.markdown(f"**{texto}**")

editar_id = st.session_state.get("editar_id")
excluir_id = st.session_state.get("excluir_id")

for r in pagina_registros:
    cols = st.columns([2, 3.5, 2.5, 2, 1, 1])
    cols[0].write(f"**{r['NumeroPendencia']}**")
    cols[1].write(id_para_just.get(r["IdJustificativa"], "?"))
    cols[2].write(id_para_area.get(r["IdAreaResponsavel"], "?"))
    cols[3].write(fmt_datahora(r["DataHora"]))
    if cols[4].button("Editar", key=f"editar_{r['Id']}"):
        st.session_state["editar_id"] = r["Id"]
        st.session_state.pop("excluir_id", None)
        st.rerun()
    if cols[5].button("Excluir", key=f"excluir_{r['Id']}"):
        st.session_state["excluir_id"] = r["Id"]
        st.session_state.pop("editar_id", None)
        st.rerun()

registro_editar = next(
    (r for r in registros if r["Id"] == editar_id), None
) if editar_id else None

if registro_editar is not None:
    st.divider()
    st.subheader(f"Editar pendência {registro_editar['NumeroPendencia']}")
    opcoes_just = {j["DescJustificativa"]: j["IdJustificativa"] for j in justificativas}
    opcoes_area = {a["NomeAreaResponsavel"]: a["IdAreaResponsavel"] for a in areas}

    with st.form("form_edicao"):
        numero_pendencia = st.text_input(
            "Número da Pendência",
            value=str(registro_editar["NumeroPendencia"]),
        )
        justificativa = st.selectbox(
            "Justificativa",
            list(opcoes_just),
            index=list(opcoes_just).index(
                id_para_just[registro_editar["IdJustificativa"]]
            ),
        )
        area_responsavel = st.selectbox(
            "Área Responsável",
            list(opcoes_area),
            index=list(opcoes_area).index(
                id_para_area[registro_editar["IdAreaResponsavel"]]
            ),
        )
        salvar = st.form_submit_button("Salvar alterações", type="primary")

    if salvar:
        numero = numero_pendencia.strip()
        if not numero:
            st.error("O número da pendência é obrigatório.")
        else:
            try:
                numero = int(numero)
            except ValueError:
                st.error("O número da pendência deve ser um inteiro.")
            else:
                try:
                    db.atualizar_registro(
                        id_registro=registro_editar["Id"],
                        id_usuario=id_usuario,
                        numero_pendencia=numero,
                        id_justificativa=opcoes_just[justificativa],
                        id_area_responsavel=opcoes_area[area_responsavel],
                    )
                    st.session_state.pop("editar_id", None)
                    st.success("Registro atualizado.")
                    st.rerun()
                except db.PendenciaDuplicadaError as err:
                    st.error(str(err))
                except Exception as err:
                    st.error(f"Erro ao atualizar: {err}")

    if st.button("Cancelar edição"):
        st.session_state.pop("editar_id", None)
        st.rerun()

registro_excluir = next(
    (r for r in registros if r["Id"] == excluir_id), None
) if excluir_id else None

if registro_excluir is not None:
    st.divider()
    st.warning(
        f"Deseja excluir definitivamente a pendência "
        f"{registro_excluir['NumeroPendencia']}?"
    )
    c1, c2 = st.columns(2)
    if c1.button("Confirmar exclusão", type="primary"):
        db.excluir_registro(registro_excluir["Id"], id_usuario)
        st.session_state.pop("excluir_id", None)
        st.success("Registro excluído.")
        st.rerun()
    if c2.button("Cancelar"):
        st.session_state.pop("excluir_id", None)
        st.rerun()
