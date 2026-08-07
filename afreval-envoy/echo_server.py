#!/usr/bin/env python3
"""Credential-echo upstream for the Envoy sidecar demo (Phase E1).

Prints the request headers that contain AfrEval/cred signals, proving the
sidecar injected the synthetic credential at the boundary.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        lines = [f"{k}: {v}" for k, v in self.headers.items()
                 if "afreval" in k.lower() or "cred" in k.lower()]
        body = ("injected-headers\n" + "\n".join(lines)).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 9000), Handler).serve_forever()
