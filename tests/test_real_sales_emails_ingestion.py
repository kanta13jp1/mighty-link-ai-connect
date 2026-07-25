"""Integration test for real sales email ingestion from eigyo@mighty-link.com (T910 / T817)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys_path = str(PROJECT_ROOT / "src")
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from app import app


def test_real_sales_emails_counts():
    review_json_path = PROJECT_ROOT / "exports" / "sales_email_extraction_review.json"
    assert review_json_path.exists(), "exports/sales_email_extraction_review.json must exist"

    data = json.loads(review_json_path.read_text(encoding="utf-8"))
    input_count = data.get("input_count", 0)
    project_count = data.get("project_requirement_count", 0)
    talent_count = data.get("talent_profile_count", 0)

    # Verify scaled real email counts
    assert input_count >= 600, f"Expected at least 600 real emails, got {input_count}"
    assert project_count >= 100, f"Expected at least 100 project requirements, got {project_count}"
    assert talent_count >= 100, f"Expected at least 100 talent profiles, got {talent_count}"


def test_sales_email_analytics_api_endpoint():
    client = TestClient(app)
    response = client.get("/api/sales-email/analytics")
    assert response.status_code == 200

    payload = response.json()
    assert payload.get("status") == "success"
    daily_counts = payload.get("daily_counts", {})
    total_daily = sum(daily_counts.values())
    assert total_daily >= 600, f"Expected at least 600 total emails in analytics, got {total_daily}"
    assert len(payload.get("domain_counts", {})) > 0
    assert len(payload.get("skill_counts", {})) > 0
