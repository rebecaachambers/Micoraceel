import ctypes
import ctypes.wintypes
from src.iconspoof import get_random_icon

WM_USER = 0x0400
WM_RBUTTONUP = 0x0205
WM_DESTROY = 0x0002
WM_TIMER = 0x0113
NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIF_MESSAGE = 1
NIF_ICON = 2
NIF_TIP = 4

shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

_DefWindowProcW = user32.DefWindowProcW
_DefWindowProcW.argtypes = [ctypes.c_size_t, ctypes.c_uint, ctypes.c_size_t, ctypes.c_size_t]
_DefWindowProcW.restype = ctypes.c_size_t


class NID(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("hWnd", ctypes.wintypes.HWND),
        ("uID", ctypes.wintypes.UINT),
        ("uFlags", ctypes.wintypes.UINT),
        ("uCallbackMessage", ctypes.wintypes.UINT),
        ("hIcon", ctypes.wintypes.HICON),
        ("szTip", ctypes.wintypes.WCHAR * 128),
    ]


class WNDCLASSEXW(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("cbSize", ctypes.wintypes.UINT),
        ("style", ctypes.wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.wintypes.HINSTANCE),
        ("hIcon", ctypes.wintypes.HICON),
        ("hCursor", ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HBRUSH),
        ("lpszMenuName", ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
        ("hIconSm", ctypes.wintypes.HICON),
    ]


WNDPROC_TYPE = ctypes.WINFUNCTYPE(
    ctypes.c_size_t,
    ctypes.c_size_t,
    ctypes.c_uint,
    ctypes.c_size_t,
    ctypes.c_size_t,
)

NID_SIZE = ctypes.sizeof(NID())

TRAY_REFRESH_TIMER_ID = 1001
TRAY_REFRESH_MS = 15000


class SystemTrayApp:
    def __init__(self, tooltip):
        self.tooltip = tooltip
        self.nid = None
        self.hwnd = None
        self._running = False
        self._on_exit = None
        self.callback_msg = WM_USER + 100
        self._wndproc_cb = None
        self._hicon = None

    def _log(self, msg):
        try:
            print(f"[tray] {msg}")
        except:
            pass

    def _window_proc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            elif msg == WM_TIMER and wparam == TRAY_REFRESH_TIMER_ID:
                self._refresh_icon()
                return 0
            elif msg == self.callback_msg and (lparam & 0xFFFFFFFF) == WM_RBUTTONUP:
                self.stop()
                return 0
        except Exception:
            pass
        return _DefWindowProcW(hwnd, msg, wparam, lparam)

    def _ensure_icon(self):
        hicon = user32.LoadIconW(0, 32515)
        if hicon:
            return hicon
        hicon = user32.LoadIconW(0, 32512)
        if hicon:
            return hicon
        hicon = get_random_icon()
        return hicon

    def _create_window(self):
        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "YTTrayWin"
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(wc)
        self._wndproc_cb = WNDPROC_TYPE(self._window_proc)
        wc.lpfnWndProc = ctypes.cast(self._wndproc_cb, ctypes.c_void_p)
        wc.hInstance = hinstance
        wc.lpszClassName = class_name
        atom = user32.RegisterClassExW(ctypes.byref(wc))
        if not atom:
            return None
        hwnd = user32.CreateWindowExW(0, class_name, "", 0, 0, 0, 0, 0, 0, 0, hinstance, 0)
        return hwnd

    def _add_icon(self):
        self.hwnd = self._create_window()
        if not self.hwnd:
            return False
        self._hicon = self._ensure_icon()
        nid = NID()
        nid.cbSize = NID_SIZE
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = self.callback_msg
        nid.hIcon = self._hicon
        nid.szTip = " "
        if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
            return False
        self.nid = nid
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
        user32.SetTimer(self.hwnd, TRAY_REFRESH_TIMER_ID, TRAY_REFRESH_MS, None)
        return True

    def _refresh_icon(self):
        if not self.nid or not self._running:
            return
        try:
            new_hicon = self._ensure_icon()
            if new_hicon:
                if self._hicon:
                    user32.DestroyIcon(ctypes.c_size_t(self._hicon))
                self._hicon = new_hicon
                self.nid.hIcon = new_hicon
                shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self.nid))
        except Exception:
            pass

    def show_balloon(self, title, msg, timeout=5):
        pass

    def set_on_exit(self, cb):
        self._on_exit = cb

    def run(self):
        if self._running:
            return
        if not self._add_icon():
            return
        self._running = True
        msg = ctypes.wintypes.MSG()
        try:
            while self._running:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret <= 0:
                    break
                user32.TranslateMessage(msg)
                user32.DispatchMessageW(msg)
        except Exception:
            pass
        finally:
            self._cleanup()

    def _cleanup(self):
        if self.hwnd:
            try:
                user32.KillTimer(self.hwnd, TRAY_REFRESH_TIMER_ID)
            except:
                pass
        if self.nid:
            try:
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.nid))
            except:
                pass
            self.nid = None
        if self._hicon:
            try:
                user32.DestroyIcon(ctypes.c_size_t(self._hicon))
            except:
                pass
            self._hicon = None
        if self.hwnd:
            try:
                user32.DestroyWindow(self.hwnd)
            except:
                pass
            self.hwnd = None

    def stop(self):
        self._running = False
        if self._on_exit:
            self._on_exit()
