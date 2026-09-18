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


def pasta_downloads_1033(limpar: bool = False) -> Path:
    """Pasta 1033 na area de Downloads. Se ja existe e limpar=True, apaga
    todos os arquivos dentro dela; se nao existe, cria."""
    p = Path.home() / "Downloads" / "1033"
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
        print(f"[ARQ] Pasta 1033 limpa: {apagados} arquivo(s) removido(s)")
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
                                print(f"[NAV] Clicado {t} '{txt}'")
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
                                print(f"[NAV] Clicado {t} (contem) '{txt}'")
                                return True
                        except Exception:
                            continue
                except Exception:
                    pass
        time.sleep(0.3)
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


def take_screenshot(driver, name: str) -> Path | None:
    if not is_driver_alive(driver):
        return None
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUTPUT_DIR / f"{name}_{stamp}.png"
        driver.save_screenshot(str(path))
        return path
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
    print(f"[DADOS] {len(lista)} estabelecimentos carregados de {xlsx.name}")
    return lista


def navegar_ate_relatorio_1033(driver, timeout: int = 20) -> bool:
    """Passos 1-6: direto Utilitarios > Impressao de relatorios > codigo 1033 > filtro > abrir."""
    print("[5/7] Navegando ate impressao de relatorios...")
    take_screenshot(driver, "05a_home")
    # 1) Aba Utilitarios (direto, timeout curto)
    if not clicar_por_texto(driver, 5, "Utilitários", "Utilitarios", tag="*"):
        print("[ERRO] Aba Utilitarios nao encontrada")
        take_screenshot(driver, "erro_aba_utilitarios")
        return False
    time.sleep(1.0)
    take_screenshot(driver, "05b_utilitarios")
    # 2) Impressao de relatorios (direto, timeout curto)
    if not clicar_por_texto(driver, 5, "Impressão de relatórios", "Impressao de relatorios", "Impressao de Relatorios", tag="*"):
        print("[ERRO] 'Impressao de relatorios' nao encontrado")
        take_screenshot(driver, "erro_impressao_relatorios")
        return False
    time.sleep(1.0)
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
    # 6) Abrir o relatorio — REPLAY 18/09: seleciona a linha CATE-1033 (1 clique)
    # e clica no botao Imprimir #handlebar-1093435 (gravado). Fallback: duplo clique.
    def _relatorio_abriu() -> bool:
        """True se saiu da Lista e entrou nos Parametros do relatorio."""
        try:
            body_txt = (driver.find_element(By.TAG_NAME, "body").text or "").lower()
        except Exception:
            return False
        marcadores_fortes = (
            "data inicio do periodo", "dimensões", "dimensoes",
            "filtro avançado", "filtro avancado",
            "sem titulo", "sem título", "ambos",
        )
        return any(m in body_txt for m in marcadores_fortes)

    # Seleciona a linha do CATE-1033 (nos-folha, sem casar ancestral)
    alvos = []
    try:
        for el in driver.find_elements(By.XPATH, "//*[contains(text(),'CATE-1033')]"):
            try:
                if not el.is_displayed():
                    continue
                txt = (el.text or "").strip()
                if "CATE-1033" not in txt:
                    continue
                alvos.append((len(txt), el))
            except Exception:
                continue
    except Exception:
        pass
    alvos.sort(key=lambda t: t[0])
    vistos = set()
    linha = None
    for _, el in alvos:
        try:
            if el.id not in vistos:
                vistos.add(el.id)
                linha = el
                break
        except Exception:
            continue
    if linha is None:
        print("[ERRO] Relatorio CATE-1033 nao encontrado na grade")
        take_screenshot(driver, "erro_relatorio_nao_achado")
        return False
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", linha)
        time.sleep(0.5)
        safe_click(driver, linha)
        time.sleep(1.0)
        print("[NAV] Linha CATE-1033 selecionada (1 clique)")
    except Exception:
        pass

    # Via principal gravada: botao Imprimir
    aberto = False
    try:
        btn_imp = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.ID, "handlebar-1093435")))
        try:
            btn_imp.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn_imp)
        print("[NAV] Botao Imprimir #handlebar-1093435 clicado (replay 18/09)")
    except Exception:
        print("[NAV-AVISO] #handlebar-1093435 nao achado, fallback duplo clique...")
        try:
            ActionChains(driver).double_click(linha).perform()
        except Exception:
            pass
    time.sleep(3)
    take_screenshot(driver, "06_relatorio_aberto")
    if _relatorio_abriu():
        print("[NAV] Relatorio CATE-1033 ABERTO via Imprimir")
        return True
    # Fallback: ENTER / Visualizar
    try:
        ActionChains(driver).double_click(linha).perform()
        time.sleep(0.8)
        try:
            linha.send_keys(Keys.ENTER)
        except Exception:
            pass
        time.sleep(3)
        if _relatorio_abriu():
            print("[NAV] Relatorio ABERTO no fallback")
            return True
    except Exception as e:
        print(f"[NAV] Fallback falhou: {e}")
    print("[ERRO] Relatorio nao abriu — veja 06_relatorio_aberto.png")
    try:
        diagnosticar_popups(driver, "RELATORIO_NAO_ABRIU")
    except Exception:
        pass
    return False


def preencher_datas_e_titulos(driver, inicio: str, fim: str) -> bool:
    """Passo 7-8: datas Inicio/Final (1x, global) + titulos=Ambos. Pula se ja preenchido."""
    print(f"[6/7] Preenchendo periodo {inicio} a {fim} + titulos=Ambos...")
    ok_ini = ok_fim = False
    for label, valor, flag in (("inicio", inicio, "ini"), ("final", inicio and fim, "fim")):
        _ = flag
    # Localiza inputs de data por label proximo (pula se valor ja confere)
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
                        try:
                            atual = (inp.get_attribute("value") or "").strip()
                        except Exception:
                            atual = ""
                        if atual == valor:
                            print(f"[FILTRO] {rotulo} ja={valor} (pulado)")
                            if rotulo.startswith("ini") or "nici" in rotulo:
                                ok_ini = True
                            else:
                                ok_fim = True
                            break
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
    # Titulos = Ambos (REPLAY GRAVADO: label#label_wid_10 / input#wid_10 value=A).
    # wid_* pode variar entre sessoes -> fallback generico abaixo.
    try:
        marcado = False
        try:
            lab10 = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "label_wid_10")))
            try:
                lab10.click()
            except Exception:
                driver.execute_script("arguments[0].click();", lab10)
            time.sleep(0.8)
            try:
                if driver.find_element(By.ID, "wid_10").is_selected():
                    print("[FILTRO] Titulos=Ambos via #label_wid_10 (verificado)")
                    marcado = True
            except Exception:
                marcado = True
        except Exception:
            pass
        if marcado:
            take_screenshot(driver, "06b_filtros_base")
            return True
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


_CACHE_DESCOBERTA: list | None = None


def carregar_lista_descoberta(driver) -> list:
    """Retorna [{'nome'}] do xlsx ja descoberto (172 itens) — SEM abrir modal.

    So redescobre (scroll no modal) se o arquivo nao existir. E por isso o
    scroll visivel sumia da rotina: a descoberta foi bootstrap 1x, agora e reuso.
    """
    xlsx_desc = OUTPUT_DIR / "estabelecimentos_descobertos.xlsx"
    if xlsx_desc.exists():
        try:
            import pandas as pd
            df = pd.read_excel(xlsx_desc)
            col = next((c for c in df.columns if "estabelec" in str(c).lower()), None)
            if col is None:
                col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            nomes = [str(v).strip() for v in df[col].tolist()]
            nomes = [n for n in nomes if n and n.lower() != "nan"]
            print(f"[LISTA] {len(nomes)} itens de {xlsx_desc.name} — sem scroll, direto ao check")
            return [{"nome": n} for n in nomes]
        except Exception as e:
            print(f"[LISTA-AVISO] {e} — redescobrindo no modal...")
    desc = descobrir_estabelecimentos(driver)
    if desc:
        salvar_descoberta_excel(desc)
    return [{"nome": d["estabelecimento"]} for d in desc]


def descobrir_estabelecimentos(driver, timeout_seg: int = 90) -> list:
    """Abre Filtro avancado > #WAFD-1 > raspa #table-items. CAPTURA UNICA por run.

    Retorna [{'ordem','estabelecimento'}] em memoria. Chamadas repetidas
    retornam o cache sem reabrir o modal.
    """
    global _CACHE_DESCOBERTA
    if _CACHE_DESCOBERTA is not None:
        print(f"[DESC] Reusando captura unica ({len(_CACHE_DESCOBERTA)} itens, sem recapturar)")
        return _CACHE_DESCOBERTA
    print("[DESC] Captura UNICA da lista (1x por run)...")
    if not clicar_por_texto(driver, 10, "Filtro avançado", "Filtro avancado", tag="*"):
        print("[DESC-ERRO] Link 'Filtro avancado' nao encontrado")
        take_screenshot(driver, "desc_erro_filtro")
        return []
    time.sleep(2)
    # Tipo Estabelecimento pelo ID exato (DOM: span#WAFD-1 dentro de #table-dimensions)
    try:
        el_tipo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "WAFD-1")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el_tipo)
        time.sleep(0.3)
        try:
            el_tipo.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el_tipo)
        time.sleep(2.0)
        print("[DESC] Tipo Estabelecimento (#WAFD-1) clicado")
    except Exception as e:
        print(f"[DESC-ERRO] #WAFD-1 nao clicado: {e}")
        take_screenshot(driver, "desc_erro_tipo")
        return []
    print("[DESC] Tipo Estabelecimento ativo. Raspando lista do meio...")
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
        print("[DESC] HTML do modal salvo em output/desc_modal.html")
    except Exception as e:
        print(f"[DESC-AVISO] Falha dump HTML: {e}")

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
        print(f"[DESC] coletados={len(vistos)} top={altura} sem_novos={sem_novos}")
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
    print(f"[DESC] Total descoberto (captura unica): {len(lista)} estabelecimentos")
    _CACHE_DESCOBERTA = lista
    return lista


def salvar_descoberta_excel(lista: list) -> Path | None:
    """Grava output/estabelecimentos_descobertos.xlsx p/ conferencia."""
    try:
        import pandas as pd
    except Exception as e:
        print(f"[DESC-ERRO] pandas indisponivel: {e}")
        return None
    OUTPUT_DIR.mkdir(exist_ok=True)
    destino = OUTPUT_DIR / "estabelecimentos_descobertos.xlsx"
    try:
        df = pd.DataFrame(lista, columns=["ordem", "estabelecimento"])
        df.to_excel(destino, index=False)
        print(f"[DESC] Excel conferencia -> {destino} ({len(df)} linhas)")
        return destino
    except Exception as e:
        print(f"[DESC-ERRO] Falha ao gravar Excel: {e}")
        return None


def selecionar_estabelecimento(driver, nome: str, timeout: int = 20) -> bool:
    """Filtro avancado: painel esq 'Estabelecimento' > painel meio pesquisa+checkbox > Selecionar."""
    print(f"[EXT] Selecionando estabelecimento '{nome}'...")
    if not clicar_por_texto(driver, 10, "Filtro avançado", "Filtro avancado", "Filtros avançados", "Filtros avancados", tag="*"):
        print("[ERRO] 'Filtro avancado' nao encontrado")
        take_screenshot(driver, "erro_filtros_avancados")
        return False
    time.sleep(2)
    take_screenshot(driver, "07a_filtros_avancados")
    # 1) Painel ESQUERDO pelo ID exato (DOM: span#WAFD-1)
    try:
        el_tipo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "WAFD-1")))
        try:
            el_tipo.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el_tipo)
        time.sleep(1.5)
        print("[EXT] Tipo 'Estabelecimento' (#WAFD-1) clicado")
    except Exception as e:
        print(f"[ERRO] #WAFD-1 nao clicado: {e}")
        take_screenshot(driver, "erro_tipo_estabelecimento")
        return False
    take_screenshot(driver, "07a1_tipo_estabelecimento")
    # 2) SEM busca: volta ao topo da lista e pega o PRIMEIRO item visivel
    # (lista alfabetica -> 1o = DaVita Advance). Nada e digitado.
    try:
        driver.execute_script(
            "var c = document.getElementById('table-items'); if (c) c.scrollTop = 0;")
        time.sleep(1.0)
    except Exception:
        pass
    take_screenshot(driver, "07a2_topo_lista")

    # 3) REPLAY GRAVADO: clique no 'div.check-element' interno da linha
    # (xpath gravado: #table-items/table/tbody/tr[N]/td/div[1]/div).
    # Localiza a linha pelo nome exato (cada item tem sua linha), clica no
    # check-element interno com clique nativo. Maquina de estados: 1 clique
    # -> reconfere fresco -> so clica de novo se ainda desmarcado.
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
                if " ".join((sp.text or "").split()).lower() == nome.strip().lower():
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
            print(f"[EXT] linha '{nome}' nao encontrada, retry...")
            time.sleep(1)
            continue
        if checked:
            print(f"[EXT] '{nome}' ja marcado (verificado fresco)")
            marcado = True
            break
        # desmarcado -> 1 clique nativo no check-element, depois reconfere
        try:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", check_el)
                time.sleep(0.4)
            except Exception:
                pass
            try:
                check_el.click()  # nativo, igual ao gravado
                print(f"[EXT] Clique nativo no check de '{nome}'")
            except Exception as e:
                print(f"[EXT] Nativo falhou ({e}), JS no TR...")
                try:
                    driver.execute_script("arguments[0].click();", tr)
                except Exception:
                    pass
            time.sleep(1.5)  # digest do Angular antes de reconferir
        except Exception as e:
            print(f"[EXT] passada com erro: {e}")
            time.sleep(1)
    if not marcado:
        print(f"[ERRO] '{nome}' nao marcado na lista do meio")
        take_screenshot(driver, "erro_estab_nao_achado")
        return False
    time.sleep(1)
    take_screenshot(driver, "07b_estab_marcado")
    # REPLAY GRAVADO: #submit-button (fallback: texto 'Selecionar')
    sel_ok = False
    try:
        btn_sel = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "submit-button")))
        try:
            btn_sel.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn_sel)
        sel_ok = True
        print("[EXT] #submit-button clicado")
    except Exception:
        sel_ok = clicar_por_texto(driver, 10, "Selecionar", tag="button")
    if not sel_ok:
        print("[ERRO] Botao Selecionar nao encontrado")
        return False
        print("[ERRO] Botao Selecionar nao encontrado")
        return False
    time.sleep(2)
    take_screenshot(driver, "07c_apos_selecionar")
    return True


def solicitar_xlsx_e_baixar(driver, download_dir: Path, timeout: int = 60) -> Path | None:
    """REPLAY 18/09: Exportar XLS #handlebar-1049356 > Continuar > download *.xls (XLS padrao)."""
    antes = ({p.name for p in download_dir.glob("*.xls*")}
             | {p.name for p in download_dir.glob("*.csv")}
             | {p.name for p in download_dir.glob("*.crdownload")})
    # 1) Exportar XLS direto (gravado 18/09, 3x seguidas)
    exp_ok = False
    try:
        btn_exp = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "handlebar-1049356")))
        try:
            btn_exp.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn_exp)
        exp_ok = True
        print("[DOWN] Exportar XLS #handlebar-1049356 clicado")
    except Exception:
        exp_ok = clicar_por_texto(driver, 8, "Exportar XLS", tag="*")
    if not exp_ok:
        print("[ERRO] Botao Exportar XLS nao encontrado")
        take_screenshot(driver, "erro_exportar_xls")
        return None
    time.sleep(2)
    take_screenshot(driver, "08a_pos_exportar")
    # 2) Continuar no ngdialog (XLS ja e padrao — sem dropdown)
    if not clicar_por_texto(driver, 10, "Continuar", tag="button"):
        print("[ERRO] Botao Continuar nao encontrado")
        take_screenshot(driver, "erro_continuar")
        return None
    print("[DOWN] Aguardando download do XLS...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not is_driver_alive(driver):
            break
        try:
            cr = list(download_dir.glob("*.crdownload"))
            cands = sorted(
                list(download_dir.glob("*.xls")) + list(download_dir.glob("*.xlsx")),
                key=lambda p: p.stat().st_mtime, reverse=True)
            novos = [c for c in cands if c.name not in antes]
            if novos and not cr:
                t1 = novos[0].stat().st_size
                time.sleep(0.5)
                if novos[0].stat().st_size == t1:
                    print(f"[DOWN] Arquivo pronto: {novos[0].name}")
                    return novos[0]
        except Exception:
            pass
        time.sleep(1)
    print("[ERRO] Timeout aguardando XLS")
    take_screenshot(driver, "erro_download_timeout")
    return None


def limpar_estabelecimento(driver, timeout: int = 10) -> bool:
    """REPLAY 18/09: clica no X da caixa inferior (div.w-token-clear em #checkout-content)."""
    try:
        x_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#checkout-content div.w-token-clear")))
        try:
            x_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", x_btn)
        print("[EXT] Estabelecimento removido via X (w-token-clear)")
        time.sleep(1.5)
        return True
    except Exception as e:
        print(f"[AVISO] X de limpeza nao clicado: {e}")
        take_screenshot(driver, "erro_limpar_estab")
        return False


def validar_tsv_baixado(caminho: Path) -> str:
    """Valida o .xls cru do Tasy (na verdade TSV). Retorna 'ok' | 'vazio' | 'invalido'.

    - 'ok': cabecalho TSV presente + >=1 linha de dados.
    - 'vazio': so cabecalho (estabelecimento sem dados no periodo) — aceita, sem retry.
    - 'invalido': sem cabecalho / ilegivel / truncado — pede retry.
    """
    try:
        if not caminho.exists() or caminho.stat().st_size < 10:
            return "invalido"
        raw = caminho.read_bytes()[:2000]
        texto = raw.decode("latin-1", errors="replace")
        if "Location Estab Conta" not in texto or "\t" not in texto:
            print(f"[VALID] {caminho.name}: cabecalho TSV ausente -> invalido")
            return "invalido"
        with open(caminho, encoding="latin-1", errors="replace") as f:
            linhas = [ln for ln in (l.strip() for l in f) if ln]
        if len(linhas) <= 1:
            print(f"[VALID] {caminho.name}: so cabecalho ({caminho.stat().st_size}B) -> vazio")
            return "vazio"
        print(f"[VALID] {caminho.name}: {len(linhas)-1} linha(s) -> ok")
        return "ok"
    except Exception as e:
        print(f"[VALID] Falha ao ler {caminho.name}: {e} -> invalido")
        return "invalido"


def converter_tsv_para_xlsx(origem: Path, nome_estab: str) -> Path | None:
    """Converte o TSV cru em XLSX real na pasta 1033 (elimina o alerta do Excel).

    Apaga qualquer destino homonimo (.xls/.xlsx) antes de gravar.
    """
    import pandas as pd

    destino_dir = pasta_downloads_1033()
    base = sanitizar_nome(nome_estab)
    destino = destino_dir / f"{base}.xlsx"
    for velho in (destino_dir / f"{base}.xls", destino):
        try:
            if velho.exists():
                velho.unlink()
        except Exception:
            pass
    try:
        df = pd.read_csv(origem, sep="\t", encoding="latin-1", dtype=str, engine="python")
        df.to_excel(destino, index=False)
        print(f"[ARQ] Convertido -> {destino.name} ({len(df)} linha(s))")
        try:
            origem.unlink()
        except Exception:
            pass
        return destino
    except Exception as e:
        print(f"[ARQ-ERRO] Conversao TSV->XLSX falhou ({origem.name}): {e}")
        return None


def baixar_com_retry(driver, download_dir: Path, nome_estab: str, max_tent: int = 3,
                     timeout: int = 60) -> tuple[str, Path | None]:
    """Exportar XLS > Continuar com ate max_tent tentativas.

    Retorna ('ok'|'vazio'|'falha', caminho_xlsx_final|None). Parciais invalidos
    sao apagados (Downloads e 1033) antes de repetir. 'vazio' nao repete.
    """
    destino_dir = pasta_downloads_1033()
    base = sanitizar_nome(nome_estab)
    for tentativa in range(1, max_tent + 1):
        if tentativa > 1:
            print(f"[RETRY] {nome_estab}: tentativa {tentativa}/{max_tent}")
            time.sleep(3)
        baixado = solicitar_xlsx_e_baixar(driver, download_dir, timeout=timeout)
        if baixado is None:
            print(f"[RETRY] {nome_estab}: sem arquivo (tentativa {tentativa})")
            continue
        status = validar_tsv_baixado(baixado)
        if status == "invalido":
            for p in (baixado, destino_dir / f"{base}.xls", destino_dir / f"{base}.xlsx"):
                try:
                    if p.exists():
                        p.unlink()
                except Exception:
                    pass
            print(f"[RETRY] {nome_estab}: invalido apagado (tentativa {tentativa})")
            continue
        final = converter_tsv_para_xlsx(baixado, nome_estab)
        if final is None:
            continue
        return (status, final)
    return ("falha", None)


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
            print("[3.5/4] Fechando popups pos-login (max 8s, sai antes se limpar)...")
            take_screenshot(driver, "03a_antes_popup")
            try:
                diagnosticar_popups(driver, "ANTES")
                n_popup = fechar_popups_pos_login(driver, timeout_total=8, per_wait=0.5)
                print(f"[INFO] Popups fechados: {n_popup}")
                diagnosticar_popups(driver, "DEPOIS")
            except Exception as e:
                print(f"[AVISO] Falha no fechador generico: {e}")
            take_screenshot(driver, "03b_apos_popup")
            take_screenshot(driver, "03_pos_login")
            time.sleep(1)
            take_screenshot(driver, "04_final")

        # ── FLUXO 1033 (passos 1-13 do roteiro) ──
        if not is_driver_alive(driver):
            print("[FIM] Navegador fechado antes do 1033.")
            return
        extracao_cfg = params.get("extracao", {})
        limite_teste = int(extracao_cfg.get("limite_teste", 1))
        download_dir = Path.home() / "Downloads"
        pasta1033 = pasta_downloads_1033(limpar=True)
        print(f"[CFG] Pasta 1033: {pasta1033} | limite_teste={limite_teste}")

        if not navegar_ate_relatorio_1033(driver, timeout=20):
            print("[FIM] Falha na navegacao ate o 1033. Veja screenshots 05*.")
            take_screenshot(driver, "erro_fluxo_1033")
            return

        # Periodo GLOBAL (parametros.json > extracao.periodo) — preenchido 1x.
        periodo = extracao_cfg.get("periodo", {}) or {}
        data_inicio = str(periodo.get("data_inicio", "")).strip()
        data_fim = str(periodo.get("data_fim", "")).strip()
        if not data_inicio or not data_fim:
            print("[ERRO] Periodo global ausente em parametros.json > extracao.periodo (data_inicio/data_fim)")
            take_screenshot(driver, "erro_periodo_global")
            return
        print(f"[CFG] Periodo global: {data_inicio} a {data_fim}")
        preencher_datas_e_titulos(driver, data_inicio, data_fim)

        # Lista reaproveitada do xlsx (sem modal/scroll); loop baixa 1 CSV por item.
        estabelecimentos = carregar_lista_descoberta(driver)
        if not estabelecimentos:
            print("[FIM] Lista vazia. Veja desc_*.png")
            return
        if limite_teste and limite_teste > 0:
            estabelecimentos = estabelecimentos[:limite_teste]
            print(f"[MODO TESTE] Executando apenas {len(estabelecimentos)} estabelecimento(s). "
                  f"Para rodar todos, ajuste extracao.limite_teste=0 em parametros.json")

        ok_count = fail = vazios = 0
        for idx, est in enumerate(estabelecimentos, 1):
            if not is_driver_alive(driver):
                print("[ENCERRADO] Navegador fechado durante o loop.")
                break
            print(f"\n===== [{idx}/{len(estabelecimentos)}] {est['nome']} "
                  f"({data_inicio} a {data_fim}) =====")
            try:
                if not selecionar_estabelecimento(driver, est["nome"]):
                    print(f"[FALHA] {est['nome']}: nao selecionou")
                    fail += 1
                    continue
                status, final = baixar_com_retry(driver, download_dir, est["nome"], max_tent=3)
                if status == "falha":
                    print(f"[FALHA] {est['nome']}: sem download apos 3 tentativas")
                    fail += 1
                elif status == "vazio":
                    print(f"[VAZIO] {est['nome']}: sem dados no periodo (aceito)")
                    vazios += 1
                    take_screenshot(driver, f"09_vazio_{sanitizar_nome(est['nome'])[:30]}")
                else:
                    print(f"[OK] {est['nome']}: {final.name}")
                    ok_count += 1
                    take_screenshot(driver, f"09_ok_{sanitizar_nome(est['nome'])[:30]}")
            except Exception as e:
                print(f"[FALHA] {est['nome']}: {e}")
                take_screenshot(driver, "erro_estabelecimento")
                fail += 1
            finally:
                # REPLAY 18/09: limpa o X da caixa inferior p/ o proximo item (sucesso ou falha)
                if idx < len(estabelecimentos) and is_driver_alive(driver):
                    try:
                        limpar_estabelecimento(driver)
                    except Exception:
                        pass
            time.sleep(int(auto.get("intervalo_entre_coletas_segundos", 2)))
        print(f"\n[4/4] FLUXO 1033 CONCLUIDO — ok={ok_count} vazios={vazios} falhas={fail} pasta={pasta1033}")
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
