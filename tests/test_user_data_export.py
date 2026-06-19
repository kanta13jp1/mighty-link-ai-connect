import os
import shutil
import sys

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import app


@pytest.fixture(autouse=True)
def setup_test_db():
    original_values = {
        "DATA_DIR": app.DATA_DIR,
        "AUDIT_DIR": app.AUDIT_DIR,
        "EXTERNAL_API_USAGE_LOG_FILE": app.EXTERNAL_API_USAGE_LOG_FILE,
        "USER_DATA_EXPORT_ALLOW_MOCK": app.USER_DATA_EXPORT_ALLOW_MOCK,
        "SUPABASE_SDK_ACTIVE": app.SUPABASE_SDK_ACTIVE,
    }
    app.DATA_DIR = os.path.join(PROJECT_ROOT, "data_test_user_export")
    app.AUDIT_DIR = os.path.join(app.DATA_DIR, "audit")
    app.EXTERNAL_API_USAGE_LOG_FILE = os.path.join(app.DATA_DIR, "external_api_usage.jsonl")
    app.USER_DATA_EXPORT_ALLOW_MOCK = False
    app.SUPABASE_SDK_ACTIVE = False

    if os.path.exists(app.DATA_DIR):
        shutil.rmtree(app.DATA_DIR)
    os.makedirs(app.DATA_DIR, exist_ok=True)
    os.makedirs(app.AUDIT_DIR, exist_ok=True)
    app.init_db()

    yield

    if os.path.exists(app.DATA_DIR):
        shutil.rmtree(app.DATA_DIR)
    for name, value in original_values.items():
        setattr(app, name, value)


@pytest.fixture
def client():
    return TestClient(app.app)


def seed_export_records():
    engineer_id = app.db_insert_engineer(
        "Export User",
        "Skills: Python, FastAPI, Supabase",
        {"backend": ["Python", "FastAPI"]},
        {"strengths": ["API design"]},
    )
    job_id = app.db_insert_job(
        "Backend API Engineer",
        "Mighty-Link",
        "Requirements: Python, API design",
        {"mandatory": ["Python"]},
        {"summary": "Remote-friendly team"},
    )
    match_id = app.db_insert_match_result(
        engineer_id,
        job_id,
        0.91,
        92,
        84,
        88,
        86,
        "Strong backend API fit.",
        [{"question": "How do you design API boundaries?"}],
    )
    app.db_insert_feedback_event(
        match_id,
        "helpful",
        9,
        "Useful export test feedback.",
        "diagnosis_report",
        "/",
        "export-session",
        {"test": "included"},
    )
    app.db_insert_feedback_event(
        None,
        "not_helpful",
        4,
        "Other session feedback.",
        "diagnosis_report",
        "/",
        "other-session",
        {"test": "excluded"},
    )
    app.db_insert_support_request(
        "privacy",
        "high",
        "k-umezawa@ml-mightylink.com",
        "データエクスポート依頼",
        "自分の登録データを確認したいです。",
        "support_form",
        "/support",
        "export-session",
        {"test": "included"},
    )
    app.db_insert_support_request(
        "general",
        "normal",
        "other@example.test",
        "別ユーザー問い合わせ",
        "別ユーザーの問い合わせ本文です。",
        "support_form",
        "/support",
        "other-session",
        {"test": "excluded"},
    )
    return match_id


def test_user_data_export_requires_real_identity_by_default(client):
    response = client.get("/api/user-data/export?session_id=export-session")
    assert response.status_code in {401, 503}


def test_user_data_export_is_scoped_to_authenticated_email_and_session(client):
    app.USER_DATA_EXPORT_ALLOW_MOCK = True
    match_id = seed_export_records()

    response = client.get("/api/user-data/export?session_id=export-session")

    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith(
        'filename="mighty-link-user-data-export.json"'
    )
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["schema_version"] == "2026-06-20.T781"
    assert payload["user"]["email"] == "k-umezawa@ml-mightylink.com"
    assert payload["record_counts"]["support_requests"] == 1
    assert payload["record_counts"]["feedback_events"] == 1
    assert payload["record_counts"]["match_results"] == 1
    assert payload["records"]["match_results"][0]["id"] == match_id
    assert payload["records"]["support_requests"][0]["subject"] == "データエクスポート依頼"
    assert payload["records"]["feedback_events"][0]["session_id"] == "export-session"
    assert payload["records"]["engineers"][0]["parsed_skills"]["backend"] == ["Python", "FastAPI"]
    assert payload["records"]["jobs"][0]["parsed_requirements"]["mandatory"] == ["Python"]
    assert "owner_uid" in payload["ownership_gaps"][1]

