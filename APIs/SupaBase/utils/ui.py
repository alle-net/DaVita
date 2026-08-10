import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --azul: #1A73E8;
  --azul-hover: #1765CC;
  --azul-escuro: #0B2447;
  --azul-medio: #123B6D;
  --azul-suave: #E8F0FE;
  --fundo: #F5F7FA;
  --texto: #1F2A3D;
  --texto-suave: #64748B;
  --borda: #E3E8F0;
  --branco: #FFFFFF;
  --perigo: #D93025;
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
  padding-top: 1.4rem;
  padding-bottom: 3rem;
}

h1, h2, h3 {
  color: var(--azul-escuro) !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em;
}

/* ===== Sidebar azul ===== */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--azul-escuro) 0%, var(--azul-medio) 100%);
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding: 0.5rem 0.6rem 0 0.6rem;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.6rem 1rem 0.6rem;
  border-bottom: 1px solid rgba(255,255,255,0.14);
  margin-bottom: 1rem;
}
.sidebar-brand .logo {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: linear-gradient(135deg, #4FC3F7, #1A73E8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 15px;
  color: #fff;
  flex-shrink: 0;
}
.sidebar-brand .nome {
  color: #FFFFFF;
  font-weight: 700;
  font-size: 15px;
  line-height: 1.2;
}
.sidebar-brand .sub {
  color: #9DB8DC;
  font-size: 11px;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px;
  padding: 0.55rem 0.7rem;
  margin-bottom: 1rem;
}
.sidebar-user .avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--azul);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sidebar-user .info {
  min-width: 0;
}
.sidebar-user .info .label {
  color: #9DB8DC;
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
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.16);
  border-radius: 10px;
  color: #EAF2FB;
  font-weight: 600;
  padding: 0.6rem 0.9rem;
  transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: rgba(255,255,255,0.16);
  border-color: rgba(255,255,255,0.28);
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: var(--azul);
  border-color: var(--azul);
  color: #fff;
}
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
  background: var(--azul-hover);
}
[class*="st-key-nav_sair"] button {
  background: rgba(217,48,37,0.16) !important;
  border-color: rgba(217,48,37,0.45) !important;
  color: #FFB4AB !important;
}

/* ===== Botoes gerais ===== */
.stButton button {
  border-radius: 10px;
  font-weight: 600;
}
.stButton button[kind="primary"] {
  background: var(--azul);
  border: 1px solid var(--azul);
}
.stButton button[kind="primary"]:hover {
  background: var(--azul-hover);
  border-color: var(--azul-hover);
}

/* ===== Cards (containers com borda) ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--branco);
  border: 1px solid var(--borda) !important;
  border-radius: 14px !important;
  box-shadow: 0 1px 3px rgba(16,42,84,0.05);
}

/* ===== Login ===== */
.st-key-login_card {
  max-width: 420px;
  margin: 1rem auto;
}
.st-key-login_card [data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 18px !important;
  box-shadow: 0 10px 30px rgba(11,36,71,0.10);
  padding: 1.1rem 1rem;
}

.login-hero {
  text-align: center;
  padding: 1.8rem 0 0.6rem;
}
.login-hero .tag {
  display: inline-block;
  background: var(--azul-suave);
  color: var(--azul);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0.3rem 0.8rem;
  border-radius: 999px;
  margin-bottom: 0.7rem;
}
.login-hero h1 {
  margin-bottom: 0.3rem;
}
.login-hero p {
  color: var(--texto-suave);
  margin: 0;
}

/* ===== Lista de registros ===== */
.row-header {
  color: var(--texto-suave);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.09em;
}
.pend-num {
  color: var(--azul-escuro);
  font-weight: 800;
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
  color: var(--azul) !important;
  border-color: rgba(26,115,232,0.4) !important;
  background: var(--azul-suave) !important;
}
[class*="st-key-excluir_"] button {
  color: var(--perigo) !important;
  border-color: rgba(217,48,37,0.4) !important;
  background: #FDECEA !important;
}
[class*="st-key-excluir_"] button:hover {
  background: #FBD7D4 !important;
}

.empty-state {
  text-align: center;
  padding: 3.5rem 1rem;
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
  border-color: rgba(26,115,232,0.45) !important;
  color: var(--azul) !important;
  background: #fff !important;
}

/* ===== Formularios ===== */
[data-testid="stForm"] {
  border: 1px solid var(--borda) !important;
  border-radius: 14px !important;
  background: var(--branco);
  padding: 0.4rem 1rem 0.9rem !important;
}

.stCaption {
  color: var(--texto-suave);
}

/* ===== Responsivo ===== */
@media (max-width: 900px) {
  .block-container {
    padding: 1rem 0.75rem 2.5rem;
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
    padding-top: 1rem;
  }
}
</style>
"""


def injetar_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def avatar(email: str) -> str:
    nome = (email or "U").strip().upper()
    return nome[0] if nome else "U"
