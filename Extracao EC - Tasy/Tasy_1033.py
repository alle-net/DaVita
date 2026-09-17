import json
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
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.protocol_handler": 2,
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
        " | //button[contains(@class,'gwt-Button')]"
        " | //button[contains(@class,'btn-gray')]"
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
                if txt not in ("fechar", "ok", "okay", "entendi"):
                    # So aceita gwt/btn-gray fora da lista se estiver em dialog
                    cls = (btn.get_attribute("class") or "").lower()
                    if "gwt-button" not in cls and "btn-gray" not in cls:
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
        print("[4/4] FLUXO CONCLUIDO")
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
