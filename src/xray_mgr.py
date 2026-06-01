import os, sys, json, urllib.request, zipfile, io, subprocess, time

def _xray_dir():
    """获取 xray-core 目录，支持 PyInstaller 打包"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    return os.path.join(os.path.abspath(base), "xray-core")

XRAY_DIR = _xray_dir()
XRAY_EXE = os.path.join(XRAY_DIR, "xray.exe")
CONFIG_PATH = os.path.join(XRAY_DIR, "config.json")
def _add_firewall_rule():
    """预先添加 Windows 防火墙规则，避免联网弹窗"""
    rule_name = "Micoraceel - xray-core"
    try:
        # 使用 bytes 模式避免 GBK 编码问题
        r = subprocess.run(
            f'netsh advfirewall firewall show rule name="{rule_name}"',
            shell=True, capture_output=True, timeout=5
        )
        if b"No rules match" in r.stdout:
            subprocess.run(
                f'netsh advfirewall firewall add rule name="{rule_name}" dir=out program="{XRAY_EXE}" action=allow',
                shell=True, capture_output=True, timeout=5
            )
    except:
        pass
XRAY_VERSION = "1.8.24"


def download_xray():
    """下载 xray-core (直接 GitHub, 超时60秒)"""
    if os.path.exists(XRAY_EXE):
        return True
    os.makedirs(XRAY_DIR, exist_ok=True)
    url = f"https://github.com/XTLS/Xray-core/releases/download/v{XRAY_VERSION}/Xray-windows-64.zip"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        resp = urllib.request.urlopen(req, timeout=60)
        data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(XRAY_DIR)
        return True
    except:
        return False


def generate_config(nodes, local_port=10808):
    outbounds = []
    for node in nodes:
        ob = {
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": node["server"], "port": node["port"],
                    "users": [{"id": node["uuid"], "encryption": node.get("encryption","none"), "flow": node.get("flow","")}]
                }]
            },
            "streamSettings": {
                "network": node.get("network", "tcp"),
                "security": node.get("security", "none"),
            },
            "tag": f"node_{node['server']}_{node['port']}"
        }
        ss = ob["streamSettings"]
        if ss["network"] == "ws":
            ws = {}
            if node.get("path"): ws["path"] = node["path"]
            if node.get("host"): ws["headers"] = {"Host": node["host"]}
            ss["wsSettings"] = ws
        if ss["security"] == "tls":
            tls = {}
            if node.get("sni"): tls["serverName"] = node["sni"]
            if node.get("fp"): tls["fingerprint"] = node["fp"]
            ss["tlsSettings"] = tls
        outbounds.append(ob)

    # 路由规则：国内直连优先，代理兜底
    rules = [
        {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
        {"type": "field", "domain": ["geosite:cn"], "outboundTag": "direct"},
        {"type": "field", "ip": ["geoip:cn"], "outboundTag": "direct"},
    ]

    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {"port": local_port, "protocol": "socks", "settings": {"udp": True}, "tag": "socks-in"},
            {"port": local_port+1, "protocol": "http", "tag": "http-in"}
        ],
        "outbounds": outbounds + [{"protocol": "freedom", "tag": "direct"}],
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "rules": rules
        },
        "policy": {"levels": {"0": {"connIdle": 300}}}
    }
    if len(outbounds) > 1:
        tags = [o["tag"] for o in outbounds]
        config["routing"]["balancers"] = [{"tag": "balancer", "selector": tags, "strategy": {"type": "random"}}]
        # balancer 规则放在最后，国内直连规则优先匹配
        rules.append({"type": "field", "port": "0-65535", "balancerTag": "balancer"})

    os.makedirs(XRAY_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return CONFIG_PATH


class XrayManager:
    def __init__(self):
        self.process = None
        self.running = False
    def start(self, nodes, local_port=10808):
        if self.running:
            return True
        if not download_xray():
            return False
        generate_config(nodes, local_port)
        _add_firewall_rule()
        try:
            self.process = subprocess.Popen(
                [XRAY_EXE, "run", "-c", CONFIG_PATH],
                cwd=XRAY_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(2)
            if self.process.poll() is None:
                self.running = True
                return True
            else:
                return False
        except:
            return False
    def stop(self):
        if self.process and self.running:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.running = False
    def restart(self, nodes, local_port=10808):
        self.stop()
        time.sleep(1)
        return self.start(nodes, local_port)



