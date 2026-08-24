"""Tests for high score alerts and autopilot queue endpoints."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app import app

client = TestClient(app)


def test_high_score_alerts_endpoint():
    response = client.get("/api/sales-email/high-score-alerts?min_score=80&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "alerts" in data
    assert data["threshold_score"] == 80


def test_autopilot_queue_endpoint():
    response = client.get("/api/sales-email/autopilot-queue?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "proposals" in data
    assert len(data["proposals"]) > 0
    assert data["proposals"][0]["is_ready_to_send"] is True
