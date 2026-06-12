import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import json

import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa


# ──────────────────────────────────────────────────────────────────────
# UTILITÁRIOS
# ──────────────────────────────────────────────────────────────────────
def formatar_tamanho(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / 1024 ** 2:.1f} MB"
    else:
        return f"{bytes_val / 1024 ** 3:.2f} GB"


def sanitizar(nome):
    invalidos = r'<>:"/\|?*'
    for c in invalidos:
        nome = nome.replace(c, '_')
    return nome[:80]


def achar_downloads():
    return os.path.join(os.path.expanduser("~"), "Downloads")


# ──────────────────────────────────────────────────────────────────────
# LÓGICA DE CONVERSÃO
# ──────────────────────────────────────────────────────────────────────
def _flatten_json(obj, prefixo="_", sep="_"):
    """Achata JSON aninhado recursivamente."""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            chave = f"{prefixo}{sep}{k}" if prefixo else k
            if isinstance(v, (dict, list)):
                items.update(_flatten_json(v, chave, sep))
            else:
                items[chave] = v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            chave = f"{prefixo}{sep}{i}" if prefixo else str(i)
            if isinstance(v, (dict, list)):
                items.update(_flatten_json(v, chave, sep))
            else:
                items[chave] = v
    return items


def ler_excel(caminho, engine):
    xls = pd.ExcelFile(caminho, engine=engine)
    dfs = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(caminho, sheet_name=sheet, engine=engine)
        dfs[sheet] = df
    return dfs


def ler_csv(caminho):
    for enc in ('utf-8', 'latin-1', 'cp1252'):
        try:
            return pd.read_csv(caminho, encoding=enc, low_memory=False)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return pd.read_csv(caminho, encoding='latin-1', low_memory=False)


def ler_txt(caminho):
    for enc in ('utf-8', 'latin-1', 'cp1252'):
        try:
            with open(caminho, 'r', encoding=enc) as f:
                amostra = f.read(8192)
        except (UnicodeDecodeError, UnicodeError):
            continue

        sep = None
        for s in [',', ';', '\t', '|']:
            if amostra.count(s) >= 3:
                sep = s
                break

        try:
            return pd.read_csv(caminho, encoding=enc, low_memory=False,
                               sep=sep, engine='python' if sep is None else 'c')
        except Exception:
            continue

    return pd.read_csv(caminho, encoding='latin-1', sep=None, engine='python')


def ler_json_adaptativo(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    if isinstance(dados, list):
        if all(isinstance(item, dict) for item in dados):
            return pd.json_normalize(dados)
        else:
            linhas = []
            for item in dados:
                linhas.append(_flatten_json(item))
            return pd.DataFrame(linhas)
    elif isinstance(dados, dict):
        if any(isinstance(v, (list, dict)) for v in dados.values()):
            for k, v in dados.items():
                if isinstance(v, list) and all(isinstance(i, dict) for i in v):
                    return pd.json_normalize(v, record_path=k) if k else pd.json_normalize(v)
            achatado = _flatten_json(dados)
            return pd.DataFrame([achatado])
        else:
            return pd.DataFrame([dados])
    else:
        raise ValueError("Formato JSON não reconhecido")


def ler_html_adaptativo(caminho):
    try:
        tabelas = pd.read_html(caminho)
        if tabelas:
            return tabelas
    except Exception:
        pass

    try:
        from lxml import html
        with open(caminho, 'r', encoding='utf-8') as f:
            tree = html.fromstring(f.read())
        todas = []
        for tbl in tree.xpath('//table'):
            linhas = []
            for tr in tbl.xpath('.//tr'):
                celulas = [td.text_content().strip() for td in tr.xpath('.//td | .//th')]
                if celulas:
                    linhas.append(celulas)
            if linhas:
                todas.append(pd.DataFrame(linhas))
        return todas if todas else None
    except Exception:
        return None


def salvar_parquet(df, saida, compressao):
    for col in df.select_dtypes(include=['datetime64[ns]']).columns:
        df[col] = df[col].astype(str)
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].where(df[col].notna(), None).astype(str)

    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, saida, compression=compressao or None)


# ──────────────────────────────────────────────────────────────────────
# MAPEAMENTO DE EXTENSÕES
# ──────────────────────────────────────────────────────────────────────
EXTENSOES = {
    '.xlsx': 'Excel',
    '.xlsm': 'Excel (Macro)',
    '.xls':  'Excel (Antigo)',
    '.ods':  'Planilha ODS',
    '.csv':  'CSV',
    '.txt':  'TXT',
    '.json': 'JSON',
    '.xml':  'XML',
    '.html': 'HTML',
    '.htm':  'HTML',
    '.parquet': 'Parquet',
}


# ──────────────────────────────────────────────────────────────────────
# INTERFACE GRÁFICA
# ──────────────────────────────────────────────────────────────────────
class ConversorParquet:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor para Parquet")
        self.root.geometry("820x620")
        self.root.minsize(650, 450)

        self.pasta_entrada = tk.StringVar()
        self.arquivos_encontrados = []
        self._processando = False
        self._criar_widgets()
        self._definir_pasta_padrao()

    def _definir_pasta_padrao(self):
        padrao = os.path.join(achar_downloads(), "Entrada")
        os.makedirs(padrao, exist_ok=True)
        self.pasta_entrada.set(padrao)

    def _criar_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ── Origem ──
        frame_origem = ttk.LabelFrame(main_frame, text="Pasta de Entrada", padding="5")
        frame_origem.pack(fill=tk.X, pady=(0, 8))
        lbl_info = ttk.Label(
            frame_origem,
            text="Coloque os arquivos nesta pasta e clique em Escanear:",
            foreground="#555"
        )
        lbl_info.pack(anchor=tk.W, pady=(0, 3))

        entrada_frame = ttk.Frame(frame_origem)
        entrada_frame.pack(fill=tk.X)
        self.entry_pasta = ttk.Entry(entrada_frame, textvariable=self.pasta_entrada)
        self.entry_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(entrada_frame, text="Escolher Pasta",
                   command=self._escolher_pasta).pack(side=tk.LEFT)

        # ── Opções ──
        frame_opcoes = ttk.LabelFrame(main_frame, text="Opções", padding="5")
        frame_opcoes.pack(fill=tk.X, pady=(0, 8))

        self.var_subpastas = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_opcoes, text="Incluir subpastas",
                        variable=self.var_subpastas).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(frame_opcoes, text="Engine Excel:").pack(side=tk.LEFT, padx=(0, 4))
        self.var_engine = tk.StringVar(value="openpyxl")
        cb_engine = ttk.Combobox(frame_opcoes, textvariable=self.var_engine,
                                 values=["openpyxl", "calamine", "odf"],
                                 state="readonly", width=12)
        cb_engine.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(frame_opcoes, text="Compressão:").pack(side=tk.LEFT, padx=(0, 4))
        self.var_compressao = tk.StringVar(value="snappy")
        cb_comp = ttk.Combobox(frame_opcoes, textvariable=self.var_compressao,
                               values=["snappy", "gzip", "brotli", "lz4", "zstd", "nenhuma"],
                               state="readonly", width=10)
        cb_comp.pack(side=tk.LEFT)

        # ── Lista de Arquivos ──
        frame_lista = ttk.LabelFrame(main_frame, text="Arquivos Encontrados", padding="5")
        frame_lista.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        colunas = ("arquivo", "tamanho", "tipo", "status")
        self.tree = ttk.Treeview(frame_lista, columns=colunas, show="headings",
                                 selectmode="extended", height=12)
        self.tree.heading("arquivo", text="Arquivo")
        self.tree.heading("tamanho", text="Tamanho")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("status", text="Status")
        self.tree.column("arquivo", width=360)
        self.tree.column("tamanho", width=90, anchor=tk.CENTER)
        self.tree.column("tipo", width=120, anchor=tk.CENTER)
        self.tree.column("status", width=140, anchor=tk.CENTER)

        scroll_y = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Ações ──
        frame_acoes = ttk.Frame(main_frame)
        frame_acoes.pack(fill=tk.X, pady=(0, 8))

        self.btn_escanear = ttk.Button(frame_acoes, text="🔍 Escanear",
                                       command=self._escanear)
        self.btn_escanear.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_converter = ttk.Button(frame_acoes, text="▶ Converter Tudo",
                                        command=self._converter_todos, state=tk.DISABLED)
        self.btn_converter.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_abrir_entrada = ttk.Button(frame_acoes, text="📂 Abrir Entrada",
                                            command=lambda: os.startfile(self.pasta_entrada.get()))
        self.btn_abrir_entrada.pack(side=tk.RIGHT, padx=(0, 0))

        # ── Progresso ──
        frame_prog = ttk.LabelFrame(main_frame, text="Progresso", padding="5")
        frame_prog.pack(fill=tk.X, pady=(0, 8))

        self.progresso = ttk.Progressbar(frame_prog, mode="determinate")
        self.progresso.pack(fill=tk.X, pady=(0, 3))

        self.lbl_status = ttk.Label(frame_prog, text="Pronto")
        self.lbl_status.pack(anchor=tk.W)

        # ── Log ──
        frame_log = ttk.LabelFrame(main_frame, text="Log", padding="5")
        frame_log.pack(fill=tk.BOTH, expand=True)

        self.txt_log = tk.Text(frame_log, height=6, state=tk.DISABLED, wrap=tk.WORD)
        scroll_log = ttk.Scrollbar(frame_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scroll_log.set)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)

    # ── LOG ──
    def _log(self, msg):
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.insert(tk.END, f"[{datetime.now():%H:%M:%S}] {msg}\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    # ── PASTA ──
    def _escolher_pasta(self):
        from tkinter import filedialog
        pasta = filedialog.askdirectory(title="Selecione a pasta com os arquivos")
        if pasta:
            self.pasta_entrada.set(pasta)
            self.arquivos_encontrados = []
            self._limpar_tree()
            self.btn_converter.configure(state=tk.DISABLED)
            self._log(f"Pasta selecionada: {pasta}")

    def _limpar_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    # ── ESCANEAR ──
    def _escanear(self):
        pasta = self.pasta_entrada.get()
        if not pasta or not os.path.isdir(pasta):
            messagebox.showwarning("Aviso", "A pasta de entrada não existe.")
            return

        self._limpar_tree()
        self.arquivos_encontrados = []
        self.btn_escanear.configure(state=tk.DISABLED)
        self.btn_converter.configure(state=tk.DISABLED)
        self.lbl_status.configure(text="Escaneando...")
        self.progresso.configure(mode="indeterminate")
        self.progresso.start()

        def escanear():
            try:
                incluir = self.var_subpastas.get()
                for raiz, _, arquivos in os.walk(pasta) if incluir else [(pasta, [], os.listdir(pasta))]:
                    for nome in sorted(arquivos):
                        caminho = os.path.join(raiz, nome)
                        if not os.path.isfile(caminho):
                            continue
                        ext = os.path.splitext(nome)[1].lower()
                        if ext not in EXTENSOES:
                            continue
                        rel = os.path.relpath(caminho, pasta)
                        self.arquivos_encontrados.append({
                            "caminho": caminho,
                            "nome": rel,
                            "tamanho": os.path.getsize(caminho),
                            "tipo": EXTENSOES[ext],
                            "status": ""
                        })
                        self.root.after(0, self._inserir_tree, rel,
                                        os.path.getsize(caminho),
                                        EXTENSOES[ext], "")
            except Exception as e:
                self._log(f"Erro ao escanear: {e}")
            finally:
                self.root.after(0, self._pos_escanear)

        threading.Thread(target=escanear, daemon=True).start()

    def _inserir_tree(self, nome, tamanho, tipo, status):
        self.tree.insert("", tk.END, values=(
            nome, formatar_tamanho(tamanho), tipo, status
        ))

    def _pos_escanear(self):
        self.progresso.stop()
        self.progresso.configure(mode="determinate", value=0)
        self.btn_escanear.configure(state=tk.NORMAL)
        total = len(self.arquivos_encontrados)
        self.lbl_status.configure(text=f"{total} arquivo(s) encontrado(s)")
        if total > 0:
            self.btn_converter.configure(state=tk.NORMAL)
        self._log(f"Escaneamento concluído: {total} arquivo(s)")

    # ── CONVERSÃO ──
    def _converter_todos(self):
        if self._processando or not self.arquivos_encontrados:
            return
        self._processando = True

        pasta_saida = os.path.join(
            achar_downloads(),
            "Saida",
            datetime.now().strftime("Saida_%Y%m%d_%H%M%S")
        )
        os.makedirs(pasta_saida, exist_ok=True)

        self._log(f"Pasta de saída: {pasta_saida}")
        self._log(f"Convertendo {len(self.arquivos_encontrados)} arquivo(s)...")

        self.btn_escanear.configure(state=tk.DISABLED)
        self.btn_converter.configure(state=tk.DISABLED)
        self.progresso.configure(value=0, maximum=len(self.arquivos_encontrados))

        def rodar():
            for i, arq in enumerate(self.arquivos_encontrados):
                self.root.after(0, self._atualizar_status, arq["nome"], "Convertendo...")
                self.root.after(0, self._set_status,
                                f"({i+1}/{len(self.arquivos_encontrados)}) {arq['nome']}")
                try:
                    self._converter_um(arq, pasta_saida)
                    self.root.after(0, self._atualizar_status, arq["nome"], "OK")
                    self.root.after(0, self._log, f"OK: {arq['nome']}")
                except Exception as e:
                    self.root.after(0, self._atualizar_status, arq["nome"], "Erro")
                    self.root.after(0, self._log, f"ERRO: {arq['nome']} -> {e}")
                self.root.after(0, self.progresso.step, 1)
            self.root.after(0, self._pos_converter, pasta_saida)

        threading.Thread(target=rodar, daemon=True).start()

    def _atualizar_status(self, nome, status):
        for item in self.tree.get_children():
            v = self.tree.item(item, "values")
            if v and v[0] == nome:
                self.tree.set(item, "status", status)
                break

    def _set_status(self, texto):
        self.lbl_status.configure(text=texto)

    def _pos_converter(self, pasta_saida):
        self._processando = False
        self.progresso.configure(value=0)
        self.btn_escanear.configure(state=tk.NORMAL)
        self.btn_converter.configure(state=tk.NORMAL)
        self.lbl_status.configure(text="Conversão concluída!")
        self._log("Conversão concluída!")

        msg = messagebox.askyesno(
            "Concluído",
            f"Conversão finalizada!\nArquivos salvos em:\n{pasta_saida}\n\nAbrir pasta?"
        )
        if msg:
            os.startfile(pasta_saida)

    # ── CONVERTER UM ARQUIVO ──
    def _converter_um(self, arq, pasta_saida):
        caminho = arq["caminho"]
        ext = os.path.splitext(caminho)[1].lower()
        nome_base = sanitizar(os.path.splitext(arq["nome"])[0])
        compressao = self.var_compressao.get()
        if compressao == "nenhuma":
            compressao = None

        if ext in ('.xlsx', '.xlsm', '.xls', '.ods'):
            engine = self.var_engine.get()
            if ext == '.ods':
                engine = 'odf'
            dfs = ler_excel(caminho, engine)
            if len(dfs) == 1:
                saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
                salvar_parquet(list(dfs.values())[0], saida, compressao)
            else:
                for sheet, df in dfs.items():
                    saida = os.path.join(pasta_saida, f"{nome_base}_{sanitizar(sheet)}.parquet")
                    salvar_parquet(df, saida, compressao)
                self._log(f"  -> {len(dfs)} planilhas convertidas")

        elif ext == '.csv':
            df = ler_csv(caminho)
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext == '.txt':
            df = ler_txt(caminho)
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext == '.json':
            df = ler_json_adaptativo(caminho)
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext == '.xml':
            df = pd.read_xml(caminho)
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext in ('.html', '.htm'):
            tabelas = ler_html_adaptativo(caminho)
            if tabelas is None or len(tabelas) == 0:
                raise ValueError("Nenhuma tabela encontrada no HTML")
            if len(tabelas) == 1:
                saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
                salvar_parquet(tabelas[0], saida, compressao)
            else:
                for i, df in enumerate(tabelas):
                    saida = os.path.join(pasta_saida, f"{nome_base}_tabela{i+1}.parquet")
                    salvar_parquet(df, saida, compressao)
                self._log(f"  -> {len(tabelas)} tabelas extraídas")

        elif ext == '.parquet':
            df = pd.read_parquet(caminho)
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)
        else:
            raise ValueError(f"Extensão não suportada: {ext}")


# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = ConversorParquet(root)
    root.mainloop()


if __name__ == "__main__":
    main()
