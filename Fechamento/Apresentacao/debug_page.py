import json
from selenium import webdriver
import time

def main():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    driver = webdriver.Edge()
    driver.get(config["url"])
    time.sleep(5)
    
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    print(f"Titulo: {driver.title}")
    print("Page source salvo em page_source.html")
    driver.quit()

if __name__ == "__main__":
    main()
