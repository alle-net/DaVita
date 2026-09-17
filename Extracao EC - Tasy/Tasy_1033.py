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
