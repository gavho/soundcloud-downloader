"""Local SoundCloud batch downloader. Run: python downloader.py, then use the page it opens."""
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp

HERE = Path(__file__).parent
OUT = HERE / "downloads"
PORT = 8765
ALLOWED_HOSTS = {"soundcloud.com", "www.soundcloud.com", "m.soundcloud.com", "on.soundcloud.com"}

tracks = {}  # title -> {"state", "percent"}
errors = []
lock = threading.Lock()


def valid_urls(text):
    """Keep only https SoundCloud links, one per line."""
    out = []
    for line in text.splitlines():
        u = urlparse(line.strip())
        if u.scheme == "https" and u.hostname in ALLOWED_HOSTS and u.path.strip("/"):
            out.append(u.geturl())
    return out


def set_track(title, state, percent=None):
    with lock:
        t = tracks.setdefault(title, {"state": "queued", "percent": 0})
        t["state"] = state
        if percent is not None:
            t["percent"] = percent


def on_progress(d):
    title = d.get("info_dict", {}).get("title", "?")
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        set_track(title, "downloading", round(100 * d.get("downloaded_bytes", 0) / total) if total else None)
    elif d["status"] == "finished":
        set_track(title, "converting", 100)


def on_postprocess(d):
    if d["status"] == "finished" and d.get("postprocessor") == "MoveFiles":
        set_track(d.get("info_dict", {}).get("title", "?"), "done", 100)


class ErrorLog:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass

    def error(self, msg):
        with lock:
            errors.append(msg)


def run(urls):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(OUT / "%(uploader)s - %(title)s.%(ext)s"),
        "ignoreerrors": True,  # one bad track must not stop the batch
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
        "progress_hooks": [on_progress],
        "postprocessor_hooks": [on_postprocess],
        "logger": ErrorLog(),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download(urls)


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/status":
            with lock:
                self.send(200, {"tracks": tracks, "errors": errors[-20:], "folder": str(OUT)})
        else:
            self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/download":
            return self.send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except json.JSONDecodeError:
            return self.send(400, {"error": "bad request"})
        urls = valid_urls(str(body.get("text", "")))
        if not urls:
            return self.send(400, {"error": "No SoundCloud links found. Use full https://soundcloud.com/... links."})
        threading.Thread(target=run, args=(urls,), daemon=True).start()
        self.send(200, {"started": len(urls)})

    def log_message(self, *args):
        pass


def self_check():
    assert valid_urls("https://soundcloud.com/artist/track") == ["https://soundcloud.com/artist/track"]
    assert valid_urls("https://on.soundcloud.com/abc123") == ["https://on.soundcloud.com/abc123"]
    assert valid_urls("https://soundcloud.com/a/sets/b\n\n  https://soundcloud.com/c/d  ") == [
        "https://soundcloud.com/a/sets/b", "https://soundcloud.com/c/d"]
    assert valid_urls("https://evil.com/soundcloud.com/x") == []
    assert valid_urls("https://soundcloud.com.evil.com/x") == []
    assert valid_urls("http://soundcloud.com/a/b") == []
    assert valid_urls("hello world\nhttps://soundcloud.com/") == []


if __name__ == "__main__":
    self_check()
    OUT.mkdir(exist_ok=True)
    # Bound to localhost only: nobody else on the network can trigger downloads.
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Open http://127.0.0.1:{PORT}  (Ctrl+C to stop). Files go to {OUT}")
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    server.serve_forever()
