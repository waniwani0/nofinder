#!/usr/bin/env python3
"""Serve the camera over HTTPS to a phone on the same link.

getUserMedia only runs in a secure context, so plain http://<ip> will not do —
this makes a self-signed certificate and serves the folder over TLS.

Listens on IPv4 and IPv6. That matters on an IPv6-only carrier: when a Mac is
tethered to an iPhone there, the Mac's only IPv4 address is 192.0.0.2, which is
the 464XLAT translation address — it is local to the Mac and nothing else can
reach it. The usable address is the global IPv6 one.
"""
import argparse
import hashlib
import http.server
import os
import re
import socket
import ssl
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8443
CERT = os.path.join(HERE, "cert.pem")
KEY = os.path.join(HERE, "key.pem")
STAMP = os.path.join(HERE, ".cert-hosts")


def interfaces():
    """Usable addresses as (interface, address, family, note).

    Skips anything another device cannot dial: loopback, link-local, the
    464XLAT address, and the rotating IPv6 privacy addresses.
    """
    try:
        out = subprocess.run(["ifconfig"], capture_output=True, text=True).stdout
    except OSError:
        return []
    found, iface = [], "?"
    for line in out.splitlines():
        if line and not line[0].isspace():
            iface = line.split(":")[0]
        if iface.startswith(("lo", "utun", "awdl", "llw", "gif", "stf", "bridge")):
            continue

        m6 = re.search(r"\binet6 ([0-9a-fA-F:]+)(?:%\w+)?\s+prefixlen\s+\d+(.*)$", line)
        if m6:
            addr, flags = m6.group(1), m6.group(2)
            if addr.lower().startswith(("fe80", "::1", "fd")):
                continue
            if "temporary" in flags or "clat46" in flags or "deprecated" in flags:
                continue
            found.append((iface, addr, socket.AF_INET6, "IPv6"))
            continue

        m4 = re.search(r"\binet (\d+\.\d+\.\d+\.\d+)", line)
        if m4:
            addr = m4.group(1)
            if addr == "127.0.0.1" or addr.startswith("169.254."):
                continue
            if addr.startswith("192.0.0."):
                continue  # 464XLAT: local to this Mac only
            found.append((iface, addr, socket.AF_INET, "IPv4"))
    # Longest-lived first: IPv6 globals, then private IPv4.
    found.sort(key=lambda r: 0 if r[2] == socket.AF_INET6 else 1)
    return found


def usb_tether_dead_end():
    """True when this Mac is USB-tethered to a phone on an IPv6-only carrier.

    iOS hands the single client 192.0.0.2/32 and keeps 192.0.0.1 for itself.
    The phone cannot dial either family back:
      * an IPv4 literal is refused before it is tried, because the phone has no
        IPv4 connectivity of its own;
      * the shared IPv6 /64 is sent out over cellular, not back down the cable.
    Personal Hotspot over Wi-Fi gives a real 172.20.10.0/28 subnet instead.
    """
    try:
        out = subprocess.run(["ifconfig"], capture_output=True, text=True).stdout
    except OSError:
        return False
    return bool(re.search(r"\binet 192\.0\.0\.\d+", out)) and "nat64" in out


def label(addr, family, dead_end=False):
    if family == socket.AF_INET6:
        if dead_end:
            return "IPv6 — 同じ Wi-Fi なら届きます（USB テザリング中は届きません）"
        return "IPv6 — 同じリンク上の端末からはこれで届きます"
    if addr.startswith("172.20.10."):
        return "iPhone のインターネット共有 (Wi-Fi) — これが本命です"
    if addr.startswith(("192.168.", "10.")) or re.match(r"172\.(1[6-9]|2\d|3[01])\.", addr):
        return "ローカル Wi-Fi / LAN — スマホを同じネットワークに"
    return "外向きのアドレス"


def local_hostname():
    try:
        name = subprocess.run(["scutil", "--get", "LocalHostName"],
                              capture_output=True, text=True).stdout.strip()
        return name + ".local" if name else None
    except OSError:
        return None


def ensure_cert(addrs, host):
    names = ["IP:%s" % a for a in addrs] + ["IP:127.0.0.1", "IP:::1", "DNS:localhost"]
    if host:
        names.append("DNS:%s" % host)
    san = ",".join(names)
    key = hashlib.sha256(san.encode()).hexdigest()[:16]
    if os.path.exists(CERT) and os.path.exists(KEY) and os.path.exists(STAMP):
        with open(STAMP) as f:
            if f.read().strip() == key:
                return
    print("  証明書を作成中…")
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "365",
        "-keyout", KEY, "-out", CERT, "-subj", "/CN=nofinder",
        "-addext", "subjectAltName=" + san,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(STAMP, "w") as f:
        f.write(key)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stdout.write("  %s\n" % (fmt % args))
        sys.stdout.flush()


Handler.extensions_map[".webmanifest"] = "application/manifest+json"


class DualStackServer(http.server.ThreadingHTTPServer):
    """One socket answering both IPv4 and IPv6."""
    address_family = socket.AF_INET6
    daemon_threads = True

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except OSError:
            pass
        return super().server_bind()


def url_for(host, port, family=None):
    if family == socket.AF_INET6 or (":" in host and not host.endswith(".local")):
        host = "[%s]" % host
    return "https://%s/" % host if port == 443 else "https://%s:%d/" % (host, port)


def main():
    ap = argparse.ArgumentParser(description="ノーファインダーを HTTPS で配信します。")
    ap.add_argument("--port", type=int, default=PORT,
                    help="待ち受けポート (既定 8443)。443 にすると URL からポートを省けますが sudo が要ります。")
    port = ap.parse_args().port

    found = interfaces()
    host = local_hostname()
    ensure_cert([a for _, a, _, _ in found], host)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)
    try:
        srv = DualStackServer(("::", port), Handler)
    except PermissionError:
        print("\n  ポート %d は管理者権限が要ります。" % port)
        print("  sudo python3 %s --port %d\n" % (os.path.basename(__file__), port))
        raise SystemExit(1)
    except OSError as err:
        if err.errno == 48:
            print("\n  ポート %d はすでに使われています。" % port)
            print("  止めるには:  lsof -ti :%d | xargs kill\n" % port)
            raise SystemExit(1)
        raise
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)

    print("")
    print("  ノーファインダー を配信中  (IPv4 / IPv6 両方で待ち受け)")
    print("")
    dead_end = usb_tether_dead_end()
    if dead_end:
        print("  ⚠  USB テザリング中です。この状態ではスマホから Mac に届きません。")
        print("")
        print("     IPv4:  スマホ自身に IPv4 の接続がないため、iOS が IPv4 宛の")
        print("            アクセスを接続前に蹴ります（「インターネットに接続され")
        print("            ていない」と出ます）。")
        print("     IPv6:  Mac と同じ /64 を共有していますが、スマホはその宛先を")
        print("            セルラー側へ送ってしまい、ケーブルの先に戻りません。")
        print("")
        print("     直し方: iPhone の「インターネット共有」を Wi-Fi でオンにして、")
        print("             Mac をその Wi-Fi に接続してください。外部の Wi-Fi は")
        print("             不要です。Mac が 172.20.10.x になったら、このサーバーを")
        print("             起動し直せば正しい URL が出ます。")
        print("")
        print("  " + "-" * 60)
        print("")
    if not found:
        print("    外から届くアドレスが見つかりません。")
        print("    Wi-Fi につなぐか、iPhone を USB でつないでテザリングしてください。")
    else:
        if host and not dead_end:
            print("  いちばん打ちやすいのはこれです:")
            print("")
            print("     %s" % url_for(host, port))
            print("       Bonjour の名前。届かなければ下の IP を使ってください。")
            print("")
        print("  iPhone の Safari で、URL を「そのまま全部」入力してください。")
        print("  https:// と :%d を省くと http の 80 番を見に行って必ず失敗します。" % port)
        print("")
        for iface, addr, family, kind in found:
            print("     %s" % url_for(addr, port, family))
            print("       %s  (%s / %s)" % (label(addr, family, dead_end), iface, kind))
    print("")
    print("    1. 「この接続はプライベートではありません」→ 詳細を表示 → このWebサイトを閲覧")
    print("    2. カメラの許可を「許可」")
    print("    3. 共有ボタン →「ホーム画面に追加」でアプリになります")
    print("")
    print("  Safari を使ってください。iOS でホーム画面にアプリとして追加できるのは Safari だけです。")
    print("")
    print("  止めるときは Ctrl+C")
    print("")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  停止しました\n")


if __name__ == "__main__":
    main()
