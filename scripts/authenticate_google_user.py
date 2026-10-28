#!/usr/bin/env python3
"""
scripts/authenticate_google_user.py
OAuth authorization with direct clickable link and local callback listener on port 8085.
"""

import os
import sys
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
PORT = 8085
REDIRECT_URI = f"http://localhost:{PORT}/"

auth_code = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <body style="background-color: #07090e; color: #facc15; font-family: sans-serif; text-align: center; padding: 4rem;">
                <h1>✨ Authentication Successful!</h1>
                <p style="color: #e2e8f0; font-size: 1.2rem;">Owner Direct Delete permissions have been activated.</p>
                <p style="color: #94a3b8;">You can now close this tab and return to the assistant.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received.")

    def log_message(self, format, *args):
        pass


def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )

    print("=" * 70, flush=True)
    print("DIRECT_AUTH_URL_START", flush=True)
    print(auth_url, flush=True)
    print("DIRECT_AUTH_URL_END", flush=True)
    print("=" * 70, flush=True)
    print(f"[*] Local server waiting for authorization on {REDIRECT_URI}...", flush=True)

    server = HTTPServer(("localhost", PORT), OAuthCallbackHandler)
    while auth_code is None:
        server.handle_request()

    print("[+] Authorization code received from browser! Exchanging for tokens...", flush=True)
    flow.fetch_token(code=auth_code)
    creds = flow.credentials

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"[✔] Token successfully saved to '{TOKEN_FILE}'!", flush=True)
    print("[✔] Direct DELETE capability is now 100% active!", flush=True)


if __name__ == "__main__":
    main()
