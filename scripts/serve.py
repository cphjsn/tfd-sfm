#!/usr/bin/env python3
"""Local preview server: python -m http.server plus HTTP Range requests (Safari only plays MP4s
with them) and no caching (an edited page or script is never served stale).

    python scripts/serve.py [port]      # serves the repository root on 127.0.0.1, default port 8765
"""
import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        """A 206 response for `Range: bytes=a-b` on a file, else what http.server does."""
        self._remaining = None
        path = self.translate_path(self.path)
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", (self.headers.get("Range") or "").strip())
        if not m or not os.path.isfile(path) or m.group(1) == m.group(2) == "":
            return super().send_head()
        size = os.path.getsize(path)
        if m.group(1) == "":  # the last n bytes
            start, end = max(0, size - int(m.group(2))), size - 1
        else:
            start = int(m.group(1))
            end = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        if self._remaining is None:
            return super().copyfile(source, outputfile)
        while self._remaining > 0:
            chunk = source.read(min(1 << 16, self._remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            self._remaining -= len(chunk)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=ROOT))
    print(f"serving {ROOT} at http://127.0.0.1:{port}")
    server.serve_forever()
