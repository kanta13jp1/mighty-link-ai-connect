import base64
import hashlib
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

CLIENT_ID = "IXf3LPaM9O-XpOZc"
REDIRECT_URI = "http://127.0.0.1:8765/callback"
VERIFIER = "antigravity_canva_mcp_verifier_123456789012345678901234567890"

digest = hashlib.sha256(VERIFIER.encode('utf-8')).digest()
CHALLENGE = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

scopes = [
    "profile:read",
    "design:meta:read",
    "design:content:write",
    "design:content:read",
    "folder:read",
    "folder:write",
    "asset:read",
    "asset:write"
]
scope_str = " ".join(scopes)

auth_url = (
    f"https://mcp.canva.com/authorize?"
    f"code_challenge_method=s256&"
    f"response_type=code&"
    f"client_id={CLIENT_ID}&"
    f"code_challenge={CHALLENGE}&"
    f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
    f"scope={urllib.parse.quote(scope_str)}"
)

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = query.get("code", [None])[0]

        if not code:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>No code received</h1>")
            return

        token_resp = requests.post(
            "https://mcp.canva.com/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "code_verifier": VERIFIER,
                "code": code,
                "redirect_uri": REDIRECT_URI
            }
        )

        if token_resp.status_code == 200:
            token_data = token_resp.json()
            access_token = token_data.get("access_token")

            config_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            config.setdefault("mcpServers", {})["canva"] = {
                "serverUrl": "https://mcp.canva.com/mcp",
                "headers": {
                    "Authorization": f"Bearer {access_token}"
                }
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Canva MCP Connected Successfully!</h1><p>Antigravity 2.0 has been configured. You can close this window.</p>")
            print("\n[SUCCESS] Canva MCP Token successfully saved to mcp_config.json!")
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h1>Token Exchange Failed</h1><p>{token_resp.text}</p>".encode("utf-8"))
            print(f"\n[ERROR] Token exchange failed: {token_resp.status_code} {token_resp.text}")

        import threading
        threading.Thread(target=httpd.shutdown).start()

print("\n=======================================================")
print("CANVA MCP DIRECT AUTH URL:")
print(auth_url)
print("=======================================================\n")

httpd = HTTPServer(("0.0.0.0", 8765), CallbackHandler)
print("Waiting for callback on port 8765...")
httpd.serve_forever()
