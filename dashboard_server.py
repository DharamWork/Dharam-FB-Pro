#!/usr/bin/env python3
"""
dashboard_server.py
Lightweight local HTTP server for previewing the Raj FB Pro PWA Phone App.
Serves the docs/ directory at http://localhost:8080
"""

import os
import sys
import http.server
import socketserver
import webbrowser

PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Clean terminal output
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("=" * 60)
    print("✨ RAJ FB PRO - LOCAL PWA DASHBOARD PREVIEW SERVER")
    print("=" * 60)
    print(f"[*] Serving docs/ directory from: {DIRECTORY}")
    print(f"[+] URL: http://localhost:{PORT}")
    print("[*] Press Ctrl+C to stop the server.")
    print("=" * 60)

    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[-] Shutting down server gracefully.")
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"[!] Port {PORT} is already in use. Try accessing http://localhost:{PORT}")
        else:
            raise


if __name__ == "__main__":
    run_server()
