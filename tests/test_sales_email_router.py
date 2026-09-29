# -*- coding: utf-8 -*-
"""
Tests for T1048: FastAPI APIRouter分割第1弾: 営業メールマッチングAPIのモジュール分離とapp.pyの負債解消.
Validates router exports, route registration on app, client reachability, and monolith slimming.
"""

from pathlib import Path
import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PY = PROJECT_ROOT / "src" / "app.py"


def test_sales_email_router_module_exists_and_exports_router():
    """Verify that src/routers/sales_email.py exists and exports an APIRouter."""
    try:
        from src.routers.sales_email import router
    except ImportError:
        from routers.sales_email import router

    assert isinstance(router, APIRouter)
    route_paths = [r.path for r in router.routes]
    expected_paths = [
        "/api/sales-email/matches",
        "/api/sales-email/proposal",
        "/api/sales-email/high-score-alerts",
        "/api/sales-email/autopilot-queue",
        "/api/sales-email/analytics",
        "/api/sales-email/sync",
        "/api/sales-email/reviews",
        "/api/sales-email/reviews/summary",
    ]
    for path in expected_paths:
        assert path in route_paths, f"Missing {path} in sales_email router"


def test_app_includes_sales_email_router():
    """Verify that src.app mounts sales_email_router and registers all routes."""
    try:
        from src.app import app
    except ImportError:
        from app import app

    app_route_paths = [getattr(r, "path", None) for r in app.routes]
    expected_paths = [
        "/api/sales-email/matches",
        "/api/sales-email/proposal",
        "/api/sales-email/high-score-alerts",
        "/api/sales-email/autopilot-queue",
        "/api/sales-email/analytics",
        "/api/sales-email/sync",
        "/api/sales-email/reviews",
        "/api/sales-email/reviews/summary",
    ]
    for path in expected_paths:
        assert path in app_route_paths, f"Missing {path} on app after router inclusion"


def test_sales_email_matches_endpoint_reachable_via_testclient():
    """Verify GET /api/sales-email/matches returns 200 via TestClient."""
    try:
        from src.app import app
    except ImportError:
        from app import app

    client = TestClient(app)
    response = client.get("/api/sales-email/matches?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    assert "matches" in data


def test_sales_email_proposal_endpoint_reachable_via_testclient():
    """Verify POST /api/sales-email/proposal returns 200 via TestClient."""
    try:
        from src.app import app
    except ImportError:
        from app import app

    client = TestClient(app)
    payload = {
        "project_title": "Python Backend Project",
        "talent_label": "Engineer A",
        "score": 92,
        "matched_skills": ["Python", "FastAPI"],
        "rate_text": "80万円",
        "contract_type": "準委任",
        "remote_type": "フルリモート",
    }
    response = client.post("/api/sales-email/proposal", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"
    assert "proposal_text" in data
    assert "Python Backend Project" in data["proposal_text"]


def test_app_py_line_count_reduced():
    """Verify that src/app.py line count has been successfully slimmed down."""
    lines = APP_PY.read_text(encoding="utf-8").splitlines()
    # Prior to T1048, src/app.py was 8,174 lines. Now it should be well below 7,800 lines.
    assert len(lines) < 7800, f"src/app.py line count {len(lines)} should be less than 7800"
