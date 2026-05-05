import threading
import time
import ctypes
import ctypes.wintypes as wintypes
import tkinter as tk
from tkinter import ttk
import json
import os
import random
import sys

# Windows API
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# DPI awareness — ensures correct positioning on scaled displays & helps with fullscreen overlay
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
except (AttributeError, OSError):
    try:
        user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass

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

user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND

user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL

user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int

user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

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
LLKHF_INJECTED = 0x00000010
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105

if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(_BASE_DIR, "settings.json")

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
                 x=10, y=10, blink=True, text_size=16):
        self._shape = shape
        self._radius = radius
        self._line_width = line_width
        self._line_length = line_length
        self._pos_x = x
        self._pos_y = y
        self._blink = blink
        self._text_size = text_size

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
        if self._shape == "text":
            # Base raster size of Terminal font (always rendered at this size, then scaled)
            base_h = 12
            base_char_w = 8
            base_w = base_char_w * 7  # 7 chars ("NOT RDY")
            scale = self._text_size / base_h
            w = int(base_w * scale) + 2
            h = int(base_h * scale) + 2
            return w, h
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
                    # Re-raise to stay on top (only when visible)
                    if self._visible:
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
        elif self._shape == "text":
            # Render text at fixed base size with bitmap Terminal font,
            # then scale up with nearest-neighbor to keep the pixel look.
            base_h = 12
            base_char_w = 8
            base_w = base_char_w * 7  # 7 chars max

            text = "ARMED" if self._active else "NOT RDY"
            txt_color = color
            if not self._active and self._blink and not self._blink_visible:
                txt_color = self.COLOR_INACTIVE_DIM

            # Create off-screen DC at base size
            mem_dc = gdi32.CreateCompatibleDC(hdc)
            mem_bmp = gdi32.CreateCompatibleBitmap(hdc, base_w, base_h)
            old_bmp = gdi32.SelectObject(mem_dc, mem_bmp)

            # Fill with black (will become transparent via color key)
            bg_brush = gdi32.CreateSolidBrush(0x00000000)
            base_rect = wintypes.RECT(0, 0, base_w, base_h)
            user32.FillRect(mem_dc, ctypes.byref(base_rect), bg_brush)
            gdi32.DeleteObject(bg_brush)

            # Create Small Fonts at its native raster size (clean minimal pixel font)
            font = gdi32.CreateFontW(
                base_h, 0, 0, 0, 400,  # normal weight
                0, 0, 0,
                0,  # DEFAULT_CHARSET
                0, 0, 0,
                0x30,  # FF_MODERN | FIXED_PITCH
                "Small Fonts"
            )
            old_font = gdi32.SelectObject(mem_dc, font)
            gdi32.SetBkMode(mem_dc, 1)  # TRANSPARENT
            gdi32.SetTextColor(mem_dc, txt_color)
            user32.DrawTextW(mem_dc, text, -1, ctypes.byref(base_rect),
                             0x0025)  # DT_CENTER | DT_VCENTER | DT_SINGLELINE

            # Scale to target size with nearest-neighbor (keeps pixels sharp)
            gdi32.SetStretchBltMode(hdc, 3)  # COLORONCOLOR — no smoothing
            gdi32.StretchBlt(
                hdc, 0, 0, w, h,
                mem_dc, 0, 0, base_w, base_h,
                0x00CC0020  # SRCCOPY
            )

            # Cleanup
            gdi32.SelectObject(mem_dc, old_font)
            gdi32.DeleteObject(font)
            gdi32.SelectObject(mem_dc, old_bmp)
            gdi32.DeleteObject(mem_bmp)
            gdi32.DeleteDC(mem_dc)
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
            flags = self.SWP_NOACTIVATE
            if self._visible:
                flags |= self.SWP_SHOWWINDOW
            user32.SetWindowPos(
                self._hwnd, self.HWND_TOPMOST, x, y, w, h,
                flags
            )

    def update_config(self, shape=None, radius=None, line_width=None,
                      line_length=None, x=None, y=None, blink=None, text_size=None):
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
        if text_size is not None:
            self._text_size = text_size
        if self._hwnd:
            w, h = self._calc_window_size()
            flags = self.SWP_NOACTIVATE
            if self._visible:
                flags |= self.SWP_SHOWWINDOW
            user32.SetWindowPos(
                self._hwnd, self.HWND_TOPMOST,
                self._pos_x, self._pos_y, w, h,
                flags
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

    # Presets: (name, min_cps, max_cps, jitter_ms)
    LMB_PRESETS = {
        "Sword PvP": (10, 15, 15),
        "Block Break": (18, 20, 5),
        "Bridge": (6, 8, 20),
        "Custom": None,
    }

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
        self._binding_mode = None

        # Smart LMB settings
        self.lmb_smart = False
        self.lmb_min_cps = 10
        self.lmb_max_cps = 15
        self.lmb_jitter_ms = 15
        self.lmb_preset = "Custom"

        # Indicator settings
        self.indicator_x = 10
        self.indicator_y = 10
        self.indicator_shape = "circle"
        self.indicator_radius = 10
        self.indicator_line_width = 6
        self.indicator_line_length = 40
        self.indicator_blink = True
        self.indicator_text_size = 16

        # Window lock settings
        self.target_window_enabled = False
        self.target_process = ""
        self.target_window_title = ""
        self._target_cache_time = 0.0
        self._target_cache_result = True
        self._window_entries = []

        self._load_settings()

        self.root = tk.Tk()
        self.root.title("AUT-CLK")
        self.root.geometry("320x900")
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
            text_size=self.indicator_text_size,
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
            self.lmb_smart = s.get("lmb_smart", False)
            self.lmb_min_cps = s.get("lmb_min_cps", 10)
            self.lmb_max_cps = s.get("lmb_max_cps", 15)
            self.lmb_jitter_ms = s.get("lmb_jitter_ms", 15)
            self.lmb_preset = s.get("lmb_preset", "Custom")
            self.show_indicator = s.get("show_indicator", False)
            self.indicator_x = s.get("indicator_x", 10)
            self.indicator_y = s.get("indicator_y", 10)
            self.indicator_shape = s.get("indicator_shape", "circle")
            self.indicator_radius = s.get("indicator_radius", 10)
            self.indicator_line_width = s.get("indicator_line_width", 6)
            self.indicator_line_length = s.get("indicator_line_length", 40)
            self.indicator_blink = s.get("indicator_blink", True)
            self.indicator_text_size = s.get("indicator_text_size", 16)
            self.target_window_enabled = s.get("target_window_enabled", False)
            self.target_process = s.get("target_process", "")
            self.target_window_title = s.get("target_window_title", "")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_settings(self):
        s = {
            "lmb_cps": self.lmb_cps,
            "rmb_cps": self.rmb_cps,
            "toggle_vk": self.toggle_vk,
            "lmb_smart": self.lmb_smart,
            "lmb_min_cps": self.lmb_min_cps,
            "lmb_max_cps": self.lmb_max_cps,
            "lmb_jitter_ms": self.lmb_jitter_ms,
            "lmb_preset": self.lmb_preset,
            "show_indicator": self.show_indicator,
            "indicator_x": self.indicator_x,
            "indicator_y": self.indicator_y,
            "indicator_shape": self.indicator_shape,
            "indicator_radius": self.indicator_radius,
            "indicator_line_width": self.indicator_line_width,
            "indicator_line_length": self.indicator_line_length,
            "indicator_blink": self.indicator_blink,
            "indicator_text_size": self.indicator_text_size,
            "target_window_enabled": self.target_window_enabled,
            "target_process": self.target_process,
            "target_window_title": self.target_window_title,
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(s, f, indent=2)

    def _on_close(self):
        self._save_settings()
        self.indicator.destroy()
        self.root.destroy()

    def _current_lmb_cps(self) -> int:
        if self.lmb_smart:
            return (self.lmb_min_cps + self.lmb_max_cps) // 2
        return self.lmb_cps

    def _current_rmb_cps(self) -> int:
        return self.rmb_cps

    def _build_gui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill="both", expand=True)

        # --- LMB section ---
        lmb_frame = ttk.LabelFrame(frame, text="LMB Auto-Click", padding=10)
        lmb_frame.pack(fill="x", pady=(0, 8))

        # Smart mode toggle
        self.lmb_smart_var = tk.BooleanVar(value=self.lmb_smart)
        ttk.Checkbutton(
            lmb_frame, text="Smart mode (range + jitter)",
            variable=self.lmb_smart_var, command=self._on_smart_toggle
        ).pack(anchor="w")

        # --- Fixed CPS (shown when smart=off) ---
        self.lmb_fixed_frame = ttk.Frame(lmb_frame)
        cps_frame_l = ttk.Frame(self.lmb_fixed_frame)
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

        # --- Smart CPS (shown when smart=on) ---
        self.lmb_smart_frame = ttk.Frame(lmb_frame)

        # Presets row
        preset_row = ttk.Frame(self.lmb_smart_frame)
        preset_row.pack(fill="x", pady=(2, 4))
        ttk.Label(preset_row, text="Preset:").pack(side="left")
        self.lmb_preset_var = tk.StringVar(value=self.lmb_preset)
        preset_combo = ttk.Combobox(
            preset_row, textvariable=self.lmb_preset_var,
            values=list(self.LMB_PRESETS.keys()), state="readonly", width=12
        )
        preset_combo.pack(side="left", padx=5)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Min CPS
        min_row = ttk.Frame(self.lmb_smart_frame)
        min_row.pack(fill="x")
        ttk.Label(min_row, text="Min CPS:").pack(side="left")
        self.lmb_min_var = tk.IntVar(value=self.lmb_min_cps)
        self.lmb_min_scale = ttk.Scale(
            min_row, from_=1, to=25, variable=self.lmb_min_var,
            orient="horizontal", command=lambda _: self._on_smart_param_change()
        )
        self.lmb_min_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.lmb_min_label = ttk.Label(min_row, text=str(self.lmb_min_cps), width=3)
        self.lmb_min_label.pack(side="right")

        # Max CPS
        max_row = ttk.Frame(self.lmb_smart_frame)
        max_row.pack(fill="x", pady=(2, 0))
        ttk.Label(max_row, text="Max CPS:").pack(side="left")
        self.lmb_max_var = tk.IntVar(value=self.lmb_max_cps)
        self.lmb_max_scale = ttk.Scale(
            max_row, from_=1, to=25, variable=self.lmb_max_var,
            orient="horizontal", command=lambda _: self._on_smart_param_change()
        )
        self.lmb_max_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.lmb_max_label = ttk.Label(max_row, text=str(self.lmb_max_cps), width=3)
        self.lmb_max_label.pack(side="right")

        # Jitter
        jitter_row = ttk.Frame(self.lmb_smart_frame)
        jitter_row.pack(fill="x", pady=(2, 0))
        ttk.Label(jitter_row, text="Jitter ms:").pack(side="left")
        self.lmb_jitter_var = tk.IntVar(value=self.lmb_jitter_ms)
        self.lmb_jitter_scale = ttk.Scale(
            jitter_row, from_=0, to=50, variable=self.lmb_jitter_var,
            orient="horizontal", command=lambda _: self._on_smart_param_change()
        )
        self.lmb_jitter_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.lmb_jitter_label = ttk.Label(jitter_row, text=str(self.lmb_jitter_ms), width=3)
        self.lmb_jitter_label.pack(side="right")

        # Show correct frame
        self._update_lmb_mode_widgets()

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

        # --- Window lock section ---
        win_frame = ttk.LabelFrame(frame, text="Window lock", padding=10)
        win_frame.pack(fill="x", pady=(0, 8))

        self.win_lock_var = tk.BooleanVar(value=self.target_window_enabled)
        ttk.Checkbutton(
            win_frame, text="Only run in selected window",
            variable=self.win_lock_var, command=self._on_win_lock_toggle
        ).pack(anchor="w")

        win_pick_row = ttk.Frame(win_frame)
        win_pick_row.pack(fill="x", pady=(4, 0))
        self.win_combo_var = tk.StringVar(value=self.target_window_title or "")
        self.win_combo = ttk.Combobox(
            win_pick_row, textvariable=self.win_combo_var,
            state="readonly", width=22
        )
        self.win_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.win_combo.bind("<<ComboboxSelected>>", self._on_win_selected)
        ttk.Button(win_pick_row, text="↻", width=3, command=self._refresh_window_list).pack(side="right")

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
        ttk.Radiobutton(shape_row, text="Text", variable=self.shape_var,
                        value="text", command=self._on_shape_change).pack(side="left", padx=(8, 0))

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

        # Text size (for text)
        self.ts_frame = ttk.Frame(self.ind_settings_frame)
        self.ts_frame.pack(fill="x", pady=(4, 0))
        ttk.Label(self.ts_frame, text="Size:").pack(side="left")
        self.ts_var = tk.IntVar(value=self.indicator_text_size)
        self.ts_scale = ttk.Scale(
            self.ts_frame, from_=8, to=72, variable=self.ts_var,
            orient="horizontal", command=lambda _: self._on_indicator_param_change()
        )
        self.ts_scale.pack(side="left", fill="x", expand=True, padx=5)
        self.ts_label = ttk.Label(self.ts_frame, text=str(self.indicator_text_size), width=4)
        self.ts_label.pack(side="right")

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
            self.ts_frame.pack_forget()
        elif self.indicator_shape == "line":
            self.radius_frame.pack_forget()
            self.lw_frame.pack(fill="x", pady=(4, 0))
            self.ll_frame.pack(fill="x", pady=(4, 0))
            self.ts_frame.pack_forget()
        else:  # text
            self.radius_frame.pack_forget()
            self.lw_frame.pack_forget()
            self.ll_frame.pack_forget()
            self.ts_frame.pack(fill="x", pady=(4, 0))

    def _on_indicator_param_change(self):
        self.indicator_radius = max(5, int(float(self.radius_var.get())))
        self.indicator_line_width = max(2, int(float(self.lw_var.get())))
        self.indicator_line_length = max(10, int(float(self.ll_var.get())))
        self.indicator_x = max(0, int(float(self.pos_x_var.get())))
        self.indicator_y = max(0, int(float(self.pos_y_var.get())))
        self.indicator_blink = self.blink_var.get()
        self.indicator_shape = self.shape_var.get()
        self.indicator_text_size = max(8, int(float(self.ts_var.get())))

        # Update labels
        self.radius_label.config(text=str(self.indicator_radius))
        self.lw_label.config(text=str(self.indicator_line_width))
        self.ll_label.config(text=str(self.indicator_line_length))
        self.ts_label.config(text=str(self.indicator_text_size))
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
            text_size=self.indicator_text_size,
        )
        self._save_settings()

    def _start_binding(self, target="toggle"):
        if self._binding_mode:
            return
        self._binding_mode = target
        if target == "toggle":
            self.bind_var.set("...")
            self.bind_hint_var.set("Press any key")
            self.bind_btn.config(state="disabled")

    def _finish_binding(self, vk):
        target = self._binding_mode
        self._binding_mode = None
        name = vk_to_name(vk) if vk else "—"
        if target == "toggle":
            self.toggle_vk = vk
            self.root.after(0, lambda: self.bind_var.set(name))
            self.root.after(0, lambda: self.bind_hint_var.set(""))
            self.root.after(0, lambda: self.bind_btn.config(state="normal"))
        self._save_settings()

    def _update_lmb_mode_widgets(self):
        if self.lmb_smart:
            self.lmb_fixed_frame.pack_forget()
            self.lmb_smart_frame.pack(fill="x", pady=(2, 0))
        else:
            self.lmb_smart_frame.pack_forget()
            self.lmb_fixed_frame.pack(fill="x", pady=(2, 0))

    def _on_smart_toggle(self):
        self.lmb_smart = self.lmb_smart_var.get()
        self._update_lmb_mode_widgets()
        self._save_settings()

    def _on_preset_change(self, event=None):
        name = self.lmb_preset_var.get()
        self.lmb_preset = name
        preset = self.LMB_PRESETS.get(name)
        if preset is not None:
            mn, mx, jt = preset
            self.lmb_min_cps = mn
            self.lmb_max_cps = mx
            self.lmb_jitter_ms = jt
            self.lmb_min_var.set(mn)
            self.lmb_max_var.set(mx)
            self.lmb_jitter_var.set(jt)
            self.lmb_min_label.config(text=str(mn))
            self.lmb_max_label.config(text=str(mx))
            self.lmb_jitter_label.config(text=str(jt))
        self._save_settings()

    def _on_smart_param_change(self):
        self.lmb_min_cps = max(1, int(float(self.lmb_min_var.get())))
        self.lmb_max_cps = max(1, int(float(self.lmb_max_var.get())))
        self.lmb_jitter_ms = max(0, int(float(self.lmb_jitter_var.get())))
        # Ensure min <= max
        if self.lmb_min_cps > self.lmb_max_cps:
            self.lmb_max_cps = self.lmb_min_cps
            self.lmb_max_var.set(self.lmb_max_cps)
        self.lmb_min_label.config(text=str(self.lmb_min_cps))
        self.lmb_max_label.config(text=str(self.lmb_max_cps))
        self.lmb_jitter_label.config(text=str(self.lmb_jitter_ms))
        # Switch to Custom preset when user manually adjusts
        self.lmb_preset = "Custom"
        self.lmb_preset_var.set("Custom")
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
            if nCode >= 0:
                info = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = info.vkCode
                is_injected = bool(info.flags & LLKHF_INJECTED)

                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN) and not is_injected:
                    if self._binding_mode:
                        self._finish_binding(vk)
                        return 1
                    elif vk == self.toggle_vk:
                        self._toggle_global()
                    # Otherwise — no special hotkeys (BedWars removed).

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
                if self.lmb_running and self.lmb_enabled and self.globally_active and self._is_target_active():
                    click_left()
                    if self.lmb_smart:
                        # Pick random CPS within the range
                        cps = random.uniform(self.lmb_min_cps, max(self.lmb_min_cps, self.lmb_max_cps))
                        base_delay = 1.0 / cps
                        # Add jitter: random offset in [-jitter, +jitter]
                        jitter = random.uniform(-self.lmb_jitter_ms, self.lmb_jitter_ms) / 1000.0
                        delay = max(0.01, base_delay + jitter)
                    else:
                        delay = 1.0 / self.lmb_cps
                    time.sleep(delay)
                else:
                    time.sleep(0.005)

        def rmb_loop():
            while True:
                if self.rmb_running and self.rmb_enabled and self.globally_active and self._is_target_active():
                    click_right()
                    time.sleep(1.0 / self.rmb_cps)
                else:
                    time.sleep(0.005)

        threading.Thread(target=lmb_loop, daemon=True).start()
        threading.Thread(target=rmb_loop, daemon=True).start()

    def _get_window_list(self):
        """Enumerate visible top-level windows, return list of (display_text, exe_name)."""
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        windows = []
        seen_exes = set()

        def enum_cb(hwnd, _):
            try:
                if not user32.IsWindowVisible(hwnd):
                    return True
                length = user32.GetWindowTextLengthW(hwnd)
                if length == 0:
                    return True
                title_buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title_buf, length + 1)
                title = title_buf.value

                pid = wintypes.DWORD(0)
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                if not h_proc:
                    return True
                path_buf = ctypes.create_unicode_buffer(512)
                size = wintypes.DWORD(512)
                kernel32.QueryFullProcessImageNameW(h_proc, 0, path_buf, ctypes.byref(size))
                kernel32.CloseHandle(h_proc)
                exe = os.path.basename(path_buf.value)
                if exe and exe not in seen_exes:
                    seen_exes.add(exe)
                    windows.append((f"{title}  ({exe})", exe))
            except Exception:
                pass
            return True

        cb = WNDENUMPROC(enum_cb)
        user32.EnumWindows(cb, 0)
        return windows

    def _refresh_window_list(self):
        wins = self._get_window_list()
        self._window_entries = wins
        self.win_combo["values"] = [w[0] for w in wins]
        if self.target_process:
            for i, (_, exe) in enumerate(wins):
                if exe.lower() == self.target_process.lower():
                    self.win_combo.current(i)
                    self.win_combo_var.set(wins[i][0])
                    break

    def _on_win_selected(self, event=None):
        idx = self.win_combo.current()
        if 0 <= idx < len(self._window_entries):
            disp, exe = self._window_entries[idx]
            self.target_process = exe
            self.target_window_title = disp
            self._save_settings()

    def _on_win_lock_toggle(self):
        self.target_window_enabled = self.win_lock_var.get()
        self._save_settings()

    def _is_target_active(self):
        if not self.target_window_enabled or not self.target_process:
            return True
        now = time.time()
        if now - self._target_cache_time < 0.05:
            return self._target_cache_result
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        result = False
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                pid = wintypes.DWORD(0)
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value:
                    h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                    if h_proc:
                        path_buf = ctypes.create_unicode_buffer(512)
                        size = wintypes.DWORD(512)
                        kernel32.QueryFullProcessImageNameW(h_proc, 0, path_buf, ctypes.byref(size))
                        kernel32.CloseHandle(h_proc)
                        result = os.path.basename(path_buf.value).lower() == self.target_process.lower()
        except Exception:
            result = False
        self._target_cache_time = now
        self._target_cache_result = result
        return result

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AutoClicker()
    app.run()
