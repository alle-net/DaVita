import json
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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


def main() -> None:
    params = load_params()
    tasy = params["tasy"]
    auto = params["automacao"]

    url = tasy["url"].strip()
    usuario = tasy["usuario"].strip()
    senha = tasy["senha"].strip()

    if not all([url, usuario, senha]):
        raise SystemExit("Preencha url, usuario e senha em parametros.json")

    driver = make_driver(auto["timeout_segundos"])
    try:
        driver.get(url)
        WebDriverWait(driver, auto["timeout_segundos"]).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        take_screenshot(driver, "01_pagina_inicial")

        user_field = find_element(
            driver,
            auto["timeout_segundos"],
            (By.ID, "username"),
            (By.ID, "user"),
            (By.ID, "login"),
            (By.NAME, "username"),
            (By.NAME, "user"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[contains(@id,'user')]"),
            (By.XPATH, "//input[contains(@name,'user')]"),
            (By.XPATH, "//input[contains(@placeholder,'usu')]"),
        )
        password_field = find_element(
            driver,
            auto["timeout_segundos"],
            (By.ID, "password"),
            (By.ID, "senha"),
            (By.NAME, "password"),
            (By.NAME, "senha"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[contains(@id,'sen') or contains(@id,'pass')]"),
        )

        if not user_field or not password_field:
            take_screenshot(driver, "erro_campos_login_nao_encontrados")
            raise SystemExit("Campos de usuario/senha nao encontrados na pagina.")

        user_field.clear()
        user_field.send_keys(usuario)
        password_field.clear()
        password_field.send_keys(senha)
        take_screenshot(driver, "02_login_preenchido")

        password_field.submit()
        try:
            WebDriverWait(driver, auto["timeout_segundos"]).until(
                lambda d: d.current_url != url
                or d.execute_script("return document.readyState") == "complete"
            )
        except Exception:
            pass

        if "login" not in driver.current_url.lower():
            print("LOGIN APARENTEMENTE OK")
        else:
            print("ATENCAO: pagina ainda pode estar na tela de login")

        take_screenshot(driver, "03_pos_login")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()