import sys, os, time, threading

# Redirect stdout/stderr to log file (safe with pythonw.exe)
# Use user's temp dir for log when frozen, project dir when developing
if getattr(sys, 'frozen', False):
    _log_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), "YTubeAccel")
else:
    _log_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(_log_dir, exist_ok=True)
_log_path = os.path.join(_log_dir, "app_log.txt")
try:
    _log_file = open(_log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = _log_file
    sys.stderr = _log_file
except:
    pass

# Add project root to sys.path (only needed in dev mode)
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.subscription import get_all_nodes
from src.speedtest import speedtest
from src.xray_mgr import XrayManager
from src.proxy_ctl import enable_system_proxy, disable_system_proxy, is_system_proxy_on
from src.diagnose import run_diagnostics
from src.tray import SystemTrayApp


def _error_popup_and_cleanup(exc_type, exc_value, exc_traceback):
    msg = str(exc_value) if exc_value else "Unknown error"
    print(f"[FATAL] {exc_type.__name__}: {msg}")
    disable_system_proxy()
    pass # silent

def _global_excepthook(exc_type, exc_value, exc_traceback):
    _error_popup_and_cleanup(exc_type, exc_value, exc_traceback)

def _thread_excepthook(args):
    _error_popup_and_cleanup(args.exc_type, args.exc_value, args.exc_traceback)

sys.excepthook = _global_excepthook
threading.excepthook = _thread_excepthook


# Startup: check and clear existing system proxy
if is_system_proxy_on():
    print("[Startup] system proxy is ON, clearing...")
    disable_system_proxy()
else:
    print("[Startup] system proxy is OFF, clean start")

SPEEDTEST_INTERVAL = 600
SUB_REFRESH_INTERVAL = 10800


class App:
    def __init__(self):
        self.xray = XrayManager()
        self.selected_nodes = []
        self.all_nodes = []
        self.xray_running = False
        self.tray = None

    def refresh_and_start(self, top_n=5, fetch_sub=False):
        if fetch_sub or not self.all_nodes:
            try:
                self.all_nodes = get_all_nodes()
            except Exception as e:
                print(f"get_all_nodes failed: {e}")
                return
        try:
            best = speedtest(self.all_nodes, top_n, 20)
        except Exception as e:
            print(f"speedtest failed: {e}")
            return
        if not best:
            print("speedtest returned no nodes")
            return
        self.selected_nodes = best
        if self.xray.running:
            ok = self.xray.restart(best, 10808)
        else:
            ok = self.xray.start(best, 10808)
        if ok:
            self.xray_running = True
            enable_system_proxy()
            if self.tray:
                pass # silent mode
        else:
            self.xray_running = False

    def stop_xray(self):
        disable_system_proxy()
        self.xray.stop()
        self.xray_running = False


def schedule_loop(app):
    time.sleep(3)
    last_sub = time.time()
    while True:
        time.sleep(SPEEDTEST_INTERVAL)
        if time.time() - last_sub >= SUB_REFRESH_INTERVAL:
            app.refresh_and_start(5, True)
            last_sub = time.time()
        else:
            app.refresh_and_start(5, False)


def _safe_call(f):
    def wrapper(*a, **kw):
        try:
            return f(*a, **kw)
        except Exception as e:
            _error_popup_and_cleanup(type(e), e, None)
            raise
    return wrapper


@_safe_call
def main():
    run_diagnostics()

    app = App()
    threading.Thread(target=lambda: app.refresh_and_start(5, True), daemon=True).start()
    threading.Thread(target=schedule_loop, args=(app,), daemon=True).start()
    tray = SystemTrayApp(tooltip="Micoraceel")
    app.tray = tray
    tray.set_on_exit(lambda: (app.stop_xray(), os._exit(0)))
    tray.run()


if __name__ == "__main__":
    main()



