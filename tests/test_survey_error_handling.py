"""T883 test spec (written test-first): survey form must surface the real reason.

Found during T882 live UAT of TS-01: submitting the survey with a 3-char free
text returned HTTP 400 `growth_feedback must be at least 10 characters`, but the
UI showed the misleading "アンケート保存APIへ接続できませんでした" (connection
failed) — the same 400-detail-swallowing defect T872 fixed for the timesheet
uploader, still present in the survey handler.

These tests pin: (1) the server rejects short free text with the specific 400
detail, and (2) both index.html and src/index.html surface the server reason
(friendly Japanese) instead of a generic connection error, and guide the user
client-side with a minlength on the free-text field.
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


@pytest.fixture
def client(tmp_path):
    saved = (app.DATA_DIR, app.AUDIT_DIR)
    app.DATA_DIR = str(tmp_path / "data")
    app.AUDIT_DIR = str(tmp_path / "data" / "audit")
    os.makedirs(app.AUDIT_DIR, exist_ok=True)
    with TestClient(app.app) as c:
        yield c
    app.DATA_DIR, app.AUDIT_DIR = saved


# --------------------------------------------------------------------------- #
# Server-side: the exact validation the UAT hit
# --------------------------------------------------------------------------- #
def test_short_growth_feedback_returns_specific_400(client):
    response = client.post(
        "/api/employee-assessment/responses",
        json={
            "employee_identifier": "emp-2026-001",
            "department": "開発本部",
            "motivation_level": 5,
            "culture_level": 4,
            "growth_feedback": "テスト",  # 3 chars < 10 -> must be rejected clearly
            "consented": True,
        },
    )
    assert response.status_code == 400
    assert "growth_feedback must be at least 10 characters" in response.json()["detail"]


# --------------------------------------------------------------------------- #
# Client-side: both HTML files must surface the reason, not a generic error
# --------------------------------------------------------------------------- #
def _submit_survey_block(text: str) -> str:
    start = text.index("async function submitSurvey")
    rest = text[start + 12:]
    # Bound the slice to the next top-level function declaration.
    m = re.search(r"\n {8}(?:async )?function ", rest)
    end = start + 12 + m.start() if m else start + 6000
    return text[start:end]


@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_survey_handler_surfaces_server_detail(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    block = _submit_survey_block(text)
    # Reads the server's `detail` on a non-OK response (T872 pattern).
    assert "serverDetail" in block or ".detail" in block, path
    # Friendly, specific message for the 10-char rule the UAT hit.
    assert "フリー記述は10文字以上" in block, path
    # The generic "connection failed" text must no longer be the only outcome:
    # a server-reason branch must exist alongside it.
    assert "サーバー応答" in block, path


@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_survey_feedback_has_client_minlength(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'<textarea id="survey-feedback"[^>]*>', text)
    assert m, path
    assert 'minlength="10"' in m.group(0), path


def test_both_index_files_survey_handler_consistent():
    blocks = [_submit_survey_block(p.read_text(encoding="utf-8", errors="replace")) for p in INDEX_FILES]
    # Both mirrors must carry the same fix markers.
    for marker in ("フリー記述は10文字以上", "サーバー応答"):
        assert all(marker in b for b in blocks), marker
