import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import time

config = json.load(open("config.json"))
driver = webdriver.Edge()
wait = WebDriverWait(driver, 15)

driver.get(config["url"])
wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(config["usuario"])
driver.find_element(By.NAME, "password").send_keys(config["senha"])
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
wait.until(EC.url_changes(config["url"]))
time.sleep(3)

wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Relat')]"))).click()
time.sleep(2)
driver.find_element(By.XPATH, "//*[contains(text(), 'Faturamento') and contains(text(), 'Mensal')]").click()
time.sleep(5)

select_elem = driver.find_element(By.NAME, "empresa")
Select(select_elem).select_by_visible_text("DaVita Amazonia")
time.sleep(1)

print("=== Testando metodo 1: send_keys direto ===")
de_input = driver.find_element(By.NAME, "mes_de")
de_input.clear()
time.sleep(0.3)
de_input.click()
time.sleep(0.3)
for char in "2026-04":
    de_input.send_keys(char)
    time.sleep(0.05)
de_input.send_keys(Keys.TAB)
time.sleep(2)
print(f"De value: '{de_input.get_attribute('value')}'")

ate_input = driver.find_element(By.NAME, "mes_ate")
ate_input.clear()
time.sleep(0.3)
ate_input.click()
time.sleep(0.3)
for char in "2026-04":
    ate_input.send_keys(char)
    time.sleep(0.05)
ate_input.send_keys(Keys.TAB)
time.sleep(2)
print(f"Ate value: '{ate_input.get_attribute('value')}'")

print("Verifique o metodo 1 (send_keys) no navegador...")
time.sleep(8)
de_input = driver.find_element(By.NAME, "mes_de")
driver.execute_script("""
    var el = document.querySelector('input[name="mes_de"]');
    el.value = '';
    el.dispatchEvent(new Event('input', {bubbles: true}));
""")
time.sleep(0.5)
driver.execute_script("""
    var el = document.querySelector('input[name="mes_de"]');
    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(el, '2026-04');
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
""")
time.sleep(2)
print(f"De value: '{de_input.get_attribute('value')}'")

ate_input = driver.find_element(By.NAME, "mes_ate")
driver.execute_script("""
    var el = document.querySelector('input[name="mes_ate"]');
    el.value = '';
    el.dispatchEvent(new Event('input', {bubbles: true}));
""")
time.sleep(0.5)
driver.execute_script("""
    var el = document.querySelector('input[name="mes_ate"]');
    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(el, '2026-04');
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
""")
time.sleep(2)
print(f"Ate value: '{ate_input.get_attribute('value')}'")

print("Verifique o metodo 2 (JavaScript) no navegador...")
time.sleep(8)
de_input = driver.find_element(By.NAME, "mes_de")
actions = ActionChains(driver)
actions.click(de_input).perform()
time.sleep(0.5)
de_input.send_keys(Keys.CONTROL + "a")
time.sleep(0.2)
de_input.send_keys("2026-04")
time.sleep(1)
print(f"De value: '{de_input.get_attribute('value')}'")

ate_input = driver.find_element(By.NAME, "mes_ate")
actions = ActionChains(driver)
actions.click(ate_input).perform()
time.sleep(0.5)
ate_input.send_keys(Keys.CONTROL + "a")
time.sleep(0.2)
ate_input.send_keys("2026-04")
time.sleep(1)
print(f"Ate value: '{ate_input.get_attribute('value')}'")

print("Verifique o metodo 3 (ActionChains) no navegador...")
time.sleep(8)
driver.quit()
