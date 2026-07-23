import os
import sys
import time
import socket
import subprocess
import httpx
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

# Keep authentication deterministic even when CI exposes managed-runtime variables.
os.environ.setdefault("BASIC_AUTH_USERNAME", "test-admin")
os.environ.setdefault("BASIC_AUTH_PASSWORD", "test-password")

def get_free_port() -> int:
    """Find and return an available free port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

@pytest.fixture(scope="module")
def fastapi_server():
    """Module-scoped fixture starting uvicorn on a dynamic free port (Port 0) to avoid TIME_WAIT and port conflicts."""
    port = get_free_port()
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=os.path.join(PROJECT_ROOT, "src")
    )
    
    base_url = f"http://127.0.0.1:{port}"
    
    # Wait for the server to become ready
    for _ in range(60):
        try:
            r = httpx.get(f"{base_url}/api/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.2)
    else:
        server_process.terminate()
        server_process.wait()
        raise RuntimeError(f"Server failed to start on port {port}.")
        
    yield base_url
    
    server_process.terminate()
    server_process.wait()
