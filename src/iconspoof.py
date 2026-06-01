import ctypes, ctypes.wintypes, random

WM_GETICON = 0x007F
ICON_SMALL2 = 2
GCLP_HICONSM = -34
SMTO_ABORTIFHUNG = 0x0002

user32 = ctypes.windll.user32

_EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_size_t, ctypes.c_size_t)
_collected = []

def _enum_cb(hwnd, lparam):
    try:
        icon = ctypes.c_size_t(0)
        user32.SendMessageTimeoutW(
            ctypes.c_size_t(hwnd), WM_GETICON, ICON_SMALL2, 0,
            SMTO_ABORTIFHUNG, 1000, ctypes.byref(icon)
        )
        if icon.value:
            _collected.append(icon.value)
            return True
        icon2 = user32.GetClassLongPtrW(ctypes.c_size_t(hwnd), GCLP_HICONSM)
        if icon2:
            _collected.append(icon2)
    except Exception:
        pass
    return True

_enum_cb_ptr = _EnumWindowsProc(_enum_cb)


def collect_app_icons():
    _collected.clear()
    user32.EnumWindows(_enum_cb_ptr, 0)
    return list(set(_collected))


def get_random_icon():
    icons = collect_app_icons()
    if not icons:
        return 0
    chosen = random.choice(icons)
    return user32.CopyIcon(ctypes.c_size_t(chosen))
