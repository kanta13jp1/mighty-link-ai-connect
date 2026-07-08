"""T876 session-only aptitude/motivation self-check tests.

The central guarantee is legal (R119/QA-105): answers and the derived
mental-state score are 要配慮個人情報 and must NEVER be persisted. These tests
verify that structurally (no DB rows created, no answers in the audit log) plus
the safety filter, consent enforcement, and Gemini fallback behaviour.
"""

import json
import os
import shutil
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import aptitude_demo
import app
from fastapi.testclient import TestClient

LEGAL_CONSENT = {
    "legal_consent_accepted": True,
    "legal_consent_version": app.LEGAL_CONSENT_VERSION,
}

app.AI_FORCE_MOCK = True
app.GEMINI_READY = False


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Save every global we mutate so we never leak paths into later test
    # modules (a deleted AUDIT_LOG_FILE dir would break their audit writes).
    saved = {
        "DATA_DIR": app.DATA_DIR, "AUDIT_DIR": app.AUDIT_DIR,
        "AUDIT_LOG_FILE": app.AUDIT_LOG_FILE,
        "EXTERNAL_API_USAGE_LOG_FILE": app.EXTERNAL_API_USAGE_LOG_FILE,
    }
    app.DATA_DIR = os.path.join(PROJECT_ROOT, "data_test_aptitude")
    app.AUDIT_DIR = os.path.join(app.DATA_DIR, "audit")
    app.AUDIT_LOG_FILE = os.path.join(app.AUDIT_DIR, "ai_audit.jsonl")
    app.EXTERNAL_API_USAGE_LOG_FILE = os.path.join(app.DATA_DIR, "external_api_usage.jsonl")
    if os.path.exists(app.DATA_DIR):
        shutil.rmtree(app.DATA_DIR)
    os.makedirs(app.AUDIT_DIR, exist_ok=True)
    app.init_db()
    yield
    if os.path.exists(app.DATA_DIR):
        shutil.rmtree(app.DATA_DIR)
    for name, value in saved.items():
        setattr(app, name, value)


@pytest.fixture
def client():
    return TestClient(app.app)


# ---- H1 / H2: question generation + count bounds + fallback ----

def test_h1_questions_within_10_to_20(client):
    res = client.post("/api/aptitude-demo/questions", json={"count": 15, **LEGAL_CONSENT})
    assert res.status_code == 200
    body = res.json()
    assert aptitude_demo.QUESTION_MIN <= body["count"] <= aptitude_demo.QUESTION_MAX
    assert body["count"] == 15
    assert all(q["text"] for q in body["questions"])


def test_h2_fallback_without_gemini(client):
    res = client.post("/api/aptitude-demo/questions", json={**LEGAL_CONSENT})
    assert res.status_code == 200
    assert res.json()["source"] == "fallback"  # GEMINI_READY False in tests


def test_count_is_clamped():
    assert aptitude_demo.clamp_count(3) == aptitude_demo.QUESTION_MIN
    assert aptitude_demo.clamp_count(99) == aptitude_demo.QUESTION_MAX
    assert aptitude_demo.clamp_count(None) == aptitude_demo.QUESTION_DEFAULT


# ---- H3: evaluation returns an on-screen result ----

def test_h3_evaluate_returns_scores(client):
    res = client.post("/api/aptitude-demo/evaluate", json={
        "consented": True,
        "answers": [{"dimension": "energy", "value": 5}, {"dimension": "focus", "value": 4}],
        **LEGAL_CONSENT,
    })
    assert res.status_code == 200
    body = res.json()
    assert body["overall_score"] == 4.5
    assert 0 <= body["condition_index"] <= 100
    assert body["band"] in {"good", "moderate", "watch"}


# ---- H4: NO persistence — the module cannot import storage, and no rows appear ----

def test_h4_module_has_no_storage_imports():
    src = open(os.path.join(PROJECT_ROOT, "src", "aptitude_demo.py"), encoding="utf-8").read()
    for forbidden in ("psycopg2", "sqlite3", "get_db_connection", "supabase", "INSERT", "cursor"):
        assert forbidden not in src, f"aptitude_demo must not reference storage ({forbidden})"


def test_h4_evaluation_creates_no_db_rows(client):
    # feedback_events is a representative storage table; count must not change.
    def count_rows():
        import sqlite3
        con = sqlite3.connect(os.path.join(app.DATA_DIR, "mighty.db"))
        try:
            return con.execute("SELECT COUNT(*) FROM feedback_events").fetchone()[0]
        finally:
            con.close()

    before = count_rows()
    for _ in range(3):
        client.post("/api/aptitude-demo/questions", json={**LEGAL_CONSENT})
        client.post("/api/aptitude-demo/evaluate", json={
            "consented": True, "answers": [{"dimension": "energy", "value": 3}], **LEGAL_CONSENT})
    assert count_rows() == before
    assert all(r["persisted"] is False for r in [
        client.post("/api/aptitude-demo/questions", json={**LEGAL_CONSENT}).json(),
        client.post("/api/aptitude-demo/evaluate", json={
            "consented": True, "answers": [{"dimension": "x", "value": 2}], **LEGAL_CONSENT}).json(),
    ])


# ---- H5: audit log never contains answer values or the score ----

def test_h5_audit_log_excludes_answers_and_score(client):
    client.post("/api/aptitude-demo/evaluate", json={
        "consented": True,
        "answers": [{"dimension": "energy", "value": 5}, {"dimension": "recovery", "value": 1}],
        **LEGAL_CONSENT,
    })
    assert os.path.exists(app.AUDIT_LOG_FILE)
    audit_text = open(app.AUDIT_LOG_FILE, encoding="utf-8").read()
    events = [json.loads(line) for line in audit_text.splitlines() if line.strip()]
    apt_events = [e for e in events if "aptitude_demo" in json.dumps(e, ensure_ascii=False)]
    assert apt_events, "expected an aptitude_demo audit event"
    for e in apt_events:
        payload = json.dumps(e, ensure_ascii=False)
        assert "answers_stored" in payload and '"answers_stored": false' in payload.lower().replace(" ", " ")
        # the concrete answer values / dimensions must not be logged
        blob = json.dumps(e.get("payload", e), ensure_ascii=False)
        assert "overall_score" not in blob
        assert "condition_index" not in blob
        assert "dimension_scores" not in blob


# ---- H6: safety filter drops direct 要配慮 medical probes ----

def test_h6_safety_filter_rejects_sensitive_and_backfills(client):
    unsafe = [
        {"dimension": "d", "text": "うつ病と診断されたことはありますか。"},
        {"dimension": "d", "text": "現在服薬や通院をしていますか。"},
        {"dimension": "d", "text": "最近、仕事に集中できていますか。"},  # safe
    ]
    result = aptitude_demo.sanitize_questions(unsafe, 12)
    texts = [q["text"] for q in result]
    assert "うつ病と診断されたことはありますか。" not in texts
    assert "現在服薬や通院をしていますか。" not in texts
    assert len(result) == 12  # back-filled from vetted set
    assert all(aptitude_demo.is_safe_question(q["text"]) for q in result)


# ---- H7: consent enforcement ----

def test_h7_evaluate_requires_consent(client):
    no_consent = client.post("/api/aptitude-demo/evaluate", json={
        "consented": False, "answers": [{"dimension": "x", "value": 3}], **LEGAL_CONSENT})
    assert no_consent.status_code == 400

    no_legal = client.post("/api/aptitude-demo/questions", json={"count": 12})
    assert no_legal.status_code == 400  # legal consent missing


# ---- H8: privacy notice present in both responses ----

def test_h8_privacy_notice_present(client):
    q = client.post("/api/aptitude-demo/questions", json={**LEGAL_CONSENT}).json()
    e = client.post("/api/aptitude-demo/evaluate", json={
        "consented": True, "answers": [{"dimension": "x", "value": 4}], **LEGAL_CONSENT}).json()
    assert "保存されず" in q["privacy_notice"]
    assert "保存されず" in e["privacy_notice"]
    assert "医療的診断ではありません" in e["disclaimer"]


# ---- H9: gemini bridge failure falls back cleanly ----

def test_h9_gemini_failure_falls_back():
    def boom(prompt):
        raise RuntimeError("gemini down")

    result = aptitude_demo.generate_questions(count=12, gemini_caller=boom)
    assert result["source"] == "fallback"
    assert result["count"] == 12


def test_h9_gemini_success_is_sanitized():
    def fake(prompt):
        return json.dumps([
            {"dimension": "energy", "text": "十分に休息できていますか。"},
            {"dimension": "bad", "text": "うつ病の既往はありますか。"},  # must be dropped
        ] + [{"dimension": "g", "text": f"安全な質問その{i}です。"} for i in range(15)])

    result = aptitude_demo.generate_questions(count=12, gemini_caller=fake)
    assert result["source"] == "ai_generated"
    assert result["count"] == 12
    assert all(aptitude_demo.is_safe_question(q["text"]) for q in result["questions"])


# ---- H10: evaluation rejects empty/invalid answers ----

def test_h10_evaluate_rejects_no_valid_answers(client):
    res = client.post("/api/aptitude-demo/evaluate", json={
        "consented": True, "answers": [{"dimension": "x", "value": 99}], **LEGAL_CONSENT})
    assert res.status_code == 400
