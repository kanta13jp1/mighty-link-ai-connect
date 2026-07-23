#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for authentication and authorization enforcement in Mighty Skill-Bridge."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import app, get_current_user

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
