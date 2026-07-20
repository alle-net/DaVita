import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import threading
import json
import time

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


# ──────────────────────────────────────────────────────────────────────
# LÓGICA DE CONVERSÃO
# ──────────────────────────────────────────────────────────────────────
def _flatten_json(obj, prefixo="_", sep="_"):
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
# GERENCIAMENTO DE PERFIS
# ──────────────────────────────────────────────────────────────────────
class PerfilManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self._base_dir = os.path.dirname(sys.executable)
        else:
            self._base_dir = os.path.dirname(os.path.abspath(__file__))
        self._arquivo = os.path.join(self._base_dir, "perfis.json")
        self._perfis = self._carregar()

    def _carregar(self):
        if os.path.exists(self._arquivo):
            try:
                with open(self._arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _salvar(self):
        with open(self._arquivo, 'w', encoding='utf-8') as f:
            json.dump(self._perfis, f, ensure_ascii=False, indent=2)

    def listar(self):
        return sorted(self._perfis.keys())

    def obter(self, nome):
        return self._perfis.get(nome, {}).copy()

    def salvar_perfil(self, nome, config):
        self._perfis[nome] = config.copy()
        self._salvar()

    def excluir(self, nome):
        if nome in self._perfis:
            del self._perfis[nome]
            self._salvar()
            return True
        return False

    def renomear(self, nome_antigo, nome_novo):
        if nome_antigo in self._perfis and nome_novo not in self._perfis:
            self._perfis[nome_novo] = self._perfis.pop(nome_antigo)
            self._salvar()
            return True
        return False


FILTROS_FILEDIALOG = [
    ("Todos os suportados", " ".join(f"*{ext}" for ext in EXTENSOES)),
    ("Excel", "*.xlsx *.xlsm *.xls"),
    ("CSV", "*.csv"),
    ("TXT", "*.txt"),
    ("JSON", "*.json"),
    ("XML", "*.xml"),
    ("HTML", "*.html *.htm"),
    ("Parquet", "*.parquet"),
    ("ODS", "*.ods"),
    ("Todos os arquivos", "*.*"),
]


# ──────────────────────────────────────────────────────────────────────
# DIÁLOGO DE PRÉ-VISUALIZAÇÃO
# ──────────────────────────────────────────────────────────────────────
class PreviewDialog:
    TIPOS_DISPONIVEIS = ["string", "integer", "float", "money", "boolean", "date", "datetime"]
    TIPO_PARA_DTYPE = {
        "string": "object",
        "integer": "int64",
        "float": "float64",
        "money": "money",
        "boolean": "bool",
        "date": "date",
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

            # Padrão: sempre "string" por primeiro
            combo = ttk.Combobox(cell, values=self.TIPOS_DISPONIVEIS, width=14, state="readonly")
            combo.set("string")
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
            self.tree_previa.column(c, width=120, minwidth=60, stretch=False)

        scroll_y2 = ttk.Scrollbar(frame_previa, orient=tk.VERTICAL, command=self.tree_previa.yview)
        scroll_x2 = ttk.Scrollbar(frame_previa, orient=tk.HORIZONTAL, command=self.tree_previa.xview)
        self.tree_previa.configure(yscrollcommand=scroll_y2.set, xscrollcommand=scroll_x2.set)
        scroll_y2.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x2.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_previa.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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

        self.arquivos_encontrados = []
        self._processando = False
        self._cancelar = False
        self._perfil_mgr = PerfilManager()
        self._ultima_config = None
        self._criar_widgets()

    def _criar_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ── Seleção de Arquivos ──
        frame_origem = ttk.LabelFrame(main_frame, text="Arquivos de Entrada", padding="5")
        frame_origem.pack(fill=tk.X, pady=(0, 8))

        btn_frame = ttk.Frame(frame_origem)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Selecionar Arquivos",
                   command=self._selecionar_arquivos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Limpar Lista",
                   command=self._limpar_lista).pack(side=tk.LEFT, padx=(0, 5))

        self.lbl_qtd = ttk.Label(btn_frame, text="Nenhum arquivo selecionado", foreground="#555")
        self.lbl_qtd.pack(side=tk.LEFT, padx=(10, 0))

        # ── Opções ──
        frame_opcoes = ttk.LabelFrame(main_frame, text="Opções", padding="5")
        frame_opcoes.pack(fill=tk.X, pady=(0, 8))

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

        # ── Perfis ──
        frame_perfis = ttk.LabelFrame(main_frame, text="Perfis de Conversão", padding="5")
        frame_perfis.pack(fill=tk.X, pady=(0, 8))

        perfis_row = ttk.Frame(frame_perfis)
        perfis_row.pack(fill=tk.X)

        ttk.Label(perfis_row, text="Perfil:").pack(side=tk.LEFT, padx=(0, 4))
        self.var_perfil = tk.StringVar()
        self.cb_perfis = ttk.Combobox(perfis_row, textvariable=self.var_perfil,
                                       values=self._perfil_mgr.listar(), width=30)
        self.cb_perfis.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(perfis_row, text="Carregar",
                   command=self._carregar_perfil).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(perfis_row, text="Salvar",
                   command=self._salvar_perfil).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(perfis_row, text="Salvar Como",
                   command=self._salvar_perfil_como).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(perfis_row, text="Excluir",
                   command=self._excluir_perfil).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(perfis_row, text="Renomear",
                   command=self._renomear_perfil).pack(side=tk.LEFT)

        # ── Lista de Arquivos ──
        frame_lista = ttk.LabelFrame(main_frame, text="Arquivos Selecionados", padding="5")
        frame_lista.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        colunas = ("arquivo", "pasta", "tamanho", "tipo", "status")
        self.tree = ttk.Treeview(frame_lista, columns=colunas, show="headings",
                                 selectmode="extended", height=12)
        self.tree.heading("arquivo", text="Arquivo")
        self.tree.heading("pasta", text="Pasta")
        self.tree.heading("tamanho", text="Tamanho")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("status", text="Status")
        self.tree.column("arquivo", width=200)
        self.tree.column("pasta", width=250)
        self.tree.column("tamanho", width=80, anchor=tk.CENTER)
        self.tree.column("tipo", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=100, anchor=tk.CENTER)

        scroll_y = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # ── Ações ──
        frame_acoes = ttk.Frame(main_frame)
        frame_acoes.pack(fill=tk.X, pady=(0, 8))

        self.btn_converter = ttk.Button(frame_acoes, text="Converter Tudo",
                                        command=self._converter_todos, state=tk.DISABLED)
        self.btn_converter.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_cancelar = ttk.Button(frame_acoes, text="Cancelar",
                                       command=self._cancelar_conversao, state=tk.DISABLED)
        self.btn_cancelar.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_visualizar = ttk.Button(frame_acoes, text="Visualizar",
                                         command=self._visualizar, state=tk.DISABLED)
        self.btn_visualizar.pack(side=tk.LEFT, padx=(0, 5))

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

    # ── SELEÇÃO DE ARQUIVOS ──
    def _selecionar_arquivos(self):
        caminhos = filedialog.askopenfilenames(
            title="Selecione os arquivos para converter",
            filetypes=FILTROS_FILEDIALOG,
        )
        if not caminhos:
            return

        exts_validas = set(EXTENSOES.keys())
        adicionados = 0
        ja_existentes = {a["caminho"] for a in self.arquivos_encontrados}

        for caminho in caminhos:
            if caminho in ja_existentes:
                continue
            ext = os.path.splitext(caminho)[1].lower()
            if ext not in exts_validas:
                continue
            nome = os.path.basename(caminho)
            pasta = os.path.dirname(caminho)
            self.arquivos_encontrados.append({
                "caminho": caminho,
                "nome": nome,
                "pasta": pasta,
                "tamanho": os.path.getsize(caminho),
                "tipo": EXTENSOES[ext],
                "status": "",
            })
            self.tree.insert("", tk.END, values=(
                nome, pasta, formatar_tamanho(os.path.getsize(caminho)),
                EXTENSOES[ext], ""
            ))
            adicionados += 1

        self._atualizar_estado_lista()
        if adicionados > 0:
            self._log(f"{adicionados} arquivo(s) adicionado(s)")

    def _limpar_lista(self):
        self.arquivos_encontrados.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._atualizar_estado_lista()
        self._log("Lista limpa")

    def _atualizar_estado_lista(self):
        total = len(self.arquivos_encontrados)
        self.lbl_qtd.configure(text=f"{total} arquivo(s) selecionado(s)")
        estado = tk.NORMAL if total > 0 else tk.DISABLED
        self.btn_converter.configure(state=estado)
        self.btn_visualizar.configure(state=estado)

    def _atualizar_combo_perfis(self):
        self.cb_perfis['values'] = self._perfil_mgr.listar()

    def _carregar_perfil(self):
        nome = self.var_perfil.get().strip()
        if not nome:
            messagebox.showinfo("Aviso", "Selecione um perfil no campo ao lado.")
            return
        config = self._perfil_mgr.obter(nome)
        if not config:
            messagebox.showerror("Erro", f"Perfil '{nome}' não encontrado.")
            return
        for arq in self.arquivos_encontrados:
            arq["colunas_config"] = config.copy()
        colunas = config.get("colunas_selecionadas", [])
        tipos = config.get("tipos", {})
        info = f"{len(colunas)} col"
        if tipos:
            info += f", {len(tipos)} tipado(s)"
        self._log(f"Perfil '{nome}' carregado: {info} -> aplicado a {len(self.arquivos_encontrados)} arquivo(s)")
        for arq in self.arquivos_encontrados:
            self._atualizar_status(arq["nome"], arq["pasta"], f"Perfil: {info}")

    def _salvar_perfil(self):
        nome = self.var_perfil.get().strip()
        if not nome:
            self._salvar_perfil_como()
            return
        if self._ultima_config is None:
            messagebox.showinfo("Aviso", "Configure um arquivo primeiro (Pré-visualizar > Aplicar).")
            return
        if nome in self._perfil_mgr.listar():
            if not messagebox.askyesno("Confirmar", f"Perfil '{nome}' já existe. Sobrescrever?"):
                return
        self._perfil_mgr.salvar_perfil(nome, self._ultima_config)
        self._atualizar_combo_perfis()
        self.cb_perfis.set(nome)
        self._log(f"Perfil '{nome}' salvo")

    def _salvar_perfil_como(self):
        if self._ultima_config is None:
            messagebox.showinfo("Aviso", "Configure um arquivo primeiro (Pré-visualizar > Aplicar).")
            return
        nome = tk.simpledialog.askstring("Salvar Perfil", "Nome do novo perfil:",
                                         parent=self.root)
        if not nome or not nome.strip():
            return
        nome = nome.strip()
        if nome in self._perfil_mgr.listar():
            if not messagebox.askyesno("Confirmar", f"Perfil '{nome}' já existe. Sobrescrever?"):
                return
        self._perfil_mgr.salvar_perfil(nome, self._ultima_config)
        self._atualizar_combo_perfis()
        self.cb_perfis.set(nome)
        self._log(f"Perfil '{nome}' criado e salvo")

    def _excluir_perfil(self):
        nome = self.var_perfil.get().strip()
        if not nome:
            messagebox.showinfo("Aviso", "Selecione um perfil para excluir.")
            return
        if not messagebox.askyesno("Confirmar", f"Excluir o perfil '{nome}'?"):
            return
        if self._perfil_mgr.excluir(nome):
            self._atualizar_combo_perfis()
            self.var_perfil.set("")
            self._log(f"Perfil '{nome}' excluído")

    def _renomear_perfil(self):
        nome = self.var_perfil.get().strip()
        if not nome:
            messagebox.showinfo("Aviso", "Selecione um perfil para renomear.")
            return
        novo_nome = tk.simpledialog.askstring("Renomear Perfil", f"Novo nome para '{nome}':",
                                               parent=self.root)
        if not novo_nome or not novo_nome.strip():
            return
        novo_nome = novo_nome.strip()
        if self._perfil_mgr.renomear(nome, novo_nome):
            self._atualizar_combo_perfis()
            self.cb_perfis.set(novo_nome)
            self._log(f"Perfil renomeado: '{nome}' -> '{novo_nome}'")
        else:
            messagebox.showerror("Erro", f"Já existe um perfil chamado '{novo_nome}'.")

    # ── CANCELAR ──
    def _cancelar_conversao(self):
        self._cancelar = True
        self._log("Conversão cancelada pelo usuário")

    # ── VISUALIZAR ──
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
        arq = next((a for a in self.arquivos_encontrados if a["nome"] == nome
                     and a["pasta"] == valores[1]), None)
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
                arq["colunas_config"] = config.copy()
                self._ultima_config = config.copy()
                colunas = config.get("colunas_selecionadas", [])
                tipos = config.get("tipos", {})
                info = f"{len(colunas)} col"
                if tipos:
                    info += f", {len(tipos)} tipado(s)"
                self._atualizar_status(nome_arquivo, arq["pasta"], f"Config: {info}")
                self._log(f"Config aplicada: {nome_arquivo} -> {info}")
                break

    # ── PROGRESSO BASEADO EM TEMPO ──
    # Mapeamento: tempo_decorrido(seg) -> percentual
    CURVA_PROGRESSO = [
        (10,  5),
        (30,  25),
        (40,  55),
        (60,  80),
        (80,  99),
    ]

    def _calcular_progresso_tempo(self, elapsed):
        if elapsed <= 0:
            return 0
        prev_t, prev_p = 0, 0
        for t, p in self.CURVA_PROGRESSO:
            if elapsed <= t:
                frac = (elapsed - prev_t) / (t - prev_t)
                return prev_p + frac * (p - prev_p)
            prev_t, prev_p = t, p
        return 99

    def _iniciar_timer_progresso(self):
        self._tempo_inicio = time.time()
        self._atualizar_timer_progresso()

    def _atualizar_timer_progresso(self):
        if not self._processando:
            return
        elapsed = time.time() - self._tempo_inicio
        pct = self._calcular_progresso_tempo(elapsed)
        self.progresso.configure(value=pct, maximum=100)
        self.lbl_status.configure(text=f"Convertendo... ({pct:.0f}%)")
        self.root.after(500, self._atualizar_timer_progresso)

    # ── CONVERSÃO ──
    def _converter_todos(self):
        if self._processando or not self.arquivos_encontrados:
            return
        self._processando = True
        self._cancelar = False

        self.btn_converter.configure(state=tk.DISABLED)
        self.btn_visualizar.configure(state=tk.DISABLED)
        self.btn_cancelar.configure(state=tk.NORMAL)

        self.progresso.configure(value=0, maximum=100)
        self._log(f"Convertendo {len(self.arquivos_encontrados)} arquivo(s)...")

        self._indice_atual = 0
        self._iniciar_timer_progresso()
        self._converter_proximo()

    def _converter_proximo(self):
        if self._cancelar or self._indice_atual >= len(self.arquivos_encontrados):
            self._pos_converter()
            return

        i = self._indice_atual
        arq = self.arquivos_encontrados[i]

        self._atualizar_status(arq["nome"], arq["pasta"], "Convertendo...")

        def executar():
            try:
                self._converter_um(arq)
                self.root.after(0, self._on_conversao_ok, arq)
            except Exception as e:
                self.root.after(0, self._on_conversao_erro, arq, str(e))

        threading.Thread(target=executar, daemon=True).start()

    def _on_conversao_ok(self, arq):
        self._atualizar_status(arq["nome"], arq["pasta"], "OK")
        self._log(f"OK: {arq['nome']}")
        self._indice_atual += 1
        self._converter_proximo()

    def _on_conversao_erro(self, arq, erro):
        self._atualizar_status(arq["nome"], arq["pasta"], "Erro")
        self._log(f"ERRO: {arq['nome']} -> {erro}")
        self._indice_atual += 1
        self._converter_proximo()

    def _atualizar_status(self, nome, pasta, status):
        for item in self.tree.get_children():
            v = self.tree.item(item, "values")
            if v and v[0] == nome and v[1] == pasta:
                self.tree.set(item, "status", status)
                break

    def _pos_converter(self):
        self._processando = False
        self.progresso.configure(value=100)
        self.btn_converter.configure(state=tk.NORMAL)
        self.btn_visualizar.configure(state=tk.NORMAL if self.arquivos_encontrados else tk.DISABLED)
        self.btn_cancelar.configure(state=tk.DISABLED)
        self.lbl_status.configure(text="Conversão concluída!")
        self._log("Conversão concluída!")
        if self._cancelar:
            self.lbl_status.configure(text="Conversão cancelada")

    # ── CONVERTER UM ARQUIVO ──
    def _converter_um(self, arq):
        caminho = arq["caminho"]
        ext = os.path.splitext(caminho)[1].lower()
        nome_base = sanitizar(os.path.splitext(arq["nome"])[0])
        pasta_saida = arq["pasta"]
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
                        elif tipo == "money":
                            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
                        elif tipo == "date":
                            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
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
