import json
import sys
import shutil
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import time
import os
import glob
from datetime import datetime

# Garante impressao correta de acentos no console Windows (cp1252 -> utf-8)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MESES = {
    "jan": "01", "fev": "02", "mar": "03", "abr": "04",
    "mai": "05", "jun": "06", "jul": "07", "ago": "08",
    "set": "09", "out": "10", "nov": "11", "dez": "12"
}

TIMEOUT_CARREGAMENTO = 600
TIMEOUT_DOWNLOAD = 1200
TIMEOUT_NOVO_ARQUIVO = 300  # espera maxima por UM download (segundos)
MAX_TENTATIVAS_DOWNLOAD = 3  # retry por unidade antes de marcar FALHA
CARACTERES_INVALIDOS_ARQUIVO = '<>:"/\\|?*'

# ---------------------------------------------------------------------------
# Nomes com acentos (Goiânia, João Pessoa, Sumaré, Vitória, Taubaté...).
# O Excel pode trazer espaços extras / NBSP e normalizacoes diferentes do
# texto exibido no <select> do site. Todas as comparacoes passam por aqui.
# ---------------------------------------------------------------------------
def normalizar_nome(texto):
    if texto is None:
        return ""
    s = str(texto).replace("\xa0", " ")  # NBSP -> espaco comum
    s = unicodedata.normalize("NFC", s)
    s = " ".join(s.strip().split())  # tira espacos duplos / bordas
    return s


def _sem_acentos(texto):
    s = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def sanitizar_nome_arquivo(nome_unidade):
    base = normalizar_nome(nome_unidade)
    for ch in CARACTERES_INVALIDOS_ARQUIVO:
        base = base.replace(ch, "_")
    return base.strip().rstrip(".")  # Windows ignora ponto/espaco final


def selecionar_unidade(select_elem, nome_unidade):
    """Seleciona a unidade no <select>, tolerando acentos/espacos/case.

    Retorna True se conseguiu, False caso contrario (sem lancar excecao).
    """
    from selenium.webdriver.support.ui import Select as _Select
    alvo = normalizar_nome(nome_unidade)
    alvo_flat = _sem_acentos(alvo)
    try:
        _Select(select_elem).select_by_visible_text(alvo)
        return True
    except Exception:
        pass
    try:
        for opt in _Select(select_elem).options:
            txt = normalizar_nome(opt.text)
            if _sem_acentos(txt) == alvo_flat or alvo_flat in _sem_acentos(txt):
                _Select(select_elem).select_by_visible_text(opt.text)
                return True
    except Exception as e:
        print(f"  ERRO ao selecionar unidade '{alvo}': {e}")
        return False
    print(f"  ERRO: unidade '{alvo}' nao encontrada nas opcoes do site")
    return False

def aguardar_excel_visivel(driver, timeout=TIMEOUT_CARREGAMENTO):
    print(f"  Aguardando dados...", end=" ", flush=True)
    inicio = time.time()
    while time.time() - inicio < timeout:
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if "Excel" in btn.text and btn.is_displayed():
                print("pronto")
                return True
        time.sleep(2)
    print("TIMEOUT")
    return False

def clicar_excel(driver):
    for btn in driver.find_elements(By.TAG_NAME, "button"):
        if "Excel" in btn.text and btn.is_displayed():
            driver.execute_script("arguments[0].click();", btn)
            return True
    return False


def aguardar_tabela_carregada(driver, timeout=30):
    """Espera a tabela de resultados carregar APOS o botao Excel aparecer.

    Retorna 'com_dados' (prossegue p/ download imediato, sem sleep fixo),
    'vazia' (site informa 'Nenhum registro' -> pula o download) ou
    'inconclusivo' (timeout -> segue o fluxo antigo com download).
    Na duvida, SEMPRE retorna inconclusivo: nunca pula unidade com dados.
    """
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            body = driver.find_element(By.TAG_NAME, "body").text
            if "Nenhum registro encontrado" in body:
                return "vazia"
            for t in driver.find_elements(By.TAG_NAME, "table"):
                if len(t.find_elements(By.TAG_NAME, "tr")) > 1:
                    return "com_dados"
        except Exception:
            pass
        time.sleep(1)
    return "inconclusivo"

def load_config():
    if not os.path.exists("config.json"):
        import shutil
        if os.path.exists("config_example.json"):
            shutil.copy("config_example.json", "config.json")
            print("config.json criado a partir de config_example.json.")
            print("EDITe config.json com seus dados (usuario, senha) antes de executar novamente.")
        else:
            print("ERRO: Nenhum arquivo de configuracao encontrado (config.json ou config_example.json)")
        exit(1)
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def converter_data(mes_abrev, ano):
    mes_abrev = mes_abrev.strip().lower()[:3]
    mes_num = MESES.get(mes_abrev)
    if not mes_num:
        raise ValueError(f"Mês desconhecido: '{mes_abrev}'")
    return f"{ano}-{mes_num}"

def preencher_campo_js(driver, nome_campo, valor):
    valor_json = json.dumps(valor)
    nome_json = json.dumps(nome_campo)
    driver.execute_script(f"""
        var el = document.querySelector('input[name={nome_json}]');
        if (!el) return;
        el.focus();
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(el, {valor_json});
        el.dispatchEvent(new Event('input', {{bubbles: true}}));
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
        el.blur();
    """)

def preencher_data(driver, nome_campo, valor):
    preencher_campo_js(driver, nome_campo, valor)
    el = driver.find_element(By.NAME, nome_campo)
    if el.get_attribute("value") == valor:
        return True

    el.clear()
    el.click()
    el.send_keys(Keys.CONTROL + "a")
    el.send_keys(valor)
    el.send_keys(Keys.TAB)
    time.sleep(1)
    if el.get_attribute("value") == valor:
        return True

    actions = ActionChains(driver)
    actions.click(el).perform()
    el.send_keys(Keys.CONTROL + "a")
    el.send_keys(valor)
    el.send_keys(Keys.TAB)
    time.sleep(1)
    return el.get_attribute("value") == valor

def _tem_arquivo_temporario(pasta_salvar):
    try:
        for f in os.listdir(pasta_salvar):
            if (f.endswith(('.crdownload', '.part', '.tmp'))
                    or f.startswith('~$')
                    or f.endswith('.download')):
                return True
    except FileNotFoundError:
        pass
    return False


def _tamanho_estavel(caminho, verificacoes=2, intervalo=1.0):
    """Confirma que o download terminou (tamanho para de crescer)."""
    try:
        anterior = -1
        iguais = 0
        for _ in range(verificacoes):
            atual = os.path.getsize(caminho)
            if atual == anterior and atual > 0:
                iguais += 1
                if iguais >= verificacoes - 1:
                    return True
            else:
                iguais = 0
            anterior = atual
            time.sleep(intervalo)
        return iguais >= verificacoes - 1
    except OSError:
        return False


def esperar_download(pasta_salvar, timeout=TIMEOUT_DOWNLOAD):
    """Mantida por compatibilidade: espera qualquer download estabilizar."""
    resultado = esperar_novo_download(pasta_salvar, set(), timeout=timeout)
    return resultado is not None


def esperar_novo_download(pasta_salvar, arquivos_antes, timeout=TIMEOUT_NOVO_ARQUIVO):
    """Espera surgir um arquivo NOVO apos o clique no botao Excel.

    Corrige o bug antigo: a versao anterior retornava True imediatamente
    porque ja existiam arquivos completos de unidades anteriores na pasta,
    sem esperar o download atual terminar (gerava arquivos vazios/trocados).
    Retorna o caminho do novo arquivo ou None em caso de timeout/bloqueio.
    """
    inicio = time.time()
    # Fase 1: aguarda o navegador iniciar o download (ate 60s). Se nada
    # surgir e nao ha temporarios, provavelmente o clique falhou ou o
    # Edge bloqueou (antivirus/SmartScreen) -> desiste cedo p/ retry.
    while time.time() - inicio < min(60, timeout):
        try:
            atuais = set(
                os.path.normpath(os.path.abspath(p))
                for p in glob.glob(os.path.join(pasta_salvar, "*"))
                if os.path.isfile(p)
            )
        except Exception:
            atuais = set()
        novos = atuais - arquivos_antes
        novos_reais = [p for p in novos
                       if not os.path.basename(p).startswith('~$')]
        if novos_reais or _tem_arquivo_temporario(pasta_salvar):
            break
        time.sleep(1)
    else:
        pass

    # Fase 2: aguarda os temporarios (.crdownload) desaparecerem.
    while time.time() - inicio < timeout:
        if not _tem_arquivo_temporario(pasta_salvar):
            break
        time.sleep(1)

    if _tem_arquivo_temporario(pasta_salvar):
        print("  AVISO: Timeout aguardando download (possivel bloqueio antivirus do navegador)")
        return None

    time.sleep(1)
    try:
        arquivos_depois = set(
            os.path.normpath(os.path.abspath(p))
            for p in glob.glob(os.path.join(pasta_salvar, "*"))
            if os.path.isfile(p)
        )
    except Exception:
        return None
    novos = [p for p in (arquivos_depois - arquivos_antes)
             if not os.path.basename(p).startswith('~$')
             and not p.endswith(('.crdownload', '.part', '.tmp', '.download'))]
    if not novos:
        return None
    # O mais recente e o do download atual.
    novos.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    candidato = novos[0]
    if not _tamanho_estavel(candidato):
        print("  AVISO: arquivo ainda crescendo apos estabilizacao")
        return None
    return candidato


def validar_excel(caminho):
    """Abre o xlsx e conta registros/soma (coluna 6 = Valor Faturado).

    Retorna (ok, n_registros, soma). ok=False = arquivo corrompido/antivirus.
    Arquivo so com cabecalho (n_registros=0) abre OK mas e sinal de alerta:
    o chamador decide retry, pois pode ser exportacao antes da tabela carregar.
    """
    try:
        wb = openpyxl.load_workbook(caminho, data_only=True)
        ws = wb.active
        n_regs = max(0, ws.max_row - 1)
        soma = 0.0
        for r in range(2, ws.max_row + 1):
            val = ws.cell(row=r, column=6).value
            if isinstance(val, (int, float)):
                soma += val
        wb.close()
        return True, n_regs, soma
    except Exception as e:
        return False, 0, 0.0

def arquivos_existentes(pasta_salvar):
    existentes = set()
    if not os.path.exists(pasta_salvar):
        return existentes
    for padrao in ["*.xlsx", "*.xls"]:
        for f in glob.glob(os.path.join(pasta_salvar, padrao)):
            if not os.path.basename(f).startswith('~$'):
                existentes.add(os.path.normpath(os.path.abspath(f)))
    return existentes


def renomear_arquivo(pasta_salvar, nome_unidade, arquivos_antes, ja_renomeados):
    """Aguarda o download atual, valida o xlsx e renomeia p/ a unidade.

    Usa nome sanitizado (acentos preservados em UTF-8, sem caracteres
    ilegais do Windows). Retorna o nome final ou False em falha.
    """
    nome_unidade = sanitizar_nome_arquivo(nome_unidade)
    caminho_baixado = esperar_novo_download(pasta_salvar, arquivos_antes)

    if not caminho_baixado:
        # Fallback legado: procura qualquer arquivo ainda nao renomeado
        # (cobre o caso de download instantaneo sem .crdownload).
        arquivos_depois = arquivos_existentes(pasta_salvar)
        candidatos = [f for f in arquivos_depois
                      if os.path.basename(f) not in ja_renomeados
                      and not os.path.basename(f).startswith('~$')]
        if not candidatos:
            print("  AVISO: Nenhum arquivo novo apos o clique (timeout/bloqueio)")
            return False
        caminho_baixado = sorted(candidatos, key=os.path.getmtime, reverse=True)[0]
        if not _tamanho_estavel(caminho_baixado):
            print("  AVISO: arquivo instavel, abortando renomeacao")
            return False

    ok, n_regs, _soma = validar_excel(caminho_baixado)
    if not ok:
        print(f"  AVISO: arquivo baixado corrompido/bloqueado "
              f"({os.path.basename(caminho_baixado)}) - sera repetido no retry")
        try:
            os.remove(caminho_baixado)
        except OSError:
            pass
        return False

    time.sleep(1)

    ext = os.path.splitext(caminho_baixado)[1] or ".xlsx"
    novo_nome = f"{nome_unidade}{ext}"
    caminho_novo = os.path.join(pasta_salvar, novo_nome)

    if os.path.exists(caminho_novo):
        counter = 1
        while os.path.exists(f"{os.path.splitext(caminho_novo)[0]}_{counter}{ext}"):
            counter += 1
        caminho_novo = f"{os.path.splitext(caminho_novo)[0]}_{counter}{ext}"

    for tentativa in range(5):
        try:
            os.rename(caminho_baixado, caminho_novo)
            break
        except PermissionError:
            print(f"  Arquivo ocupado, tentativa {tentativa+1}/5...")
            time.sleep(3)
    else:
        print(f"  ERRO: Não foi possível renomear após 5 tentativas")
        return False
    print(f"  Renomeado: {os.path.basename(caminho_baixado)} -> {os.path.basename(caminho_novo)}")
    return os.path.basename(caminho_novo)

def gerar_resumo(pasta_salvar, arquivo_unidades, aba_unidades, coluna_unidade,
                 status_unidades=None):
    """Gera Resumo.xlsx com o consolidado por unidade.

    status_unidades: dict opcional {unidade: 'OK'|'VAZIO'|'FALHA'} preenchido
    pelo loop de downloads. Se ausente, o status e inferido do arquivo.
    Nomes sao comparados de forma normalizada (acentos/espacos), entao
    'DaVita Taubate 2' encontra 'DaVita Taubaté 2.xlsx' sem erro.
    """
    print("\nGerando Resumo...")

    unidades = []
    mes_ref = ""
    ano_ref = ""
    wb_lista = openpyxl.load_workbook(arquivo_unidades, data_only=True)
    ws_lista = wb_lista[aba_unidades]
    header = [str(ws_lista.cell(row=1, column=c).value or "").strip() for c in range(1, ws_lista.max_column + 1)]
    col_unidade = header.index(coluna_unidade) + 1
    col_mes = next((i + 1 for i, h in enumerate(header) if h.lower().strip() == "mes"), None)
    col_ano = header.index("ano") + 1
    for r in range(2, ws_lista.max_row + 1):
        v = ws_lista.cell(row=r, column=col_unidade).value
        if v and normalizar_nome(v):
            unidades.append(normalizar_nome(v))
        if not mes_ref and col_mes and col_ano:
            m = ws_lista.cell(row=r, column=col_mes).value
            a = ws_lista.cell(row=r, column=col_ano).value
            if m and a:
                mes_ref = str(m).strip().lower()[:3]
                if isinstance(a, (int, float)):
                    ano_ref = str(int(float(a)))
                else:
                    ano_ref = str(a).strip()
    wb_lista.close()

    if mes_ref:
        ref_formatada = converter_data(mes_ref, ano_ref)
        partes = ref_formatada.split("-")
        ref_texto = f"{partes[1]}/{partes[0]}"
    else:
        ref_texto = ""

    # Mapa arquivo -> (n_regs, soma) com chave normalizada (acentos/space-safe)
    achados = {}
    for padrao in ["*.xlsx", "*.xls"]:
        for arquivo in glob.glob(os.path.join(pasta_salvar, padrao)):
            base = os.path.basename(arquivo)
            if base.startswith("~$") or base in ("Resumo.csv", "Resumo.xlsx"):
                continue
            chave = _sem_acentos(normalizar_nome(os.path.splitext(base)[0]))
            ok, n_regs, soma = validar_excel(arquivo)
            if not ok:
                achados[chave] = (0, 0.0, "FALHA")
            else:
                achados[chave] = (n_regs, soma, None)

    total_geral = 0.0
    linhas = []  # (unidade, n_regs, valor, status)
    for unidade in unidades:
        chave = _sem_acentos(unidade)
        n_regs, valor, auto = achados.get(chave, (0, 0.0, "FALHA"))
        if status_unidades and unidade in status_unidades:
            status = status_unidades[unidade]
        elif auto:
            status = auto
        else:
            status = "OK" if n_regs > 0 else "VAZIO"
        if status != "FALHA":
            total_geral += valor
        linhas.append((unidade, n_regs, valor, status))

    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # ---- Resumo.xlsx (novo formato principal) ----
    caminho_xlsx = os.path.join(pasta_salvar, "Resumo.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumo"
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    titulo_font = Font(size=14, bold=True)
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4472C4")
    total_font = Font(bold=True)
    borda = Border(left=Side(style="thin", color="B0B0B0"),
                   right=Side(style="thin", color="B0B0B0"),
                   top=Side(style="thin", color="B0B0B0"),
                   bottom=Side(style="thin", color="B0B0B0"))
    centro = Alignment(horizontal="center", vertical="center")
    moeda_fmt = '#,##0.00'

    ws["A1"] = "RESUMO DO PROCESSO"
    ws["A1"].font = titulo_font
    ws["A2"] = now
    ws["A3"] = f"Referencia de: {ref_texto}"
    ws["A4"] = "Valor Total Faturado"
    ws["C4"] = total_geral
    ws["C4"].number_format = moeda_fmt
    ws["C4"].font = Font(bold=True, size=12)

    cab = ["Unidade", "Registros", "Valor Faturado (R$)", "Status"]
    r0 = 6
    for c, h in enumerate(cab, start=1):
        cell = ws.cell(row=r0, column=c, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = centro
        cell.border = borda

    for i, (unidade, n_regs, valor, status) in enumerate(linhas, start=1):
        r = r0 + i
        ws.cell(row=r, column=1, value=unidade).border = borda
        c2 = ws.cell(row=r, column=2, value=n_regs)
        c2.border = borda
        c2.alignment = centro
        c3 = ws.cell(row=r, column=3, value=valor)
        c3.number_format = moeda_fmt
        c3.border = borda
        c4 = ws.cell(row=r, column=4, value=status)
        c4.border = borda
        c4.alignment = centro

    rt = r0 + len(linhas) + 1
    ws.cell(row=rt, column=1, value="TOTAL").font = total_font
    ws.cell(row=rt, column=2, value=sum(n for _, n, _, _ in linhas)).font = total_font
    ct = ws.cell(row=rt, column=3, value=total_geral)
    ct.number_format = moeda_fmt
    ct.font = total_font

    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 12
    ws.freeze_panes = "A7"
    ws.auto_filter.ref = f"A{r0}:D{r0 + len(linhas)}"
    wb.save(caminho_xlsx)
    wb.close()

    print(f"Resumo salvo em: {caminho_xlsx}")
    print(f"Valor total faturado: R$ {total_geral:.2f}")
    faltas = [u for u, _, _, s in linhas if s == "FALHA"]
    vazias = [u for u, _, _, s in linhas if s == "VAZIO"]
    if faltas:
        print(f"ATENCAO: {len(faltas)} unidade(s) com FALHA: {', '.join(faltas)}")
    if vazias:
        print(f"AVISO: {len(vazias)} unidade(s) vazia(s) (0 registros): {', '.join(vazias)}")
    return caminho_xlsx

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Automacao Apresentacao DaVita")
    parser.add_argument("--unidade", action="append", default=[],
                        help="Processa SOMENTE esta(s) unidade(s). "
                             'Ex.: python main.py --unidade "DaVita Bueno". '
                             "Sem o argumento, processa todas (comportamento atual).")
    args = parser.parse_args()

    config = load_config()
    url = config["url"]
    usuario = config["usuario"]
    senha = config["senha"]
    arquivo_unidades = config["arquivo_unidades"]
    aba_unidades = config["aba_unidades"]
    coluna_unidade = config.get("coluna_unidade", "unidade")
    pasta_salvar = config["pasta_salvar"]
    pasta_downloads = os.path.join(os.environ["USERPROFILE"], "Downloads")
    pasta_salvar = os.path.join(pasta_downloads, f'{datetime.now().strftime("%Y%m%d")} Apresentacao')

    wb = openpyxl.load_workbook(arquivo_unidades, data_only=True)
    ws = wb[aba_unidades]

    header = [str(ws.cell(row=1, column=c).value or "").strip() for c in range(1, ws.max_column + 1)]
    col_unidade = header.index(coluna_unidade) + 1
    col_mes = next((i + 1 for i, h in enumerate(header) if h.lower().strip() == "mes"), None)
    col_ano = header.index("ano") + 1
    if col_mes is None:
        raise ValueError("Coluna 'mes' não encontrada no cabeçalho")

    dados = []
    for r in range(2, ws.max_row + 1):
        unidade = ws.cell(row=r, column=col_unidade).value
        mes = ws.cell(row=r, column=col_mes).value
        ano = ws.cell(row=r, column=col_ano).value
        if not unidade or not mes or not ano:
            continue
        mes_str = str(mes).strip().lower()
        if isinstance(ano, (int, float)):
            ano_str = str(int(float(ano)))
        else:
            ano_str = str(ano).strip()
        data_formatada = converter_data(mes_str, ano_str)
        dados.append({"unidade": normalizar_nome(unidade), "mes_ano": data_formatada})

    if args.unidade:
        def _casa(nome_lista, alvo):
            a = _sem_acentos(normalizar_nome(nome_lista))
            b = _sem_acentos(normalizar_nome(alvo))
            return bool(a) and bool(b) and (a == b or b in a or a in b)
        dados = [d for d in dados
                 if any(_casa(d["unidade"], a) for a in args.unidade)]
        if not dados:
            print("Nenhuma unidade da Lista_Unidades corresponde ao filtro "
                  f"{args.unidade}. Verifique a grafia.")
            return
        print(f"Filtro --unidade ativo: {len(dados)} unidade(s)")

    print(f"Registros carregados: {len(dados)}")
    for d in dados:
        print(f"  {d['unidade']} | {d['mes_ano']}")

    os.makedirs(pasta_salvar, exist_ok=True)
    print(f"Pasta: '{pasta_salvar}'")

    options = webdriver.EdgeOptions()
    prefs = {
        "download.default_directory": os.path.abspath(pasta_salvar),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        # Desliga a verificacao antivirus/SmartScreen do Edge que bloqueava
        # os xlsx (ficavam presos como .crdownload / "com falha").
        "safebrowsing.enabled": False,
        "safebrowsing.enhanced": False,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--safebrowsing-disable-download-protection")

    driver = webdriver.Edge(options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(usuario)
        driver.find_element(By.NAME, "password").send_keys(senha)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.url_changes(url))
        print("Login efetuado!")
        time.sleep(3)

        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Relat')]"))).click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//*[contains(text(), 'Faturamento') and contains(text(), 'Mensal')]").click()
        time.sleep(5)

        base_url = driver.current_url
        print(f"URL base: {base_url}")

        ja_renomeados = set()
        status_unidades = {}

        for i, item in enumerate(dados):
            unidade = sanitizar_nome_arquivo(item["unidade"])
            print(f"[{i + 1}/{len(dados)}] {unidade} | {item['mes_ano']}")

            # Retoma execucao anterior SOMENTE se o arquivo existente for
            # valido E contiver registros. Arquivo vazio/corrompido (caso
            # DaVita Bueno) e baixado novamente em vez de ser pulado.
            caminho_unidade = os.path.join(pasta_salvar, f"{unidade}.xlsx")
            if os.path.exists(caminho_unidade):
                ok_ex, n_ex, _s_ex = validar_excel(caminho_unidade)
                if ok_ex and n_ex > 0:
                    print(f"  JA EXISTE com {n_ex} registros: pulando...")
                    ja_renomeados.add(os.path.basename(caminho_unidade))
                    status_unidades[unidade] = "OK"
                    continue
                if ok_ex:
                    # Vazio valido ja verificado hoje (pasta do dia): nao
                    # rebaixa — economiza 3 tentativas de download a toa.
                    print(f"  JA EXISTE vazio (verificado): mantendo VAZIO...")
                    ja_renomeados.add(os.path.basename(caminho_unidade))
                    status_unidades[unidade] = "VAZIO"
                    continue
                print(f"  Arquivo existente corrompido: baixando novamente...")
                try:
                    os.remove(caminho_unidade)
                except OSError:
                    pass

            sucesso = False
            for tentativa in range(1, MAX_TENTATIVAS_DOWNLOAD + 1):
                if tentativa > 1:
                    print(f"  Tentativa {tentativa}/{MAX_TENTATIVAS_DOWNLOAD}...")
                try:
                    driver.get(base_url)
                    time.sleep(2)
                    wait_local = WebDriverWait(driver, 20)
                except Exception:
                    driver.refresh()
                    time.sleep(2)
                    wait_local = WebDriverWait(driver, 20)

                try:
                    select_elem = wait_local.until(
                        EC.element_to_be_clickable((By.NAME, "empresa"))
                    )
                    if not selecionar_unidade(select_elem, unidade):
                        continue
                    print(f"  Unidade: '{unidade}'")
                except Exception as e:
                    print(f"  ERRO ao selecionar unidade: {e}")
                    continue

                if not preencher_data(driver, "mes_de", item["mes_ano"]):
                    print(f"  ERRO: campo mes_de não preenchido")
                    continue
                if not preencher_data(driver, "mes_ate", item["mes_ano"]):
                    print(f"  ERRO: campo mes_ate não preenchido")
                    continue

                de_val = driver.find_element(By.NAME, "mes_de").get_attribute("value")
                ate_val = driver.find_element(By.NAME, "mes_ate").get_attribute("value")
                print(f"  mes_de='{de_val}' | mes_ate='{ate_val}'")

                for btn in driver.find_elements(By.TAG_NAME, "button"):
                    if btn.text.strip() == "CONSULTAR":
                        driver.execute_script("arguments[0].click();", btn)
                        break

                if not aguardar_excel_visivel(driver):
                    print(f"  ERRO: Timeout no carregamento dos dados")
                    continue
                # Aguarda a tabela em vez de sleep fixo: com dados, baixa na
                # hora; vazia confirmada, pula o download (economiza 3 retry).
                estado_tabela = aguardar_tabela_carregada(driver)
                if estado_tabela == "vazia":
                    print(f"  Site sem registros: VAZIO (download pulado)")
                    status_unidades[unidade] = "VAZIO"
                    sucesso = True
                    break
                if estado_tabela == "inconclusivo":
                    time.sleep(2)

                arquivos_antes = arquivos_existentes(pasta_salvar)
                if not clicar_excel(driver):
                    print(f"  ERRO: Botão Excel não encontrado")
                    continue
                print(f"  Download iniciado")

                nome_renomeado = renomear_arquivo(pasta_salvar, unidade, arquivos_antes, ja_renomeados)
                if not nome_renomeado:
                    print(f"  Tentativa {tentativa} sem arquivo (retry)...")
                    continue
                ja_renomeados.add(nome_renomeado)
                ok_v, n_v, _s_v = validar_excel(os.path.join(pasta_salvar, nome_renomeado))
                if ok_v and n_v > 0:
                    print(f"  OK: {unidade} ({n_v} registros)")
                    status_unidades[unidade] = "OK"
                    sucesso = True
                    break
                # Arquivo valido porem vazio: pode ser unidade sem movimento
                # OU exportacao precoce. Tenta de novo; se persistir, marca.
                if tentativa < MAX_TENTATIVAS_DOWNLOAD:
                    try:
                        os.remove(os.path.join(pasta_salvar, nome_renomeado))
                        ja_renomeados.discard(nome_renomeado)
                    except OSError:
                        pass
                    print(f"  Arquivo vazio (0 registros), repetindo...")
                    time.sleep(2)
                else:
                    print(f"  VAZIO apos {MAX_TENTATIVAS_DOWNLOAD}x: mantido p/ revisao manual")
                    status_unidades[unidade] = "VAZIO"

            if not sucesso and unidade not in status_unidades:
                status_unidades[unidade] = "FALHA"
                print(f"  FALHA: {unidade} apos {MAX_TENTATIVAS_DOWNLOAD} tentativas")

        print("\n=== Processo concluído! ===")
        for f in os.listdir(pasta_salvar):
            print(f"  - {f}")

        gerar_resumo(pasta_salvar, arquivo_unidades, aba_unidades, coluna_unidade,
                     status_unidades=status_unidades)

    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
