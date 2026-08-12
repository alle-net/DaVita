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
  --azul-900: #08203C;
  --azul-800: #0B2A4E;
  --azul-700: #0F3D6E;
  --azul-600: #0076B6;
  --azul-500: #1F8FD6;
  --azul-400: #4FA9E0;
  --azul-100: #D6EBF8;
  --azul-50: #EEF6FC;
  --fundo: #F2F6FB;
  --branco: #FFFFFF;
  --texto: #0F2438;
  --texto-suave: #5C7289;
  --borda: #DCE6F0;
  --perigo: #DC2626;
  --raio: 16px;
  --sombra: 0 1px 3px rgba(8,32,60,0.05), 0 8px 24px rgba(8,32,60,0.05);
}

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
}

.stApp {
  background:
    radial-gradient(1100px 520px at 88% -8%, rgba(0,118,182,0.10), transparent 62%),
    radial-gradient(900px 480px at -6% 108%, rgba(11,42,78,0.07), transparent 60%),
    linear-gradient(180deg, #F7FAFD 0%, #EDF4FA 100%);
  background-attachment: fixed;
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
  font-weight: 800 !important;
  letter-spacing: -0.025em;
}

.block-container h1::after {
  content: "";
  display: block;
  width: 64px;
  height: 4px;
  margin-top: 0.5rem;
  border-radius: 999px;
  background: linear-gradient(90deg, #0076B6, #4FA9E0);
}
.login-hero h1::after {
  display: none;
}

/* ===== Sidebar (degrade vertical) ===== */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0E4072 0%, #016FAE 100%);
  box-shadow: inset -1px 0 0 rgba(255,255,255,0.10);
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding: 1.5rem 1rem 1rem 1rem;
}
[data-testid="stSidebar"]::-webkit-scrollbar { width: 6px; }
[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.15); border-radius: 3px;
}

.sidebar-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
  padding: 0.4rem 0.2rem 1.3rem 0.2rem;
  border-bottom: 1px solid rgba(255,255,255,0.10);
  margin-bottom: 1.4rem;
  text-align: center;
  width: 100%;
}
.sidebar-brand .logo-img {
  max-width: 92%;
  max-height: 44px;
  width: auto;
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,0.35));
}
.sidebar-brand .logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--azul-600), var(--azul-500));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0,118,182,0.35);
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px;
  padding: 0.65rem 0.8rem;
  margin-bottom: 1.4rem;
  backdrop-filter: blur(4px);
}
.sidebar-user .avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1F8FD6, #7CC0E8);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,118,182,0.4);
}
.sidebar-user .info {
  min-width: 0;
}
.sidebar-user .info .label {
  color: #9FB8CE;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  font-weight: 600;
}
.sidebar-user .info .email {
  color: #EAF3FB;
  font-size: 12.5px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-testid="stSidebar"] .stButton button {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.13);
  border-radius: 12px;
  color: #DCE9F5;
  font-weight: 600;
  padding: 0.55rem 0.9rem;
  transition: all 0.18s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: rgba(255,255,255,0.13);
  border-color: rgba(255,255,255,0.22);
  color: #FFFFFF;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: linear-gradient(135deg, var(--azul-600), var(--azul-700));
  border-color: rgba(255,255,255,0.15);
  color: #fff;
  box-shadow: 0 4px 14px rgba(0,118,182,0.4);
}
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
  background: linear-gradient(135deg, var(--azul-500), var(--azul-600));
  border-color: rgba(255,255,255,0.25);
  transform: translateY(-1px);
}
[class*="st-key-nav_sair"] button {
  background: #8B0E0E !important;
  border: 1px solid rgba(255,255,255,0.25) !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  box-shadow: 0 4px 16px rgba(139,14,14,0.45) !important;
}
[class*="st-key-nav_sair"] button:hover {
  background: #A31212 !important;
  border-color: rgba(255,255,255,0.4) !important;
  box-shadow: 0 6px 20px rgba(139,14,14,0.55) !important;
  transform: translateY(-1px) !important;
}
[class*="st-key-nav_sair"] button:active {
  transform: translateY(0) !important;
}

/* ===== Botoes ===== */
.stButton button {
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.18s ease;
  outline: none;
}
.stButton button:active { transform: scale(0.97); }
.stButton button[kind="primary"] {
  background: linear-gradient(135deg, var(--azul-600), var(--azul-700));
  border: 1px solid rgba(0,118,182,0.3);
  box-shadow: 0 4px 14px rgba(0,118,182,0.28);
}
.stButton button[kind="primary"]:hover {
  background: linear-gradient(135deg, var(--azul-500), var(--azul-600));
  border-color: rgba(0,118,182,0.45);
  box-shadow: 0 6px 18px rgba(0,118,182,0.35);
  transform: translateY(-1px);
}

/* ===== Cards ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--branco);
  border: 1px solid var(--borda) !important;
  border-radius: var(--raio) !important;
  box-shadow: var(--sombra);
  transition: box-shadow 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(0,118,182,0.30) !important;
  box-shadow: 0 4px 10px rgba(8,32,60,0.05), 0 14px 32px rgba(8,32,60,0.08);
}

/* ===== Campos de entrada ===== */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
  border-radius: 10px !important;
  border-color: var(--borda) !important;
  background: #FBFDFE !important;
}
[data-testid="stTextInput"] input:hover,
[data-testid="stNumberInput"] input:hover,
[data-testid="stTextArea"] textarea:hover {
  border-color: #B9CDE0 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--azul-600) !important;
  box-shadow: 0 0 0 3px rgba(0,118,182,0.14) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
  border-radius: 10px !important;
  border-color: var(--borda) !important;
  background: #FBFDFE !important;
}

/* ===== Login ===== */
.st-key-login_card {
  max-width: 420px;
  margin: 1rem auto;
  position: relative;
}
.st-key-login_card [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 20px !important;
  border-color: rgba(0,118,182,0.14) !important;
  box-shadow: 0 2px 6px rgba(8,32,60,0.06), 0 20px 48px rgba(8,32,60,0.12);
  padding: 1.8rem 1.5rem 1.6rem;
  overflow: hidden;
}
.st-key-login_card [data-testid="stVerticalBlockBorderWrapper"]::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 5px;
  background: linear-gradient(90deg, #0076B6, #1F8FD6 55%, #7CC0E8);
}
.st-key-login_card [data-testid="stVerticalBlockBorderWrapper"] h2 {
  font-size: 1.35rem;
  margin-bottom: 0.9rem;
}

.login-hero {
  text-align: center;
  padding: 2.6rem 0 1rem;
}
.login-hero .login-logo {
  max-width: 210px;
  width: 100%;
  height: auto;
  margin-bottom: 0.9rem;
  object-fit: contain;
  filter: drop-shadow(0 6px 18px rgba(8,32,60,0.14));
}
.login-hero .tag {
  display: inline-block;
  background: var(--azul-50);
  color: var(--azul-600);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  padding: 0.32rem 0.95rem;
  border-radius: 999px;
  margin-bottom: 0.9rem;
  border: 1px solid rgba(0,118,182,0.15);
}
.login-hero h1 {
  margin-bottom: 0.5rem;
  font-size: 2.15rem;
  background: linear-gradient(120deg, #08203C 30%, #0076B6);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.login-hero p {
  color: var(--texto-suave);
  margin: 0;
  font-size: 0.98rem;
}

/* ===== Lista de registros ===== */
.row-header {
  color: #7E93AB;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.11em;
  padding: 0.2rem 0.15rem;
}
.pend-num {
  display: inline-block;
  background: var(--azul-50);
  border: 1px solid rgba(0,118,182,0.16);
  color: var(--azul-700);
  font-weight: 700;
  font-size: 0.92rem;
  padding: 0.22rem 0.7rem;
  border-radius: 8px;
}
.pend-data {
  color: var(--texto-suave);
  font-size: 0.85rem;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.pend-just {
  color: var(--texto);
  font-weight: 600;
  font-size: 0.93rem;
}
.pend-area {
  color: var(--texto-suave);
  font-size: 0.88rem;
}

[data-testid="stVerticalBlockBorderWrapper"] .stButton button {
  padding: 0.3rem 0.6rem;
  font-size: 0.78rem;
  border-radius: 9px;
}
[class*="st-key-editar_"] button {
  color: var(--azul-600) !important;
  border-color: rgba(0,118,182,0.30) !important;
  background: var(--azul-50) !important;
}
[class*="st-key-editar_"] button:hover {
  background: linear-gradient(135deg, #D6EBF8, #BFDFF2) !important;
  border-color: rgba(0,118,182,0.5) !important;
  color: var(--azul-800) !important;
  transform: translateY(-1px) !important;
}
[class*="st-key-excluir_"] button {
  color: var(--perigo) !important;
  border-color: rgba(220,38,38,0.28) !important;
  background: #FEF2F2 !important;
}
[class*="st-key-excluir_"] button:hover {
  background: linear-gradient(135deg, #EF4444, #B91C1C) !important;
  border-color: rgba(220,38,38,0.6) !important;
  color: #FFFFFF !important;
  transform: translateY(-1px) !important;
}

.empty-state {
  text-align: center;
  padding: 4rem 1rem;
}
.empty-state .icone {
  font-size: 2.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 25%, var(--azul-50), var(--azul-100));
  border: 1px solid rgba(0,118,182,0.15);
}
.empty-state h3 {
  margin: 1rem 0 0.35rem;
}
.empty-state p {
  color: var(--texto-suave);
  margin: 0;
}

.pag-info {
  color: var(--texto-suave);
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  background: var(--azul-50);
  border: 1px solid rgba(0,118,182,0.12);
  display: inline-block;
  padding: 0.3rem 0.9rem;
  border-radius: 999px;
}
[class*="st-key-nav_prev"] button,
[class*="st-key-nav_next"] button {
  border-color: rgba(0,118,182,0.35) !important;
  color: var(--azul-600) !important;
  background: #fff !important;
}
[class*="st-key-nav_prev"] button:hover,
[class*="st-key-nav_next"] button:hover {
  background: var(--azul-50) !important;
  border-color: rgba(0,118,182,0.55) !important;
  color: var(--azul-800) !important;
}
[class*="st-key-nav_prev"] button:disabled,
[class*="st-key-nav_next"] button:disabled {
  opacity: 0.45;
  box-shadow: none;
}

/* ===== Formulario ===== */
[data-testid="stForm"] {
  border: 1px solid var(--borda) !important;
  border-radius: var(--raio) !important;
  background: var(--branco);
  padding: 0.5rem 1.2rem 1.1rem !important;
  box-shadow: var(--sombra);
  overflow: hidden;
  position: relative;
}
[data-testid="stForm"]::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 5px;
  background: linear-gradient(90deg, #0076B6, #1F8FD6 55%, #7CC0E8);
}

.stCaption {
  color: var(--texto-suave);
}

/* ===== Rodapé da sessão ===== */
.st-key-nav_sair { margin-top: 1.4rem; }

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
    padding-top: 1.4rem;
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
