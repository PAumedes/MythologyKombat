#!/usr/bin/env python3
"""Tiny local HTTP server for tools/test_updater.ps1 (T3.21). Stdlib only, binds 127.0.0.1.

  python -I tests/updater_test_server.py --root DIR --port N

GET/HEAD serve files under DIR. If "<file>.route.json" exists it wins:
  {"status": 302, "headers": {"Location": "..."}, "body": "text"}
Every request is appended to DIR/../requests.log as "METHOD /path STATUS".
Nothing here speaks to the network beyond 127.0.0.1.
"""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    root = "."

    def log_message(self, *a):
        pass

    def _log(self, status):
        try:
            with open(os.path.join(self.root, "..", "requests.log"), "a") as f:
                f.write("%s %s %s\n" % (self.command, self.path, status))
        except OSError:
            pass

    def _serve(self, head):
        rel = unquote(urlsplit(self.path).path).lstrip("/")
        full = os.path.normpath(os.path.join(self.root, rel))
        if not full.startswith(os.path.normpath(self.root)):
            return self._send(403, {}, b"", head)
        route = full + ".route.json"
        if os.path.isfile(route):
            with open(route, "r") as f:
                r = json.load(f)
            return self._send(r.get("status", 200), r.get("headers", {}), r.get("body", "").encode(), head)
        if os.path.isfile(full):
            with open(full, "rb") as f:
                data = f.read()
            return self._send(200, {"Content-Type": "application/octet-stream"}, data, head)
        self._send(404, {}, b"not found", head)

    def _send(self, status, headers, body, head):
        self._log(status)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def do_GET(self):
        self._serve(False)

    def do_HEAD(self):
        self._serve(True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--port", type=int, required=True)
    a = ap.parse_args()
    H.root = os.path.abspath(a.root)
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
