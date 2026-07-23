#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for authentication and authorization enforcement in Mighty Skill-Bridge."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import app as app_module
from app import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME, app, get_current_user

client = TestClient(app)

def test_public_endpoints_accessible():
    """Verify that public endpoints like health check return 200 OK without auth."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") in ["healthy", "ok", "degraded"]

def test_auth_me_endpoint_mock_mode(monkeypatch):
    """Verify /api/auth/me response under mock mode."""
    monkeypatch.setenv("MOCK_AUTH", "1")
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert "user" in data
    assert data["user"]["uid"] == "user_9999"

def test_auth_me_endpoint_requires_auth_when_mock_disabled(monkeypatch):
    """Verify /api/auth/me returns 401 when MOCK_AUTH is disabled and no token is provided."""
    monkeypatch.setenv("MOCK_AUTH", "0")
    res = client.get("/api/auth/me")
    assert res.status_code in [401, 403]

def test_root_index_requires_basic_auth():
    """The application HTML must never be returned to an anonymous request."""
    anonymous = client.get("/")
    assert anonymous.status_code == 401
    assert anonymous.headers["www-authenticate"] == "Basic"
    assert "Mighty Skill-Bridge" not in anonymous.text

    authenticated = client.get(
        "/",
        auth=(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD),
    )
    assert authenticated.status_code == 200
    assert "Mighty Skill-Bridge" in authenticated.text
    assert "no-store" in authenticated.headers["cache-control"]


def test_root_index_fails_closed_when_managed_credentials_are_missing(monkeypatch):
    """Missing production credentials must not reactivate known fallback values."""
    monkeypatch.setattr(app_module, "BASIC_AUTH_USERNAME", None)
    monkeypatch.setattr(app_module, "BASIC_AUTH_PASSWORD", None)

    response = client.get("/", auth=("unexpected", "unexpected"))

    assert response.status_code == 503
    assert "Mighty Skill-Bridge" not in response.text


def test_managed_runtime_never_loads_local_basic_auth_defaults():
    """A managed runtime without auth env vars must remain inaccessible."""
    env = os.environ.copy()
    env["K_SERVICE"] = "auth-fail-closed-test"
    env["AI_FORCE_MOCK"] = "1"
    env["USE_SUPABASE"] = "0"
    env.pop("BASIC_AUTH_USERNAME", None)
    env.pop("BASIC_AUTH_PASSWORD", None)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import app; "
                "assert app.IS_MANAGED_RUNTIME is True; "
                "assert app.BASIC_AUTH_USERNAME is None; "
                "assert app.BASIC_AUTH_PASSWORD is None"
            ),
        ],
        cwd=SRC_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_index_html_contains_early_sync_lockout():
    """Verify index.html contains synchronous early auth lockout script in head."""
    index_path = PROJECT_ROOT / "index.html"
    content = index_path.read_text(encoding="utf-8")
    assert "early-auth-lockout-style" in content
    assert "Synchronous Security Lockout Script" in content

