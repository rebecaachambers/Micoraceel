import os
import sys
import ctypes
import urllib.request
import zipfile
import io
import subprocess


def self_diagnose():
    """全面自检，返回问题列表"""
    issues = []

    # 1. 检查 Python 版本
    if sys.version_info < (3, 8):
        issues.append("Python version too old")

    # 2. 检查 xray-core
    xray_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "xray-core")
    xray_exe = os.path.join(xray_dir, "xray.exe")
    if not os.path.exists(xray_exe):
        issues.append("xray-core binary not found")
    else:
        # 验证可执行
        try:
            r = subprocess.run([xray_exe, "--version"], capture_output=True, timeout=5, cwd=xray_dir)
            if r.returncode != 0:
                issues.append("xray-core binary not executable")
        except Exception:
            issues.append("xray-core binary error")

    # 3. 检查系统代理状态
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                             0, winreg.KEY_READ)
        enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
        server, _ = winreg.QueryValueEx(key, "ProxyServer")
        winreg.CloseKey(key)
        if enabled == 1:
            issues.append(f"system proxy is ON ({server}) - conflicting with program")
    except Exception:
        pass

    # 4. 检查端口冲突
    for port in [10808, 10809]:
        try:
            sock = __import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_STREAM)
            sock.settimeout(1)
            r = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if r == 0:
                issues.append(f"port {port} already in use")
        except Exception:
            pass

    return issues


def auto_fix(issues):
    """自动修复已知问题"""
    fixed = []
    failed = []

    for issue in issues:
        if issue.startswith("system proxy is ON"):
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                     0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                fixed.append("cleared system proxy")
            except Exception as e:
                failed.append(f"failed to clear proxy: {e}")

        elif issue == "xray-core binary not found":
            try:
                from src.xray_mgr import download_xray
                if download_xray():
                    fixed.append("downloaded xray-core")
                else:
                    failed.append("download xray-core failed")
            except Exception as e:
                failed.append(f"xray download error: {e}")

        elif issue.startswith("port"):
            try:
                import subprocess
                port = int(issue.split()[1])
                r = subprocess.run(
                    f'netstat -ano | findstr :{port}',
                    shell=True, capture_output=True, text=True, timeout=5
                )
                for line in r.stdout.split("\n"):
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, timeout=3)
                        fixed.append(f"killed process on port {port} (PID {pid})")
            except Exception as e:
                failed.append(f"failed to free port {port}")

        else:
            failed.append(f"cannot auto-fix: {issue}")

    return fixed, failed


def run_diagnostics():
    """运行全面诊断 + 自动修复"""
    print("=" * 50)
    print("  YouTube Accelerator - Self Diagnostics")
    print("=" * 50)

    issues = self_diagnose()
    if not issues:
        print("\n[OK] No issues found\n")
        return True

    print(f"\n[INFO] Found {len(issues)} issue(s):")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

    print("\n[FIX] Attempting auto-fix...")
    fixed, failed = auto_fix(issues)

    for f in fixed:
        print(f"  [OK] {f}")
    for f in failed:
        print(f"  [FAIL] {f}")

    if fixed and not failed:
        print("\n[OK] Auto-fix completed successfully\n")
        return True
    elif failed:
        print(f"\n[WARN] {len(failed)} issue(s) could not be auto-fixed\n")
        return False
    else:
        print("\n[OK] No fix needed\n")
        return True
