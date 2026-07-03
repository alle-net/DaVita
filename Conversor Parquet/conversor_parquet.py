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
# DIÁLOGO DE PRÉ-VISUALIZAÇÃO
# ──────────────────────────────────────────────────────────────────────
class PreviewDialog:
    TIPOS_DISPONIVEIS = ["string", "integer", "float", "boolean", "datetime"]
    TIPO_PARA_DTYPE = {
        "string": "object",
        "integer": "int64",
        "float": "float64",
        "boolean": "bool",
        "datetime": "datetime64[ns]",
    }
    DTYPE_PARA_TIPO = {v: k for k, v in TIPO_PARA_DTYPE.items()}

    def __init__(self, parent, nome_arquivo, df, config_atual, callback):
        self.callback = callback
        self.nome_arquivo = nome_arquivo
        self.colunas = list(df.columns)
        self.df_original = df
        self.config = config_atual.copy() if config_atual else {}
        if "colunas_selecionadas" not in self.config:
            self.config["colunas_selecionadas"] = self.colunas[:]
        if "tipos" not in self.config:
            self.config["tipos"] = {}

        self.janela = tk.Toplevel(parent)
        self.janela.title(f"Pré-visualização: {nome_arquivo}")
        self.janela.geometry("900x650")
        self.janela.minsize(700, 500)
        self.janela.transient(parent)
        self.janela.grab_set()

        main = ttk.Frame(self.janela, padding="10")
        main.pack(fill=tk.BOTH, expand=True)

        # ── Configuração de colunas ──
        frame_config = ttk.LabelFrame(main, text="Configuração das Colunas", padding="5")
        frame_config.pack(fill=tk.X, pady=(0, 8))

        canvas = tk.Canvas(frame_config, height=120, highlightthickness=0)
        scroll_h = ttk.Scrollbar(frame_config, orient=tk.HORIZONTAL, command=canvas.xview)
        scroll_v = ttk.Scrollbar(frame_config, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(xscrollcommand=scroll_h.set, yscrollcommand=scroll_v.set)

        frame_cols = ttk.Frame(canvas)
        frame_cols.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=frame_cols, anchor="nw")
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_h.pack(side=tk.BOTTOM, fill=tk.X)

        self.check_vars = {}
        self.tipo_combos = {}

        for i, col in enumerate(self.colunas):
            cell = ttk.Frame(frame_cols, borderwidth=1, relief="solid", padding="3")
            cell.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)

            var = tk.BooleanVar(value=col in self.config["colunas_selecionadas"])
            self.check_vars[col] = var
            cb = ttk.Checkbutton(cell, text=col, variable=var)
            cb.pack(anchor=tk.W)

            tipo_raw = self.config["tipos"].get(col, str(self.df_original[col].dtype))
            tipo_exibicao = self.DTYPE_PARA_TIPO.get(tipo_raw, tipo_raw)
            if tipo_exibicao not in self.TIPOS_DISPONIVEIS:
                tipo_exibicao = "string"
            combo = ttk.Combobox(cell, values=self.TIPOS_DISPONIVEIS, width=14, state="readonly")
            combo.set(tipo_exibicao)
            combo.pack(anchor=tk.W, pady=(2, 0))
            self.tipo_combos[col] = combo

            frame_cols.columnconfigure(i, weight=0)

        # ── Prévia dos dados ──
        frame_previa = ttk.LabelFrame(main, text="Prévia dos Dados (primeiras linhas)", padding="5")
        frame_previa.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        cols_tree = list(df.columns)
        self.tree_previa = ttk.Treeview(frame_previa, columns=cols_tree, show="headings",
                                        height=12)
        for c in cols_tree:
            self.tree_previa.heading(c, text=c)
            self.tree_previa.column(c, width=100, minwidth=60)

        scroll_y2 = ttk.Scrollbar(frame_previa, orient=tk.VERTICAL, command=self.tree_previa.yview)
        scroll_x2 = ttk.Scrollbar(frame_previa, orient=tk.HORIZONTAL, command=self.tree_previa.xview)
        self.tree_previa.configure(yscrollcommand=scroll_y2.set, xscrollcommand=scroll_x2.set)
        self.tree_previa.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y2.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x2.pack(side=tk.BOTTOM, fill=tk.X)

        for _, row in df.head(50).iterrows():
            vals = [str(v) if v is not None else "" for v in row]
            self.tree_previa.insert("", tk.END, values=vals)

        # ── Ações ──
        frame_acoes = ttk.Frame(main)
        frame_acoes.pack(fill=tk.X)

        ttk.Button(frame_acoes, text="Selecionar Todas",
                   command=self._selecionar_todas).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(frame_acoes, text="Limpar Seleção",
                   command=self._limpar_selecao).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(frame_acoes, text="Aplicar",
                   command=self._aplicar).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(frame_acoes, text="Cancelar",
                   command=self.janela.destroy).pack(side=tk.RIGHT)

    def _selecionar_todas(self):
        for var in self.check_vars.values():
            var.set(True)

    def _limpar_selecao(self):
        for var in self.check_vars.values():
            var.set(False)

    def _aplicar(self):
        selecionadas = [col for col, var in self.check_vars.items() if var.get()]
        if not selecionadas:
            messagebox.showwarning("Aviso", "Selecione pelo menos uma coluna.", parent=self.janela)
            return
        tipos = {}
        for col, combo in self.tipo_combos.items():
            if col in selecionadas:
                tipo_exibicao = combo.get()
                if tipo_exibicao:
                    tipo_dtype = self.TIPO_PARA_DTYPE.get(tipo_exibicao, tipo_exibicao)
                    tipo_raw_original = str(self.df_original[col].dtype)
                    tipo_original_exib = self.DTYPE_PARA_TIPO.get(tipo_raw_original, tipo_raw_original)
                    if tipo_exibicao != tipo_original_exib:
                        tipos[col] = tipo_dtype
        config = {"colunas_selecionadas": selecionadas, "tipos": tipos}
        self.callback(self.nome_arquivo, config)
        self.janela.destroy()


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
        self.pasta_saida = tk.StringVar()
        self.arquivos_encontrados = []
        self._processando = False
        self._criar_widgets()
        self._definir_pasta_padrao()

    def _definir_pasta_padrao(self):
        padrao = os.path.join(achar_downloads(), "Entrada")
        os.makedirs(padrao, exist_ok=True)
        self.pasta_entrada.set(padrao)
        padrao_saida = os.path.join(achar_downloads(), "Saida")
        os.makedirs(padrao_saida, exist_ok=True)
        self.pasta_saida.set(padrao_saida)

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

        # ── Saída ──
        frame_saida = ttk.LabelFrame(main_frame, text="Pasta de Saída", padding="5")
        frame_saida.pack(fill=tk.X, pady=(0, 8))

        saida_frame = ttk.Frame(frame_saida)
        saida_frame.pack(fill=tk.X)
        self.entry_pasta_saida = ttk.Entry(saida_frame, textvariable=self.pasta_saida)
        self.entry_pasta_saida.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(saida_frame, text="Escolher Pasta",
                   command=self._escolher_pasta_saida).pack(side=tk.LEFT)

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
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # ── Ações ──
        frame_acoes = ttk.Frame(main_frame)
        frame_acoes.pack(fill=tk.X, pady=(0, 8))

        self.btn_escanear = ttk.Button(frame_acoes, text="🔍 Escanear",
                                       command=self._escanear)
        self.btn_escanear.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_converter = ttk.Button(frame_acoes, text="▶ Converter Tudo",
                                        command=self._converter_todos, state=tk.DISABLED)
        self.btn_converter.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_visualizar = ttk.Button(frame_acoes, text="👁 Visualizar",
                                         command=self._visualizar, state=tk.DISABLED)
        self.btn_visualizar.pack(side=tk.LEFT, padx=(0, 5))

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
            self.btn_visualizar.configure(state=tk.DISABLED)
            self._log(f"Pasta selecionada: {pasta}")

    def _escolher_pasta_saida(self):
        from tkinter import filedialog
        pasta = filedialog.askdirectory(title="Selecione a pasta de saída")
        if pasta:
            self.pasta_saida.set(pasta)
            self._log(f"Pasta de saída: {pasta}")

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
        self.btn_visualizar.configure(state=tk.DISABLED)
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
            self.btn_visualizar.configure(state=tk.NORMAL)
        self._log(f"Escaneamento concluído: {total} arquivo(s)")

    def _on_tree_double_click(self, event):
        self._visualizar()

    def _visualizar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um arquivo na lista.")
            return
        item = sel[0]
        valores = self.tree.item(item, "values")
        if not valores:
            return
        nome = valores[0]
        arq = next((a for a in self.arquivos_encontrados if a["nome"] == nome), None)
        if arq is None:
            return

        caminho = arq["caminho"]
        ext = os.path.splitext(caminho)[1].lower()

        df_preview = self._ler_amostra(caminho, ext)
        if df_preview is None:
            messagebox.showerror("Erro", "Não foi possível ler o arquivo para preview.")
            return

        config = arq.get("colunas_config", {})
        PreviewDialog(self.root, arq["nome"], df_preview, config, self._aplicar_config_colunas)

    def _ler_amostra(self, caminho, ext):
        try:
            if ext in ('.xlsx', '.xlsm', '.xls'):
                engine = self.var_engine.get()
                return pd.read_excel(caminho, engine=engine, nrows=100)
            elif ext == '.ods':
                return pd.read_excel(caminho, engine='odf', nrows=100)
            elif ext == '.csv':
                for enc in ('utf-8', 'latin-1', 'cp1252'):
                    try:
                        return pd.read_csv(caminho, encoding=enc, nrows=100)
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                return pd.read_csv(caminho, encoding='latin-1', nrows=100)
            elif ext == '.txt':
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
                        return pd.read_csv(caminho, encoding=enc, sep=sep, nrows=100,
                                           engine='python' if sep is None else 'c')
                    except Exception:
                        continue
                return pd.read_csv(caminho, encoding='latin-1', sep=None, engine='python', nrows=100)
            elif ext == '.json':
                return ler_json_adaptativo(caminho).head(100)
            elif ext == '.xml':
                return pd.read_xml(caminho).head(100)
            elif ext in ('.html', '.htm'):
                tabelas = ler_html_adaptativo(caminho)
                if tabelas:
                    return tabelas[0].head(100)
                return None
            elif ext == '.parquet':
                return pd.read_parquet(caminho).head(100)
            return None
        except Exception:
            return None

    def _aplicar_config_colunas(self, nome_arquivo, config):
        for arq in self.arquivos_encontrados:
            if arq["nome"] == nome_arquivo:
                arq["colunas_config"] = config
                colunas = config.get("colunas_selecionadas", [])
                tipos = config.get("tipos", {})
                info = f"{len(colunas)} col"
                if tipos:
                    info += f", {len(tipos)} tipado(s)"
                self._atualizar_status(nome_arquivo, f"Config: {info}")
                self._log(f"Config aplicada: {nome_arquivo} -> {info}")
                break

    # ── CONVERSÃO ──
    def _converter_todos(self):
        if self._processando or not self.arquivos_encontrados:
            return
        self._processando = True

        pasta_saida = self.pasta_saida.get().strip()
        if not pasta_saida or not os.path.isdir(pasta_saida):
            pasta_saida = os.path.join(achar_downloads(), "Saida")
            os.makedirs(pasta_saida, exist_ok=True)

        self._log(f"Pasta de saída: {pasta_saida}")
        self._log(f"Convertendo {len(self.arquivos_encontrados)} arquivo(s)...")

        self.btn_escanear.configure(state=tk.DISABLED)
        self.btn_converter.configure(state=tk.DISABLED)
        self.btn_visualizar.configure(state=tk.DISABLED)
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
                self.root.after(0, self._step_progresso)
            self.root.after(0, self._pos_converter, pasta_saida)

        threading.Thread(target=rodar, daemon=True).start()

    def _atualizar_status(self, nome, status):
        for item in self.tree.get_children():
            v = self.tree.item(item, "values")
            if v and v[0] == nome:
                self.tree.set(item, "status", status)
                break

    def _step_progresso(self):
        self.progresso.step(1)
        self.root.update_idletasks()

    def _set_status(self, texto):
        self.lbl_status.configure(text=texto)

    def _pos_converter(self, pasta_saida):
        self._processando = False
        self.progresso.configure(value=0)
        self.btn_escanear.configure(state=tk.NORMAL)
        self.btn_converter.configure(state=tk.NORMAL)
        self.btn_visualizar.configure(state=tk.NORMAL if self.arquivos_encontrados else tk.DISABLED)
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

        config = arq.get("colunas_config", {})
        colunas_selecionadas = config.get("colunas_selecionadas")
        tipos = config.get("tipos", {})

        def _aplicar_config(df):
            if colunas_selecionadas:
                cols_validas = [c for c in colunas_selecionadas if c in df.columns]
                df = df[cols_validas]
            for col, tipo in tipos.items():
                if col in df.columns:
                    try:
                        if tipo == "datetime64[ns]":
                            df[col] = pd.to_datetime(df[col], errors="coerce")
                        else:
                            df[col] = df[col].astype(tipo, errors="ignore")
                    except Exception:
                        pass
            return df

        if ext in ('.xlsx', '.xlsm', '.xls', '.ods'):
            engine = self.var_engine.get()
            if ext == '.ods':
                engine = 'odf'
            dfs = ler_excel(caminho, engine)
            if len(dfs) == 1:
                df = _aplicar_config(list(dfs.values())[0])
                saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
                salvar_parquet(df, saida, compressao)
            else:
                for sheet, df in dfs.items():
                    df = _aplicar_config(df)
                    saida = os.path.join(pasta_saida, f"{nome_base}_{sanitizar(sheet)}.parquet")
                    salvar_parquet(df, saida, compressao)
                self._log(f"  -> {len(dfs)} planilhas convertidas")

        elif ext == '.csv':
            df = _aplicar_config(ler_csv(caminho))
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext == '.txt':
            df = _aplicar_config(ler_txt(caminho))
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext == '.json':
            df = _aplicar_config(ler_json_adaptativo(caminho))
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext == '.xml':
            df = _aplicar_config(pd.read_xml(caminho))
            saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
            salvar_parquet(df, saida, compressao)

        elif ext in ('.html', '.htm'):
            tabelas = ler_html_adaptativo(caminho)
            if tabelas is None or len(tabelas) == 0:
                raise ValueError("Nenhuma tabela encontrada no HTML")
            if len(tabelas) == 1:
                df = _aplicar_config(tabelas[0])
                saida = os.path.join(pasta_saida, f"{nome_base}.parquet")
                salvar_parquet(df, saida, compressao)
            else:
                for i, df in enumerate(tabelas):
                    df = _aplicar_config(df)
                    saida = os.path.join(pasta_saida, f"{nome_base}_tabela{i+1}.parquet")
                    salvar_parquet(df, saida, compressao)
                self._log(f"  -> {len(tabelas)} tabelas extraídas")

        elif ext == '.parquet':
            df = _aplicar_config(pd.read_parquet(caminho))
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
