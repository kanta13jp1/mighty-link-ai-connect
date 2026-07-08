"""T866 (R114 postmortem) regression tests.

1. Cold start: the schema is guaranteed before the first request — a POST that
   arrives immediately after startup must succeed with no explicit init_db call
   (the daemon-thread design lost this race on Cloud Run).
2. Storage failures are classified (relation_missing / connection / constraint)
   and the HTTP 500 detail carries the category + correlation ID without leaking
   SQL text or personal data.
"""

import os
import shutil
import sqlite3
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import app
from fastapi.testclient import TestClient


@pytest.fixture
def cold_start_dirs(tmp_path):
    saved = (app.DATA_DIR, app.AUDIT_DIR, app.EXTERNAL_API_USAGE_LOG_FILE)
    app.DATA_DIR = str(tmp_path / "data")
    app.AUDIT_DIR = str(tmp_path / "data" / "audit")
    app.EXTERNAL_API_USAGE_LOG_FILE = str(tmp_path / "data" / "external_api_usage.jsonl")
    os.makedirs(app.AUDIT_DIR, exist_ok=True)
    yield
    app.DATA_DIR, app.AUDIT_DIR, app.EXTERNAL_API_USAGE_LOG_FILE = saved


def test_cold_start_first_post_succeeds_without_explicit_init(cold_start_dirs):
    # No app.init_db() here on purpose: entering the TestClient context runs the
    # lifespan, which must now complete init_db BEFORE the first request.
    with TestClient(app.app) as client:
        response = client.post(
            "/api/feedback",
            json={"rating": "helpful", "nps_score": 8, "comment": "cold start check"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["feedback_id"] > 0


def test_lifespan_has_no_daemon_thread_starter():
    # The racy design must not come back.
    assert not hasattr(app, "start_db_init_thread")


@pytest.mark.parametrize(
    "exc,expected",
    [
        (sqlite3.OperationalError("no such table: feedback_events"), "relation_missing"),
        (Exception('relation "attendance_punches" does not exist'), "relation_missing"),
        (Exception("could not connect to server: Connection refused"), "connection"),
        (Exception("canceling statement due to statement timeout"), "connection"),
        (sqlite3.IntegrityError("NOT NULL constraint failed: feedback_events.rating"), "constraint"),
        (Exception("new row violates check constraint"), "constraint"),
        (Exception("something completely different"), "unknown"),
    ],
)
def test_classify_storage_error(exc, expected):
    assert app.classify_storage_error(exc) == expected


def test_storage_500_detail_carries_category_and_correlation_id(cold_start_dirs, monkeypatch):
    def failing_insert(**kwargs):
        app.record_storage_failure(
            "insert_feedback_event",
            sqlite3.OperationalError("no such table: feedback_events"),
        )
        return 0

    monkeypatch.setattr(app, "db_insert_feedback_event", failing_insert)
    with TestClient(app.app) as client:
        response = client.post("/api/feedback", json={"rating": "helpful"})
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "category=relation_missing" in detail
    assert "correlation_id=st-" in detail
    # No SQL text / table internals in the client-facing message.
    assert "no such table" not in detail


def test_correlation_id_is_unique_per_failure():
    a = app.record_storage_failure("op", Exception("x"))
    b = app.record_storage_failure("op", Exception("x"))
    assert a != b and a.startswith("st-") and b.startswith("st-")
