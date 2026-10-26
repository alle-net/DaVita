import json
import logging
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

# ── Auto-detect venv ────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent

LOG = logging.getLogger("tasy_1059")
if not LOG.handlers:
    LOG.setLevel(logging.INFO)
    LOG.propagate = False
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setFormatter(logging.Formatter("%(message)s"))
    LOG.addHandler(_console_handler)

_VENV_PYTHON = _SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
if sys.prefix == sys.base_prefix and _VENV_PYTHON.exists():
    # Não estamos no venv — relança com o Python do venv
    LOG.info(f"[VENV] Reinterpretando com {_VENV_PYTHON} ...")
    result = subprocess.run([str(_VENV_PYTHON)] + sys.argv, cwd=str(_SCRIPT_DIR))
    raise SystemExit(result.returncode)
# ─────────────────────────────────────────────────────────────────────────────

if not any(isinstance(h, logging.FileHandler) for h in LOG.handlers):
    try:
        _log_dir = _SCRIPT_DIR / "output"
        _log_dir.mkdir(exist_ok=True)
        _file_handler = logging.FileHandler(_log_dir / "tasy_1059.log", encoding="utf-8")
        _file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        LOG.addHandler(_file_handler)
    except Exception:
        pass

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from certificado_handler import NativeDialogHandler

BASE_DIR = Path(__file__).resolve().parent
PARAMS_PATH = BASE_DIR / "parametros.json"
OUTPUT_DIR = BASE_DIR / "output"
_RELATORIO_CODIGO_DEFAULT = "1059"
RELATORIO_CODIGO = _RELATORIO_CODIGO_DEFAULT


def pasta_downloads_1059(limpar: bool = False) -> Path:
    """Pasta 1059 na area de Downloads. Se ja existe e limpar=True, apaga
    todos os arquivos dentro dela; se nao existe, cria."""
    p = Path.home() / "Downloads" / "1059"
    p.mkdir(parents=True, exist_ok=True)
    if limpar:
        apagados = 0
        for f in p.iterdir():
            try:
                if f.is_file() or f.is_symlink():
                    f.unlink()
                    apagados += 1
            except Exception:
                pass
        LOG.info(f"[ARQ] Pasta 1059 limpa: {apagados} arquivo(s) removido(s)")
    return p


def sanitizar_nome(nome: str) -> str:
    n = re.sub(r"[\\/:*?\"<>|]+", "_", nome.strip())
    n = re.sub(r"\s+", " ", n).strip()
    return n[:120] if n else "estabelecimento"


def norm_nome(s: str) -> str:
    """Normaliza p/ comparacao: minusculas, espacos colapsados, sem acento."""
    s = " ".join((s or "").split()).lower()
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def safe_click(driver, el) -> bool:
    try:
        el.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False


def clicar_por_texto(driver, timeout: int, *textos, tag: str = "button") -> bool:
    """Clica no primeiro elemento visivel cujo texto exato (case-insensitive) bata."""
    # Otimizacao: tag="*" varria o DOM inteiro (//*) 2x por passada — muito
    # lento na home do Tasy. Agora tenta tags clicaveis primeiro.
    tags = ["a", "button", "div", "span", "li"] if tag == "*" else [tag]
    deadline = time.time() + timeout
    while time.time() < deadline:
        for t in tags:
            for txt in textos:
                try:
                    els = driver.find_elements(
                        By.XPATH,
                        f"//{t}[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='{txt.lower()}']",
                    )
                    for el in els:
                        try:
                            if el.is_displayed() and el.is_enabled() and safe_click(driver, el):
                                LOG.info(f"[NAV] Clicado {t} '{txt}'")
                                return True
                        except Exception:
                            continue
                except Exception:
                    pass
        # fallback parcial: contem o texto (so nas mesmas tags)
        for t in tags:
            for txt in textos:
                try:
                    els = driver.find_elements(By.XPATH, f"//{t}[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{txt.lower()}')]")
                    for el in els:
                        try:
                            if el.is_displayed() and el.is_enabled() and safe_click(driver, el):
                                LOG.info(f"[NAV] Clicado {t} (contem) '{txt}'")
                                return True
                        except Exception:
                            continue
                except Exception:
                    pass
        time.sleep(0.3)
    return False


def load_params() -> dict:
    with open(PARAMS_PATH, encoding="utf-8-sig") as f:
        return json.load(f)


def _codigo_relatorio(extracao_cfg: dict | None = None) -> str:
    """Codigo do 1059 vindo de extracao.relatorio_codigo_1059 (default 1059)."""
    if extracao_cfg is None:
        extracao_cfg = load_params().get("extracao", {})
    codigo = str(extracao_cfg.get("relatorio_codigo_1059", "") or "").strip()
    return codigo or _RELATORIO_CODIGO_DEFAULT


def make_driver(timeout: int) -> webdriver.Edge:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    # Suprime bubble "Bloquear/Permitir — Acessar outros aplicativos"
    # (permissao de protocolo externo / app). Auto-nega sem exibir o bubble.
    options.add_argument("--deny-permission-prompts")
    options.add_argument("--disable-features=PermissionChip,PermissionPredictionService")
    dl_dir = str(Path.home() / "Downloads")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.protocol_handler": 2,
        "download.default_directory": dl_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        # 18/09: o .xls do Tasy (TSV com extensao falsa) cai no bloqueio
        # "nao foi possivel verificar virus" do Edge/SmartScreen. Origem e
        # conhecida (digisystem.cloud), entao desliga a verificacao p/ nao
        # faltar arquivo. Revisar se o RPA passar a baixar de outras fontes.
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True,
    })
    options.add_argument("--safebrowsing-disable-download-protection")
    options.add_argument(
        '--auto-select-certificate-for-urls=' + json.dumps([
            {
                "pattern": "https://cert.sso.davita.com/*",
                "filter": {
                    "ISSUER": {"CN": "DaVita.corp Intermediate CA"}
                },
            }
        ])
    )
    options.page_load_strategy = "none"
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(timeout)
    driver.command_executor.set_timeout(min(timeout, 10))
    return driver


def find_element(driver, timeout: int, *locators, per_locator: float = 2.0):
    """Busca rapida: timeout total respeitado, cada locator tenta no max per_locator."""
    deadline = time.time() + timeout
    for by, value in locators:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        try:
            element = WebDriverWait(driver, min(per_locator, remaining)).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except Exception:
            continue
    return None


def is_driver_alive(driver) -> bool:
    """Retorna False se o usuario fechou o navegador / sessao caiu."""
    try:
        _ = driver.window_handles
        return True
    except Exception:
        return False


_SHOTS_SUCESSO = False  # main() liga via automacao.fotos_sucesso (default: so erros)


def take_screenshot(driver, name: str, force: bool = False) -> Path | None:
    # Otimizacao 18/09: em rodada normal so erros (nome erro_*) geram PNG.
    if not force and not _SHOTS_SUCESSO and not name.startswith("erro_"):
        return None
    try:
        if not is_driver_alive(driver):
            return None
    except Exception:
        return None
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUTPUT_DIR / f"{name}_{stamp}.png"
        driver.save_screenshot(str(path))
        return path
    except (InvalidSessionIdException, WebDriverException, OSError, ConnectionError):
        return None
    except Exception:
        return None


def click_ok_in_popup(driver, timeout: int = 2) -> bool:
    # 1 wait unico para checkbox (curto, nao bloqueia)
    try:
        checkbox = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, "do-not-ask-again"))
        )
        if not checkbox.is_selected():
            try:
                checkbox.click()
            except Exception:
                pass
    except Exception:
        pass

    # 1 wait unico com UNION de XPaths (ok/okay/fechar) — em vez de 4+ waits
    xpath_union = (
        "//button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='ok']"
        " | //button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='okay']"
        " | //button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='fechar']"
        " | //button[contains(@class,'gwt-Button')]"
    )
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath_union))
        )
        btn.click()
        return True
    except Exception:
        return False


def close_recorded_dialog(driver, timeout: int = 2) -> bool:
    """Fecha o dialogo HTML registrado durante a navegacao manual."""
    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "#ngdialog1 tasy-wdlgpanel-button button.gwt-Button.btn-gray",
                )
            )
        )
        if button.text.strip().lower() == "fechar":
            button.click()
            LOG.info("[INFO] Dialogo HTML registrado fechado")
            return True
    except Exception:
        pass
    return False


def fechar_popups_pos_login(driver, timeout_total: int = 15, per_wait: float = 1.0) -> int:
    """Fechador generico dos 2 popups pos-login (ngdialog / gwt / dialog).

    Estrategia sem waits longos: usa find_elements (retorno imediato) em loop
    ate timeout_total, fechando em sequencia. Retorna qtd fechada.
    Nao mexe no fluxo de login — so fecha o que estiver visivel.
    """
    xpath_botoes = (
        "//button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='fechar']"
        " | //button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='ok']"
        " | //button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='okay']"
        " | //button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='entendi']"
    )
    css_close_icons = [
        ".ngdialog-close",
        "[class*='ngdialog-close']",
        "[class*='dialog-close']",
        "button[aria-label='Fechar']",
        "button[aria-label='Close']",
        "[title='Fechar']",
    ]
    deadline = time.time() + timeout_total
    fechados = 0
    passadas_sem_popup = 0
    while time.time() < deadline:
        if not is_driver_alive(driver):
            break
        clicou_nesta_passada = False
        # Marca "nao perguntar / nao perguntar novamente" por ID ou por texto
        # (TasyNative usa checkbox sem id, so com label "Não perguntar novamente")
        try:
            for cb in driver.find_elements(By.XPATH, "//input[@type='checkbox']"):
                try:
                    if not cb.is_displayed():
                        continue
                    marcar = False
                    if cb.get_attribute("id") == "do-not-ask-again":
                        marcar = True
                    else:
                        try:
                            label_txt = (
                                cb.find_element(By.XPATH, "./following-sibling::*[1]").text
                                + " " + cb.find_element(By.XPATH, "./parent::*").text
                            ).lower()
                            if "n" in label_txt and "perguntar" in label_txt:
                                marcar = True
                        except Exception:
                            pass
                    if marcar and not cb.is_selected():
                        cb.click()
                        LOG.info("[POPUP] Checkbox 'nao perguntar' marcado")
                except Exception:
                    pass
        except Exception:
            pass
        # Diagnostico: despeja botoes visiveis 1x por passada sem popup fechado
        # (ajuda a mapear o seletor exato do TasyNative)
        # 1) Botoes Fechar/OK/gwt — texto manda, independente de ancestor
        # (o TasyNative nao usa ngdialog/gwt-Button, entao a trava antiga
        # impedia o clique; agora texto esperado sempre fecha)
        try:
            botoes = driver.find_elements(By.XPATH, xpath_botoes)
        except Exception:
            botoes = []
        for btn in botoes:
            try:
                if not btn.is_displayed() or not btn.is_enabled():
                    continue
                txt = (btn.text or "").strip().lower()
                # Restrito a textos exatos (evita falso positivo 'copiar url')
                if txt not in ("fechar", "ok", "okay", "entendi"):
                    continue
                # Nunca clicar em "Abrir o processo de download" (nao esta no xpath)
                try:
                    btn.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", btn)
                fechados += 1
                clicou_nesta_passada = True
                LOG.info(f"[POPUP] Fechado ({fechados}): '{txt or btn.get_attribute('class')}'")
                time.sleep(1.0)
                break  # revarre a pagina para pegar o 2o popup em sequencia
            except Exception:
                continue
        if clicou_nesta_passada:
            passadas_sem_popup = 0
            continue
        # 2) Icones X de fechar (sem wait)
        for css in css_close_icons:
            try:
                for el in driver.find_elements(By.CSS_SELECTOR, css):
                    try:
                        if el.is_displayed() and el.is_enabled():
                            try:
                                el.click()
                            except Exception:
                                driver.execute_script("arguments[0].click();", el)
                            fechados += 1
                            clicou_nesta_passada = True
                            LOG.info(f"[POPUP] Fechado via icone ({fechados}): '{css}'")
                            time.sleep(1.0)
                            break
                    except Exception:
                        continue
                if clicou_nesta_passada:
                    break
            except Exception:
                continue
        if clicou_nesta_passada:
            passadas_sem_popup = 0
            continue
        passadas_sem_popup += 1
        # Early-exit: 2 passadas seguidas sem nada = sem mais popups.
        # Evita ficar parado os 15s cheios apos fechar (era a lentidao pos-popup).
        if passadas_sem_popup >= 2:
            break
        time.sleep(per_wait)
    return fechados


def diagnosticar_popups(driver, tag: str) -> None:
    """Lista botoes/inputs visiveis para mapear o seletor exato (TasyNative)."""
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        path = OUTPUT_DIR / "diagnostico_popups.txt"
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n===== {tag} {datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
            for btn in driver.find_elements(By.XPATH, "//button | //input[@type='checkbox'] | //a[contains(@class,'close')]"):
                try:
                    if not btn.is_displayed():
                        continue
                    f.write(
                        f"tag={btn.tag_name} text={(btn.text or '').strip()[:80]!r} "
                        f"id={btn.get_attribute('id')!r} class={btn.get_attribute('class')!r}\n"
                    )
                except Exception:
                    continue
        LOG.info(f"[DIAG] Botoes visiveis registrados em {path.name}")
    except Exception as e:
        LOG.info(f"[DIAG] Falha no diagnostico: {e}")


def handle_user_selection(driver, timeout: int = 2) -> bool:
    """Trata tela de seleção de usuário pós-login (versao rapida, 1-2 waits)."""
    try:
        user_select = find_element(
            driver,
            1,
            (By.XPATH, "//select[contains(@id,'user') or contains(@name,'user')]"),
            (By.CSS_SELECTOR, "select"),
            per_locator=1.0,
        )
        if user_select:
            LOG.info("[INFO] Dropdown de usuário encontrado, selecionando...")
            from selenium.webdriver.support.ui import Select
            try:
                Select(user_select).select_by_index(1)
                time.sleep(0.5)
            except Exception:
                pass

        xpath_union = (
            "//button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='ok']"
            " | //button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='confirmar']"
            " | //button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='avançar']"
            " | //button[contains(@class,'gwt-Button')]"
        )
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath_union))
        )
        btn.click()
        LOG.info("[INFO] Botão de confirmação clicado na seleção de usuário")
        return True
    except Exception:
        return False


def carregar_estabelecimentos() -> list:
    """Le ListaEstabelecimentos.xlsx (aba Lista). Retorna [{nome}].

    Periodo agora e GLOBAL em parametros.json > extracao.periodo
    (data_inicio/data_fim) para reuso entre fluxos. Colunas inicio/fim
    na planilha sao ignoradas se ainda existirem.
    """
    import pandas as pd

    params = load_params()
    entrada = params.get("entrada", {})
    xlsx = BASE_DIR / entrada.get("arquivo_estabelecimentos", "ListaEstabelecimentos.xlsx")
    # Nome da aba case-insensitive ('lista' vs 'Lista')
    aba_cfg = (entrada.get("planilha", "lista") or "lista")
    try:
        xls_abas = pd.ExcelFile(xlsx)
        real = next((s for s in xls_abas.sheet_names if s.lower() == aba_cfg.lower()), aba_cfg)
    except Exception:
        real = aba_cfg
    df = pd.read_excel(xlsx, sheet_name=real)
    df.columns = [str(c).strip() for c in df.columns]
    # Coluna de nome: tenta ds_estabelecimento ou primeira coluna
    col_nome = None
    for cand in ("ds_estabelecimento", "estabelecimento", "nome", "unidade"):
        for c in df.columns:
            if c.lower() == cand:
                col_nome = c
                break
    if col_nome is None:
        col_nome = df.columns[0]

    lista = []
    for _, row in df.iterrows():
        nome = str(row[col_nome]).strip()
        if not nome or nome.lower() == "nan":
            continue
        lista.append({"nome": nome})
    LOG.info(f"[DADOS] {len(lista)} estabelecimentos carregados de {xlsx.name}")
    return lista


def navegar_ate_relatorio_1059(driver, timeout: int = 20) -> bool:
    """Passos 1-6: Utilitarios > Impressao de relatorios > codigo configurado > filtro > abrir."""
    codigo = RELATORIO_CODIGO
    LOG.info(f"[5/7] Navegando ate impressao de relatorios (codigo {codigo})...")
    take_screenshot(driver, "05a_home")
    # 1) Aba Utilitarios (direto, timeout curto)
    if not clicar_por_texto(driver, 5, "Utilitários", "Utilitarios", tag="*"):
        LOG.info("[ERRO] Aba Utilitarios nao encontrada")
        take_screenshot(driver, "erro_aba_utilitarios")
        return False
    time.sleep(1.0)
    take_screenshot(driver, "05b_utilitarios")
    # 2) Impressao de relatorios (direto, timeout curto)
    if not clicar_por_texto(driver, 5, "Impressão de relatórios", "Impressao de relatorios", "Impressao de Relatorios", tag="*"):
        LOG.info("[ERRO] 'Impressao de relatorios' nao encontrado")
        take_screenshot(driver, "erro_impressao_relatorios")
        return False
    time.sleep(1.0)
    take_screenshot(driver, "05c_impressao")
    # 3) Textbox codigo = configurado (default 1059)
    codigo_ok = False
    for xp in ("//input[contains(translate(@placeholder,'CODIGO','codigo'),'codigo')]",
               "//label[contains(translate(.,'CODIGO','codigo'),'digo')]/following::input[1]",
               "//span[contains(translate(.,'CODIGO','codigo'),'digo')]/following::input[1]",
               "//input[@type='text']"):
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    if el.is_displayed() and el.is_enabled():
                        el.clear()
                        el.send_keys(codigo)
                        codigo_ok = True
                        LOG.info(f"[NAV] Codigo {codigo} digitado ({xp[:40]})")
                        break
                except Exception:
                    continue
            if codigo_ok:
                break
        except Exception:
            continue
    if not codigo_ok:
        LOG.info("[ERRO] Textbox codigo nao encontrado")
        take_screenshot(driver, "erro_codigo_1059")
        return False
    time.sleep(1)

    def _marcar_checkbox(termo: str, marcar: bool) -> None:
        """Marca/desmarca 'Relatorios do usuario' (termo='usu') ou
        'Relatorios do perfil ativo' (termo='perfil')."""
        up = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        low = "abcdefghijklmnopqrstuvwxyz"
        nome = "Relatorios do Usuario" if termo == "usu" else "Relatorios do Perfil Ativo"
        xps = (
            f"//label[contains(translate(.,'{up}','{low}'),'relat') and contains(translate(.,'{up}','{low}'),'{termo}')]",
            f"//span[contains(translate(.,'{up}','{low}'),'relat') and contains(translate(.,'{up}','{low}'),'{termo}')]",
        )
        for xp in xps:
            try:
                for lab in driver.find_elements(By.XPATH, xp):
                    try:
                        if not lab.is_displayed():
                            continue
                        try:
                            cb = lab.find_element(
                                By.XPATH,
                                "./preceding::input[@type='checkbox'][1] | .//input[@type='checkbox']",
                            )
                        except Exception:
                            cb = None
                        if cb is not None:
                            if cb.is_selected() != marcar:
                                safe_click(driver, cb)
                                LOG.info(f"[NAV] Check '{nome}' {'marcado' if marcar else 'desmarcado'}")
                        elif marcar:
                            safe_click(driver, lab)
                            LOG.info(f"[NAV] Check '{nome}' marcado (label)")
                        return
                    except Exception:
                        continue
            except Exception:
                continue

    def _candidatos_relatorio() -> list:
        """Elementos visiveis que representam a linha do relatorio configurado."""
        titulo = f"CATE-{codigo}"
        alvos = []
        # 1) Mesmo criterio do 1033: texto direto contendo CATE-<codigo>
        try:
            for el in driver.find_elements(By.XPATH, f"//*[contains(text(),'{titulo}')]"):
                try:
                    txt = (el.text or "").strip()
                    if el.is_displayed() and titulo in txt:
                        alvos.append((len(txt), el))
                except Exception:
                    continue
        except Exception:
            pass
        # 2) Linhas de tabela/grid contendo o codigo
        if not alvos:
            try:
                for el in driver.find_elements(
                    By.XPATH,
                    f"//tr[contains(.,'{codigo}')] | //*[@role='row'][contains(.,'{codigo}')]",
                ):
                    try:
                        txt = (el.text or "").strip()
                        if el.is_displayed() and codigo in txt:
                            alvos.append((len(txt), el))
                    except Exception:
                        continue
            except Exception:
                pass
        # 3) Qualquer no-folha com o codigo, ignorando o chip 'Codigo: <codigo>'
        if not alvos:
            try:
                for el in driver.find_elements(By.XPATH, f"//*[contains(text(),'{codigo}')]"):
                    try:
                        txt = " ".join((el.text or "").split())
                        low = txt.lower()
                        if not el.is_displayed() or len(txt) <= 8:
                            continue
                        if low.startswith(("código", "codigo")):
                            continue
                        alvos.append((len(txt), el))
                    except Exception:
                        continue
            except Exception:
                pass
        alvos.sort(key=lambda t: t[0])
        vistos = set()
        cands = []
        for _, el in alvos:
            try:
                if el.id in vistos:
                    continue
                vistos.add(el.id)
                cands.append(el)
            except Exception:
                continue
        return cands

    # 4/5) Tenta combinacoes de filtro ate a grade listar o 1059.
    # O 1033 e "Relatorios do usuario"; o 1059 pode estar no "perfil ativo".
    linha = None
    combinacoes = ((True, False), (False, True), (True, True))
    for user_on, perfil_on in combinacoes:
        _marcar_checkbox("usu", user_on)
        _marcar_checkbox("perfil", perfil_on)
        take_screenshot(driver, f"05d_filtro_1059_u{int(user_on)}_p{int(perfil_on)}")
        if not clicar_por_texto(driver, 10, "Filtrar", tag="button"):
            LOG.info("[ERRO] Botao Filtrar nao encontrado")
            take_screenshot(driver, "erro_filtrar")
            return False
        limite = time.time() + 6
        while time.time() < limite:
            cands = _candidatos_relatorio()
            if cands:
                linha = cands[0]
                break
            time.sleep(0.5)
        if linha is not None:
            take_screenshot(driver, "05e_resultado_filtro")
            LOG.info(f"[NAV] Relatorio {codigo} na grade (usuario={user_on}, perfil={perfil_on})")
            break
        LOG.info(f"[NAV] Grade sem {codigo} (usuario={user_on}, perfil={perfil_on}); tentando proxima combinacao...")
        take_screenshot(driver, f"05e_falha_1059_u{int(user_on)}_p{int(perfil_on)}", force=True)
    if linha is None:
        try:
            body_txt = driver.find_element(By.TAG_NAME, "body").text or ""
            visiveis = [t.strip() for t in body_txt.splitlines() if codigo in t]
            LOG.info(f"[NAV] Textos visiveis com {codigo}: {visiveis[:10]}")
        except Exception:
            pass
        LOG.info(f"[ERRO] Relatorio {codigo} nao encontrado na grade em nenhuma combinacao")
        take_screenshot(driver, "erro_relatorio_nao_achado")
        return False
    # 6) Abre o relatorio. Fluxo gravado: DUPLO CLIQUE no titulo
    # (#title_1_1) -> abre direto os parametros, sem o modal "Tipo arquivo".
    def _relatorio_abriu() -> bool:
        """True se saiu da Lista e entrou nos Parametros do relatorio."""
        # Marcador mais forte: campos de data da tela de parametros.
        try:
            for el in driver.find_elements(By.CSS_SELECTOR, "input[placeholder='DD/MM/YYYY']"):
                if el.is_displayed():
                    return True
        except Exception:
            pass
        try:
            for el in driver.find_elements(By.ID, "detail_2_container"):
                if el.is_displayed():
                    return True
        except Exception:
            pass
        try:
            body_txt = (driver.find_element(By.TAG_NAME, "body").text or "").lower()
        except Exception:
            body_txt = ""
        marcadores_fortes = (
            "parametros relatorio", "parametros rel",
            "data inicio do periodo", "data inicial", "data final",
            "dimensões", "dimensoes", "filtro avançado", "filtro avancado",
            "sem titulo", "sem título",
        )
        return any(m in body_txt for m in marcadores_fortes)

    def _confirmar_tipo_arquivo_xls() -> bool:
        """Confirma o modal 'Tipo arquivo' (XLS) caso o Imprimir o abra."""
        try:
            dlg = None
            for el in driver.find_elements(By.CSS_SELECTOR, "div.dialog-box, .ngdialog, [role='dialog']"):
                try:
                    txt = (el.text or "").lower()
                    if el.is_displayed() and ("tipo arquivo" in txt or "tipo de arquivo" in txt):
                        dlg = el
                        break
                except Exception:
                    continue
            if dlg is None:
                return False
            # Select nativo (se houver): garante XLS
            try:
                from selenium.webdriver.support.ui import Select
                for sel in dlg.find_elements(By.TAG_NAME, "select"):
                    try:
                        Select(sel).select_by_visible_text("XLS")
                        LOG.info("[NAV] Modal Tipo arquivo: XLS selecionado")
                        break
                    except Exception:
                        continue
            except Exception:
                pass
            # Dropdown customizado: clica na opcao XLS visivel
            try:
                for opt in dlg.find_elements(By.XPATH, ".//*[normalize-space(.)='XLS']"):
                    if opt.is_displayed():
                        safe_click(driver, opt)
                        break
            except Exception:
                pass
            # Confirma no rodape do proprio dialogo
            for btn in dlg.find_elements(By.TAG_NAME, "button"):
                try:
                    txt = (btn.text or "").strip().lower()
                    if btn.is_displayed() and txt in (
                        "imprimir", "ok", "continuar", "confirmar", "gerar",
                    ):
                        safe_click(driver, btn)
                        LOG.info(f"[NAV] Modal Tipo arquivo confirmado ('{txt}')")
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    # Seleciona a linha do 1059 (localizada na etapa de filtro acima)
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", linha)
        time.sleep(0.5)
        safe_click(driver, linha)
        time.sleep(0.6)
        LOG.info(f"[NAV] Linha do relatorio {codigo} selecionada (1 clique)")
    except Exception:
        pass

    # Via principal (gravada): duplo clique no titulo do relatorio.
    try:
        ActionChains(driver).double_click(linha).perform()
        LOG.info(f"[NAV] Duplo clique no titulo do relatorio {codigo}")
    except Exception as e:
        LOG.info(f"[NAV-AVISO] Duplo clique falhou: {e}")

    fim_abertura = time.time() + 10
    while time.time() < fim_abertura and not _relatorio_abriu():
        time.sleep(0.5)
    take_screenshot(driver, "06_relatorio_aberto")
    if _relatorio_abriu():
        LOG.info(f"[NAV] Relatorio {codigo} ABERTO (duplo clique)")
        return True

    # Fallback: Imprimir (abre modal 'Tipo arquivo') -> confirma XLS
    LOG.info("[NAV-AVISO] Duplo clique nao abriu; tentando Imprimir + Tipo arquivo...")
    if clicar_por_texto(driver, 4, "Imprimir", tag="button"):
        LOG.info("[NAV] Botao Imprimir clicado")
        time.sleep(1)
        _confirmar_tipo_arquivo_xls()
        fim_abertura = time.time() + 10
        while time.time() < fim_abertura and not _relatorio_abriu():
            time.sleep(0.5)
        take_screenshot(driver, "06_relatorio_aberto")
        if _relatorio_abriu():
            LOG.info(f"[NAV] Relatorio {codigo} ABERTO via Imprimir")
            return True
    # Fallback: ENTER
    try:
        ActionChains(driver).double_click(linha).perform()
        time.sleep(0.8)
        try:
            linha.send_keys(Keys.ENTER)
        except Exception:
            pass
        fim_abertura = time.time() + 8
        while time.time() < fim_abertura and not _relatorio_abriu():
            time.sleep(0.5)
        if _relatorio_abriu():
            LOG.info("[NAV] Relatorio ABERTO no fallback ENTER")
            return True
    except Exception as e:
        LOG.info(f"[NAV] Fallback falhou: {e}")
    LOG.info("[ERRO] Relatorio nao abriu — veja 06_relatorio_aberto.png")
    try:
        diagnosticar_popups(driver, "RELATORIO_NAO_ABRIU")
    except Exception:
        pass
    return False


def preencher_datas_e_titulos(driver, inicio: str, fim: str) -> bool:
    """Passo 7-8: datas Inicio/Final (1x, global) + titulos=Ambos. Pula se ja preenchido."""
    LOG.info(f"[6/7] Preenchendo periodo {inicio} a {fim} + titulos=Ambos...")
    ok_ini = ok_fim = False
    # Localiza inputs de data por label proximo (pula se valor ja confere)
    for rotulo, valor in (("inicial", inicio), ("inicio", inicio), ("início", inicio), ("final", fim), ("fim", fim)):
        if not valor:
            continue
        try:
            labs = driver.find_elements(By.XPATH,
                f"//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{rotulo}')]"
                f" | //span[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{rotulo}')]")
            for lab in labs:
                try:
                    if not lab.is_displayed():
                        continue
                    inp = lab.find_element(By.XPATH, "./following::input[1]")
                    if inp.is_displayed() and inp.is_enabled():
                        try:
                            atual = (inp.get_attribute("value") or "").strip()
                        except Exception:
                            atual = ""
                        if atual == valor:
                            LOG.info(f"[FILTRO] {rotulo} ja={valor} (pulado)")
                            if rotulo not in ("final", "fim"):
                                ok_ini = True
                            else:
                                ok_fim = True
                            break
                        inp.clear()
                        inp.send_keys(valor)
                        inp.send_keys(Keys.TAB)
                        LOG.info(f"[FILTRO] {rotulo}={valor}")
                        if rotulo not in ("final", "fim"):
                            ok_ini = True
                        else:
                            ok_fim = True
                        break
                except Exception:
                    continue
        except Exception:
            continue
    # Fallback: dois primeiros inputs de data visiveis (tambem com guard)
    if not (ok_ini and ok_fim):
        try:
            datas = [e for e in driver.find_elements(By.XPATH, "//input[contains(@placeholder,'/') or @type='text']") if e.is_displayed()]
            vals = [v for v in (inicio, fim) if v]
            for el, v in zip(datas[:2], vals):
                try:
                    try:
                        atual = (el.get_attribute("value") or "").strip()
                    except Exception:
                        atual = ""
                    if atual == v:
                        continue
                    el.clear()
                    el.send_keys(v)
                    el.send_keys(Keys.TAB)
                except Exception:
                    pass
        except Exception:
            pass
    # Titulos = Ambos (generico por texto; sem IDs especificos de outro relatorio)
    try:
        marcado = False
        for inp in driver.find_elements(By.XPATH, "//input[@type='radio']"):
            try:
                if not inp.is_displayed():
                    continue
                try:
                    ctx = (
                        (inp.find_element(By.XPATH, "./parent::*").text or "")
                        + " " + (inp.find_element(By.XPATH, "./following-sibling::*[1]").text or "")
                        + " " + (inp.get_attribute("value") or "")
                        + " " + (inp.find_element(By.XPATH, "./parent::label").text or "")
                    ).lower()
                except Exception:
                    try:
                        ctx = ((inp.get_attribute("value") or "") + " " + (inp.find_element(By.XPATH, "./following::*[1]").text or "")).lower()
                    except Exception:
                        continue
                if "ambos" in ctx:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
                        time.sleep(0.3)
                    except Exception:
                        pass
                    if not inp.is_selected():
                        try:
                            inp.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", inp)
                        time.sleep(0.5)
                    # verifica de verdade
                    try:
                        if inp.is_selected():
                            LOG.info("[FILTRO] Titulos=Ambos marcado (verificado)")
                            marcado = True
                            break
                    except Exception:
                        marcado = True
                        break
            except Exception:
                continue
        if not marcado:
            # fallback: clica no label/span "Ambos" via JS
            for xp in (
                "//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'ambos')]",
                "//span[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'ambos')]",
            ):
                try:
                    for r in driver.find_elements(By.XPATH, xp):
                        try:
                            if r.is_displayed():
                                driver.execute_script("arguments[0].click();", r)
                                time.sleep(0.5)
                                LOG.info("[FILTRO] Titulos=Ambos clicado via label (fallback)")
                                marcado = True
                                break
                        except Exception:
                            continue
                    if marcado:
                        break
                except Exception:
                    continue
        if not marcado:
            LOG.info("[FILTRO] Opcao 'Titulos=Ambos' ausente (normal no 1059: so datas/dimensoes)")
    except Exception as e:
        LOG.info(f"[AVISO] Falha radio Ambos: {e}")
    take_screenshot(driver, "06b_filtros_base")
    return True


_CACHE_DESCOBERTA: list | None = None
_VISTOS_RUN: set = set()  # nomes normalizados ja vistos no modal neste run


def carregar_lista_descoberta(driver) -> list:
    """Descoberta completa no modal (auditoria manual; fora do fluxo padrao).

    O fluxo padrao usa a lista FIXA (ListaEstabelecimentos.xlsx). Esta funcao
    permanece para re-auditoria sob demanda. Sobrescreve o xlsx de conferencia.
    """
    global _VISTOS_RUN
    _VISTOS_RUN = set()
    desc = descobrir_estabelecimentos(driver)
    if desc:
        salvar_descoberta_excel(desc)
    LOG.info(f"[LISTA] {len(desc)} itens frescos do modal")
    return [{"nome": d["estabelecimento"]} for d in desc]


def filtrar_pendentes(estabelecimentos: list) -> list:
    """Rodada complementar: mantem so os ausentes na 1059 (compara nome sanitizado)."""
    dest = pasta_downloads_1059()
    tem = {p.stem.lower() for p in dest.glob("*.xlsx")}
    pend = [e for e in estabelecimentos if sanitizar_nome(e["nome"]).lower() not in tem]
    LOG.info(f"[LISTA] {len(pend)} pendente(s) de {len(estabelecimentos)} (1059 ja tem {len(tem)})")
    return pend


def ativar_dimensao_estabelecimento(driver) -> bool:
    """INICIO DO LOOP (passos 2-3): localiza 'Estabelecimento' na tabela de
    dimensoes (o ID WAFD-N varia: no 1033 e WAFD-1, no 1059 e WAFD-0) e clica
    na linha. Verifica ativa; reabre o modal 1x se travar.

    Sem dimensao ativa, o painel do meio lista convenios e a busca da unidade
    nunca acha. Robustez: reabre o modal 1x se travar. Fallback: clique direto.
    """
    def _dim_el():
        """Elemento visivel 'Estabelecimento' na tabela de dimensoes (sem ID fixo)."""
        xps = (
            "//*[@id='table-dimensions']//*[normalize-space(.)='Estabelecimento']",
            "//*[contains(@id,'WAFD') and normalize-space(.)='Estabelecimento']",
            "//*[contains(@id,'table-dimensions')]//td[normalize-space(.)='Estabelecimento']",
        )
        for xp in xps:
            try:
                for el in driver.find_elements(By.XPATH, xp):
                    try:
                        if el.is_displayed():
                            return el
                    except Exception:
                        continue
            except Exception:
                continue
        return None

    def _linha_dim(el):
        try:
            return el.find_element(By.XPATH, "./ancestor::tr[1]")
        except Exception:
            return el

    def _clicar_wafd_fresco() -> bool:
        try:
            WebDriverWait(driver, 8).until(lambda d: _dim_el() is not None)
            el = _dim_el()
            if el is None:
                LOG.info("[EXT-AVISO] Dimensao 'Estabelecimento' nao encontrada")
                return False
            alvo = el
            try:
                alvo = _linha_dim(el).find_element(By.XPATH, "./td[1]")
            except Exception:
                pass
            try:
                alvo.click()
            except Exception:
                driver.execute_script("arguments[0].click();", alvo)
            LOG.info(f"[EXT] Dimensao 'Estabelecimento' clicada (id={el.get_attribute('id') or 'sem-id'})")
            return True
        except Exception as e:
            LOG.info(f"[EXT-AVISO] Dimensao 'Estabelecimento' nao clicavel: {e}")
            return False

    def _dimensao_ativa() -> bool:
        try:
            el = _dim_el()
            if el is None:
                return False
            cls = (el.get_attribute("class") or "")
            row_cls = (_linha_dim(el).get_attribute("class") or "")
            return ("active" in cls) or ("selected" in row_cls) or ("active" in row_cls)
        except Exception:
            return False

    def _reabrir_modal() -> bool:
        try:
            # So clica em Cancelar se o modal de filtros estiver aberto; na tela
            # de parametros o Cancelar fecha o relatorio inteiro.
            if (driver.find_elements(By.ID, "table-dimensions")
                    or driver.find_elements(By.ID, "submit-button")):
                clicar_por_texto(driver, 3, "Cancelar", tag="button")
                time.sleep(1.0)
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "button-open-filter")))
            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            LOG.info("[EXT] Modal reaberto, repetindo dimensao...")
            return True
        except Exception:
            return False

    for tentativa in (1, 2):
        # 2) Busca da dimensao no painel esquerdo (se a caixa existir)
        try:
            dim_search = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "search-dimension")))
            try:
                dim_search.clear()
            except Exception:
                pass
            dim_search.send_keys("Estabelecimento")
            time.sleep(0.8)
            LOG.info("[EXT] Dimensao filtrada: 'Estabelecimento'")
        except Exception:
            pass  # caixa ausente: segue no clique direto
        # 3) Clica #WAFD-1 fresco + verifica ativa
        if _clicar_wafd_fresco():
            try:
                WebDriverWait(driver, 4).until(lambda d: _dimensao_ativa())
            except Exception:
                pass
            if _dimensao_ativa():
                LOG.info("[EXT] Dimensao Estabelecimento ATIVA (verificada)")
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: len(d.find_elements(
                            By.CSS_SELECTOR, "#table-items span.w-item-label-elipses")) > 0)
                except Exception:
                    pass
                return True
            LOG.info(f"[EXT-AVISO] #WAFD-1 clicado mas dimensao nao ativou (tentativa {tentativa})")
        take_screenshot(driver, "erro_tipo_estabelecimento")
        _reabrir_modal()
    LOG.info("[ERRO] Dimensao Estabelecimento nao ativada apos reabertura")
    return False


def descobrir_estabelecimentos(driver, timeout_seg: int = 90) -> list:
    """Abre Filtro avancado > #WAFD-1 > raspa #table-items. CAPTURA UNICA por run.

    Retorna [{'ordem','estabelecimento'}] em memoria. Chamadas repetidas
    retornam o cache sem reabrir o modal.
    """
    global _CACHE_DESCOBERTA
    if _CACHE_DESCOBERTA is not None:
        LOG.info(f"[DESC] Reusando captura unica ({len(_CACHE_DESCOBERTA)} itens, sem recapturar)")
        return _CACHE_DESCOBERTA
    LOG.info("[DESC] Captura UNICA da lista (1x por run)...")
    if not clicar_por_texto(driver, 10, "Filtro avançado", "Filtro avancado", tag="*"):
        LOG.info("[DESC-ERRO] Link 'Filtro avancado' nao encontrado")
        take_screenshot(driver, "desc_erro_filtro")
        return []
    time.sleep(2)
    # Dimensao via helper padrao (busca #search-dimension + verifica ativa)
    if not ativar_dimensao_estabelecimento(driver):
        LOG.info("[DESC-ERRO] Dimensao Estabelecimento nao ativada")
        take_screenshot(driver, "desc_erro_tipo")
        return []
    LOG.info("[DESC] Tipo Estabelecimento ativo. Raspando lista do meio...")
    take_screenshot(driver, "desc_lista_inicial")
    # Dump do HTML do modal p/ inspecao offline (responde: "qual item contem a lista?")
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        html = driver.execute_script(
            """var m = null;
               var els = document.querySelectorAll('*');
               for (var e of els) {
                 try { if ((e.innerText || '').indexOf('Filtros selecionados') >= 0 && (e.innerText || '').indexOf('DaVita') >= 0) { m = e; break; } } catch (x) {}
               }
               return m ? m.outerHTML.slice(0, 200000) : document.documentElement.outerHTML.slice(0, 200000);""")
        with open(OUTPUT_DIR / "desc_modal.html", "w", encoding="utf-8") as f:
            f.write(html)
        LOG.info("[DESC] HTML do modal salvo em output/desc_modal.html")
    except Exception as e:
        LOG.info(f"[DESC-AVISO] Falha dump HTML: {e}")

    # Container exato do scroll (seu print: div#table-items > table > tbody > tr).
    # Itens: span.w-item-label-elipses (nome) + div.w-item-label-align[data-code] (valor).
    # Coleta em 1 chamada JS (ms, nao N lookups Selenium) — scroll rapido.
    def _coletar_nomes() -> dict:
        """Coleta spans exatos da lista do meio + data-code."""
        try:
            pares = driver.execute_script(
                "var out = [];"
                "document.querySelectorAll(\"#table-items span.w-item-label-elipses\").forEach(function(sp){"
                "  var t = (sp.textContent || '').trim().replace(/\\s+/g, ' ');"
                "  if (!t || t.length > 80) return;"
                "  var code = '';"
                "  var box = sp.closest('div.w-item-label-align');"
                "  if (box) code = box.getAttribute('data-code') || '';"
                "  out.push([t, code]);"
                "});"
                "return out;")
        except Exception:
            return {}
        achados = {}
        for t, c in (pares or []):
            if t not in vistos and t not in achados:
                achados[t] = c or ""
        return achados

    vistos: dict = {}
    sem_novos = 0
    deadline = time.time() + timeout_seg
    ultima_altura = -1
    while time.time() < deadline:
        novos = _coletar_nomes()
        for n, v in novos.items():
            vistos[n] = v
        # Rola o container exato #table-items (infinite-scroll carrega o proximo lote)
        try:
            info = driver.execute_script(
                """var c = document.getElementById('table-items');
                   if (!c) return null;
                   c.scrollTop = c.scrollTop + 800;
                   return {top: c.scrollTop, h: c.scrollHeight, c: c.clientHeight};""")
            time.sleep(0.9)
            if not info:
                break
            no_fim = info["top"] + info["c"] >= info["h"] - 10
            altura = info["top"]
        except Exception:
            break
        if altura == ultima_altura:
            sem_novos += 1
        else:
            sem_novos = 0
        ultima_altura = altura
        LOG.info(f"[DESC] coletados={len(vistos)} top={altura} sem_novos={sem_novos}")
        if no_fim and sem_novos >= 1:
            time.sleep(1.0)  # ultimo lote do infinite-scroll
            for n, v in _coletar_nomes().items():
                if n not in vistos:
                    vistos[n] = v
            break
        if sem_novos >= 4:
            break
    take_screenshot(driver, "desc_lista_final")
    # fecha o modal sem selecionar nada (volta p/ parametros limpo)
    try:
        clicar_por_texto(driver, 3, "Cancelar", tag="button")
        time.sleep(1.5)
    except Exception:
        pass
    lista = [{"ordem": i + 1, "estabelecimento": n}
             for i, n in enumerate(sorted(vistos.keys(), key=lambda k: k.lower()))]
    LOG.info(f"[DESC] Total descoberto (captura unica): {len(lista)} estabelecimentos")
    _CACHE_DESCOBERTA = lista
    return lista


def salvar_descoberta_excel(lista: list) -> Path | None:
    """Grava output/estabelecimentos_descobertos.xlsx p/ conferencia."""
    try:
        import pandas as pd
    except Exception as e:
        LOG.info(f"[DESC-ERRO] pandas indisponivel: {e}")
        return None
    OUTPUT_DIR.mkdir(exist_ok=True)
    destino = OUTPUT_DIR / "estabelecimentos_descobertos.xlsx"
    try:
        df = pd.DataFrame(lista, columns=["ordem", "estabelecimento"])
        df.to_excel(destino, index=False)
        LOG.info(f"[DESC] Excel conferencia -> {destino} ({len(df)} linhas)")
        return destino
    except Exception as e:
        LOG.info(f"[DESC-ERRO] Falha ao gravar Excel: {e}")
        return None


def selecionar_estabelecimento(driver, nome: str, timeout: int = 12) -> bool:
    """Filtro avancado: painel esq 'Estabelecimento' > painel meio pesquisa+checkbox > Selecionar.

    Otimizado 18/09: IDs diretos + waits explicitos curtos (sem sleeps fixos).
    """
    LOG.info(f"[EXT] Selecionando estabelecimento '{nome}'...")
    # Via principal gravada: #button-open-filter direto (fallback: texto)
    try:
        btn_fa = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "button-open-filter")))
        try:
            btn_fa.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn_fa)
    except Exception:
        if not clicar_por_texto(driver, 5, "Filtro avançado", "Filtro avancado", tag="*"):
            LOG.info("[ERRO] 'Filtro avancado' nao encontrado")
            take_screenshot(driver, "erro_filtros_avancados")
            return False
    take_screenshot(driver, "07a_filtros_avancados")
    # 1) INICIO DO LOOP: dimensao Estabelecimento via busca + verificacao ativa.
    # Sem isso o painel do meio lista convenios (padrao do Tasy) e a unidade nunca acha.
    if not ativar_dimensao_estabelecimento(driver):
        return False
    take_screenshot(driver, "07a1_tipo_estabelecimento")
    # 2) SCROLL-AND-SCAN 18/09: a lista e virtualizada (so ~50 linhas no DOM).
    # Rola #table-items em passos e confere o nome a cada passo, com early-stop.
    # Match com dobra de acento/caixa; fallback contains de candidato unico.
    def _norm(s: str) -> str:
        return norm_nome(s)

    def _coletar_visiveis() -> set:
        # Otimizacao: 1 roundtrip JS (textos visiveis) em vez de N is_displayed().
        try:
            textos = driver.execute_script(
                "return Array.from(document.querySelectorAll("
                " '#table-items span.w-item-label-elipses'))"
                " .filter(function(e){ return e.offsetParent !== null; })"
                " .map(function(e){ return (e.textContent || '').trim(); });")
        except Exception:
            return set()
        return {_norm(t) for t in (textos or []) if t}

    alvo_norm = _norm(nome)
    vistos = set(_VISTOS_RUN)  # reaproveita nomes ja vistos neste run
    take_screenshot(driver, "07a2_topo_lista")
    achou = None

    # 2a) BUSCA DIGITADA primeiro (sem rolar a tela pelos outros itens).
    # Anti-stale 18/09: digita -> aguarda assentar -> re-localiza TUDO do zero.
    busca_ok = False
    try:
        # Otimizacao: localiza a caixa em 1 roundtrip JS (era ate 4 waits de 2s).
        try:
            cand = driver.execute_script(
                "var sels = [\"#table-items input[type='search']\","
                " \"#table-items input[type='text']\","
                " \"input[type='search']\"];"
                " for (var i = 0; i < sels.length; i++) {"
                "   var els = document.querySelectorAll(sels[i]);"
                "   for (var j = 0; j < els.length; j++) {"
                "     if (els[j].offsetParent !== null) return els[j];"
                "   }"
                " }"
                " var t = document.getElementById('table-items');"
                " if (t) { var p = t; for (var k = 0; k < 6 && p; k++) {"
                "   p = p.parentElement;"
                "   if (p) { var inp = p.querySelector('input');"
                "     if (inp && inp.offsetParent !== null) return inp; } } }"
                " return null;")
            search_input = None
            if cand is not None:
                try:
                    WebDriverWait(driver, 3).until(EC.element_to_be_clickable(cand))
                    search_input = cand
                except Exception:
                    search_input = None
        except Exception:
            search_input = None
        if search_input is not None:
            try:
                search_input.clear()
            except Exception:
                pass
            search_input.send_keys(nome)
            LOG.info(f"[EXT] Busca digitada: '{nome}'")
            # Aguarda a lista assentar (contagem estabiliza, teto 4s; 1 roundtrip/poll)
            anterior = -1
            estavel = 0
            t_fim = time.time() + 4
            while time.time() < t_fim:
                try:
                    n = driver.execute_script(
                        "return document.querySelectorAll("
                        " '#table-items span.w-item-label-elipses').length;")
                except Exception:
                    n = -1
                if n == anterior and n >= 0:
                    estavel += 1
                    if estavel >= 2:
                        break
                else:
                    estavel = 0
                anterior = n
                time.sleep(0.3)
            # Re-localiza do zero (elementos pos-busca, nunca os pre-busca).
            # O match precisa estar no lote ATUAL (nao no seed de runs/item anterior).
            lote = _coletar_visiveis()
            vistos.update(lote)
            if alvo_norm in lote:
                achou = alvo_norm
                busca_ok = True
                LOG.info(f"[EXT] '{nome}' achado via busca digitada")
            else:
                LOG.info(f"[EXT] Busca sem match exato, limpando p/ scroll...")
                try:
                    search_input.clear()
                    try:
                        # clear() nem sempre esvazia no Angular: garante via teclado
                        if (search_input.get_attribute("value") or "") != "":
                            search_input.send_keys(Keys.CONTROL, "a")
                            search_input.send_keys(Keys.DELETE)
                    except Exception:
                        pass
                    time.sleep(0.8)
                except Exception:
                    pass
    except Exception as e:
        LOG.info(f"[EXT-AVISO] Busca digitada indisponivel ({e}), indo ao scroll...")

    # 2b) SCROLL-AND-SCAN (fallback / lista virtualizada com ~50 linhas no DOM).
    if not busca_ok:
        try:
            driver.execute_script(
                "var c = document.getElementById('table-items'); if (c) c.scrollTop = 0;")
            time.sleep(0.3)
        except Exception:
            pass
        deadline_scan = time.time() + 25
        while time.time() < deadline_scan and achou is None:
            lote = _coletar_visiveis()
            vistos.update(lote)
            if alvo_norm in lote:  # lote atual, nao seed de item anterior
                achou = alvo_norm
                break
            try:
                info = driver.execute_script(
                    "var c = document.getElementById('table-items');"
                    " if (!c) return null;"
                    " c.scrollTop = c.scrollTop + 800;"
                    " return {top: c.scrollTop, h: c.scrollHeight, c: c.clientHeight};")
            except Exception:
                info = None
            time.sleep(0.6)
            if not info or info["top"] + info["c"] >= info["h"] - 10:
                vistos.update(_coletar_visiveis())
                break
    _VISTOS_RUN.update(vistos)
    if achou is None:
        LOG.info(f"[FALHA] '{nome}': nao localizado no filtro")
        take_screenshot(driver, "erro_estab_nao_achado")
        return False
    LOG.info(f"[EXT] '{nome}' localizado na lista")

    # 3) REPLAY GRAVADO: clique no 'div.check-element' interno da linha
    # (xpath gravado: #table-items/table/tbody/tr[N]/td/div[1]/div).
    # Re-localiza elementos FRESCOS (sem scroll — item ja esta renderizado).
    # Maquina de estados: 1 clique -> reconfere fresco -> so clica de novo se desmarcado.
    def _linha_por_nome():
        """Retorna (tr, check_el, checked) da linha do 'nome', elementos frescos."""
        try:
            spans = driver.find_elements(By.CSS_SELECTOR, "#table-items span.w-item-label-elipses")
        except Exception:
            return None, None, False
        alvo = None
        for sp in spans:
            try:
                if not sp.is_displayed():
                    continue
                if _norm(sp.text) == achou:
                    alvo = sp.find_element(By.XPATH, "./ancestor::tr[1]")
                    break
            except Exception:
                continue
        if alvo is None:
            return None, None, False
        try:
            try:
                check_el = alvo.find_element(By.CSS_SELECTOR, "div.w-item-checkbox > div.check-element")
            except Exception:
                try:
                    check_el = alvo.find_element(By.CSS_SELECTOR, "div.w-item-checkbox")
                except Exception:
                    check_el = alvo
            cls = ((alvo.get_attribute("class") or "") + " "
                   + (alvo.find_element(By.CSS_SELECTOR, "div.w-item-checkbox").get_attribute("class") or ""))
            return alvo, check_el, ("selected" in cls or "checked" in cls)
        except Exception:
            return None, None, False  # stale: trata como nao verificado

    deadline = time.time() + timeout
    marcado = False
    while time.time() < deadline and not marcado:
        tr, check_el, checked = _linha_por_nome()
        if tr is None:
            LOG.info(f"[EXT] linha '{nome}' nao encontrada, retry...")
            time.sleep(0.5)
            continue
        if checked:
            LOG.info(f"[EXT] '{nome}' ja marcado (verificado fresco)")
            marcado = True
            break
        # desmarcado -> 1 clique nativo no check-element, depois reconfere
        try:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", check_el)
            except Exception:
                pass
            try:
                check_el.click()  # nativo, igual ao gravado
                LOG.info(f"[EXT] Clique nativo no check de '{nome}'")
            except Exception as e:
                LOG.info(f"[EXT] Nativo falhou ({e}), JS no TR...")
                try:
                    driver.execute_script("arguments[0].click();", tr)
                except Exception:
                    pass
            time.sleep(0.8)  # digest do Angular antes de reconferir
        except Exception as e:
            LOG.info(f"[EXT] passada com erro: {e}")
            time.sleep(0.5)
    if not marcado:
        LOG.info(f"[ERRO] '{nome}' nao marcado na lista do meio")
        take_screenshot(driver, "erro_estab_nao_achado")
        return False
    take_screenshot(driver, "07b_estab_marcado")
    # REPLAY GRAVADO: #submit-button (fallback: texto 'Selecionar')
    sel_ok = False
    try:
        btn_sel = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "submit-button")))
        try:
            btn_sel.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn_sel)
        sel_ok = True
        LOG.info("[EXT] #submit-button clicado")
    except Exception:
        sel_ok = clicar_por_texto(driver, 4, "Selecionar", tag="button")
    if not sel_ok:
        LOG.info("[ERRO] Botao Selecionar nao encontrado")
        return False
    # Espera o modal fechar / Exportar liberar (em vez de sleep fixo 2s)
    try:
        WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='exportar xls']")))
    except Exception:
        time.sleep(1)
    take_screenshot(driver, "07c_apos_selecionar")
    return True


def _snapshot_downloads(download_dir: Path) -> dict:
    """Snapshot robusto: nome -> (mtime, size). Evita falso 'novo' por nome repetido."""
    snap = {}
    for p in list(download_dir.glob("*.xls")) + list(download_dir.glob("*.xlsx")):
        try:
            st = p.stat()
            snap[p.name] = (st.st_mtime, st.st_size)
        except Exception:
            continue
    return snap


def _clicar_download_nativo(driver) -> bool:
    """Trata o dialogo nativo do Tasy que trava o 2o download.

    Casos vistos em diagnostico_popups.txt:
    - #download-button 'Iniciar download' + #copy-url-button
    - 'Abrir o processo de download' + #do-not-ask-again
    Retorna True se clicou em algo (download deve iniciar em seguida).
    """
    clicou = False
    # Marca 'nao perguntar novamente' p/ nao reexibir no proximo item
    try:
        for cb in driver.find_elements(By.ID, "do-not-ask-again"):
            try:
                if cb.is_displayed() and not cb.is_selected():
                    cb.click()
                    LOG.info("[DOWN] Checkbox 'nao perguntar' marcado")
            except Exception:
                pass
    except Exception:
        pass
    # Via principal: #download-button
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "download-button")))
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)
        LOG.info("[DOWN] 'Iniciar download' clicado")
        return True
    except Exception:
        pass
    # Fallbacks por texto (curtos, sem travar o fluxo feliz)
    for txt in ("Iniciar download", "Abrir o processo de download"):
        try:
            els = driver.find_elements(By.XPATH,
                f"//button[contains(normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')),'{txt.lower()}')]")
            for el in els:
                try:
                    if el.is_displayed() and el.is_enabled():
                        try:
                            el.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", el)
                        LOG.info(f"[DOWN] '{txt}' clicado (fallback)")
                        clicou = True
                        break
                except Exception:
                    continue
            if clicou:
                break
        except Exception:
            continue
    return clicou


def solicitar_xlsx_e_baixar(driver, download_dir: Path, timeout: int = 30) -> Path | None:
    """REPLAY 18/09 + fix 19/09: Exportar XLS > Continuar > [Iniciar download] > *.xls."""
    # Limpa parciais orfaos da tentativa/item anterior (senao o wait trava a toa)
    for p in list(download_dir.glob("*.crdownload")):
        try:
            # So apaga se mais velho que 5s (evita matar download recem-iniciado)
            if time.time() - p.stat().st_mtime > 5:
                p.unlink()
        except Exception:
            pass
    antes = _snapshot_downloads(download_dir)
    # 1) Exportar XLS por texto (mesmo botao visivel no relatorio)
    exp_ok = clicar_por_texto(driver, 8, "Exportar XLS", tag="button")
    if not exp_ok:
        exp_ok = clicar_por_texto(driver, 3, "Exportar XLS", tag="*")
    if exp_ok:
        LOG.info("[DOWN] Exportar XLS clicado")
    if not exp_ok:
        LOG.info("[ERRO] Botao Exportar XLS nao encontrado")
        take_screenshot(driver, "erro_exportar_xls")
        return None
    take_screenshot(driver, "08a_pos_exportar")
    # 2) Continuar no ngdialog (XLS ja e padrao — sem dropdown; o wait cobre o delay)
    if not clicar_por_texto(driver, 6, "Continuar", tag="button"):
        LOG.info("[ERRO] Botao Continuar nao encontrado")
        take_screenshot(driver, "erro_continuar")
        return None
    # 2.5) FIX 19/09: dialogo nativo 'Iniciar download' (causa raiz do 2o item falhar).
    # Espera curta com early-exit: se nao aparecer, segue (fluxo feliz inalterado).
    time.sleep(1.0)
    try:
        _clicar_download_nativo(driver)
    except Exception:
        pass
    LOG.info("[DOWN] Aguardando download do XLS...")
    deadline = time.time() + timeout
    ultima_checagem_driver = 0.0  # is_driver_alive throttled (roundtrip caro)
    ultimo_log = 0.0
    while time.time() < deadline:
        if time.time() - ultima_checagem_driver >= 3:
            ultima_checagem_driver = time.time()
            try:
                if not is_driver_alive(driver):
                    break
            except Exception:
                break
        # 2a) Se o dialogo nativo abriu com atraso, clica (so 1x por passada)
        try:
            if driver.find_elements(By.ID, "download-button"):
                _clicar_download_nativo(driver)
        except Exception:
            pass
        try:
            cr = list(download_dir.glob("*.crdownload"))
            cands = sorted(
                list(download_dir.glob("*.xls")) + list(download_dir.glob("*.xlsx")),
                key=lambda p: p.stat().st_mtime, reverse=True)
            novos = []
            for c in cands:
                try:
                    st = c.stat()
                    key = (st.st_mtime, st.st_size)
                    # Novo se: nome inedito OU mesmo nome mas mtime/size mudou (Edge reusa nome)
                    if c.name not in antes or antes[c.name] != key:
                        # Ignora arquivo ainda crescendo via .crdownload correspondente
                        novos.append(c)
                except Exception:
                    continue
            if novos and not cr:
                t1 = novos[0].stat().st_size
                time.sleep(0.5)
                if novos[0].stat().st_size == t1:
                    LOG.info(f"[DOWN] Arquivo pronto: {novos[0].name}")
                    return novos[0]
            if time.time() - ultimo_log >= 5:
                ultimo_log = time.time()
                LOG.info(f"[DOWN] ... aguardando ({len(cands)} xls, {len(cr)} parciais)")
        except Exception:
            pass
        time.sleep(0.4)
    LOG.info("[ERRO] Timeout aguardando XLS")
    take_screenshot(driver, "erro_download_timeout")
    return None


def limpar_estabelecimento(driver, timeout: int = 6) -> bool:
    """REPLAY 18/09: clica no X da caixa inferior (div.w-token-clear em #checkout-content)."""
    try:
        x_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#checkout-content div.w-token-clear")))
        try:
            x_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", x_btn)
        LOG.info("[EXT] Estabelecimento removido via X (w-token-clear)")
        try:
            WebDriverWait(driver, 3).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#checkout-content div.w-token-clear")))
        except Exception:
            time.sleep(0.5)
        return True
    except Exception as e:
        LOG.info(f"[AVISO] X de limpeza nao clicado: {e}")
        take_screenshot(driver, "erro_limpar_estab")
        return False


def _decodificar_export(raw: bytes) -> str:
    """Decodifica o TSV do Tasy aceitando UTF-8 (com/sem BOM) ou cp1252.

    O export padrao do Tasy e cp1252 (single-byte); se um dia vier UTF-8,
    o fallback evita mojibake de acentos. latin-1 e o ultimo recurso para
    nunca perder a linha inteira.
    """
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1252", errors="replace")


def validar_e_converter_tsv(origem: Path, nome_estab: str) -> tuple[str, Path | None]:
    """Validacao + conversao em LEITURA UNICA do disco (otimizacao 18/09).

    O .xls cru do Tasy e TSV. Retorna ('ok'|'vazio'|'invalido', xlsx_final|None).
    'ok': cabecalho + dados -> grava XLSX real na 1059 (sem alerta do Excel).
    'vazio': so cabecalho (sem dados no periodo) -> grava XLSX so com cabecalho.
    'invalido': sem cabecalho/truncado -> None (chamador apaga e repete).
    """
    import pandas as pd

    try:
        if not origem.exists() or origem.stat().st_size < 10:
            return ("invalido", None)
        texto = _decodificar_export(origem.read_bytes())
    except Exception as e:
        LOG.info(f"[VALID] Falha ao ler {origem.name}: {e} -> invalido")
        return ("invalido", None)
    linhas = texto.splitlines()
    if not linhas or "Cd estabelecimento" not in linhas[0] or "\t" not in linhas[0]:
        LOG.info(f"[VALID] {origem.name}: cabecalho TSV ausente -> invalido")
        return ("invalido", None)
    header = linhas[0].split("\t")
    n_cols = len(header)
    dados = []
    for ln in linhas[1:]:
        if not ln.strip():
            continue
        cols = ln.split("\t")
        if len(cols) != n_cols:
            continue
        c0 = cols[0].strip()
        if not c0 or c0.lower().startswith(("lote", "processo")):
            continue
        dados.append(cols)
    try:
        df = pd.DataFrame(dados, columns=header, dtype=str)
    except Exception as e:
        LOG.info(f"[VALID] {origem.name}: montagem TSV falhou ({e}) -> invalido")
        return ("invalido", None)
    status = "vazio" if len(df) == 0 else "ok"
    LOG.info(f"[VALID] {origem.name}: {len(df)} linha(s) -> {status}")

    destino_dir = pasta_downloads_1059()
    base = sanitizar_nome(nome_estab)
    destino = destino_dir / f"{base}.xlsx"
    for velho in (destino_dir / f"{base}.xls", destino):
        try:
            if velho.exists():
                velho.unlink()
        except Exception:
            pass
    try:
        df.to_excel(destino, index=False)
        LOG.info(f"[ARQ] Convertido -> {destino.name} ({len(df)} linha(s))")
        try:
            origem.unlink()
        except Exception:
            pass
        return (status, destino)
    except Exception as e:
        LOG.info(f"[ARQ-ERRO] Conversao TSV->XLSX falhou ({origem.name}): {e}")
        return ("invalido", None)


def baixar_com_retry(driver, download_dir: Path, nome_estab: str, max_tent: int = 3,
                     timeout: int = 30) -> tuple[str, Path | None]:
    """Exportar XLS > Continuar com ate max_tent tentativas.

    Retorna ('ok'|'vazio'|'falha', caminho_xlsx_final|None). Parciais invalidos
    sao apagados (Downloads e 1059) antes de repetir. 'vazio' nao repete.
    """
    destino_dir = pasta_downloads_1059()
    base = sanitizar_nome(nome_estab)
    for tentativa in range(1, max_tent + 1):
        if tentativa > 1:
            LOG.info(f"[RETRY] {nome_estab}: tentativa {tentativa}/{max_tent}")
            # Limpa parciais travados (.crdownload) da tentativa anterior:
            # senao o proximo wait os enxerga e espera ate o timeout a toa.
            for p in list(download_dir.glob("*.crdownload")):
                try:
                    p.unlink()
                except Exception:
                    pass
            time.sleep(1)
        baixado = solicitar_xlsx_e_baixar(driver, download_dir, timeout=timeout)
        if baixado is None:
            LOG.info(f"[RETRY] {nome_estab}: sem arquivo (tentativa {tentativa})")
            continue
        status, final = validar_e_converter_tsv(baixado, nome_estab)
        if status == "invalido":
            for p in (baixado, destino_dir / f"{base}.xls", destino_dir / f"{base}.xlsx"):
                try:
                    if p.exists():
                        p.unlink()
                except Exception:
                    pass
            LOG.info(f"[RETRY] {nome_estab}: invalido apagado (tentativa {tentativa})")
            continue
        return (status, final)
    return ("falha", None)


def read_current_url(driver) -> str:
    try:
        return driver.current_url or ""
    except (WebDriverException, OSError, ConnectionError):
        return ""


def _destino_consolidado_1059() -> tuple[Path, str]:
    saida = load_params().get("saida", {}) or {}
    raw = str(saida.get("consolidado_diretorio", "") or "").strip()
    base = Path(raw).expanduser() if raw else Path.home() / "Downloads"
    prefixo = str(saida.get("consolidado_prefixo_1059", "") or "").strip() or "1059"
    return base, prefixo


def consolidar_1059() -> Path | None:
    """Consolida todos os XLSX da pasta 1059 em um unico CSV.GZ.

    Mantem as 56 colunas originais (inclusive nomes repetidos, como
    'Dt venc') e acrescenta apenas a coluna 'atualizacao'.
    """
    import pandas as pd

    origem = pasta_downloads_1059()
    arquivos = sorted(origem.glob("*.xlsx"))
    if not arquivos:
        LOG.info(f"[1059] Nada a consolidar — sem *.xlsx em {origem}")
        return None
    run_dt = datetime.now()
    carimbo = run_dt.strftime("%Y-%m-%d %H:%M:%S")
    LOG.info(f"[1059] {len(arquivos)} arquivo(s), atualizacao={carimbo}")
    header = None
    partes = []
    for f in arquivos:
        try:
            df = pd.read_excel(f, dtype=str, header=None)
        except Exception as e:
            LOG.info(f"[1059-AVISO] {f.name}: leitura falhou ({e}) — pulado")
            continue
        if df.empty:
            continue
        if header is None:
            header = [str(c) for c in df.iloc[0].tolist()]
        if len(header) != df.shape[1]:
            LOG.info(f"[1059-AVISO] {f.name}: {df.shape[1]} colunas != {len(header)} — pulado")
            continue
        partes.append(df.iloc[1:].reset_index(drop=True))
        LOG.info(f"[1059] {f.name}: {max(len(df) - 1, 0)} linha(s)")
    if not partes or header is None:
        LOG.info("[1059] Nenhum dado legivel — nada gerado")
        return None
    total = pd.concat(partes, ignore_index=True)
    total.columns = header
    total["atualizacao"] = carimbo
    dest_dir, prefixo = _destino_consolidado_1059()
    nome = f"{prefixo}-{run_dt:%Y%m%d}-{run_dt:%H%M}.csv.gz"
    dest_dir.mkdir(parents=True, exist_ok=True)
    destino = dest_dir / nome
    total.to_csv(destino, sep=";", encoding="utf-8-sig", index=False, compression="gzip")
    LOG.info(f"[1059] {destino.name}: {len(total)} linhas x {len(total.columns)} cols, "
             f"{destino.stat().st_size / 1024:.0f} KB")
    return destino


def main() -> None:
    global _SHOTS_SUCESSO, _VISTOS_RUN, RELATORIO_CODIGO
    params = load_params()
    tasy = params["tasy"]
    auto = params["automacao"]
    RELATORIO_CODIGO = _codigo_relatorio(params.get("extracao", {}))
    LOG.info(f"[CFG] Codigo do relatorio 1059: {RELATORIO_CODIGO}")
    _SHOTS_SUCESSO = bool(auto.get("fotos_sucesso", False))
    if not _SHOTS_SUCESSO:
        LOG.info("[CFG] Screenshots de sucesso DESLIGADOS (otimizacao; erros ainda geram PNG)")

    url = tasy["url"].strip()
    usuario = tasy["usuario"].strip()
    senha = tasy["senha"].strip()

    if not all([url, usuario, senha]):
        raise SystemExit("Preencha url, usuario e senha em parametros.json")

    dialog_handler = NativeDialogHandler()
    driver = make_driver(auto["timeout_segundos"])

    try:
        LOG.info("[1/4] Abrindo sistema...")
        driver.get(url)
        WebDriverWait(driver, auto["timeout_segundos"]).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)
        take_screenshot(driver, "01_pagina_inicial")

        user_field = find_element(
            driver,
            auto["timeout_segundos"],
            (By.ID, "username"),
            (By.NAME, "username"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[contains(@id,'user')]"),
        )
        password_field = find_element(
            driver,
            auto["timeout_segundos"],
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[contains(@id,'sen') or contains(@id,'pass')]"),
        )

        if not user_field or not password_field:
            take_screenshot(driver, "erro_campos_login_nao_encontrados")
            raise SystemExit("Campos de usuario/senha nao encontrados na pagina.")

        LOG.info("[2/4] Preenchendo login...")
        user_field.clear()
        user_field.send_keys(usuario)
        password_field.clear()
        password_field.send_keys(senha)
        take_screenshot(driver, "02_login_preenchido")

        dialog_handler.start(timeout=60)
        LOG.info("[3/4] Enviando login (aguardando certificado)...")
        driver.execute_script("arguments[0].form.submit();", password_field)

        logado = False
        browser_fechado = False
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(1.5)
            # Se o usuario fechou o navegador, encerra imediatamente
            if not is_driver_alive(driver):
                LOG.info("[ENCERRADO] Janela do navegador fechada pelo usuario.")
                browser_fechado = True
                break
            try:
                handles = driver.window_handles
                if len(handles) > 1:
                    driver.switch_to.window(handles[-1])
                    LOG.info(f"[INFO] Nova aba detectada: {handles[-1]}")
                # Timeouts curtos (1s) — nao bloqueiam o loop
                click_ok_in_popup(driver, 1)
                close_recorded_dialog(driver, 1)
                handle_user_selection(driver, 1)
            except Exception:
                pass
            try:
                url_atual = read_current_url(driver)
                if url_atual and "login" not in url_atual.lower() and url_atual != url:
                    logado = True
                    break
            except (WebDriverException, OSError, ConnectionError):
                # Sessao caiu junto com o navegador
                if not is_driver_alive(driver):
                    LOG.info("[ENCERRADO] Sessao perdida (navegador fechado).")
                    browser_fechado = True
                    break
                continue
            LOG.info(f"    ... aguardando ({attempt + 1}/{max_attempts})")

        # Certificado ja foi tratado ou login concluiu -> para a vigia na hora
        dialog_handler.stop()

        if browser_fechado:
            LOG.info("[FIM] Encerrado pelo usuario, sem screenshots finais.")
            return

        if logado:
            LOG.info("LOGIN APARENTEMENTE OK")
            try:
                LOG.info(f"URL atual: {driver.current_url}")
            except Exception:
                pass
        else:
            LOG.info("ATENCAO: pode ainda estar na tela de login ou popup pendente")

        try:
            if is_driver_alive(driver):
                handles = driver.window_handles
                if len(handles) > 1:
                    driver.switch_to.window(handles[-1])
        except Exception:
            pass

        if is_driver_alive(driver):
            LOG.info("[3.5/4] Fechando popups pos-login (max 8s, sai antes se limpar)...")
            take_screenshot(driver, "03a_antes_popup")
            try:
                diagnosticar_popups(driver, "ANTES")
                n_popup = fechar_popups_pos_login(driver, timeout_total=8, per_wait=0.5)
                LOG.info(f"[INFO] Popups fechados: {n_popup}")
                diagnosticar_popups(driver, "DEPOIS")
            except Exception as e:
                LOG.info(f"[AVISO] Falha no fechador generico: {e}")
            take_screenshot(driver, "03b_apos_popup")
            take_screenshot(driver, "03_pos_login")
            time.sleep(1)
            take_screenshot(driver, "04_final")

        # ── FLUXO 1059 (passos 1-13 do roteiro) ──
        if not is_driver_alive(driver):
            LOG.info("[FIM] Navegador fechado antes do 1059.")
            return
        extracao_cfg = params.get("extracao", {})
        limite_teste = int(extracao_cfg.get("limite_teste", 0))
        pular_existentes = bool(extracao_cfg.get("pular_existentes", False))
        download_dir = Path.home() / "Downloads"
        # Rodada cheia limpa a 1059; complementar mantem e processa so os ausentes.
        pasta1059 = pasta_downloads_1059(limpar=not pular_existentes)
        LOG.info(f"[CFG] Pasta 1059: {pasta1059} | limite_teste={limite_teste} | pular_existentes={pular_existentes}")

        if not navegar_ate_relatorio_1059(driver, timeout=20):
            LOG.info("[FIM] Falha na navegacao ate o 1059. Veja screenshots 05*.")
            take_screenshot(driver, "erro_fluxo_1059")
            return

        # Periodo GLOBAL (parametros.json > extracao.periodo) — preenchido 1x.
        periodo = extracao_cfg.get("periodo", {}) or {}
        data_inicio = str(periodo.get("data_inicio", "")).strip()
        data_fim = str(periodo.get("data_fim", "")).strip()
        if not data_inicio or not data_fim:
            LOG.info("[ERRO] Periodo global ausente em parametros.json > extracao.periodo (data_inicio/data_fim)")
            take_screenshot(driver, "erro_periodo_global")
            return
        LOG.info(f"[CFG] Periodo global: {data_inicio} a {data_fim}")
        preencher_datas_e_titulos(driver, data_inicio, data_fim)

        # Lista FIXA (ListaEstabelecimentos.xlsx, mantida pelo usuario);
        # loop baixa 1 XLSX por item. Auditoria fixa x modal sai no fim do run.
        _VISTOS_RUN = set()
        estabelecimentos = carregar_estabelecimentos()
        if not estabelecimentos:
            LOG.info("[FIM] Lista vazia. Confira ListaEstabelecimentos.xlsx")
            return
        if pular_existentes:
            estabelecimentos = filtrar_pendentes(estabelecimentos)
            if not estabelecimentos:
                LOG.info("[FIM] Nada pendente — 1059 ja completa.")
                return
        if limite_teste and limite_teste > 0:
            estabelecimentos = estabelecimentos[:limite_teste]
            LOG.info(f"[MODO TESTE] Executando apenas {len(estabelecimentos)} estabelecimento(s). "
                  f"Para rodar todos, ajuste extracao.limite_teste=0 em parametros.json")

        ok_count = fail = vazios = 0
        for idx, est in enumerate(estabelecimentos, 1):
            if not is_driver_alive(driver):
                LOG.info("[ENCERRADO] Navegador fechado durante o loop.")
                break
            LOG.info(f"\n===== [{idx}/{len(estabelecimentos)}] {est['nome']} "
                  f"({data_inicio} a {data_fim}) =====")
            try:
                if not selecionar_estabelecimento(driver, est["nome"]):
                    LOG.info(f"[FALHA] {est['nome']}: nao selecionou")
                    fail += 1
                    continue
                status, final = baixar_com_retry(driver, download_dir, est["nome"], max_tent=3)
                if status == "falha":
                    LOG.info(f"[FALHA] {est['nome']}: sem download apos 3 tentativas")
                    fail += 1
                elif status == "vazio":
                    LOG.info(f"[VAZIO] {est['nome']}: sem dados no periodo (aceito)")
                    vazios += 1
                    take_screenshot(driver, f"09_vazio_{sanitizar_nome(est['nome'])[:30]}")
                else:
                    LOG.info(f"[OK] {est['nome']}: {final.name}")
                    ok_count += 1
                    take_screenshot(driver, f"09_ok_{sanitizar_nome(est['nome'])[:30]}")
            except Exception as e:
                LOG.info(f"[FALHA] {est['nome']}: {e}")
                take_screenshot(driver, "erro_estabelecimento")
                fail += 1
            finally:
                # REPLAY 18/09 + fix 19/09: limpa o X p/ o proximo item; se falhar,
                # o proximo selecionar empilharia 2 filtros (causa de download invalido).
                if idx < len(estabelecimentos) and is_driver_alive(driver):
                    try:
                        if not limpar_estabelecimento(driver):
                            LOG.info(f"[AVISO] {est['nome']}: token nao limpou — proximo pode empilhar filtro")
                    except Exception:
                        pass
            intervalo = int(auto.get("intervalo_entre_coletas_segundos", 2) or 0)
            if intervalo < 2:
                intervalo = 2  # minimo p/ dialogo nativo fechar (evita corrida no 2o item)
            time.sleep(intervalo)
        LOG.info(f"\n[4/4] FLUXO 1059 CONCLUIDO — ok={ok_count} vazios={vazios} falhas={fail} pasta={pasta1059}")
        # [5/5] Consolidacao automatica no mesmo fluxo (consolidar_1059).
        LOG.info("\n[5/5] Consolidando CSV.GZ (1059)...")
        try:
            destino_ec = consolidar_1059()
            if destino_ec is not None:
                LOG.info(f"[5/5] CONSOLIDADO: {destino_ec}")
            else:
                LOG.info("[5/5-AVISO] Nada consolidado")
        except Exception as e:
            LOG.info(f"[5/5-AVISO] Consolidacao automatica falhou: {e}")
    finally:
        try:
            dialog_handler.stop()
        except Exception:
            pass
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
