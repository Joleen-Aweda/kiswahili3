#!/usr/bin/env python3
"""Serve this static ADT bundle locally and reload the browser after file saves."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WATCHED_SUFFIXES = {
    ".css", ".gif", ".html", ".jpeg", ".jpg", ".js", ".json", ".png",
    ".svg", ".webp", ".xml",
}
IGNORED_DIRECTORIES = {".git", "__pycache__", "node_modules", "tmp"}
RELOAD_PATH = "/__live_reload__"
RELOAD_CLIENT = """
<script data-live-reload>
(() => {
  let version = null;
  const poll = async () => {
    try {
      const response = await fetch('/__live_reload__', {cache: 'no-store'});
      const state = await response.json();
      if (version === null) version = state.version;
      else if (state.version !== version) location.reload();
    } catch (_) {
      // The next poll reconnects automatically when the local server returns.
    }
  };
  poll();
  setInterval(poll, 500);
})();
</script>
""".encode("utf-8")


class ChangeTracker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.version = time.time_ns()
        self._snapshot: dict[Path, tuple[int, int]] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def files(self):
        for directory, names, filenames in os.walk(self.root):
            names[:] = [name for name in names if name not in IGNORED_DIRECTORIES]
            base = Path(directory)
            for filename in filenames:
                path = base / filename
                if path.suffix.lower() in WATCHED_SUFFIXES:
                    yield path

    def take_snapshot(self) -> dict[Path, tuple[int, int]]:
        snapshot = {}
        for path in self.files():
            try:
                stat = path.stat()
                snapshot[path] = (stat.st_mtime_ns, stat.st_size)
            except FileNotFoundError:
                continue
        return snapshot

    def watch(self) -> None:
        self._snapshot = self.take_snapshot()
        while not self._stop.wait(0.5):
            current = self.take_snapshot()
            if current != self._snapshot:
                self._snapshot = current
                with self._lock:
                    self.version = time.time_ns()

    def current_version(self) -> int:
        with self._lock:
            return self.version

    def stop(self) -> None:
        self._stop.set()


class LiveReloadHandler(SimpleHTTPRequestHandler):
    tracker: ChangeTracker

    def log_message(self, message: str, *args: object) -> None:
        if urlsplit(self.path).path != RELOAD_PATH:
            super().log_message(message, *args)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self) -> None:
        if urlsplit(self.path).path == RELOAD_PATH:
            payload = json.dumps({"version": self.tracker.current_version()}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        path = self.local_path()
        if path.is_dir():
            path = path / "index.html"
        if path.is_file() and path.suffix.lower() == ".html":
            content = path.read_bytes()
            marker = b"</body>"
            content = content.replace(marker, RELOAD_CLIENT + marker, 1)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        super().do_GET()

    def local_path(self) -> Path:
        request_path = unquote(urlsplit(self.path).path).lstrip("/")
        candidate = (ROOT / request_path).resolve()
        if candidate != ROOT and ROOT not in candidate.parents:
            return ROOT / "__not_found__"
        return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.chdir(ROOT)
    tracker = ChangeTracker(ROOT)
    LiveReloadHandler.tracker = tracker
    watcher = threading.Thread(target=tracker.watch, name="file-watcher", daemon=True)
    watcher.start()
    server = ThreadingHTTPServer((args.host, args.port), LiveReloadHandler)
    print(f"Live preview: http://{args.host}:{args.port}/", flush=True)
    print("Save a file in VS Code to refresh the browser automatically.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()
        server.server_close()


if __name__ == "__main__":
    main()
