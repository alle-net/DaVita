import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

config = json.load(open("config.json"))
driver = webdriver.Edge()
driver.get(config["url"])
driver.find_element(By.NAME, "username").send_keys(config["usuario"])
driver.find_element(By.NAME, "password").send_keys(config["senha"])
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
WebDriverWait(driver, 15).until(EC.url_changes(config["url"]))
time.sleep(3)

driver.find_element(By.XPATH, "//button[contains(text(), 'Relat')]").click()
time.sleep(2)
driver.find_element(By.XPATH, "//button[contains(text(), 'Produ')]").click()
time.sleep(5)

inputs = driver.find_elements(By.TAG_NAME, "input")
print(f"Total inputs: {len(inputs)}")
for i, inp in enumerate(inputs):
    attrs = {}
    for attr in ["type", "name", "id", "placeholder", "class", "value"]:
        v = inp.get_attribute(attr)
        if v:
            attrs[attr] = v
    print(f"  Input {i}: {attrs}")

labels = driver.find_elements(By.TAG_NAME, "label")
for i, lbl in enumerate(labels):
    t = lbl.text.strip()
    if t:
        print(f"  Label {i}: '{t}'")

buttons = driver.find_elements(By.TAG_NAME, "button")
print(f"Total buttons: {len(buttons)}")
for i, btn in enumerate(buttons):
    t = btn.text.strip()
    print(f"  Button {i}: '{t}'")

driver.quit()
