import ctypes
import re
import threading
import time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)

VK_RETURN = 0x0D
VK_DOWN = 0x28
VK_HOME = 0x24
VK_TAB = 0x09
BM_CLICK = 0x00F5
SW_SHOW = 5
SW_RESTORE = 9
SW_SHOWNA = 8

LOG_PATH = Path(__file__).resolve().parent / "dialogos_nativos.log"

RTITLE_DEFAULTS = [
    re.compile(r"certificad", re.I),
    re.compile(r"certificate", re.I),
    re.compile(r"autentica", re.I),
    re.compile(r"selecion", re.I),
]

BUTTON_OK = re.compile(r"\bok\b|confirmar|aceitar|avan", re.I)
BUTTON_CANCEL = re.compile(r"cancel|cancelar", re.I)
LIST_CLASS = re.compile(r"ListBox|ComboBox|Listview|SysListView32", re.I)
CERTIFICATE_WINDOW = re.compile(r"selecionar um certificado|select a certificate", re.I)
CERTIFICATE_USER = re.compile(r"ALEXANDRESILVA3", re.I)


class NativeDialogHandler:
    def __init__(self, title_patterns=None, scan_interval=1.0,
                 pid_refresh_seg=5.0, uia_cooldown_seg=10.0):
        self.patterns = title_patterns or RTITLE_DEFAULTS
        self.scan_interval = scan_interval
        self.pid_refresh_seg = pid_refresh_seg
        self.uia_cooldown_seg = uia_cooldown_seg
        self.edge_pids = set()
        self._stop = threading.Event()
        self.detected = []
        self.last_action = ""
        self._last_pid_collect = 0.0
        self._last_uia_ok = 0.0
        self._last_uia_error = ""
        self._last_uia_error_time = 0.0
        self._desktop = None
        self._pywinauto_ok = None

    def _log(self, msg: str) -> None:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")

    @staticmethod
    def _window_title(hwnd) -> str:
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value

    @staticmethod
    def _window_class(hwnd) -> str:
        buf = ctypes.create_unicode_buffer(128)
        user32.GetClassNameW(hwnd, buf, 128)
        return buf.value

    @staticmethod
    def _window_pid(hwnd) -> int:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value

    @staticmethod
    def _child_windows(hwnd):
        children = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(child, _):
            children.append(child)
            return True

        user32.EnumChildWindows(hwnd, cb, 0)
        return children

    def _collect_edge_pids(self) -> None:
        procs = (wintypes.DWORD * 1024)()
        needed = wintypes.DWORD()
        psapi.EnumProcesses(procs, ctypes.sizeof(procs), ctypes.byref(needed))
        count = needed.value // ctypes.sizeof(wintypes.DWORD)
        for i in range(count):
            pid = procs[i]
            if not pid:
                continue
            hproc = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not hproc:
                continue
            buf = ctypes.create_unicode_buffer(260)
            size = ctypes.c_ulong(260)
            try:
                ret = kernel32.QueryFullProcessImageNameW(
                    hproc, 0, buf, ctypes.byref(size)
                )
            except Exception:
                ret = 0
            kernel32.CloseHandle(hproc)
            if ret and "msedge.exe" in buf.value.lower():
                self.edge_pids.add(pid)

    def _window_is_edge(self, hwnd) -> bool:
        return self._window_pid(hwnd) in self.edge_pids

    def _find_candidate_windows(self):
        found = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            title = self._window_title(hwnd)
            cls = self._window_class(hwnd)
            title_matches = title.strip() and any(
                p.search(title) for p in self.patterns
            )
            if title_matches:
                found.append(hwnd)
            elif (
                cls in ("#32770", "Dialog")
                and not title.strip()
                and self._window_pid(hwnd) in self.edge_pids
            ):
                found.append(hwnd)
            return True

        user32.EnumWindows(cb, 0)
        return found

    def _force_foreground(self, hwnd) -> None:
        current_thread = kernel32.GetCurrentThreadId()
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        fg_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        user32.ShowWindow(hwnd, SW_RESTORE)
        if current_thread != target_thread:
            user32.AttachThreadInput(current_thread, target_thread, True)
            user32.AttachThreadInput(fg_thread, target_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            time.sleep(0.1)
            user32.AttachThreadInput(current_thread, target_thread, False)
            user32.AttachThreadInput(fg_thread, target_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)

    def _button_by_title(self, hwnd, regex):
        for child in self._child_windows(hwnd):
            title = self._window_title(child)
            cls = self._window_class(child)
            if not title.strip():
                continue
            if "Button" in cls and regex.search(title):
                return child
        return None

    def _first_list_control(self, hwnd):
        for child in self._child_windows(hwnd):
            cls = self._window_class(child)
            if LIST_CLASS.search(cls):
                return child
        return None

    def _click(self, hwnd) -> None:
        user32.SendMessageW(hwnd, BM_CLICK, 1, 0)

    def _send_key(self, hwnd, vk, repeat=1) -> None:
        self._force_foreground(hwnd)
        time.sleep(0.1)
        for _ in range(repeat):
            user32.keybd_event(vk, 0, 0, 0)
            user32.keybd_event(vk, 0, 2, 0)
            time.sleep(0.08)

    def _handle_dialog(self, hwnd) -> None:
        title = self._window_title(hwnd)
        cls = self._window_class(hwnd)
        self._log(f"Dialog detectado | titulo='{title}' | class='{cls}'")

        self._force_foreground(hwnd)
        time.sleep(0.3)

        ok_btn = self._button_by_title(hwnd, BUTTON_OK)
        cancel_btn = self._button_by_title(hwnd, BUTTON_CANCEL)

        list_ctrl = self._first_list_control(hwnd)
        if list_ctrl:
            self._log(f"Lista de certificados encontrada: {self._window_class(list_ctrl)}")
            self._force_foreground(list_ctrl)
            self._send_key(list_ctrl, VK_HOME)
            self._send_key(list_ctrl, VK_DOWN)
            self.last_action = "selecionou_primeiro_item"
            self._log("Acao: primeiro certificado selecionado (HOME+DOWN)")

        if ok_btn:
            self._click(ok_btn)
            self.last_action = "clicou_OK"
            self._log(f"Acao: botao OK clicado ('{self._window_title(ok_btn)}')")
            return

        self._press_enter(hwnd)
        self.last_action = "pressionou_ENTER"
        self._log("Acao: ENTER enviado como fallback")

    def _press_enter(self, hwnd) -> None:
        self._send_key(hwnd, VK_RETURN)

    def _get_desktop(self):
        """Importa pywinauto uma unica vez e reutiliza o objeto Desktop."""
        if self._pywinauto_ok is False:
            return None
        if self._desktop is not None:
            return self._desktop
        try:
            from pywinauto import Desktop

            self._desktop = Desktop(backend="uia")
            self._pywinauto_ok = True
            return self._desktop
        except Exception as exc:
            self._pywinauto_ok = False
            self._log_once(f"UIA indisponivel: {exc}")
            return None

    def _log_once(self, msg: str, cooldown: float = 30.0) -> None:
        """Evita spam de log: repete a mesma mensagem no max a cada cooldown."""
        now = time.time()
        if msg == self._last_uia_error and (now - self._last_uia_error_time) < cooldown:
            return
        self._last_uia_error = msg
        self._last_uia_error_time = now
        self._log(msg)

    def _handle_with_ui_automation(self) -> bool:
        """Controla o seletor moderno do Edge usando Windows UI Automation."""
        # Cooldown apos sucesso: nao precisa varrer tudo a cada 1s
        if time.time() - self._last_uia_ok < self.uia_cooldown_seg:
            return True
        try:
            desktop = self._get_desktop()
            if desktop is None:
                return False
            dialog_windows = []
            for top_window in desktop.windows():
                dialog_windows.extend(
                    control
                    for control in top_window.descendants()
                    if control.element_info.control_type == "Window"
                    and CERTIFICATE_WINDOW.search(control.window_text())
                )

            for window in dialog_windows:
                if not window.is_visible():
                    continue

                self._log(
                    f"Dialogo UIA detectado | titulo='{window.window_text()}'"
                )
                controls = window.descendants()
                user_item = next(
                    (
                        control
                        for control in controls
                        if control.element_info.control_type == "List"
                        and CERTIFICATE_USER.search(control.window_text())
                    ),
                    None,
                )
                if user_item is not None:
                    user_item.click_input()
                    self.last_action = "selecionou_certificado_UIA"
                    self._log("Acao UIA: certificado do usuario selecionado")
                else:
                    self._log("Acao UIA: certificado do usuario nao encontrado")
                    return False

                ok_button = next(
                    (
                        control
                        for control in controls
                        if control.element_info.control_type == "Button"
                        and control.window_text().strip().upper() == "OK"
                    ),
                    None,
                )
                if ok_button is not None:
                    ok_button.click_input()
                    self.last_action = "clicou_OK_UIA"
                    self._last_uia_ok = time.time()
                    self._log("Acao UIA: botao OK clicado")
                    return True

                self._log("Acao UIA: botao OK nao encontrado")
        except Exception as exc:
            self._log_once(f"UIA indisponivel ou dialogo ainda nao pronto: {exc}")
        return False

    def monitor(self, timeout: float = 90.0) -> None:
        start = time.time()
        self._collect_edge_pids()
        self._last_pid_collect = time.time()
        self._log(
            f"Inicio vigia | edge_pids={sorted(self.edge_pids)} | timeout={timeout}s"
        )
        while not self._stop.is_set():
            if time.time() - start > timeout:
                self._log("Timeout da vigia de dialogs alcancado")
                break
            # Coleta de PIDs cara: so a cada pid_refresh_seg
            if time.time() - self._last_pid_collect >= self.pid_refresh_seg:
                self._collect_edge_pids()
                self._last_pid_collect = time.time()
            self._handle_with_ui_automation()
            # Se ja tratou certificado via UIA, reduz varredura Win32
            if time.time() - self._last_uia_ok < self.uia_cooldown_seg:
                time.sleep(self.scan_interval)
                continue
            candidates = self._find_candidate_windows()
            for hwnd in candidates:
                if self._stop.is_set():
                    break
                if hwnd in self.detected:
                    continue
                self.detected.append(hwnd)
                self._handle_dialog(hwnd)
                time.sleep(1.0)
            time.sleep(self.scan_interval)
        self._log("Vigia de dialogs encerrada")

    def start(self, timeout: float = 90.0) -> threading.Thread:
        thread = threading.Thread(target=self.monitor, args=(timeout,), daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        self._stop.set()