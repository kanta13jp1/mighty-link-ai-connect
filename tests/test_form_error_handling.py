"""T884 test spec (written test-first): every data-mutation form must surface the
real server reason, not a generic connection error.

Context: T872 (timesheet uploader) and T883 (survey form) fixed the same defect —
the handler read `!response.ok` but discarded the server's 400/401 `detail`, so a
user who hit a validation error saw a misleading "接続できませんでした / 送信失敗"
(connection failed) message and could not tell what to fix. A T882-driven audit
found the identical defect still present in five more handlers:

    submitFeedback          -> POST /api/feedback
    submitSupportRequest    -> POST /api/support/request
    punchCard               -> POST /api/attendance/punch
    approveAttendanceData   -> POST /api/attendance/timesheet/approve  (401 Basic)
    downloadUserDataExport  -> GET  /api/user-data/export              (401 Bearer)

These tests pin, for both index.html and src/index.html mirrors, that each handler
(1) reads the server `detail` on a non-OK response and (2) surfaces it (サーバー応答)
while (3) still keeping a true-connection-failure fallback (接続) so the static
GitHub Pages demo — where these APIs 404 / are unreachable — degrades gracefully.

The server-side tests pin the exact 400/401 details the UI now surfaces, so the
regression guard and the reason strings cannot silently drift apart.
"""

import os
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

INDEX_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]

# handler function name -> the connection-failure keyword that must remain so the
# static demo (no backend) still shows a plain "could not reach server" message.
HANDLERS = {
    "submitFeedback": "接続",
    "submitSupportRequest": "接続",
    "punchCard": "接続",
    "approveAttendanceData": "接続",
    "downloadUserDataExport": "接続",
}


@pytest.fixture
def client(tmp_path):
    saved = (app.DATA_DIR, app.AUDIT_DIR)
    app.DATA_DIR = str(tmp_path / "data")
    app.AUDIT_DIR = str(tmp_path / "data" / "audit")
    os.makedirs(app.AUDIT_DIR, exist_ok=True)
    with TestClient(app.app) as c:
        yield c
    app.DATA_DIR, app.AUDIT_DIR = saved


def _handler_block(text: str, fn_name: str) -> str:
    """Slice a top-level handler function body up to the next function declaration."""
    marker = f"function {fn_name}("
    start = text.index(marker)
    rest = text[start + len(marker):]
    m = re.search(r"\n {8}(?:async )?function ", rest)
    end = start + len(marker) + (m.start() if m else 6000)
    return text[start:end]


# --------------------------------------------------------------------------- #
# Client-side: both HTML mirrors must surface the server reason in every handler
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("fn_name,fallback_kw", list(HANDLERS.items()))
@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_handler_surfaces_server_detail(path, fn_name, fallback_kw):
    block = _handler_block(path.read_text(encoding="utf-8", errors="replace"), fn_name)
    # (1) reads the server's `detail` on a non-OK response (T872/T883 pattern)
    assert "serverDetail" in block or ".detail" in block, (path.name, fn_name)
    # (2) surfaces that reason to the user instead of only a generic message
    assert "サーバー応答" in block, (path.name, fn_name)
    # (3) keeps a genuine connection-failure fallback for the static demo
    assert fallback_kw in block, (path.name, fn_name)


@pytest.mark.parametrize("fn_name", list(HANDLERS))
def test_both_mirrors_consistent(fn_name):
    blocks = [
        _handler_block(p.read_text(encoding="utf-8", errors="replace"), fn_name)
        for p in INDEX_FILES
    ]
    for marker in ("サーバー応答",):
        assert all(marker in b for b in blocks), (fn_name, marker)


# --------------------------------------------------------------------------- #
# Server-side: the exact 400/401 details each fixed handler now surfaces
# --------------------------------------------------------------------------- #
def test_feedback_rejects_out_of_range_nps_with_specific_400(client):
    r = client.post("/api/feedback", json={"rating": "helpful", "nps_score": 99})
    assert r.status_code == 400
    assert "nps_score must be between 0 and 10" in r.json()["detail"]


def test_feedback_rejects_bad_rating_with_specific_400(client):
    r = client.post("/api/feedback", json={"rating": "bogus"})
    assert r.status_code == 400
    assert "rating must be helpful or not_helpful" in r.json()["detail"]


def test_support_rejects_short_message_with_specific_400(client):
    r = client.post(
        "/api/support/request",
        json={
            "category": "general",
            "contact_email": "tester@example.com",
            "subject": "件名テスト",
            "message": "short",  # < 10 chars -> specific 400
        },
    )
    assert r.status_code == 400
    assert "message must be at least 10 characters" in r.json()["detail"]


def test_punch_rejects_missing_consent_with_specific_400(client):
    r = client.post(
        "/api/attendance/punch",
        json={"employee_identifier": "emp-2026-001", "event_type": "in", "consented": False},
    )
    assert r.status_code == 400
    assert "consent is required before storing attendance data" in r.json()["detail"]


def test_punch_rejects_short_identifier_with_specific_400(client):
    r = client.post(
        "/api/attendance/punch",
        json={"employee_identifier": "ab", "event_type": "in", "consented": True},
    )
    assert r.status_code == 400
    assert "employee_identifier must be at least 3 characters" in r.json()["detail"]


def test_approve_requires_basic_auth_401(client):
    r = client.post(
        "/api/attendance/timesheet/approve",
        json={"import_id": 1, "decision": "approved"},
    )
    assert r.status_code == 401  # admin Basic Auth wall -> UI must say so, not "接続失敗"


def test_approve_rejects_bad_import_id_with_specific_400(client):
    r = client.post(
        "/api/attendance/timesheet/approve",
        json={"import_id": -1, "decision": "approved"},
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert r.status_code == 400
    assert "import_id must be positive" in r.json()["detail"]


def test_user_data_export_rejects_unauthenticated_request(client):
    saved = app.USER_DATA_EXPORT_ALLOW_MOCK
    app.USER_DATA_EXPORT_ALLOW_MOCK = False
    try:
        r = client.get("/api/user-data/export")
    finally:
        app.USER_DATA_EXPORT_ALLOW_MOCK = saved
    # Firebase available -> 401 (token required); unavailable -> 503. Either way a
    # non-OK rejection with a `detail` string the client must now surface.
    assert r.status_code in (401, 403, 503)
    assert isinstance(r.json().get("detail"), str) and r.json()["detail"]


# --------------------------------------------------------------------------- #
# Integration: the 10-hypothesis audit harness must be all-green
# --------------------------------------------------------------------------- #
def test_audit_harness_all_hypotheses_pass():
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import audit_form_error_handling as audit  # noqa: E402

    report = audit.evaluate()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
    assert len(report["hypotheses"]) == 10
