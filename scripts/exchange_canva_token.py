import base64
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

CLIENT_ID = os.environ.get("CANVA_CLIENT_ID", "OC-AaAJt87X1DaV")
CLIENT_SECRET = os.environ.get("CANVA_CLIENT_SECRET", "")
REDIRECT_URI = "http://127.0.0.1:8765/callback"
VERIFIER = "antigravity_canva_secure_verifier_123456789012345678901234567890"

def exchange_and_save(code):
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode("utf-8")).decode("utf-8")
    token_resp = requests.post(
        "https://api.canva.com/rest/v1/oauth/token",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "authorization_code",
            "code_verifier": VERIFIER,
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

        print("\n=======================================================")
        print("[SUCCESS] Canva Access Token obtained and saved to mcp_config.json!")
        print("=======================================================\n")
        return True, access_token
    else:
        print(f"\n[ERROR] Token exchange failed: {token_resp.status_code} {token_resp.text}")
        return False, token_resp.text

if len(sys.argv) > 1:
    code_arg = sys.argv[1]
    if "code=" in code_arg:
        code_arg = code_arg.split("code=")[1].split("&")[0]
    code_arg = urllib.parse.unquote(code_arg)
    exchange_and_save(code_arg)
    sys.exit(0)

class RobustCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = query.get("code", [None])[0]
        error = query.get("error", [None])[0]

        if error:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h2>Error: {error}</h2>".encode("utf-8"))
            return

        if code:
            ok, res = exchange_and_save(code)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            if ok:
                self.wfile.write(b"<h1>Canva OAuth Successful!</h1><p>Antigravity is now connected to Canva MCP. You can close this tab.</p>")
            else:
                self.wfile.write(f"<h1>Failed</h1><p>{res}</p>".encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Waiting for code...</h1>")

        import threading
        threading.Thread(target=httpd.shutdown).start()

    def log_message(self, format, *args):
        pass

httpd = HTTPServer(("127.0.0.1", 8765), RobustCallbackHandler)
print("Waiting for callback on http://127.0.0.1:8765/callback...")
httpd.serve_forever()
