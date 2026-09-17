import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Auto-detect venv ────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"
if sys.prefix == sys.base_prefix and _VENV_PYTHON.exists():
    # Não estamos no venv — relança com o Python do venv
    print(f"[VENV] Reinterpretando com {_VENV_PYTHON} ...")
    result = subprocess.run([str(_VENV_PYTHON)] + sys.argv, cwd=str(_SCRIPT_DIR))
    raise SystemExit(result.returncode)
# ─────────────────────────────────────────────────────────────────────────────

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from certificado_handler import NativeDialogHandler

BASE_DIR = Path(__file__).resolve().parent
PARAMS_PATH = BASE_DIR / "parametros.json"
OUTPUT_DIR = BASE_DIR / "output"
RELATORIO_NOME = "DaVita - Etapa Conta - Por Periodo da Conta (CATE-1033)"
RELATORIO_CODIGO = "1033"


def pasta_downloads_1033() -> Path:
    """Pasta 1033 na area de Downloads (passo 9 do roteiro)."""
    p = Path.home() / "Downloads" / "1033"
    p.mkdir(parents=True, exist_ok=True)
    return p


def sanitizar_nome(nome: str) -> str:
    n = re.sub(r"[\\/:*?\"<>|]+", "_", nome.strip())
    n = re.sub(r"\s+", " ", n).strip()
    return n[:120] if n else "estabelecimento"


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
    deadline = time.time() + timeout
    while time.time() < deadline:
        for txt in textos:
            try:
                els = driver.find_elements(
                    By.XPATH,
                    f"//{tag}[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='{txt.lower()}']",
                )
                for el in els:
                    try:
                        if el.is_displayed() and el.is_enabled() and safe_click(driver, el):
                            print(f"[NAV] Clicado {tag} '{txt}'")
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
        # fallback parcial: contem o texto
        for txt in textos:
            try:
                els = driver.find_elements(By.XPATH, f"//{tag}[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{txt.lower()}')]")
                for el in els:
                    try:
                        if el.is_displayed() and el.is_enabled() and safe_click(driver, el):
                            print(f"[NAV] Clicado {tag} (contem) '{txt}'")
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
        time.sleep(0.5)
    return False


def load_params() -> dict:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        return json.load(f)


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
        "safebrowsing.enabled": True,
    })
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


def take_screenshot(driver, name: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{name}_{stamp}.png"
    driver.save_screenshot(str(path))
    return path


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
            print("[INFO] Dialogo HTML registrado fechado")
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
                        print("[POPUP] Checkbox 'nao perguntar' marcado")
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
                print(f"[POPUP] Fechado ({fechados}): '{txt or btn.get_attribute('class')}'")
                time.sleep(1.0)
                break  # revarre a pagina para pegar o 2o popup em sequencia
            except Exception:
                continue
        if clicou_nesta_passada:
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
                            print(f"[POPUP] Fechado via icone ({fechados}): '{css}'")
                            time.sleep(1.0)
                            break
                    except Exception:
                        continue
                if clicou_nesta_passada:
                    break
            except Exception:
                continue
        if clicou_nesta_passada:
            continue
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
        print(f"[DIAG] Botoes visiveis registrados em {path.name}")
    except Exception as e:
        print(f"[DIAG] Falha no diagnostico: {e}")


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
            print("[INFO] Dropdown de usuário encontrado, selecionando...")
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
        print("[INFO] Botão de confirmação clicado na seleção de usuário")
        return True
    except Exception:
        return False


def carregar_estabelecimentos() -> list:
    """Le ListaEstabelecimentos.xlsx (aba Lista). Retorna [{nome, inicio, fim}]."""
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
    col_ini = next((c for c in df.columns if c.lower() in ("inicio", "início", "dt_inicio", "data_inicio")), None)
    col_fim = next((c for c in df.columns if c.lower() in ("final", "fim", "dt_fim", "data_fim")), None)
    # Fallback global da aba Parametros
    ini_global = fim_global = None
    try:
        xls = pd.read_excel(xlsx, sheet_name=None)
        for aba in xls.values():
            aba.columns = [str(c).strip() for c in aba.columns]
            cmap = {c.lower(): c for c in aba.columns}
            if "inicio" in cmap or "início" in cmap:
                ci = cmap.get("inicio", cmap.get("início"))
                cf = cmap.get("final", cmap.get("fim"))
                ini_global = aba.iloc[0][ci]
                fim_global = aba.iloc[0][cf] if cf else None
                break
    except Exception:
        pass

    def fmt(v, fallback):
        v = v if v is not None and str(v) != "nan" else fallback
        if v is None:
            return ""
        try:
            d = pd.to_datetime(v, dayfirst=True)
            return d.strftime("%d/%m/%Y")
        except Exception:
            return str(v).strip()

    lista = []
    for _, row in df.iterrows():
        nome = str(row[col_nome]).strip()
        if not nome or nome.lower() == "nan":
            continue
        ini = fmt(row[col_ini] if col_ini else None, ini_global)
        fim = fmt(row[col_fim] if col_fim else None, fim_global)
        lista.append({"nome": nome, "inicio": ini, "fim": fim})
    print(f"[DADOS] {len(lista)} estabelecimentos carregados de {xlsx.name}")
    return lista


def navegar_ate_relatorio_1033(driver, timeout: int = 20) -> bool:
    """Passos 1-6: Utilitarios > Impressao de relatorios > codigo 1033 > filtro > duplo clique."""
    print("[5/7] Navegando ate impressao de relatorios...")
    take_screenshot(driver, "05a_home")
    # 1) Aba Utilitarios
    if not clicar_por_texto(driver, 10, "Utilitários", "Utilitarios", tag="*"):
        print("[ERRO] Aba Utilitarios nao encontrada")
        take_screenshot(driver, "erro_aba_utilitarios")
        return False
    time.sleep(1.5)
    take_screenshot(driver, "05b_utilitarios")
    # 2) Impressao de relatorios
    ok = clicar_por_texto(driver, 10, "Impressão de relatórios", "Impressao de relatorios", "Impressao de Relatorios", tag="*")
    if not ok:
        # tenta via busca superior como fallback
        print("[NAV] Tentando via busca superior 'Impressao de relatorios'...")
        try:
            busca = find_element(driver, 8,
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[not(@type) or @type='search']"),
                (By.CSS_SELECTOR, "input"),
                per_locator=2.0)
            if busca:
                busca.clear()
                busca.send_keys("Impressao de relatorios")
                time.sleep(2)
                clicar_por_texto(driver, 5, "Impressão de relatórios", "Impressao de relatorios", tag="*")
        except Exception:
            pass
    time.sleep(2)
    take_screenshot(driver, "05c_impressao")
    # 3) Textbox codigo = 1033
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
                        el.send_keys(RELATORIO_CODIGO)
                        codigo_ok = True
                        print(f"[NAV] Codigo 1033 digitado ({xp[:40]})")
                        break
                except Exception:
                    continue
            if codigo_ok:
                break
        except Exception:
            continue
    if not codigo_ok:
        print("[ERRO] Textbox codigo nao encontrado")
        take_screenshot(driver, "erro_codigo_1033")
        return False
    time.sleep(1)
    # 4) Check 'Relatorios do Usuario' / 'Relatórios do Usuário'
    try:
        for xp in ("//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'relat') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'usu')]",
                   "//span[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'relat') and contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'usu')]"):
            for lab in driver.find_elements(By.XPATH, xp):
                try:
                    if lab.is_displayed():
                        try:
                            cb = lab.find_element(By.XPATH, "./preceding::input[@type='checkbox'][1] | .//input[@type='checkbox']")
                        except Exception:
                            cb = None
                        if cb is not None:
                            try:
                                if not cb.is_selected():
                                    safe_click(driver, cb)
                                print("[NAV] Check Relatorios do Usuario marcado")
                            except Exception:
                                safe_click(driver, lab)
                        else:
                            safe_click(driver, lab)
                        break
                except Exception:
                    continue
    except Exception:
        pass
    take_screenshot(driver, "05d_filtro_1033")
    # 5) Botao Filtrar
    if not clicar_por_texto(driver, 10, "Filtrar", tag="button"):
        print("[ERRO] Botao Filtrar nao encontrado")
        take_screenshot(driver, "erro_filtrar")
        return False
    time.sleep(3)
    take_screenshot(driver, "05e_resultado_filtro")
    # 6) Abrir o relatorio (com verificacao real de navegacao)
    # BUG ANTIGO: //*[contains(.,'CATE-1033')] casa ANCESTRAIS (body/divs)
    # grandes primeiro -> duplo clique no container nao faz nada, mas
    # logava sucesso. Screenshots 06_* provaram que continuava na Lista.
    def _relatorio_abriu() -> bool:
        """True se saiu da Lista e entrou nos Parametros do relatorio."""
        try:
            body_txt = (driver.find_element(By.TAG_NAME, "body").text or "").lower()
        except Exception:
            return False
        marcadores_fortes = (
            "filtros avançados", "filtros avancados", "filtro avançado",
            "estabelecimento", "títulos", "titulos",
            "período da conta", "periodo da conta",
        )
        return any(m in body_txt for m in marcadores_fortes)

    # Candidatos FOLHA: contains(text(),...) nao casa ancestral como contains(.,...)
    candidatos = []
    for xp in (
        "//*[contains(text(),'CATE-1033')]",
        f"//*[contains(text(),'{RELATORIO_NOME[:30]}')]",
    ):
        try:
            for el in driver.find_elements(By.XPATH, xp):
                try:
                    if not el.is_displayed():
                        continue
                    txt = (el.text or "").strip()
                    if "CATE-1033" not in txt and RELATORIO_NOME[:20] not in txt:
                        continue
                    # prefere o no mais especifico (texto mais curto = mais folha)
                    candidatos.append((len(txt), el))
                except Exception:
                    continue
        except Exception:
            continue
    # ordena: menor texto primeiro (linha/celula, nao o body inteiro)
    candidatos.sort(key=lambda t: t[0])
    # remove duplicados do mesmo elemento
    vistos = set()
    alvos = []
    for _, el in candidatos:
        try:
            key = el.id
        except Exception:
            continue
        if key not in vistos:
            vistos.add(key)
            alvos.append(el)
    if not alvos:
        print("[ERRO] Relatorio CATE-1033 nao encontrado na grade")
        take_screenshot(driver, "erro_relatorio_nao_achado")
        return False
    print(f"[NAV] {len(alvos)} candidato(s) folha para CATE-1033")
    alvo = alvos[0]
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", alvo)
        time.sleep(0.5)
    except Exception:
        pass

    aberto = False
    for tentativa in range(1, 4):
        try:
            # re-resolve o alvo (evita stale) — pega o 1o visivel de novo
            try:
                els = driver.find_elements(By.XPATH, "//*[contains(text(),'CATE-1033')]")
                for e in sorted(els, key=lambda x: len((x.text or ""))):
                    try:
                        if e.is_displayed() and "CATE-1033" in (e.text or ""):
                            alvo = e
                            break
                    except Exception:
                        continue
            except Exception:
                pass
            if tentativa == 1:
                # 1) click simples p/ selecionar + duplo clique ActionChains
                safe_click(driver, alvo)
                time.sleep(1.0)
                ActionChains(driver).double_click(alvo).perform()
                print(f"[NAV] Tentativa {tentativa}: click + duplo clique ActionChains")
            elif tentativa == 2:
                # 2) duplo clique + ENTER (Tasy costuma abrir com Enter)
                ActionChains(driver).double_click(alvo).perform()
                time.sleep(0.8)
                alvo.send_keys(Keys.ENTER)
                print(f"[NAV] Tentativa {tentativa}: duplo clique + ENTER")
            else:
                # 3) click simples + botao Visualizar (visivel no rodape da Lista)
                safe_click(driver, alvo)
                time.sleep(1.0)
                print(f"[NAV] Tentativa {tentativa}: click + botao Visualizar")
                if not clicar_por_texto(driver, 5, "Visualizar", tag="button"):
                    # fallback: duplo clique via JS (dispara dblclick nativo)
                    try:
                        driver.execute_script(
                            "var e1=new MouseEvent('dblclick',{bubbles:true,cancelable:true});"
                            "arguments[0].dispatchEvent(e1);", alvo)
                    except Exception:
                        pass
            time.sleep(3)
            take_screenshot(driver, f"06_tentativa_{tentativa}")
            if _relatorio_abriu():
                print(f"[NAV] Relatorio CATE-1033 ABERTO (tentativa {tentativa})")
                aberto = True
                break
            else:
                print(f"[NAV] Tentativa {tentativa} nao saiu da Lista, retry...")
        except Exception as e:
            print(f"[NAV] Tentativa {tentativa} falhou: {e}")
            time.sleep(2)
    take_screenshot(driver, "06_relatorio_aberto")
    if not aberto:
        print("[ERRO] Relatorio nao abriu apos 3 tentativas — continua na Lista. Veja 06_tentativa_*.png")
        try:
            diagnosticar_popups(driver, "RELATORIO_NAO_ABRIU")
        except Exception:
            pass
        return False
    return True


def preencher_datas_e_titulos(driver, inicio: str, fim: str) -> bool:
    """Passo 7-8: datas Inicio/Final + titulos=ambos."""
    print(f"[6/7] Preenchendo periodo {inicio} a {fim} + titulos=ambos...")
    ok_ini = ok_fim = False
    for label, valor, flag in (("inicio", inicio, "ini"), ("final", inicio and fim, "fim")):
        _ = flag
    # Localiza inputs de data por label proximo
    for rotulo, valor in (("inicio", inicio), ("início", inicio), ("final", fim), ("fim", fim)):
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
                        inp.clear()
                        inp.send_keys(valor)
                        inp.send_keys(Keys.TAB)
                        print(f"[FILTRO] {rotulo}={valor}")
                        if rotulo.startswith("ini") or "nici" in rotulo:
                            ok_ini = True
                        else:
                            ok_fim = True
                        break
                except Exception:
                    continue
        except Exception:
            continue
    # Fallback: dois primeiros inputs de data visiveis
    if not (ok_ini and ok_fim):
        try:
            datas = [e for e in driver.find_elements(By.XPATH, "//input[contains(@placeholder,'/') or @type='text']") if e.is_displayed()]
            vals = [v for v in (inicio, fim) if v]
            for el, v in zip(datas[:2], vals):
                try:
                    el.clear()
                    el.send_keys(v)
                    el.send_keys(Keys.TAB)
                except Exception:
                    pass
        except Exception:
            pass
    # Titulos = Ambos (radio) — robusto: associa input ao texto vizinho
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
                            print("[FILTRO] Titulos=Ambos marcado (verificado)")
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
                                print("[FILTRO] Titulos=Ambos clicado via label (fallback)")
                                marcado = True
                                break
                        except Exception:
                            continue
                    if marcado:
                        break
                except Exception:
                    continue
        if not marcado:
            print("[AVISO] Radio 'Ambos' nao confirmado — veja 06b_filtros_base.png")
    except Exception as e:
        print(f"[AVISO] Falha radio Ambos: {e}")
    except Exception:
        pass
    take_screenshot(driver, "06b_filtros_base")
    return True


def selecionar_estabelecimento(driver, nome: str, timeout: int = 20) -> bool:
    """Passos 9-10: Filtro avancado (singular, link canto inferior) > buscar > Selecionar."""
    print(f"[EXT] Selecionando estabelecimento '{nome}'...")
    if not clicar_por_texto(driver, 10, "Filtro avançado", "Filtro avancado", "Filtros avançados", "Filtros avancados", tag="*"):
        print("[ERRO] 'Filtros avancados' nao encontrado")
        take_screenshot(driver, "erro_filtros_avancados")
        return False
    time.sleep(2)
    take_screenshot(driver, "07a_filtros_avancados")
    # Busca o estabelecimento (input de pesquisa dentro do modal)
    digitado = False
    for xp in ("//div[contains(@class,'modal') or contains(@class,'dialog')]//input[@type='text']",
               "//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'estabelec') or contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'pesquis') or contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'buscar')]",
               "//input[@type='text']"):
        try:
            for el in driver.find_elements(By.XPATH, xp):
                try:
                    if el.is_displayed() and el.is_enabled():
                        el.clear()
                        el.send_keys(nome)
                        time.sleep(1.5)
                        digitado = True
                        break
                except Exception:
                    continue
            if digitado:
                break
        except Exception:
            continue
    # Tenta clicar na linha do estabelecimento (radio/checkbox/linha)
    deadline = time.time() + timeout
    selecionado = False
    while time.time() < deadline and not selecionado:
        try:
            linhas = driver.find_elements(By.XPATH, f"//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{nome.lower()[:15]}')]")
            for ln in linhas:
                try:
                    if not ln.is_displayed():
                        continue
                    # clica no input associado ou na linha
                    try:
                        inp = ln.find_element(By.XPATH, ".//input[@type='radio' or @type='checkbox'] | ./preceding::input[1]")
                        safe_click(driver, inp)
                        selecionado = True
                        break
                    except Exception:
                        if ln.tag_name in ("tr", "div", "span", "td", "label"):
                            safe_click(driver, ln)
                            selecionado = True
                            break
                except Exception:
                    continue
        except Exception:
            pass
        if not selecionado:
            time.sleep(1)
    if not selecionado:
        print(f"[ERRO] Estabelecimento '{nome}' nao selecionado na lista")
        take_screenshot(driver, "erro_estab_nao_achado")
        return False
    time.sleep(1)
    take_screenshot(driver, "07b_estab_marcado")
    if not clicar_por_texto(driver, 10, "Selecionar", tag="button"):
        print("[ERRO] Botao Selecionar nao encontrado")
        return False
    time.sleep(2)
    return True


def solicitar_csv_e_baixar(driver, download_dir: Path, timeout: int = 90) -> Path | None:
    """Passo 11: Visualizar > janela CSV > Continuar > aguarda download novo."""
    antes = {p.name for p in download_dir.glob("*.csv")} | {p.name for p in download_dir.glob("*.crdownload")}
    if not clicar_por_texto(driver, 15, "Visualizar", tag="button"):
        print("[ERRO] Botao Visualizar nao encontrado")
        take_screenshot(driver, "erro_visualizar")
        return None
    time.sleep(3)
    take_screenshot(driver, "08a_pos_visualizar")
    # Janela: selecionar CSV (radio/combo/botao)
    try:
        clicado_csv = clicar_por_texto(driver, 8, "CSV", tag="*")
        if clicado_csv:
            print("[DOWN] Formato CSV selecionado")
    except Exception:
        pass
    time.sleep(1)
    take_screenshot(driver, "08b_csv")
    if not clicar_por_texto(driver, 10, "Continuar", "Confirmar", "OK", tag="button"):
        print("[ERRO] Botao Continuar nao encontrado")
        take_screenshot(driver, "erro_continuar")
        return None
    print("[DOWN] Aguardando download do CSV...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not is_driver_alive(driver):
            break
        try:
            cr = list(download_dir.glob("*.crdownload"))
            csvs = sorted(download_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
            novos = [c for c in csvs if c.name not in antes]
            if novos and not cr:
                # estabilidade: tamanho nao muda por 2s
                t1 = novos[0].stat().st_size
                time.sleep(2)
                if novos[0].stat().st_size == t1:
                    print(f"[DOWN] Arquivo pronto: {novos[0].name}")
                    return novos[0]
        except Exception:
            pass
        time.sleep(2)
    print("[ERRO] Timeout aguardando CSV")
    take_screenshot(driver, "erro_download_timeout")
    return None


def mover_para_1033(origem: Path, nome_estab: str) -> Path:
    """Passo 12: move para ~/Downloads/1033 renomeado com nome do estabelecimento."""
    destino_dir = pasta_downloads_1033()
    destino = destino_dir / f"{sanitizar_nome(nome_estab)}.csv"
    i = 1
    while destino.exists():
        destino = destino_dir / f"{sanitizar_nome(nome_estab)}_{i}.csv"
        i += 1
    shutil.move(str(origem), str(destino))
    print(f"[ARQ] Movido -> {destino}")
    return destino


def read_current_url(driver) -> str:
    try:
        return driver.current_url or ""
    except (WebDriverException, OSError, ConnectionError):
        return ""


def main() -> None:
    params = load_params()
    tasy = params["tasy"]
    auto = params["automacao"]

    url = tasy["url"].strip()
    usuario = tasy["usuario"].strip()
    senha = tasy["senha"].strip()

    if not all([url, usuario, senha]):
        raise SystemExit("Preencha url, usuario e senha em parametros.json")

    dialog_handler = NativeDialogHandler()
    driver = make_driver(auto["timeout_segundos"])

    try:
        print("[1/4] Abrindo sistema...")
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

        print("[2/4] Preenchendo login...")
        user_field.clear()
        user_field.send_keys(usuario)
        password_field.clear()
        password_field.send_keys(senha)
        take_screenshot(driver, "02_login_preenchido")

        dialog_handler.start(timeout=60)
        print("[3/4] Enviando login (aguardando certificado)...")
        driver.execute_script("arguments[0].form.submit();", password_field)

        logado = False
        browser_fechado = False
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(1.5)
            # Se o usuario fechou o navegador, encerra imediatamente
            if not is_driver_alive(driver):
                print("[ENCERRADO] Janela do navegador fechada pelo usuario.")
                browser_fechado = True
                break
            try:
                handles = driver.window_handles
                if len(handles) > 1:
                    driver.switch_to.window(handles[-1])
                    print(f"[INFO] Nova aba detectada: {handles[-1]}")
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
                    print("[ENCERRADO] Sessao perdida (navegador fechado).")
                    browser_fechado = True
                    break
                continue
            print(f"    ... aguardando ({attempt + 1}/{max_attempts})")

        # Certificado ja foi tratado ou login concluiu -> para a vigia na hora
        dialog_handler.stop()

        if browser_fechado:
            print("[FIM] Encerrado pelo usuario, sem screenshots finais.")
            return

        if logado:
            print("LOGIN APARENTEMENTE OK")
            try:
                print(f"URL atual: {driver.current_url}")
            except Exception:
                pass
        else:
            print("ATENCAO: pode ainda estar na tela de login ou popup pendente")

        try:
            if is_driver_alive(driver):
                handles = driver.window_handles
                if len(handles) > 1:
                    driver.switch_to.window(handles[-1])
        except Exception:
            pass

        if is_driver_alive(driver):
            print("[3.5/4] Fechando popups pos-login (generico, 15s)...")
            take_screenshot(driver, "03a_antes_popup")
            try:
                diagnosticar_popups(driver, "ANTES")
                n_popup = fechar_popups_pos_login(driver, timeout_total=15)
                print(f"[INFO] Popups fechados: {n_popup}")
                diagnosticar_popups(driver, "DEPOIS")
            except Exception as e:
                print(f"[AVISO] Falha no fechador generico: {e}")
            take_screenshot(driver, "03b_apos_popup")
            take_screenshot(driver, "03_pos_login")
            time.sleep(2)
            take_screenshot(driver, "04_final")

        # ── FLUXO 1033 (passos 1-13 do roteiro) ──
        if not is_driver_alive(driver):
            print("[FIM] Navegador fechado antes do 1033.")
            return
        extracao_cfg = params.get("extracao", {})
        limite_teste = int(extracao_cfg.get("limite_teste", 1))  # modo teste: 1 estab primeiro
        intervalo = int(auto.get("intervalo_entre_coletas_segundos", 2))
        download_dir = Path.home() / "Downloads"
        pasta1033 = pasta_downloads_1033()
        print(f"[CFG] Pasta 1033: {pasta1033} | limite_teste={limite_teste}")

        if not navegar_ate_relatorio_1033(driver, timeout=20):
            print("[FIM] Falha na navegacao ate o 1033. Veja screenshots 05*.")
            take_screenshot(driver, "erro_fluxo_1033")
            return

        estabelecimentos = carregar_estabelecimentos()
        if limite_teste and limite_teste > 0:
            estabelecimentos = estabelecimentos[:limite_teste]
            print(f"[MODO TESTE] Executando apenas {len(estabelecimentos)} estabelecimento(s). "
                  f"Para rodar os 148, ajuste extracao.limite_teste=0 em parametros.json")
        # Filtros base (passo 7-8) com o periodo do 1o estabelecimento
        if estabelecimentos:
            preencher_datas_e_titulos(driver, estabelecimentos[0]["inicio"], estabelecimentos[0]["fim"])

        ok_count = fail = 0
        for idx, est in enumerate(estabelecimentos, 1):
            if not is_driver_alive(driver):
                print("[ENCERRADO] Navegador fechado durante o loop.")
                break
            print(f"\n===== [{idx}/{len(estabelecimentos)}] {est['nome']} "
                  f"({est['inicio']} a {est['fim']}) =====")
            try:
                # Periodo pode variar por estabelecimento
                preencher_datas_e_titulos(driver, est["inicio"], est["fim"])
                if not selecionar_estabelecimento(driver, est["nome"]):
                    print(f"[FALHA] {est['nome']}: nao selecionou")
                    fail += 1
                    continue
                baixado = solicitar_csv_e_baixar(driver, download_dir)
                if not baixado:
                    print(f"[FALHA] {est['nome']}: sem download")
                    fail += 1
                    continue
                mover_para_1033(baixado, est["nome"])
                ok_count += 1
                take_screenshot(driver, f"09_ok_{sanitizar_nome(est['nome'])[:30]}")
            except Exception as e:
                print(f"[FALHA] {est['nome']}: {e}")
                take_screenshot(driver, "erro_estabelecimento")
                fail += 1
            time.sleep(intervalo)
        print(f"\n[4/4] FLUXO 1033 CONCLUIDO — ok={ok_count} falhas={fail} pasta={pasta1033}")
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
