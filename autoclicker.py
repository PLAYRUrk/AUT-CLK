import threading
import time
import ctypes
import ctypes.wintypes as wintypes
import tkinter as tk
from tkinter import ttk

# Windows API
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
LLMHF_INJECTED = 0x00000001

# Low-level mouse hook struct
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)


def click():
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


class AutoClicker:
    def __init__(self):
        self.running = False
        self.enabled = False
        self.cps = 20
        self.physical_lmb_down = False

        self.root = tk.Tk()
        self.root.title("AUT-CLK")
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self._build_gui()
        self._start_clicker_thread()
        self._install_mouse_hook()

    def _build_gui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Clicks per second:").pack(anchor="w")

        self.cps_var = tk.IntVar(value=self.cps)
        cps_frame = ttk.Frame(frame)
        cps_frame.pack(fill="x", pady=(0, 10))

        self.cps_scale = ttk.Scale(
            cps_frame, from_=1, to=100, variable=self.cps_var,
            orient="horizontal", command=self._on_cps_change
        )
        self.cps_scale.pack(side="left", fill="x", expand=True)

        self.cps_label = ttk.Label(cps_frame, text=str(self.cps), width=4)
        self.cps_label.pack(side="right", padx=(5, 0))

        self.status_var = tk.StringVar(value="OFF")
        self.status_label = ttk.Label(
            frame, textvariable=self.status_var, font=("Segoe UI", 16, "bold")
        )
        self.status_label.pack(pady=5)

        self.toggle_btn = ttk.Button(
            frame, text="Enable (hold LMB to click)", command=self._toggle
        )
        self.toggle_btn.pack(fill="x", pady=(5, 0))

        ttk.Label(
            frame, text="Hold LMB while enabled to auto-click",
            foreground="gray"
        ).pack(pady=(10, 0))

    def _on_cps_change(self, _):
        self.cps = max(1, int(float(self.cps_var.get())))
        self.cps_label.config(text=str(self.cps))

    def _toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.status_var.set("ON — waiting for LMB")
            self.toggle_btn.config(text="Disable")
        else:
            self.running = False
            self.physical_lmb_down = False
            self.status_var.set("OFF")
            self.toggle_btn.config(text="Enable (hold LMB to click)")

    def _install_mouse_hook(self):
        """Install a low-level mouse hook to track physical LMB presses,
        ignoring injected (synthetic) events from our own clicks."""

        def hook_proc(nCode, wParam, lParam):
            if nCode >= 0:
                info = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                is_injected = info.flags & LLMHF_INJECTED

                if not is_injected and self.enabled:
                    if wParam == WM_LBUTTONDOWN:
                        self.physical_lmb_down = True
                        self.running = True
                        self.root.after(0, lambda: self.status_var.set("ON — clicking"))
                    elif wParam == WM_LBUTTONUP:
                        self.physical_lmb_down = False
                        self.running = False
                        self.root.after(0, lambda: self.status_var.set("ON — waiting for LMB"))

            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # prevent garbage collection of the callback
        self._hook_proc = HOOKPROC(hook_proc)

        def hook_thread():
            self._hook = user32.SetWindowsHookExW(
                WH_MOUSE_LL, self._hook_proc, None, 0
            )
            # Message loop required for the hook to work
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        t = threading.Thread(target=hook_thread, daemon=True)
        t.start()

    def _start_clicker_thread(self):
        """Separate thread that performs clicks when running is True."""
        def loop():
            while True:
                if self.running and self.enabled:
                    click()
                    time.sleep(1.0 / self.cps)
                else:
                    time.sleep(0.01)

        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AutoClicker()
    app.run()
