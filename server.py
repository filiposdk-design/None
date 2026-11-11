#!/usr/bin/env python3
"""TV Home Theater - a tiny LAN media server with an Android TV friendly UI.

Usage:  python3 server.py [--media ./media] [--port 8080]
Then open http://<this-computer's-LAN-IP>:8080 in your TV's browser.
Standard library only. Supports HTTP Range requests so seeking works.
"""
import argparse, json, mimetypes, os, re, socket, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

VIDEO_EXT = {".mp4": "video/mp4", ".m4v": "video/mp4", ".webm": "video/webm",
             ".mkv": "video/x-matroska", ".mov": "video/quicktime", ".ogv": "video/ogg"}
SUB_EXT = {".vtt"}
POSTER_EXT = (".jpg", ".jpeg", ".png", ".webp")
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
CHUNK = 1024 * 1024


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def safe_join(root, rel):
    path = os.path.realpath(os.path.join(root, rel))
    if path != root and not path.startswith(root + os.sep):
        return None
    return path


def library(root):
    items = []
    for dirpath, _, files in os.walk(root):
        for f in sorted(files):
            stem, ext = os.path.splitext(f)
            if ext.lower() not in VIDEO_EXT:
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            relstem = os.path.splitext(rel)[0]
            poster = next((relstem + e for e in POSTER_EXT
                           if os.path.exists(os.path.join(root, relstem + e))), None)
            subs = [os.path.relpath(os.path.join(dirpath, s), root) for s in sorted(files)
                    if s.startswith(stem) and os.path.splitext(s)[1].lower() in SUB_EXT]
            title = re.sub(r"[._]+", " ", stem).strip()
            items.append({"id": rel, "title": title, "poster": poster, "subs": subs,
                          "size": os.path.getsize(os.path.join(root, rel))})
    items.sort(key=lambda i: i["title"].lower())
    return items


class Handler(BaseHTTPRequestHandler):
    media_root = None

    def log_message(self, fmt, *args):
        pass

    def do_HEAD(self):
        self.head_only = True
        self.do_GET()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(url.path)
        if path == "/api/library":
            body = json.dumps(library(self.media_root)).encode()
            return self.send_bytes(body, "application/json")
        if path.startswith("/media/"):
            target = safe_join(self.media_root, path[len("/media/"):])
            return self.send_file(target)
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        return self.send_file(safe_join(STATIC, rel))

    def send_bytes(self, body, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not getattr(self, "head_only", False):
            self.wfile.write(body)

    def send_file(self, path):
        if not path or not os.path.isfile(path):
            return self.send_bytes(b"Not found", "text/plain", 404)
        ext = os.path.splitext(path)[1].lower()
        ctype = VIDEO_EXT.get(ext) or ("text/vtt" if ext == ".vtt" else None) \
            or mimetypes.guess_type(path)[0] or "application/octet-stream"
        size = os.path.getsize(path)
        start, end, code = 0, size - 1, 200
        m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if m and size:
            if m.group(1):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
            elif m.group(2):
                start = max(0, size - int(m.group(2)))
            end = min(end, size - 1)
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            code = 206
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if getattr(self, "head_only", False):
            return
        try:
            with open(path, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    buf = f.read(min(CHUNK, left))
                    if not buf:
                        break
                    self.wfile.write(buf)
                    left -= len(buf)
        except (BrokenPipeError, ConnectionResetError):
            pass  # TV skipped ahead / closed the stream


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--media", default=os.path.join(HERE, "media"))
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()
    Handler.media_root = os.path.realpath(a.media)
    os.makedirs(Handler.media_root, exist_ok=True)
    print(f"Serving videos from {Handler.media_root}")
    print(f"On this computer:  http://localhost:{a.port}")
    print(f"On your TV:        http://{lan_ip()}:{a.port}")
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
