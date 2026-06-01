import base64
import urllib.request
import urllib.parse
import json
SUB_URL = "https://vps.azena.dpdns.org/sub?token=d70c3e33c59725b4e8c4a664a339a832"

def fetch_subscription(url=None):
    url = url or SUB_URL
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    resp = urllib.request.urlopen(req, timeout=30)
    raw = resp.read().decode()
    try:
        decoded = base64.b64decode(raw).decode()
    except Exception:
        decoded = raw
    return decoded

def parse_vless_url(url):
    if not url.startswith("vless://"):
        return None
    rest = url[8:]
    id_part, rest = rest.split("@", 1)
    addr_port, query_part = rest.split("?", 1)
    server = addr_port.split(":")[0]
    port_str = addr_port.split(":")[1]
    query = {}
    for part in query_part.split("&"):
        if "#" in part:
            part = part.split("#")[0]
        if "=" in part:
            k, v = part.split("=", 1)
            query[k] = urllib.parse.unquote(v)
    remark = ""
    if "#" in query_part:
        remark = urllib.parse.unquote(query_part.split("#", 1)[1])
    return {
        "uuid": id_part, "server": server, "port": int(port_str),
        "remark": remark, "type": query.get("type", "tcp"),
        "security": query.get("security", "none"),
        "network": query.get("type", "tcp"),
        "host": query.get("host", ""), "path": query.get("path", ""),
        "sni": query.get("sni", ""), "fp": query.get("fp", ""),
        "encryption": query.get("encryption", "none"),
        "flow": query.get("flow", ""),
    }

def get_all_nodes():
    text = fetch_subscription()
    nodes = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or not line.startswith("vless://"):
            continue
        node = parse_vless_url(line)
        if node:
            nodes.append(node)
    return nodes
