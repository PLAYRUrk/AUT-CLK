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

user32.DefWindowProcW.argtypes = [wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_long

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.c_uint
]

user32.SetLayeredWindowAttributes.argtypes = [
    wintypes.HWND, wintypes.COLORREF, ctypes.c_byte, wintypes.DWORD
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
WM_SYSKEYDOWN = 0x0104
LLMHF_INJECTED = 0x00000001

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

# Virtual key code -> human-readable name
VK_NAMES = {
    0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter", 0x10: "Shift", 0x11: "Ctrl",
    0x12: "Alt", 0x13: "Pause", 0x14: "CapsLock", 0x1B: "Esc",
    0x20: "Space", 0x21: "PgUp", 0x22: "PgDn", 0x23: "End", 0x24: "Home",
    0x25: "Left", 0x26: "Up", 0x27: "Right", 0x28: "Down",
    0x2C: "PrtSc", 0x2D: "Insert", 0x2E: "Delete",
    0x5B: "LWin", 0x5C: "RWin",
    0x60: "Num0", 0x61: "Num1", 0x62: "Num2", 0x63: "Num3", 0x64: "Num4",
    0x65: "Num5", 0x66: "Num6", 0x67: "Num7", 0x68: "Num8", 0x69: "Num9",
    0x6A: "Num*", 0x6B: "Num+", 0x6D: "Num-", 0x6E: "Num.", 0x6F: "Num/",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4", 0x74: "F5", 0x75: "F6",
    0x76: "F7", 0x77: "F8", 0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
    0x90: "NumLock", 0x91: "ScrollLock",
    0xA0: "LShift", 0xA1: "RShift", 0xA2: "LCtrl", 0xA3: "RCtrl",
    0xA4: "LAlt", 0xA5: "RAlt",
    0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".", 0xBF: "/",
    0xC0: "~", 0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'",
}


def vk_to_name(vk):
    if 0x30 <= vk <= 0x39:
        return chr(vk)
    if 0x41 <= vk <= 0x5A:
        return chr(vk)
    return VK_NAMES.get(vk, f"0x{vk:02X}")


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


class IndicatorOverlay:
    """Native Win32 overlay dot — visible on top of fullscreen (borderless) apps."""

    COLOR_ACTIVE = 0x0050C822    # ARGB: green (#22c850)
    COLOR_INACTIVE = 0x004444EF  # ARGB: red  (#ef4444)
    COLOR_INACTIVE_DIM = 0x00222277  # dimmed red for blink-off phase

    # Win32 constants
    WS_EX_TOPMOST = 0x00000008
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_NOACTIVATE = 0x08000000
    WS_POPUP = 0x80000000
    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040
    GWL_EXSTYLE = -20
    LWA_COLORKEY = 0x01
    LWA_ALPHA = 0x02
    ULW_ALPHA = 0x02
    AC_SRC_OVER = 0x00
    AC_SRC_ALPHA = 0x01
    DIB_RGB_COLORS = 0
    BI_RGB = 0
    CS_VREDRAW = 0x0001
    CS_HREDRAW = 0x0002
    IDC_ARROW = 32512
    WM_DESTROY = 0x0002
    WM_PAINT = 0x000F
    WM_TIMER = 0x0113
    SW_SHOWNOACTIVATE = 4
    SW_HIDE = 0

    def __init__(self, shape="circle", radius=10, line_width=6, line_length=40,
                 x=10, y=10, blink=True):
        self._shape = shape
        self._radius = radius
        self._line_width = line_width
        self._line_length = line_length
        self._pos_x = x
        self._pos_y = y
        self._blink = blink

        self._active = True
        self._blink_visible = True
        self._hwnd = None
        self._visible = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        for _ in range(100):
            if self._hwnd:
                break
            time.sleep(0.01)

    def _calc_window_size(self):
        if self._shape == "line":
            return self._line_length, self._line_width
        return self._radius * 2, self._radius * 2

    def _run(self):
        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long, wintypes.HWND, ctypes.c_uint,
            wintypes.WPARAM, wintypes.LPARAM
        )

        class WNDCLASSEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("style", ctypes.c_uint),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HANDLE),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
                ("hIconSm", wintypes.HICON),
            ]

        def wnd_proc(hwnd, msg, wp, lp):
            if msg == self.WM_PAINT:
                self._paint(hwnd)
                return 0
            if msg == self.WM_TIMER:
                if wp == 1:
                    # Re-raise to stay on top
                    user32.SetWindowPos(
                        self._hwnd, self.HWND_TOPMOST, 0, 0, 0, 0,
                        self.SWP_NOMOVE | self.SWP_NOSIZE | self.SWP_NOACTIVATE | self.SWP_SHOWWINDOW
                    )
                elif wp == 2:
                    # Blink timer
                    if not self._active and self._blink:
                        self._blink_visible = not self._blink_visible
                        user32.InvalidateRect(self._hwnd, None, True)
                return 0
            if msg == self.WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wp, lp)

        self._wnd_proc_ref = WNDPROC(wnd_proc)

        hInstance = kernel32.GetModuleHandleW(None)
        className = "AUTCLK_OVERLAY"

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = self.CS_HREDRAW | self.CS_VREDRAW
        wc.lpfnWndProc = self._wnd_proc_ref
        wc.hInstance = hInstance
        wc.hCursor = user32.LoadCursorW(None, self.IDC_ARROW)
        wc.lpszClassName = className
        user32.RegisterClassExW(ctypes.byref(wc))

        ex_style = (
            self.WS_EX_TOPMOST | self.WS_EX_LAYERED |
            self.WS_EX_TRANSPARENT | self.WS_EX_TOOLWINDOW |
            self.WS_EX_NOACTIVATE
        )

        w, h = self._calc_window_size()
        self._hwnd = user32.CreateWindowExW(
            ex_style, className, "AUT-CLK Indicator",
            self.WS_POPUP,
            self._pos_x, self._pos_y, w, h,
            None, None, hInstance, None
        )

        # Set full window as color-keyed on black, so only our painted shape shows
        user32.SetLayeredWindowAttributes(
            self._hwnd, 0x00000000, 0, self.LWA_COLORKEY
        )

        self._paint(self._hwnd)

        # Timer 1: re-raise overlay every 500ms
        user32.SetTimer(self._hwnd, 1, 500, None)
        # Timer 2: blink every 400ms
        user32.SetTimer(self._hwnd, 2, 400, None)

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _paint(self, hwnd):
        gdi32 = ctypes.windll.gdi32

        class PAINTSTRUCT(ctypes.Structure):
            _fields_ = [
                ("hdc", wintypes.HDC),
                ("fErase", wintypes.BOOL),
                ("rcPaint", wintypes.RECT),
                ("fRestore", wintypes.BOOL),
                ("fIncUpdate", wintypes.BOOL),
                ("rgbReserved", ctypes.c_byte * 32),
            ]

        w, h = self._calc_window_size()

        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

        # Fill background with black (color key — will be transparent)
        black_brush = gdi32.CreateSolidBrush(0x00000000)
        rect = wintypes.RECT(0, 0, w, h)
        user32.FillRect(hdc, ctypes.byref(rect), black_brush)
        gdi32.DeleteObject(black_brush)

        # Determine color
        if self._active:
            color = self.COLOR_ACTIVE
            pen_color = 0x00346616  # dark green
        else:
            if self._blink and not self._blink_visible:
                color = self.COLOR_INACTIVE_DIM
                pen_color = 0x00111155  # very dark red
            else:
                color = self.COLOR_INACTIVE
                pen_color = 0x001B1B99  # dark red

        brush = gdi32.CreateSolidBrush(color)
        pen = gdi32.CreatePen(0, 2, pen_color)
        old_brush = gdi32.SelectObject(hdc, brush)
        old_pen = gdi32.SelectObject(hdc, pen)

        if self._shape == "line":
            gdi32.Rectangle(hdc, 0, 0, w, h)
        else:
            gdi32.Ellipse(hdc, 0, 0, w, h)

        gdi32.SelectObject(hdc, old_brush)
        gdi32.SelectObject(hdc, old_pen)
        gdi32.DeleteObject(brush)
        gdi32.DeleteObject(pen)

        user32.EndPaint(hwnd, ctypes.byref(ps))

    def set_active(self, active):
        self._active = active
        if active:
            self._blink_visible = True
        if self._hwnd:
            user32.InvalidateRect(self._hwnd, None, True)

    def set_position(self, x, y):
        self._pos_x = x
        self._pos_y = y
        if self._hwnd:
            w, h = self._calc_window_size()
            user32.SetWindowPos(
                self._hwnd, self.HWND_TOPMOST, x, y, w, h,
                self.SWP_NOACTIVATE | self.SWP_SHOWWINDOW
            )

    def update_config(self, shape=None, radius=None, line_width=None,
                      line_length=None, x=None, y=None, blink=None):
        if shape is not None:
            self._shape = shape
        if radius is not None:
            self._radius = radius
        if line_width is not None:
            self._line_width = line_width
        if line_length is not None:
            self._line_length = line_length
        if x is not None:
            self._pos_x = x
        if y is not None:
            self._pos_y = y
        if blink is not None:
            self._blink = blink
        if self._hwnd:
            w, h = self._calc_window_size()
            user32.SetWindowPos(
                self._hwnd, self.HWND_TOPMOST,
                self._pos_x, self._pos_y, w, h,
                self.SWP_NOACTIVATE | self.SWP_SHOWWINDOW
            )
            user32.InvalidateRect(self._hwnd, None, True)

    def show(self):
        if self._hwnd and not self._visible:
            self._visible = True
            user32.ShowWindow(self._hwnd, self.SW_SHOWNOACTIVATE)

    def hide(self):
        if self._hwnd and self._visible:
            self._visible = False
            user32.ShowWindow(self._hwnd, self.SW_HIDE)

    def destroy(self):
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)


class AutoClicker:
    DEFAULT_TOGGLE_VK = 0xC0  # ~ key

    def __init__(self):
        self.lmb_running = False
        self.rmb_running = False
        self.lmb_enabled = False
        self.rmb_enabled = False
        self.lmb_cps = 20
        self.rmb_cps = 50
        self.globally_active = True
        self.toggle_vk = self.DEFAULT_TOGGLE_VK
        self.show_indicator = False
        self._binding_mode = False

        # Indicator settings
        self.indicator_x = 10
        self.indicator_y = 10
        self.indicator_shape = "circle"
        self.indicator_radius = 10
        self.indicator_line_width = 6
        self.indicator_line_length = 40
        self.indicator_blink = True

        self._load_settings()

        self.root = tk.Tk()
        self.root.title("AUT-CLK")
        self.root.geometry("320x620")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.indicator = IndicatorOverlay(
            shape=self.indicator_shape,
            radius=self.indicator_radius,
            line_width=self.indicator_line_width,
            line_length=self.indicator_line_length,
            x=self.indicator_x,
            y=self.indicator_y,
            blink=self.indicator_blink,
        )
        if self.show_indicator:
            self.indicator.show()

        self._build_gui()
        self._start_clicker_threads()
        self._install_hooks()

    def _load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                s = json.load(f)
            self.lmb_cps = s.get("lmb_cps", 20)
            self.rmb_cps = s.get("rmb_cps", 50)
            self.toggle_vk = s.get("toggle_vk", self.DEFAULT_TOGGLE_VK)
            self.show_indicator = s.get("show_indicator", False)
            self.indicator_x = s.get("indicator_x", 10)
            self.indicator_y = s.get("indicator_y", 10)
            self.indicator_shape = s.get("indicator_shape", "circle")
            self.indicator_radius = s.get("indicator_radius", 10)
            self.indicator_line_width = s.get("indicator_line_width", 6)
            self.indicator_line_length = s.get("indicator_line_length", 40)
            self.indicator_blink = s.get("indicator_blink", True)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_settings(self):
        s = {
            "lmb_cps": self.lmb_cps,
            "rmb_cps": self.rmb_cps,
            "toggle_vk": self.toggle_vk,
            "show_indicator": self.show_indicator,
            "indicator_x": self.indicator_x,
            "indicator_y": self.indicator_y,
            "indicator_shape": self.indicator_shape,
            "indicator_radius": self.indicator_radius,
            "indicator_line_width": self.indicator_line_width,
            "indicator_line_length": self.indicator_line_length,
            "indicator_blink": self.indicator_blink,
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(s, f, indent=2)

    def _on_close(self):
        self._save_settings()
        self.indicator.destroy()
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

        # --- Hotkey bind section ---
        bind_frame = ttk.LabelFrame(frame, text="Toggle hotkey", padding=10)
        bind_frame.pack(fill="x", pady=(0, 8))

        bind_row = ttk.Frame(bind_frame)
        bind_row.pack(fill="x")

        self.bind_var = tk.StringVar(value=vk_to_name(self.toggle_vk))
        self.bind_label = ttk.Label(bind_row, textvariable=self.bind_var, font=("Segoe UI", 12, "bold"), width=10, anchor="center")
        self.bind_label.pack(side="left", padx=(0, 10))

        self.bind_btn = ttk.Button(bind_row, text="Rebind", command=self._start_binding)
        self.bind_btn.pack(side="left")

        self.bind_hint_var = tk.StringVar(value="")
        self.bind_hint = ttk.Label(bind_row, textvariable=self.bind_hint_var, foreground="gray")
        self.bind_hint.pack(side="right")

        # --- Indicator toggle ---
        self.indicator_var = tk.BooleanVar(value=self.show_indicator)
        ttk.Checkbutton(
            frame, text="Show overlay indicator",
            variable=self.indicator_var, command=self._toggle_indicator
        ).pack(anchor="w", pady=(4, 0))

        # --- Indicator settings ---
        self.ind_settings_frame = ttk.LabelFrame(frame, text="Indicator settings", padding=8)
        self.ind_settings_frame.pack(fill="x", pady=(4, 4))

        # Shape radio buttons
        shape_row = ttk.Frame(self.ind_settings_frame)
        shape_row.pack(fill="x")
        ttk.Label(shape_row, text="Shape:").pack(side="left")
        self.shape_var = tk.StringVar(value=self.indicator_shape)
        ttk.Radiobutton(shape_row, text="Circle", variable=self.shape_var,
                        value="circle", command=self._on_shape_change).pack(side="left", padx=(8, 0))
        ttk.Radiobutton(shape_row, text="Line", variable=self.shape_var,
                        value="line", command=self._on_shape_change).pack(side="left", padx=(8, 0))

        # Radius (for circle)
        self.radius_frame = ttk.Frame(self.ind_settings_frame)
        self.radius_frame.pack(fill="x", pady=(4, 0))
        ttk.Label(self.radius_frame, text="Radius:").pack(side="left")
        self.radius_var = tk.IntVar(value=self.indicator_radius)
        self.radius_scale = ttk.Scale(
            self.radius_frame, from_=5, to=50, variable=self.radius_var,
            orient="horizontal", command=lambda _: self._on_indicator_param_change()
        )
        self.radius_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.radius_label = ttk.Label(self.radius_frame, text=str(self.indicator_radius), width=4)
        self.radius_label.pack(side="right")

        # Line width (for line)
        self.lw_frame = ttk.Frame(self.ind_settings_frame)
        self.lw_frame.pack(fill="x", pady=(4, 0))
        ttk.Label(self.lw_frame, text="Line W:").pack(side="left")
        self.lw_var = tk.IntVar(value=self.indicator_line_width)
        self.lw_scale = ttk.Scale(
            self.lw_frame, from_=2, to=20, variable=self.lw_var,
            orient="horizontal", command=lambda _: self._on_indicator_param_change()
        )
        self.lw_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.lw_label = ttk.Label(self.lw_frame, text=str(self.indicator_line_width), width=4)
        self.lw_label.pack(side="right")

        # Line length (for line)
        self.ll_frame = ttk.Frame(self.ind_settings_frame)
        self.ll_frame.pack(fill="x", pady=(4, 0))
        ttk.Label(self.ll_frame, text="Line L:").pack(side="left")
        self.ll_var = tk.IntVar(value=self.indicator_line_length)
        self.ll_scale = ttk.Scale(
            self.ll_frame, from_=10, to=200, variable=self.ll_var,
            orient="horizontal", command=lambda _: self._on_indicator_param_change()
        )
        self.ll_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.ll_label = ttk.Label(self.ll_frame, text=str(self.indicator_line_length), width=4)
        self.ll_label.pack(side="right")

        # Position X
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        pos_x_row = ttk.Frame(self.ind_settings_frame)
        pos_x_row.pack(fill="x", pady=(4, 0))
        ttk.Label(pos_x_row, text="Pos X:").pack(side="left")
        self.pos_x_var = tk.IntVar(value=self.indicator_x)
        self.pos_x_scale = ttk.Scale(
            pos_x_row, from_=0, to=screen_w, variable=self.pos_x_var,
            orient="horizontal", command=lambda _: self._on_indicator_param_change()
        )
        self.pos_x_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.pos_x_label = ttk.Label(pos_x_row, text=str(self.indicator_x), width=5)
        self.pos_x_label.pack(side="right")

        # Position Y
        pos_y_row = ttk.Frame(self.ind_settings_frame)
        pos_y_row.pack(fill="x", pady=(4, 0))
        ttk.Label(pos_y_row, text="Pos Y:").pack(side="left")
        self.pos_y_var = tk.IntVar(value=self.indicator_y)
        self.pos_y_scale = ttk.Scale(
            pos_y_row, from_=0, to=screen_h, variable=self.pos_y_var,
            orient="horizontal", command=lambda _: self._on_indicator_param_change()
        )
        self.pos_y_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.pos_y_label = ttk.Label(pos_y_row, text=str(self.indicator_y), width=5)
        self.pos_y_label.pack(side="right")

        # Blink checkbox
        self.blink_var = tk.BooleanVar(value=self.indicator_blink)
        ttk.Checkbutton(
            self.ind_settings_frame, text="Blink when inactive",
            variable=self.blink_var, command=self._on_indicator_param_change
        ).pack(anchor="w", pady=(4, 0))

        # Show/hide shape-specific widgets
        self._update_shape_widgets()

        # --- Global status & hint ---
        self.global_status_var = tk.StringVar(value="ACTIVE")
        ttk.Label(
            frame, textvariable=self.global_status_var,
            font=("Segoe UI", 11, "bold"), foreground="green"
        ).pack(pady=(6, 0))

        ttk.Label(
            frame, text="Hold mouse button while enabled to auto-click",
            foreground="gray"
        ).pack(pady=(3, 0))

    def _toggle_indicator(self):
        self.show_indicator = self.indicator_var.get()
        if self.show_indicator:
            self.indicator.set_active(self.globally_active)
            self.indicator.show()
        else:
            self.indicator.hide()
        self._save_settings()

    def _on_shape_change(self):
        self.indicator_shape = self.shape_var.get()
        self._update_shape_widgets()
        self._on_indicator_param_change()

    def _update_shape_widgets(self):
        if self.indicator_shape == "circle":
            self.radius_frame.pack(fill="x", pady=(4, 0))
            self.lw_frame.pack_forget()
            self.ll_frame.pack_forget()
        else:
            self.radius_frame.pack_forget()
            self.lw_frame.pack(fill="x", pady=(4, 0))
            self.ll_frame.pack(fill="x", pady=(4, 0))

    def _on_indicator_param_change(self):
        self.indicator_radius = max(5, int(float(self.radius_var.get())))
        self.indicator_line_width = max(2, int(float(self.lw_var.get())))
        self.indicator_line_length = max(10, int(float(self.ll_var.get())))
        self.indicator_x = max(0, int(float(self.pos_x_var.get())))
        self.indicator_y = max(0, int(float(self.pos_y_var.get())))
        self.indicator_blink = self.blink_var.get()
        self.indicator_shape = self.shape_var.get()

        # Update labels
        self.radius_label.config(text=str(self.indicator_radius))
        self.lw_label.config(text=str(self.indicator_line_width))
        self.ll_label.config(text=str(self.indicator_line_length))
        self.pos_x_label.config(text=str(self.indicator_x))
        self.pos_y_label.config(text=str(self.indicator_y))

        # Update indicator on the fly
        self.indicator.update_config(
            shape=self.indicator_shape,
            radius=self.indicator_radius,
            line_width=self.indicator_line_width,
            line_length=self.indicator_line_length,
            x=self.indicator_x,
            y=self.indicator_y,
            blink=self.indicator_blink,
        )
        self._save_settings()

    def _start_binding(self):
        self._binding_mode = True
        self.bind_var.set("...")
        self.bind_hint_var.set("Press any key")
        self.bind_btn.config(state="disabled")

    def _finish_binding(self, vk):
        self._binding_mode = False
        self.toggle_vk = vk
        self.root.after(0, lambda: self.bind_var.set(vk_to_name(vk)))
        self.root.after(0, lambda: self.bind_hint_var.set(""))
        self.root.after(0, lambda: self.bind_btn.config(state="normal"))
        self._save_settings()

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
            self.root.after(0, lambda: self.global_status_var.set("ACTIVE"))
        else:
            self.lmb_running = False
            self.rmb_running = False
            self.root.after(0, lambda: self.global_status_var.set("PAUSED"))
        if self.show_indicator:
            self.root.after(0, lambda: self.indicator.set_active(self.globally_active))

    def _install_hooks(self):
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

        def kb_hook_proc(nCode, wParam, lParam):
            if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                info = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = info.vkCode

                if self._binding_mode:
                    self._finish_binding(vk)
                elif vk == self.toggle_vk:
                    self._toggle_global()

            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        self._kb_hook_cb = HOOKPROC(kb_hook_proc)

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
