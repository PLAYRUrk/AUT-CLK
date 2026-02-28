import threading
import time
import ctypes
import ctypes.wintypes as wintypes
import tkinter as tk
from tkinter import ttk
import json
import os

# Windows API
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Set proper argument/return types for hook functions
user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int, ctypes.c_void_p, wintypes.HINSTANCE, wintypes.DWORD
]
user32.SetWindowsHookExW.restype = ctypes.c_void_p

user32.CallNextHookEx.argtypes = [
    ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
]
user32.CallNextHookEx.restype = ctypes.c_long

user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG), wintypes.HWND, ctypes.c_uint, ctypes.c_uint
]

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

WH_MOUSE_LL = 14
WH_KEYBOARD_LL = 13
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_KEYDOWN = 0x0100
LLMHF_INJECTED = 0x00000001
VK_OEM_3 = 0xC0  # ~ (tilde / backtick) key

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

KBDLLHOOKPROC = ctypes.CFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


def click_left():
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def click_right():
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


# --- Windows 10 toast notification via PowerShell ---
def show_notification(title, message):
    ps_script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
        "ContentType = WindowsRuntime] > $null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]::"
        "GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$textNodes = $template.GetElementsByTagName('text'); "
        f"$textNodes.Item(0).AppendChild($template.CreateTextNode('{title}')) > $null; "
        f"$textNodes.Item(1).AppendChild($template.CreateTextNode('{message}')) > $null; "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
        "$toast.ExpirationTime = [DateTimeOffset]::Now.AddSeconds(3); "
        "$notifier = [Windows.UI.Notifications.ToastNotificationManager]::"
        "CreateToastNotifier('AUT-CLK'); "
        "$notifier.Show($toast)"
    )
    threading.Thread(
        target=lambda: os.popen(f'powershell -Command "{ps_script}"'),
        daemon=True
    ).start()


class AutoClicker:
    DEFAULT_SETTINGS = {
        "lmb_cps": 20,
        "rmb_cps": 50,
    }

    def __init__(self):
        self.lmb_running = False
        self.rmb_running = False
        self.lmb_enabled = False
        self.rmb_enabled = False
        self.lmb_cps = 20
        self.rmb_cps = 50
        self.globally_active = True

        self._load_settings()

        self.root = tk.Tk()
        self.root.title("AUT-CLK")
        self.root.geometry("320x350")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_gui()
        self._start_clicker_threads()
        self._install_hooks()

    def _load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                s = json.load(f)
            self.lmb_cps = s.get("lmb_cps", self.DEFAULT_SETTINGS["lmb_cps"])
            self.rmb_cps = s.get("rmb_cps", self.DEFAULT_SETTINGS["rmb_cps"])
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_settings(self):
        s = {
            "lmb_cps": self.lmb_cps,
            "rmb_cps": self.rmb_cps,
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(s, f, indent=2)

    def _on_close(self):
        self._save_settings()
        self.root.destroy()

    def _build_gui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill="both", expand=True)

        # --- LMB section ---
        lmb_frame = ttk.LabelFrame(frame, text="LMB Auto-Click", padding=10)
        lmb_frame.pack(fill="x", pady=(0, 8))

        cps_frame_l = ttk.Frame(lmb_frame)
        cps_frame_l.pack(fill="x")
        ttk.Label(cps_frame_l, text="CPS:").pack(side="left")
        self.lmb_cps_var = tk.IntVar(value=self.lmb_cps)
        self.lmb_scale = ttk.Scale(
            cps_frame_l, from_=1, to=100, variable=self.lmb_cps_var,
            orient="horizontal", command=lambda _: self._on_cps_change("lmb")
        )
        self.lmb_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.lmb_cps_label = ttk.Label(cps_frame_l, text=str(self.lmb_cps), width=4)
        self.lmb_cps_label.pack(side="right")

        btn_status_l = ttk.Frame(lmb_frame)
        btn_status_l.pack(fill="x", pady=(5, 0))
        self.lmb_status_var = tk.StringVar(value="OFF")
        self.lmb_btn = ttk.Button(btn_status_l, text="Enable", command=lambda: self._toggle("lmb"))
        self.lmb_btn.pack(side="left")
        ttk.Label(btn_status_l, textvariable=self.lmb_status_var, font=("Segoe UI", 12, "bold")).pack(side="right")

        # --- RMB section ---
        rmb_frame = ttk.LabelFrame(frame, text="RMB Auto-Click", padding=10)
        rmb_frame.pack(fill="x", pady=(0, 8))

        cps_frame_r = ttk.Frame(rmb_frame)
        cps_frame_r.pack(fill="x")
        ttk.Label(cps_frame_r, text="CPS:").pack(side="left")
        self.rmb_cps_var = tk.IntVar(value=self.rmb_cps)
        self.rmb_scale = ttk.Scale(
            cps_frame_r, from_=1, to=100, variable=self.rmb_cps_var,
            orient="horizontal", command=lambda _: self._on_cps_change("rmb")
        )
        self.rmb_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.rmb_cps_label = ttk.Label(cps_frame_r, text=str(self.rmb_cps), width=4)
        self.rmb_cps_label.pack(side="right")

        btn_status_r = ttk.Frame(rmb_frame)
        btn_status_r.pack(fill="x", pady=(5, 0))
        self.rmb_status_var = tk.StringVar(value="OFF")
        self.rmb_btn = ttk.Button(btn_status_r, text="Enable", command=lambda: self._toggle("rmb"))
        self.rmb_btn.pack(side="left")
        ttk.Label(btn_status_r, textvariable=self.rmb_status_var, font=("Segoe UI", 12, "bold")).pack(side="right")

        # --- Global status & hint ---
        self.global_status_var = tk.StringVar(value="ACTIVE  [~]")
        ttk.Label(
            frame, textvariable=self.global_status_var,
            font=("Segoe UI", 11, "bold"), foreground="green"
        ).pack(pady=(8, 0))

        ttk.Label(
            frame, text="Press ~ to toggle  |  Hold button to auto-click",
            foreground="gray"
        ).pack(pady=(3, 0))

    def _on_cps_change(self, which):
        if which == "lmb":
            self.lmb_cps = max(1, int(float(self.lmb_cps_var.get())))
            self.lmb_cps_label.config(text=str(self.lmb_cps))
        else:
            self.rmb_cps = max(1, int(float(self.rmb_cps_var.get())))
            self.rmb_cps_label.config(text=str(self.rmb_cps))
        self._save_settings()

    def _toggle(self, which):
        if which == "lmb":
            self.lmb_enabled = not self.lmb_enabled
            if self.lmb_enabled:
                self.lmb_status_var.set("ON")
                self.lmb_btn.config(text="Disable")
            else:
                self.lmb_running = False
                self.lmb_status_var.set("OFF")
                self.lmb_btn.config(text="Enable")
        else:
            self.rmb_enabled = not self.rmb_enabled
            if self.rmb_enabled:
                self.rmb_status_var.set("ON")
                self.rmb_btn.config(text="Disable")
            else:
                self.rmb_running = False
                self.rmb_status_var.set("OFF")
                self.rmb_btn.config(text="Enable")

    def _toggle_global(self):
        self.globally_active = not self.globally_active
        if self.globally_active:
            self.root.after(0, lambda: self.global_status_var.set("ACTIVE  [~]"))
            show_notification("AUT-CLK", "Autoclicker ON")
        else:
            self.lmb_running = False
            self.rmb_running = False
            self.root.after(0, lambda: self.global_status_var.set("PAUSED  [~]"))
            show_notification("AUT-CLK", "Autoclicker OFF")

    def _install_hooks(self):
        # --- Mouse hook ---
        def mouse_hook_proc(nCode, wParam, lParam):
            if nCode >= 0 and self.globally_active:
                info = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                is_injected = info.flags & LLMHF_INJECTED

                if not is_injected:
                    if wParam == WM_LBUTTONDOWN and self.lmb_enabled:
                        self.lmb_running = True
                    elif wParam == WM_LBUTTONUP:
                        self.lmb_running = False
                    elif wParam == WM_RBUTTONDOWN and self.rmb_enabled:
                        self.rmb_running = True
                    elif wParam == WM_RBUTTONUP:
                        self.rmb_running = False

            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        self._mouse_hook_cb = HOOKPROC(mouse_hook_proc)

        # --- Keyboard hook ---
        def kb_hook_proc(nCode, wParam, lParam):
            if nCode >= 0 and wParam == WM_KEYDOWN:
                info = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if info.vkCode == VK_OEM_3:
                    self._toggle_global()

            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        self._kb_hook_cb = KBDLLHOOKPROC(kb_hook_proc)

        def hook_thread():
            user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_hook_cb, None, 0)
            user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._kb_hook_cb, None, 0)
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        t = threading.Thread(target=hook_thread, daemon=True)
        t.start()

    def _start_clicker_threads(self):
        def lmb_loop():
            while True:
                if self.lmb_running and self.lmb_enabled and self.globally_active:
                    click_left()
                    time.sleep(1.0 / self.lmb_cps)
                else:
                    time.sleep(0.005)

        def rmb_loop():
            while True:
                if self.rmb_running and self.rmb_enabled and self.globally_active:
                    click_right()
                    time.sleep(1.0 / self.rmb_cps)
                else:
                    time.sleep(0.005)

        threading.Thread(target=lmb_loop, daemon=True).start()
        threading.Thread(target=rmb_loop, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AutoClicker()
    app.run()
