import base64
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_LOGO_CLARO = RAIZ / "imagens" / "Logo Claro.png"
CAMINHO_LOGO_ESCURO = RAIZ / "imagens" / "Logo Escuro.png"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --azul-900: #0A2540;
  --azul-800: #14315C;
  --azul-700: #1D4ED8;
  --azul-600: #2563EB;
  --azul-500: #3B82F6;
  --azul-100: #DBEAFE;
  --azul-50: #EFF6FF;
  --fundo: #F8FAFC;
  --branco: #FFFFFF;
  --texto: #0F172A;
  --texto-suave: #64748B;
  --borda: #E2E8F0;
  --perigo: #DC2626;
}

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
  background: var(--fundo);
}

[data-testid="stHeader"] {
  background: transparent;
}

.block-container {
  max-width: 1440px;
  padding-top: 2.2rem;
  padding-bottom: 3.5rem;
}

h1, h2, h3 {
  color: var(--azul-900) !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
}

/* ===== Sidebar ===== */
[data-testid="stSidebar"] {
  background: #0076B6;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding: 1.2rem 1rem 0 1rem;
}

.sidebar-brand {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.4rem 0.2rem 1.1rem 0.2rem;
  border-bottom: 1px solid rgba(255,255,255,0.12);
  margin-bottom: 1.2rem;
  text-align: center;
  width: 100%;
}
.sidebar-brand .logo-img {
  max-width: 100%;
  max-height: 44px;
  width: auto;
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.15));
}
.sidebar-brand .logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--azul-600);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  color: #fff;
  flex-shrink: 0;
}
.sidebar-brand .nome {
  color: #FFFFFF;
  font-weight: 600;
  font-size: 15px;
  line-height: 1.3;
}
.sidebar-brand .sub {
  color: #8FA8C8;
  font-size: 11px;
  letter-spacing: 0.02em;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 0.6rem 0.75rem;
  margin-bottom: 1.2rem;
}
.sidebar-user .avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--azul-500);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sidebar-user .info {
  min-width: 0;
}
.sidebar-user .info .label {
  color: #8FA8C8;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.sidebar-user .info .email {
  color: #EAF2FB;
  font-size: 12.5px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-testid="stSidebar"] .stButton button {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 10px;
  color: #EAF2FB;
  font-weight: 600;
  padding: 0.55rem 0.9rem;
  transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: rgba(255,255,255,0.14);
  border-color: rgba(255,255,255,0.24);
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: var(--azul-600);
  border-color: var(--azul-600);
  color: #fff;
}
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
  background: var(--azul-700);
  border-color: var(--azul-700);
}
[class*="st-key-nav_sair"] button {
  background: #DC2626 !important;
  border: 1px solid #DC2626 !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 10px rgba(220,38,38,0.40) !important;
}
[class*="st-key-nav_sair"] button:hover {
  background: #B91C1C !important;
  border-color: #B91C1C !important;
  box-shadow: 0 4px 14px rgba(220,38,38,0.55) !important;
  transform: translateY(-1px);
}

/* ===== Botoes ===== */
.stButton button {
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.15s ease;
}
.stButton button[kind="primary"] {
  background: var(--azul-600);
  border: 1px solid var(--azul-600);
}
.stButton button[kind="primary"]:hover {
  background: var(--azul-700);
  border-color: var(--azul-700);
}

/* ===== Cards ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--branco);
  border: 1px solid var(--borda) !important;
  border-radius: 14px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  transition: box-shadow 0.15s ease;
}

/* ===== Campos de entrada ===== */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
  border-radius: 10px !important;
  border-color: var(--borda) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--azul-500) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
  border-radius: 10px !important;
  border-color: var(--borda) !important;
}

/* ===== Login ===== */
.st-key-login_card {
  max-width: 420px;
  margin: 1.2rem auto;
}
.st-key-login_card [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px !important;
  box-shadow: 0 8px 24px rgba(10,37,64,0.08);
  padding: 1.4rem 1.2rem;
}

.login-hero {
  text-align: center;
  padding: 2.4rem 0 0.8rem;
}
.login-hero .login-logo {
  max-width: 210px;
  width: 100%;
  height: auto;
  margin-bottom: 0.6rem;
  object-fit: contain;
}
.login-hero .tag {
  display: inline-block;
  background: var(--azul-50);
  color: var(--azul-600);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0.3rem 0.85rem;
  border-radius: 999px;
  margin-bottom: 0.8rem;
}
.login-hero h1 {
  margin-bottom: 0.4rem;
  font-size: 2rem;
}
.login-hero p {
  color: var(--texto-suave);
  margin: 0;
}

/* ===== Lista de registros ===== */
.row-header {
  color: var(--texto-suave);
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
}
.pend-num {
  color: var(--azul-900);
  font-weight: 700;
  font-size: 1rem;
}
.pend-data {
  color: var(--texto-suave);
  font-size: 0.85rem;
  white-space: nowrap;
}
.pend-just {
  color: var(--texto);
  font-weight: 500;
}
.pend-area {
  color: var(--texto-suave);
}

[data-testid="stVerticalBlockBorderWrapper"] .stButton button {
  padding: 0.28rem 0.55rem;
  font-size: 0.78rem;
  border-radius: 8px;
}
[class*="st-key-editar_"] button {
  color: var(--azul-600) !important;
  border-color: rgba(37,99,235,0.35) !important;
  background: var(--azul-50) !important;
}
[class*="st-key-editar_"] button:hover {
  background: var(--azul-100) !important;
}
[class*="st-key-excluir_"] button {
  color: var(--perigo) !important;
  border-color: rgba(220,38,38,0.35) !important;
  background: #FEF2F2 !important;
}
[class*="st-key-excluir_"] button:hover {
  background: #FEE2E2 !important;
}

.empty-state {
  text-align: center;
  padding: 4rem 1rem;
}
.empty-state .icone {
  font-size: 2.6rem;
}
.empty-state h3 {
  margin: 0.8rem 0 0.3rem;
}
.empty-state p {
  color: var(--texto-suave);
  margin: 0;
}

.pag-info {
  color: var(--texto-suave);
  font-size: 0.85rem;
}
[class*="st-key-nav_prev"] button,
[class*="st-key-nav_next"] button {
  border-color: rgba(37,99,235,0.4) !important;
  color: var(--azul-600) !important;
  background: #fff !important;
}

/* ===== Formulario ===== */
[data-testid="stForm"] {
  border: 1px solid var(--borda) !important;
  border-radius: 14px !important;
  background: var(--branco);
  padding: 0.4rem 1.1rem 1rem !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}

.stCaption {
  color: var(--texto-suave);
}

/* ===== Responsivo ===== */
@media (max-width: 900px) {
  .block-container {
    padding: 1.2rem 0.75rem 2.5rem;
  }
  [data-testid="stColumn"] {
    min-width: 100% !important;
    width: 100% !important;
    flex: 0 0 100% !important;
  }
  .st-key-login_card {
    margin: 0.6rem auto;
  }
  .login-hero {
    padding-top: 1.2rem;
  }
}
</style>
"""


def injetar_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False, max_entries=4)
def _logo_base64(caminho: Path) -> str | None:
    if caminho.is_file():
        return base64.b64encode(caminho.read_bytes()).decode("ascii")
    return None


def logo_html() -> str:
    """Logo claro (sidebar, fundo azul). Fallback: quadrado com letra J."""
    dados = _logo_base64(CAMINHO_LOGO_CLARO)
    if dados:
        return (
            '<img class="logo-img" src="data:image/png;base64,'
            f'{dados}" alt="DaVita">'
        )
    return '<span class="logo">J</span>'


def logo_escuro_html() -> str:
    """Logo escuro (tela de login, fundo claro). Fallback: tag de texto."""
    dados = _logo_base64(CAMINHO_LOGO_ESCURO)
    if dados:
        return (
            '<img class="login-logo" src="data:image/png;base64,'
            f'{dados}" alt="DaVita">'
        )
    return '<span class="tag">Controle de Pendências</span>'


def avatar(email: str) -> str:
    nome = (email or "U").strip().upper()
    return nome[0] if nome else "U"
