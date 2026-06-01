import socket
import time
import concurrent.futures

TEST_TIMEOUT = 5

def tcp_ping(host, port, timeout=TEST_TIMEOUT):
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return (time.time() - start) * 1000
    except Exception:
        return None

def test_node(node, timeout=TEST_TIMEOUT):
    host = node["server"]
    port = node["port"]
    latency = tcp_ping(host, port, timeout)
    return {**node, "latency": latency, "alive": latency is not None}

def speedtest(nodes, top_n=5, max_workers=20):
    print(f"测速: {len(nodes)} 个节点")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = list(ex.map(lambda n: test_node(n), nodes))
    alive = [r for r in results if r["alive"]]
    alive.sort(key=lambda x: x["latency"])
    print(f"存活: {len(alive)}/{len(nodes)}")
    for n in alive[:top_n]:
        print(f"  {n['latency']:.0f}ms  {n['server']}:{n['port']}  {n['remark']}")
    return alive[:top_n]
