import hashlib
import html
import importlib
from pathlib import Path

import streamlit as st
from st_keyup import st_keyup
from zoneinfo import ZoneInfo

_MODULOS_UTILS = ("ui", "sessao", "db")
_RAIZ_APP = Path(__file__).resolve().parent
_ESTADO_ANTERIOR_MODULOS: dict[str, str] | None = None


def _assinatura_modulos() -> dict[str, str]:
    """Hash md5 do conteúdo dos módulos locais de utils/.

    Mais confiável que mtime+tamanho: detecta qualquer mudança de
    conteúdo, mesmo que um checkout do git preserve timestamps.
    """
    assinaturas: dict[str, str] = {}
    for nome in _MODULOS_UTILS:
        caminho = _RAIZ_APP / "utils" / f"{nome}.py"
        try:
            assinaturas[nome] = hashlib.md5(caminho.read_bytes()).hexdigest()
        except OSError:
            assinaturas[nome] = ""
    return assinaturas


def _recarregar_utils_se_necessario() -> None:
    """Recarrega os módulos locais quando os arquivos mudarem.

    O Streamlit re-executa o app.py a cada interação, mas módulos
    importados ficam em cache no sys.modules. Sem este recarregamento,
    edições em utils/ (ou um novo commit no Cloud) só valem após
    reiniciar o processo. O utils/banco.py é preservado de propósito:
    ele guarda o pool de conexões (reload o destruiria).
    """
    global _ESTADO_ANTERIOR_MODULOS
    atual = _assinatura_modulos()
    if _ESTADO_ANTERIOR_MODULOS is None or atual != _ESTADO_ANTERIOR_MODULOS:
        for nome in _MODULOS_UTILS:
            importlib.reload(importlib.import_module(f"utils.{nome}"))
        _ESTADO_ANTERIOR_MODULOS = atual


_recarregar_utils_se_necessario()

from utils import db, sessao, ui

PAGE_SIZE = 15
FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

st.set_page_config(page_title="Justificativas de Pendências", layout="wide")
ui.injetar_css()


def fmt_datahora(valor) -> str:
    if valor.tzinfo is None:
        from datetime import timezone

        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(FUSO_BRASIL).strftime("%d/%m/%Y %H:%M")


def _flash() -> None:
    msg = st.session_state.pop("_flash", None)
    if not msg:
        return
    tipo, texto = msg
    if tipo == "ok":
        st.success(texto)
    else:
        st.error(texto)


def _trocar_view(view: str) -> None:
    st.session_state["_view"] = view
    st.rerun()


def _busca_alterada() -> None:
    st.session_state["pagina_registros"] = 0


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------
def view_login() -> None:
    st.markdown(
        '<div class="login-hero">'
        f'{ui.logo_escuro_html()}'
        "<h1>Justificativas de Pendências</h1>"
        "<p>Acesse com seu e-mail corporativo.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    espaco, meio, espaco2 = st.columns([1, 1.4, 1])
    with meio:
        with st.container(border=True, key="login_card"):
            st.subheader("Entrar")
            with st.form("form_login"):
                email = st.text_input(
                    "Email", placeholder="seu.email@empresa.com"
                )
                senha = st.text_input("Senha", type="password", placeholder="••••••••")
                entrar = st.form_submit_button(
                    "Entrar", type="primary", use_container_width=True
                )

            if entrar:
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
                        sessao.fazer_login(
                            usuario["IdUsuario"], usuario["EmailUsuario"]
                        )
                        st.rerun()


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
def sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">'
            f'{ui.logo_html()}'
            "</div>",
            unsafe_allow_html=True,
        )

        email = st.session_state.get("usuario_email", "")
        st.markdown(
            '<div class="sidebar-user">'
            f'<span class="avatar">{ui.avatar(email)}</span>'
            '<div class="info">'
            '<div class="label">Usuário</div>'
            f'<div class="email">{email}</div>'
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Sair", key="nav_sair", use_container_width=True):
            sessao.fazer_logout()
            st.rerun()


# --------------------------------------------------------------------------
# Confirmacao de exclusao (modal)
# --------------------------------------------------------------------------
@st.dialog("Confirmar exclusão")
def confirmar_exclusao() -> None:
    rid = st.session_state.get("excluir_id")
    numero = st.session_state.get("excluir_numero", "")
    if rid is None:
        st.rerun()
    st.warning(
        f"Deseja excluir definitivamente a pendência **{numero}**? "
        "Essa ação não pode ser desfeita."
    )
    c1, c2 = st.columns(2)
    if c1.button("Excluir", type="primary", use_container_width=True):
        db.excluir_registro(rid, st.session_state["usuario_id"])
        st.session_state.pop("excluir_id", None)
        st.session_state.pop("excluir_numero", None)
        st.session_state["_flash"] = ("ok", "Registro excluído.")
        st.rerun()
    if c2.button("Cancelar", use_container_width=True):
        st.session_state.pop("excluir_id", None)
        st.session_state.pop("excluir_numero", None)
        st.rerun()


# --------------------------------------------------------------------------
# Meus Registros (linhas com Editar/Excluir e edicao inline)
# --------------------------------------------------------------------------
def view_registros() -> None:
    _flash()
    sessao.iniciar_pagina("registros")

    id_usuario = st.session_state["usuario_id"]
    termo = st.session_state.get("busca_registros", "").strip()

    total = db.contar_meus_registros(id_usuario, busca=termo or None)

    col_titulo, col_acao = st.columns([4, 1])
    with col_titulo:
        st.title("Meus Registros")
        if termo:
            st.caption(f"{total} resultado(s) para a busca")
        else:
            st.caption(f"{total} registro(s) justificado(s) por você")
    with col_acao:
        if st.button("＋ Novo Registro", type="primary", use_container_width=True):
            _trocar_view("novo")

    st_keyup(
        "Buscar",
        key="busca_registros",
        debounce=300,
        placeholder="Nº da pendência (número exato), justificativa, área ou data",
        label_visibility="collapsed",
        on_change=_busca_alterada,
    )

    if not total:
        if termo:
            st.markdown(
                '<div class="empty-state">'
                '<div class="icone">🔍</div>'
                "<h3>Nenhum registro encontrado</h3>"
                f"<p>Nenhum registro corresponde a <b>{html.escape(termo)}</b>. "
                "Ajuste o termo de busca ou use <b>＋ Novo Registro</b>.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="empty-state">'
                '<div class="icone">🗒️</div>'
                "<h3>Nenhum registro ainda</h3>"
                "<p>Use o botão <b>＋ Novo Registro</b> para incluir sua primeira "
                "pendência justificada.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
        return

    justificativas = db.listar_justificativas()
    areas = db.listar_areas()
    id_para_just = {
        j["IdJustificativa"]: j["DescJustificativa"] for j in justificativas
    }
    id_para_area = {a["IdAreaResponsavel"]: a["NomeAreaResponsavel"] for a in areas}
    opcoes_just = list(id_para_just.values())
    opcoes_area = list(id_para_area.values())

    total_paginas = max(1, -(-total // PAGE_SIZE))
    pagina = st.session_state.get("pagina_registros", 0)
    if pagina >= total_paginas:
        pagina = total_paginas - 1
        st.session_state["pagina_registros"] = pagina

    registros = db.listar_meus_registros(
        id_usuario,
        limite=PAGE_SIZE,
        deslocamento=pagina * PAGE_SIZE,
        busca=termo or None,
    )

    c_prev, c_info, c_next = st.columns([1, 2, 1])
    with c_prev:
        if st.button(
            "◀ Anterior",
            key="nav_prev",
            use_container_width=True,
            disabled=pagina == 0,
        ):
            st.session_state["pagina_registros"] = pagina - 1
            st.rerun()
    with c_info:
        st.markdown(
            f'<div style="text-align:center;" class="pag-info">'
            f"Página {pagina + 1} de {total_paginas} "
            f"· {total} registros</div>",
            unsafe_allow_html=True,
        )
    with c_next:
        if st.button(
            "Próxima ▶",
            key="nav_next",
            use_container_width=True,
            disabled=pagina >= total_paginas - 1,
        ):
            st.session_state["pagina_registros"] = pagina + 1
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

    header = st.columns([1, 3.5, 2.5, 1.8, 0.9, 0.9])
    for col, texto in zip(
        header,
        ["Pendência", "Justificativa", "Área Responsável", "Data/Hora", "", ""],
    ):
        col.markdown(f'<span class="row-header">{texto}</span>', unsafe_allow_html=True)

    editar_id = st.session_state.get("editar_id")

    for r in registros:
        if editar_id == r["Id"]:
            _linha_edicao(
                r, id_usuario, opcoes_just, opcoes_area, id_para_just, id_para_area
            )
        else:
            _linha_leitura(r, id_para_just, id_para_area)

    if st.session_state.get("excluir_id"):
        confirmar_exclusao()


def _linha_leitura(r: dict, id_para_just: dict, id_para_area: dict) -> None:
    justificativa = id_para_just.get(r["IdJustificativa"], "?")
    area = id_para_area.get(r["IdAreaResponsavel"], "?")
    with st.container(border=True):
        c1, c2, c3, c4, c5, c6 = st.columns([1, 3.5, 2.5, 1.8, 0.9, 0.9])
        c1.markdown(
            f'<span class="pend-num">{r["NumeroPendencia"]}</span>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<span class="pend-just">{justificativa}</span>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<span class="pend-area">{area}</span>',
            unsafe_allow_html=True,
        )
        c4.markdown(
            f'<span class="pend-data">{fmt_datahora(r["DataHora"])}</span>',
            unsafe_allow_html=True,
        )
        if c5.button("Editar", key=f"editar_{r['Id']}", use_container_width=True):
            st.session_state["editar_id"] = r["Id"]
            st.session_state.pop("excluir_id", None)
            st.rerun()
        if c6.button("Excluir", key=f"excluir_{r['Id']}", use_container_width=True):
            st.session_state["excluir_id"] = r["Id"]
            st.session_state["excluir_numero"] = r["NumeroPendencia"]
            st.session_state.pop("editar_id", None)
            st.rerun()


def _linha_edicao(
    r: dict,
    id_usuario: int,
    opcoes_just: list[str],
    opcoes_area: list[str],
    id_para_just: dict,
    id_para_area: dict,
) -> None:
    just_atual = id_para_just.get(r["IdJustificativa"])
    area_atual = id_para_area.get(r["IdAreaResponsavel"])

    try:
        idx_just = opcoes_just.index(just_atual)
    except ValueError:
        idx_just = 0
    try:
        idx_area = opcoes_area.index(area_atual)
    except ValueError:
        idx_area = 0

    with st.container(border=True):
        st.markdown(
            f'<span class="row-header">Editando pendência {r["NumeroPendencia"]}</span>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        numero = c1.text_input(
            "Nº Pendência",
            value=str(r["NumeroPendencia"]),
            key=f"ed_num_{r['Id']}",
        )
        justificativa = c2.selectbox(
            "Justificativa",
            opcoes_just,
            index=idx_just,
            key=f"ed_just_{r['Id']}",
        )
        area = c3.selectbox(
            "Área Responsável",
            opcoes_area,
            index=idx_area,
            key=f"ed_area_{r['Id']}",
        )

        c_ok, c_cancel = st.columns(2)
        salvar = c_ok.button(
            "Salvar alterações", type="primary", key=f"ed_salvar_{r['Id']}", use_container_width=True
        )
        cancelar = c_cancel.button(
            "Cancelar", key=f"ed_cancelar_{r['Id']}", use_container_width=True
        )

        if cancelar:
            st.session_state.pop("editar_id", None)
            st.rerun()

        if salvar:
            numero_limpo = numero.strip()
            if not numero_limpo:
                st.error("O número da pendência é obrigatório.")
            else:
                try:
                    numero_int = int(numero_limpo)
                except ValueError:
                    st.error("O número da pendência deve ser um inteiro.")
                else:
                    try:
                        db.atualizar_registro(
                            id_registro=r["Id"],
                            id_usuario=id_usuario,
                            numero_pendencia=numero_int,
                            id_justificativa=id_para_just[justificativa],
                            id_area_responsavel=id_para_area[area],
                        )
                        st.session_state.pop("editar_id", None)
                        st.session_state["_flash"] = ("ok", "Registro atualizado.")
                        st.rerun()
                    except db.PendenciaDuplicadaError as err:
                        st.error(str(err))
                    except Exception as err:
                        st.error(f"Erro ao atualizar: {err}")


# --------------------------------------------------------------------------
# Novo Registro
# --------------------------------------------------------------------------
def view_novo() -> None:
    _flash()
    visita = sessao.iniciar_pagina("novo")

    col_titulo, col_voltar = st.columns([4, 1])
    with col_titulo:
        st.title("Novo Registro")
        st.caption("Preencha os dados da pendência justificada.")
    with col_voltar:
        if st.button("← Voltar", key="voltar_novo", use_container_width=True):
            _trocar_view("registros")

    justificativas = db.listar_justificativas()
    areas = db.listar_areas()
    opcoes_just = list(dict.fromkeys(j["DescJustificativa"] for j in justificativas))
    opcoes_area = list(dict.fromkeys(a["NomeAreaResponsavel"] for a in areas))
    id_para_just = {
        j["DescJustificativa"]: j["IdJustificativa"] for j in justificativas
    }
    id_para_area = {
        a["NomeAreaResponsavel"]: a["IdAreaResponsavel"] for a in areas
    }

    with st.form("form_novo"):
        numero_pendencia = st.text_input(
            "Número da Pendência",
            key=f"novo_pendencia_{visita}",
            placeholder="Digite o número da pendência",
        )
        justificativa = st.selectbox(
            "Justificativa",
            opcoes_just,
            index=None,
            placeholder="Selecione a justificativa",
            key=f"novo_just_{visita}",
        )
        area_responsavel = st.selectbox(
            "Área Responsável",
            opcoes_area,
            index=None,
            placeholder="Selecione a área responsável",
            key=f"novo_area_{visita}",
        )
        salvar = st.form_submit_button(
            "Salvar registro", type="primary", use_container_width=True
        )

    if salvar:
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
                        id_justificativa=id_para_just[justificativa],
                        id_area_responsavel=id_para_area[area_responsavel],
                    )
                    st.session_state["_flash"] = (
                        "ok",
                        f"Pendência {numero} registrada com sucesso.",
                    )
                    _trocar_view("registros")
                except db.PendenciaDuplicadaError as err:
                    st.error(str(err))
                except Exception as err:
                    st.error(f"Erro ao salvar: {err}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
if st.session_state.get("logado"):
    sidebar()
    view = st.session_state.get("_view", "registros")
    if view == "novo":
        view_novo()
    else:
        view_registros()
else:
    view_login()
