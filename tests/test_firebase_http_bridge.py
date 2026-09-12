"""Exercise the deployed Firebase HTTP wrapper without production services."""

import os
from pathlib import Path
import subprocess
import sys
import types
from unittest.mock import Mock

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _exercise_bridge(script_name: str, path_info: str) -> None:
    """Run in a fresh interpreter so SDK globals and loop threads cannot leak."""
    import firebase_admin
    from firebase_functions import https_fn
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    probe_app = FastAPI()

    @probe_app.post("/api/probe")
    async def probe(request: Request):
        response = JSONResponse(
            {
                "body": await request.json(),
                "query": request.query_params["label"],
            },
            status_code=201,
            headers={"X-Bridge-Probe": "preserved"},
        )
        response.set_cookie("first", "one", httponly=True)
        response.set_cookie("second", "two", samesite="strict")
        return response

    # Import main's real SDK decorator, but never import the application module
    # or initialize an Admin client that could discover external credentials.
    fake_src = types.ModuleType("src")
    fake_src.__path__ = []
    fake_app = types.ModuleType("src.app")
    fake_app.app = probe_app
    fake_src.app = fake_app
    sys.modules["src"] = fake_src
    sys.modules["src.app"] = fake_app
    firebase_admin.initialize_app = Mock(name="initialize_app")
    sys.path.insert(0, str(PROJECT_ROOT))

    import main
    from a2wsgi import ASGIMiddleware

    assert main._wsgi_app is None
    firebase_admin.initialize_app.assert_not_called()

    adapter = None
    for sequence in (1, 2):
        payload = {"message": "編集可能な橋 🌉", "sequence": sequence}
        request = https_fn.Request.from_values(
            path=path_info,
            method="POST",
            query_string={"label": "確認 + bridge"},
            json=payload,
            environ_overrides={"SCRIPT_NAME": script_name, "PATH_INFO": path_info},
        )
        try:
            # Invoke the exported function, including its actual SDK wrapper.
            response = main.api(request)
            assert isinstance(response, https_fn.Response)
            assert response.status_code == 201
            assert response.get_json() == {
                "body": payload,
                "query": "確認 + bridge",
            }
            assert response.mimetype == "application/json"
            assert response.headers["X-Bridge-Probe"] == "preserved"
            assert response.headers.getlist("Set-Cookie") == [
                "first=one; HttpOnly; Path=/; SameSite=lax",
                "second=two; Path=/; SameSite=strict",
            ]
            # Normalization must not mutate the incoming Firebase request.
            assert request.environ["SCRIPT_NAME"] == script_name
            assert request.environ["PATH_INFO"] == path_info
            response.close()
        finally:
            request.close()

        assert isinstance(main._wsgi_app, ASGIMiddleware)
        firebase_admin.initialize_app.assert_called_once_with()
        if adapter is None:
            adapter = main._wsgi_app
        else:
            assert main._wsgi_app is adapter

    assert sys.modules["src.app"] is fake_app


@pytest.mark.parametrize(
    ("script_name", "path_info"),
    [("", "/api/probe"), ("/api", "/probe"), ("/api", "/api/probe")],
    ids=["full-path", "stripped-prefix", "prefix-already-present"],
)
def test_firebase_http_bridge_roundtrip(script_name, path_info):
    # Keep only interpreter/OS paths; never pass app credentials, DB URLs, or
    # provider configuration from the parent environment to the probe process.
    env = {
        key: os.environ[key]
        for key in (
            "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP",
            "USERPROFILE", "APPDATA", "LOCALAPPDATA",
        )
        if key in os.environ
    }
    env.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), script_name, path_info],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


if __name__ == "__main__":
    _exercise_bridge(sys.argv[1], sys.argv[2])
