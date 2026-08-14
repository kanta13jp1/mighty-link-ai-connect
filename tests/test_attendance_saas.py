"""Tests for External Attendance SaaS OAuth2 Module (T947)."""

import pytest
from fastapi.testclient import TestClient
from src.app import app, LEGAL_CONSENT_VERSION
from src import attendance_saas


@pytest.fixture
def client():
    return TestClient(app)


def test_list_providers_info():
    providers = attendance_saas.list_providers_info()
    assert isinstance(providers, list)
    assert len(providers) == 3
    provider_ids = [p["provider_id"] for p in providers]
    assert "jobcan" in provider_ids
    assert "king_of_time" in provider_ids
    assert "freee" in provider_ids


def test_get_provider():
    jobcan = attendance_saas.get_provider("jobcan")
    assert jobcan is not None
    assert jobcan.display_name == "ジョブカン勤怠管理"

    kot = attendance_saas.get_provider("king_of_time")
    assert kot is not None
    assert kot.display_name == "KING OF TIME"

    freee = attendance_saas.get_provider("freee")
    assert freee is not None
    assert freee.display_name == "freee人事労務 (勤怠)"

    invalid = attendance_saas.get_provider("nonexistent")
    assert invalid is None


def test_build_authorization_url():
    jobcan = attendance_saas.get_provider("jobcan")
    info = jobcan.build_authorization_url(redirect_uri="https://example.com/callback", state="teststate123")
    assert "authorization_url" in info
    assert "jobcan" in info["authorization_url"].lower() or info["provider_id"] == "jobcan"


@pytest.mark.anyio
async def test_exchange_code_and_fetch_data():
    jobcan = attendance_saas.get_provider("jobcan")
    token = await jobcan.exchange_code_for_token(code="testcode", redirect_uri="https://example.com/callback")
    assert "access_token" in token

    punches = await jobcan.fetch_punches(token, "emp-test-001")
    assert len(punches) > 0
    assert punches[0].event_type == "in"

    summary = await jobcan.fetch_timesheet_summary(token, "emp-test-001")
    assert summary.work_minutes > 0
    assert summary.parser == "jobcan_oauth2_v1"


def test_api_list_providers(client):
    res = client.get("/api/attendance/providers")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["providers"]) == 3


def test_api_connect_provider(client):
    res = client.get("/api/attendance/providers/connect?provider_id=jobcan")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "authorization_url" in data

    bad_res = client.get("/api/attendance/providers/connect?provider_id=invalid")
    assert bad_res.status_code == 400


def test_api_callback_provider(client):
    res = client.get("/api/attendance/providers/callback?provider_id=freee&code=samplecode123")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["provider_id"] == "freee"


def test_api_sync_provider(client):
    req_body = {
        "provider_id": "jobcan",
        "employee_identifier": "emp-2026-saas-001",
        "consented": True
    }
    res = client.post("/api/attendance/providers/sync", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["provider_id"] == "jobcan"
    assert data["punches_synced"] >= 1
    assert "timesheet_import" in data
    assert data["timesheet_import"]["id"] > 0


def test_api_sync_provider_validation_failures(client):
    # Unconsented
    res1 = client.post("/api/attendance/providers/sync", json={"provider_id": "jobcan", "employee_identifier": "emp-001", "consented": False})
    assert res1.status_code == 400
    assert "consented must be true" in res1.json()["detail"]

    # Identifier too short
    res2 = client.post("/api/attendance/providers/sync", json={"provider_id": "jobcan", "employee_identifier": "ab", "consented": True})
    assert res2.status_code == 400
    assert "at least 3 characters" in res2.json()["detail"]

    # Unsupported provider
    res3 = client.post("/api/attendance/providers/sync", json={"provider_id": "invalid_saas", "employee_identifier": "emp-001", "consented": True})
    assert res3.status_code == 400
    assert "Unsupported attendance provider" in res3.json()["detail"]
