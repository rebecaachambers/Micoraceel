"""
Windows 系统代理控制 (通过注册表 + InternetSetOption 刷新)
"""
import winreg
import ctypes
import ctypes.wintypes

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
PROXY_HOST = "127.0.0.1:10809"

# InternetSetOption constants
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37

wininet = ctypes.windll.wininet


def _set_reg(name, value, type=winreg.REG_SZ):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, name, 0, type, value)
        winreg.CloseKey(key)
        return True
    except:
        return False


def _delete_reg(name):
    """删除注册表值"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
    except:
        pass


def _get_reg(name):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return value
    except:
        return None


def _refresh():
    """通知 Windows 代理设置已更改"""
    try:
        wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
    except:
        pass


def enable_system_proxy():
    """开启系统代理 -> 127.0.0.1:10809"""
    _set_reg("ProxyServer", PROXY_HOST)
    _set_reg("ProxyOverride", "<local>;192.168.*;10.*;172.16.*;127.0.0.1")
    _set_reg("ProxyEnable", 1, winreg.REG_DWORD)
    _refresh()
    return True


def disable_system_proxy():
    """完全清除系统代理设置（开关、地址、跳过列表）"""
    _set_reg("ProxyEnable", 0, winreg.REG_DWORD)
    _delete_reg("ProxyServer")
    _delete_reg("ProxyOverride")
    _refresh()
    return True


def is_system_proxy_on():
    """检查系统代理是否开启（只检查 ProxyEnable）"""
    val = _get_reg("ProxyEnable")
    return val == 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "on":
            enable_system_proxy()
        elif sys.argv[1] == "off":
            disable_system_proxy()
        elif sys.argv[1] == "status":
            print("on" if is_system_proxy_on() else "off")
