import json
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
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
    options.page_load_strategy = "none"
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(timeout)
    return driver


def find_element(driver, timeout: int, *locators):
    wait = WebDriverWait(driver, timeout)
    for by, value in locators:
        try:
            element = wait.until(EC.element_to_be_clickable((by, value)))
            return element
        except Exception:
            continue
    return None


def take_screenshot(driver, name: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{name}_{stamp}.png"
    driver.save_screenshot(str(path))
    return path


def click_ok_in_popup(driver, timeout: int) -> bool:
    checkbox = find_element(
        driver,
        timeout,
        (By.ID, "do-not-ask-again"),
        (By.XPATH, "//input[@type='checkbox']"),
    )
    if checkbox:
        if not checkbox.is_selected():
            try:
                checkbox.click()
            except Exception:
                pass

    for txt in ["ok", "OK", "Ok", "okay"]:
        try:
            btn = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//button[normalize-space(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'))='{txt.lower()}']")
                )
            )
            btn.click()
            return True
        except Exception:
            continue

    try:
        btn = find_element(
            driver,
            timeout,
            (By.CSS_SELECTOR, "button.gwt-Button"),
            (By.XPATH, "//button[contains(., 'OK')]"),
            (By.XPATH, "//button[contains(., 'Ok')]"),
        )
        if btn:
            btn.click()
            return True
    except Exception:
        pass
    return False


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
        time.sleep(3)
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

        dialog_handler.start(timeout=120)
        print("[3/4] Enviando login (aguardando certificado)...")
        password_field.send_keys(Keys.ENTER)

        logado = False
        for attempt in range(30):
            time.sleep(2)
            try:
                handles = driver.window_handles
                if len(handles) > 1:
                    driver.switch_to.window(handles[-1])
                    print(f"[INFO] Nova aba detectada: {handles[-1]}")
                click_ok_in_popup(driver, 3)
            except Exception:
                pass
            try:
                url_atual = driver.current_url or ""
                if url_atual and "login" not in url_atual.lower() and url_atual != url:
                    logado = True
                    break
            except Exception:
                continue
            print(f"    ... aguardando ({attempt + 1}/30)")

        if logado:
            print("LOGIN APARENTEMENTE OK")
            print(f"URL atual: {driver.current_url}")
        else:
            print("ATENCAO: pode ainda estar na tela de login ou popup pendente")

        try:
            handles = driver.window_handles
            if len(handles) > 1:
                driver.switch_to.window(handles[-1])
        except Exception:
            pass

        take_screenshot(driver, "03_pos_login")
        time.sleep(3)
        take_screenshot(driver, "04_final")
        print("[4/4] FLUXO CONCLUIDO")
    finally:
        dialog_handler.stop()
        driver.quit()


if __name__ == "__main__":
    main()
