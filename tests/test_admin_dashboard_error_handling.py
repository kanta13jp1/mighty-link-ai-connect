"""T886 test spec (written test-first): admin dashboard loaders must tell an
operator *why* the load failed — above all, a 401 (wrong/missing Basic Auth).

Context: loadOperationsDashboard() and downloadOperationsDashboardCsv() both hit
Basic-Auth-gated admin APIs but, on any non-OK response, showed a generic
"Real data unavailable; static demo remains" / "CSV export unavailable". The #1
real cause — wrong or missing admin credentials (HTTP 401) — was indistinguishable
from a server outage, so an operator could not tell they just needed to re-enter
credentials. Same error-swallowing family as T884 (forms) and T885 (diagnosis).

The fix is additive and demo-safe: only when the backend actually errors
(!response.ok AND status !== 404) is the specific reason surfaced (401 -> admin
auth required). The static GitHub Pages mirror (every /api route 404s) keeps its
"static demo" fallback, so the CEO-shared demo is unchanged.

These tests pin, for both index.html and src/index.html, that each admin loader
reads the server detail, distinguishes 404 (silent demo) from a real error, and
surfaces the auth reason. Server-side tests pin that the admin routes really do
return 401 without credentials and 200 with them.
"""

import base64
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
HANDLERS = ["loadOperationsDashboard", "downloadOperationsDashboardCsv"]


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
    marker = f"function {fn_name}("
    start = text.index(marker)
    rest = text[start + len(marker):]
    m = re.search(r"\n {8}(?:async )?function ", rest)
    end = start + len(marker) + (m.start() if m else 5000)
    return text[start:end]


# --------------------------------------------------------------------------- #
# Client-side: both mirrors surface the real reason (esp. 401) per handler
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("fn_name", HANDLERS)
@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_admin_loader_reads_detail(path, fn_name):
    block = _handler_block(path.read_text(encoding="utf-8", errors="replace"), fn_name)
    assert "serverDetail" in block or ".detail" in block, (path.name, fn_name)


@pytest.mark.parametrize("fn_name", HANDLERS)
@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_admin_loader_distinguishes_404(path, fn_name):
    block = _handler_block(path.read_text(encoding="utf-8", errors="replace"), fn_name)
    assert "!== 404" in block, (path.name, fn_name)


@pytest.mark.parametrize("fn_name", HANDLERS)
@pytest.mark.parametrize("path", INDEX_FILES, ids=lambda p: p.name)
def test_admin_loader_surfaces_auth_reason(path, fn_name):
    block = _handler_block(path.read_text(encoding="utf-8", errors="replace"), fn_name)
    assert "認証" in block, (path.name, fn_name)


@pytest.mark.parametrize("fn_name", HANDLERS)
def test_both_mirrors_identical(fn_name):
    blocks = [_handler_block(p.read_text(encoding="utf-8", errors="replace"), fn_name) for p in INDEX_FILES]
    assert blocks[0] == blocks[1], fn_name


# --------------------------------------------------------------------------- #
# Server-side: the admin routes really 401 without creds and 200 with them
# --------------------------------------------------------------------------- #
def test_operations_dashboard_requires_auth(client):
    assert client.get("/api/admin/operations-dashboard?limit=20").status_code == 401


def test_operations_dashboard_csv_requires_auth(client):
    assert client.get("/api/admin/operations-dashboard/report.csv?limit=100").status_code == 401


def test_operations_dashboard_ok_with_auth(client):
    r = client.get(
        "/api/admin/operations-dashboard?limit=20",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert r.status_code == 200
    assert r.json().get("status") == "success"


# --------------------------------------------------------------------------- #
# Integration: the 10-hypothesis audit harness must be all-green
# --------------------------------------------------------------------------- #
def test_audit_harness_all_hypotheses_pass():
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import audit_admin_dashboard_error_handling as audit  # noqa: E402

    report = audit.evaluate()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
    assert len(report["hypotheses"]) == 10
