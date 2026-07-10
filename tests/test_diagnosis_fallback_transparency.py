"""T885 test spec (written test-first): the diagnosis flow must not present
hardcoded sample scores as a genuine AI result when the live backend errors.

Context: runAnalysis() posts to /api/match and only uses the response when
`response.ok`. On any non-OK status it silently fell through to the pre-seeded
mock scores (95/88/92/82) and rendered them exactly like a real AI diagnosis —
so a 429 (rate limit) or 500 on the production backend showed a fabricated
"perfect" fit with no indication. For a hiring/matching tool that is a real
trust defect (same family as the T872/T883/T884 error-swallowing fixes).

The fix is additive and demo-safe: only when the backend actually responds with
an error (`!response.ok` AND `status !== 404`) does the UI surface a warning that
the shown scores are sample values. The static GitHub Pages mirror (where every
/api route 404s and a sample diagnosis IS the intended demo) and true offline
(network error) keep the silent mock fallback, so the CEO-shared demo is
byte-for-byte unchanged.

These tests pin, for both index.html and src/index.html:
  * runAnalysis reads the server detail on a non-OK response,
  * it distinguishes 404 (silent demo mock) from a real backend error,
  * it labels the shown scores as サンプル on a real error,
  * it keeps the original mock fallback path, and
  * both mirrors stay byte-identical.
Server-side tests pin that /api/match really can return the errors (400 without
consent, 429 under the expensive-path rate limit) the UI now handles honestly.
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


def _run_analysis_block(text: str) -> str:
    marker = "function runAnalysis("
    start = text.index(marker)
    rest = text[start + len(marker):]
    m = re.search(r"\n {8}(?:async )?function ", rest)
    end = start + len(marker) + (m.start() if m else 8000)
    return text[start:end]


# --------------------------------------------------------------------------- #
# Client-side: both mirrors surface a sample-value warning on a real backend error
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_run_analysis_reads_server_detail(path):
    block = _run_analysis_block(path.read_text(encoding="utf-8", errors="replace"))
    assert "serverDetail" in block or ".detail" in block, path.name


@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_run_analysis_distinguishes_404_demo(path):
    block = _run_analysis_block(path.read_text(encoding="utf-8", errors="replace"))
    # Static demo mirror 404s every /api route -> must stay a silent demo mock.
    assert "!== 404" in block, path.name


@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_run_analysis_labels_scores_as_sample_on_error(path):
    block = _run_analysis_block(path.read_text(encoding="utf-8", errors="replace"))
    assert "サンプル" in block, path.name


@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_run_analysis_keeps_silent_mock_fallback(path):
    block = _run_analysis_block(path.read_text(encoding="utf-8", errors="replace"))
    # The offline / static-demo path must still fall back to the mock quietly.
    assert "Falling back to default mock" in block, path.name


def test_both_mirrors_run_analysis_identical():
    blocks = [_run_analysis_block(p.read_text(encoding="utf-8", errors="replace")) for p in INDEX_FILES]
    assert blocks[0] == blocks[1], "index.html and src/index.html runAnalysis drift"


# --------------------------------------------------------------------------- #
# Server-side: /api/match really returns the errors the UI now handles honestly
# --------------------------------------------------------------------------- #
def test_match_rejects_without_consent_400(client):
    r = client.post(
        "/api/match",
        json={"engineer_content": "スキル: Python", "job_content": "案件: バックエンド"},
    )
    assert r.status_code == 400
    assert "consent is required" in r.json()["detail"]


def test_match_is_a_rate_limited_expensive_path():
    # 429 (the primary TS-17 scenario) is reachable because /api/match is an
    # expensive, rate-limited path.
    assert "/api/match" in app.RATE_LIMIT_EXPENSIVE_API_PATHS


# --------------------------------------------------------------------------- #
# Integration: the 10-hypothesis audit harness must be all-green
# --------------------------------------------------------------------------- #
def test_audit_harness_all_hypotheses_pass():
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import audit_diagnosis_fallback_transparency as audit  # noqa: E402

    report = audit.evaluate()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
    assert len(report["hypotheses"]) == 10
