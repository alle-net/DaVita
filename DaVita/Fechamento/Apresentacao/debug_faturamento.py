import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
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

# Lista TODOS os inputs com name contendo "mes" ou "de" ou "ate"
inputs = driver.find_elements(By.CSS_SELECTOR, "input")
print(f"Total inputs: {len(inputs)}")
for i, inp in enumerate(inputs):
    attrs = {}
    for a in ["type", "name", "id", "placeholder", "class"]:
        v = inp.get_attribute(a)
        if v:
            attrs[a] = v
    print(f"  Input {i}: {attrs}")

# Verifica selects
selects = driver.find_elements(By.CSS_SELECTOR, "select")
print(f"\nTotal selects: {len(selects)}")
for i, sel in enumerate(selects):
    print(f"  Select {i}: name={sel.get_attribute('name')}, options={len(sel.find_elements(By.TAG_NAME, 'option'))}")

# Labels
labels = driver.find_elements(By.TAG_NAME, "label")
print("\nLabels:")
for lbl in labels:
    t = lbl.text.strip()
    if t:
        print(f"  '{t}'")

# Clica em CONSULTAR
select_elem = driver.find_element(By.NAME, "empresa")
from selenium.webdriver.support.ui import Select as Sel
Sel(select_elem).select_by_visible_text("DaVita Amazonia")
time.sleep(1)

# Clica no campo de mes_de para ver o calendario
mes_de = driver.find_element(By.NAME, "mes_de")
print(f"\nCampo mes_de: value='{mes_de.get_attribute('value')}'")
mes_de.click()
time.sleep(2)

# Verifica o que apareceu (dropdown de mes/ano)
dropdowns = driver.find_elements(By.CSS_SELECTOR, "select")
print(f"\nDropdowns apos clicar no calendario: {len(dropdowns)}")
for i, d in enumerate(dropdowns):
    print(f"  Dropdown {i}: name={d.get_attribute('name')}, options={[o.text for o in d.find_elements(By.TAG_NAME, 'option')]}")

# Verifica se ha um calendario aberto
calendar_elements = driver.find_elements(By.CSS_SELECTOR, "div.calendar, table.pika-lendar, .pika-table")
print(f"\nCalendar elements: {len(calendar_elements)}")

all_elements = driver.find_elements(By.CSS_SELECTOR, "select, input")
print(f"\nTodos os inputs/selects visiveis agora:")
for j, el in enumerate(all_elements):
    tag = el.tag_name
    name = el.get_attribute("name")
    value = el.get_attribute("value")
    visible = el.is_displayed()
    print(f"  [{j}] {tag} name='{name}' value='{value}' visible={visible}")

input("\nPressione Enter para fechar...")
driver.quit()
