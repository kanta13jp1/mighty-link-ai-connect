"""T849_1 WBS completion evidence aggregator tests."""

import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_wbs_completion_evidence as agg


def test_all_hypotheses_pass():
    report = agg.build_report("2026-07-09")
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["hypotheses_total"] == 10
    assert failing == [], f"unexpected failing hypotheses: {failing}"
    assert report["status"] == "ok"


def test_stats_sum_to_total():
    report = agg.build_report("2026-07-09")
    s = report["wbs_stats"]
    assert s["done"] + s["in_progress"] + s["not_started"] == s["total"]
    assert s["completion_rate_pct"] > 90.0


def test_evidence_artifacts_exist():
    report = agg.build_report("2026-07-09")
    missing = [k for k, v in report["evidence_index"].items() if not v["exists"]]
    assert missing == [], f"missing evidence artifacts: {missing}"


def test_gate_related_wbs_all_exist():
    wbs = agg.load_wbs()
    criteria = agg.load_criteria()
    ids = {r["タスクID"] for r in wbs}
    for c in criteria:
        for t in (c.get("related_wbs") or "").split(";"):
            if t:
                assert t in ids or any(k.startswith(t + "_") for k in ids), f"gate {c.get('criterion_id')} references missing WBS {t}"


def test_reevaluate_candidate_suppressed_by_open_blocking_issue():
    """T849_2: 'all related WBS complete' is NOT sufficient to recommend PASS.

    A gate whose related tasks are all 完了 but which still has an OPEN issue
    touching those tasks must not be advertised as a PASS re-evaluation
    candidate — acting on it would flip a GA gate green while a real defect is
    outstanding. It must be classified as blocked_by_open_issue instead, naming
    the issue so the closure owner knows what to resolve.
    """
    criteria = [{
        "criterion_id": "TEST-01", "current_state": "BLOCKED",
        "related_wbs": "TX1;TX2", "related_issue": "",
    }]
    wbs = [
        {"タスクID": "TX1", "ステータス": "完了", "担当": "Codex"},
        {"タスクID": "TX2", "ステータス": "完了", "担当": "Codex"},
    ]
    issues = [
        {"ID": "R900", "状態": "open", "関連 WBS": "TX2;TX9"},
        {"ID": "R901", "状態": "resolved", "関連 WBS": "TX1"},
    ]
    out = agg.classify_remaining(criteria, wbs, issues)
    gate = out["non_pass_gates"][0]
    assert gate["class"] == "blocked_by_open_issue", gate
    assert gate["open_issues"] == ["R900"], gate
    assert "TEST-01" not in out["reevaluate_candidates"]


def test_reevaluate_candidate_kept_when_no_open_issue():
    """The recommendation still fires when nothing is actually outstanding."""
    criteria = [{
        "criterion_id": "TEST-02", "current_state": "BLOCKED",
        "related_wbs": "TY1", "related_issue": "",
    }]
    wbs = [{"タスクID": "TY1", "ステータス": "完了", "担当": "Codex"}]
    issues = [{"ID": "R902", "状態": "resolved", "関連 WBS": "TY1"}]
    out = agg.classify_remaining(criteria, wbs, issues)
    assert out["non_pass_gates"][0]["class"] == "reevaluate_candidate"
    assert out["reevaluate_candidates"] == ["TEST-02"]


def test_deferred_review_is_not_recommended_for_immediate_pass():
    criteria = [{
        "criterion_id": "TEST-DEFERRED", "current_state": "BLOCKED",
        "related_wbs": "TZ1", "related_issue": "",
        "notes": "【再評価待ち: 2026-09-24有償公開月次レビュー】延期CLOSE",
    }]
    wbs = [{"タスクID": "TZ1", "ステータス": "完了", "担当": "Codex"}]
    out = agg.classify_remaining(criteria, wbs, [])
    assert out["non_pass_gates"][0]["class"] == "deferred_review"
    assert out["reevaluate_candidates"] == []
    assert out["deferred_reviews"] == ["TEST-DEFERRED"]


def test_real_repo_operational_blockers_prevent_false_reevaluation():
    """PUBLIC-11 stays blocked by T944 and the reopened T999 incident."""
    report = agg.build_report("2026-07-25")
    cands = report["remaining_for_ga"]["reevaluate_candidates"]
    assert "PUBLIC-11" not in cands
    assert "PUBLIC-14" not in cands
    by_gate = {g["gate"]: g for g in report["remaining_for_ga"]["non_pass_gates"]}
    open_tasks = set(by_gate["PUBLIC-11"]["open_tasks"])
    assert "T944" in open_tasks
    assert "T999" in open_tasks
    assert "PUBLIC-14" not in by_gate


def test_overdue_detection_is_a_list():
    report = agg.build_report("2026-07-09")
    assert isinstance(report["wbs_stats"]["overdue_incomplete"], list)


def test_default_reporting_date_is_current_jst_date():
    value = agg.jst_today()
    assert date.fromisoformat(value) == datetime.now(ZoneInfo("Asia/Tokyo")).date()
