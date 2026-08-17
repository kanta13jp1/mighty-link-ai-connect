import base64
import hashlib
import json
import os
import secrets
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

CLIENT_ID = os.environ.get("CANVA_CLIENT_ID", "OC-AaAJt87X1DaV")
CLIENT_SECRET = os.environ.get("CANVA_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("CANVA_REDIRECT_URI", "http://127.0.0.1:8765/callback")
PORT = int(os.getenv("CANVA_PORT", "8765"))

def generate_pkce_pair():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    return verifier, challenge

verifier, challenge = generate_pkce_pair()

# 有効化された全スコープを登録
scopes = [
    "app:read",
    "app:write",
    "asset:read",
    "asset:write",
    "brandtemplate:content:read",
    "brandtemplate:content:write",
    "brandtemplate:meta:read",
    "comment:read",
    "comment:write",
    "design:content:read",
    "design:content:write",
    "design:meta:read",
    "design:meta:write",
    "design:permission:read",
    "design:permission:write",
    "folder:read",
    "folder:write",
    "folder:permission:read",
    "folder:permission:write",
    "profile:read"
]
scope_str = " ".join(scopes)

auth_url = (
    f"https://www.canva.com/api/oauth/authorize?"
    f"code_challenge_method=s256&"
    f"response_type=code&"
    f"client_id={CLIENT_ID}&"
    f"code_challenge={challenge}&"
    f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
    f"scope={urllib.parse.quote(scope_str)}"
)

print("\n=======================================================")
print("CANVA AUTHENTICATION URL:")
print(auth_url)
print("=======================================================\n")

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/callback"):
            query = urllib.parse.parse_qs(parsed.query)
            code = query.get("code", [None])[0]
            error = query.get("error", [None])[0]
            error_desc = query.get("error_description", [""])[0]

            if error:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h2>認証エラー: {error}</h2><p>{error_desc}</p>".encode("utf-8"))
                print(f"\n[ERROR] OAuth Error: {error} - {error_desc}")
                return

            if code:
                auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")).decode("utf-8")
                token_resp = requests.post(
                    "https://api.canva.com/rest/v1/oauth/token",
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "grant_type": "authorization_code",
                        "code_verifier": verifier,
                        "code": code,
                        "redirect_uri": REDIRECT_URI
                    }
                )

                if token_resp.status_code == 200:
                    token_data = token_resp.json()
                    access_token = token_data.get("access_token")

                    config_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
                    if os.path.exists(config_path):
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)
                    else:
                        config = {"mcpServers": {}}

                    config.setdefault("mcpServers", {})["canva"] = {
                        "serverUrl": "https://mcp.canva.com/mcp",
                        "headers": {
                            "Authorization": f"Bearer {access_token}"
                        }
                    }

                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"<h1>Canva OAuth Authentication Successful!</h1><p>Antigravity config has been updated. You can close this window.</p>")
                    print("\n[SUCCESS] Token acquired and mcp_config.json updated successfully!")
                else:
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f"<h2>Token Exchange Failed ({token_resp.status_code})</h2><p>{token_resp.text}</p>".encode("utf-8"))
                    print(f"\n[ERROR] Token exchange failed: {token_resp.status_code} {token_resp.text}")

        import threading
        threading.Thread(target=httpd.shutdown).start()

    def log_message(self, format, *args):
        pass

httpd = HTTPServer(("127.0.0.1", PORT), OAuthCallbackHandler)
print(f"Waiting for callback on {REDIRECT_URI}...")
httpd.serve_forever()
