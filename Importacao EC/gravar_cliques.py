import json
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait

BASE_DIR = Path(__file__).resolve().parent
PARAMS_PATH = BASE_DIR / "parametros.json"
LOG_PATH = BASE_DIR / "cliques_registrados.txt"

MESSAGES = {
    "ativo": "[GRAVADOR ATIVO]",
    "login": "Faça o login e clique livremente nos elementos.",
    "encerrar": "Para ENCERRAR: feche a janela do Edge.",
    "fechado": "[ENCERRADO] Janela do navegador fechada ou sessao perdida.",
    "ok": "[OK] cliques capturados -> cliques_registrados.txt",
    "banner": "=" * 70,
    "titulo": "GRAVADOR DE CLIQUES ATIVO EM ",
    "aviso": "[AVISO]",
}


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def load_params() -> dict:
    with open(PARAMS_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_recorder_js() -> str:
    return r"""
(function () {
    if (window.__clickRecorderInstalled) { return; }
    window.__clickRecorderInstalled = true;

    function cssPath(el) {
        if (!(el instanceof Element)) return '';
        if (el.id) return '#' + CSS.escape(el.id);
        const parts = [];
        const max = 5;
        while (el && el.nodeType === 1 && parts.length < max) {
            let selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + CSS.escape(el.id);
                parts.unshift(selector);
                break;
            }
            if (el.className && typeof el.className === 'string') {
                selector += '.' + el.className.trim().split(/\s+/).join('.');
            }
            const parent = el.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(s => s !== el);
                if (siblings.length > 0) {
                    const idx = Array.from(parent.children).indexOf(el) + 1;
                    selector += ':nth-of-type(' + el.nodeName.toLowerCase() + ':nth-child(' + idx + '))';
                }
            }
            parts.unshift(selector);
            el = parent;
        }
        return parts.join(' > ');
    }

    function xpath(el) {
        if (!(el instanceof Element)) return '';
        if (el.id) return '//*[@id="' + el.id + '"]';
        const parts = [];
        let node = el;
        while (node && node.nodeType === 1) {
            if (node.id) { parts.unshift('*[@id="' + node.id + '"]'); break; }
            let part = node.nodeName.toLowerCase();
            const parent = node.parentNode;
            if (parent) {
                const siblings = Array.from(parent.children).filter(s => s.nodeName === node.nodeName);
                if (siblings.length > 1) {
                    part += '[' + (siblings.indexOf(node) + 1) + ']';
                }
            }
            parts.unshift(part);
            node = node.parentNode;
            if (node === document.documentElement) break;
        }
        return '/html/' + parts.join('/');
    }

    document.addEventListener('click', function (e) {
        const target = e.target;
        const rec = {
            timestamp: new Date().toISOString(),
            tag: target.tagName,
            css: cssPath(target),
            xpath: xpath(target),
            text: (target.textContent || '').trim().slice(0, 120),
            value: (target.value || ''),
            type: target.getAttribute('type') || '',
            placeholders: target.getAttribute('placeholder') || ''
        };
        window.__cliquesRegistrados = window.__cliquesRegistrados || [];
        window.__cliquesRegistrados.push(rec);
        console.log('[CLIQUE] ' + JSON.stringify(rec));
    }, true);

    document.addEventListener('input', function (e) {
        const target = e.target;
        if (!target || typeof target.value === 'undefined') return;
        const rec = {
            timestamp: new Date().toISOString(),
            event: 'input',
            tag: target.tagName,
            css: cssPath(target),
            xpath: xpath(target),
            text: (target.value || '').trim().slice(0, 200),
            type: target.getAttribute('type') || '',
            placeholders: target.getAttribute('placeholder') || ''
        };
        window.__cliquesRegistrados = window.__cliquesRegistrados || [];
        window.__cliquesRegistrados.push(rec);
        console.log('[INPUT] ' + JSON.stringify(rec));
    }, true);

    window.__dumpCliques = function () {
        return JSON.stringify(window.__cliquesRegistrados || [], null, 2);
    };
})();
"""


def log_to_file(records) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n===== Sessao de gravacao: {stamp} =====\n")
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> None:
    params = load_params()
    tasy = params["tasy"]
    auto = params["automacao"]
    url = tasy["url"].strip()

    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(auto["timeout_segundos"])

    driver.get(url)
    time.sleep(1.5)

    safe_print("=" * 70)
    safe_print(MESSAGES["titulo"] + url)
    safe_print(MESSAGES["login"])
    safe_print(MESSAGES["encerrar"])
    safe_print("=" * 70)

    injected_pages = []
    try:
        while True:
            try:
                WebDriverWait(driver, auto["timeout_segundos"]).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                driver.execute_script(build_recorder_js())
                current = driver.execute_script("return location.href")
                if current not in injected_pages:
                    injected_pages.append(current)
                    safe_print(f"{MESSAGES['ativo']} {current}")

                dump = driver.execute_script(
                    "return window.__dumpCliques ? window.__dumpCliques() : '[]'"
                )
                records = json.loads(dump)
                if records:
                    log_to_file(records)
                    safe_print(f"[OK] {len(records)} {MESSAGES['ok']}")
                    driver.execute_script("window.__cliquesRegistrados = []")
            except Exception:
                safe_print(MESSAGES["fechado"])
                break
            time.sleep(2)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()