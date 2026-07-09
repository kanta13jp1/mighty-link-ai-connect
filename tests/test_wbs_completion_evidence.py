"""T849_1 WBS completion evidence aggregator tests."""

import sys
from pathlib import Path

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
                assert t in ids, f"gate {c.get('criterion_id')} references missing WBS {t}"


def test_reevaluate_candidates_detected():
    # PUBLIC-11 (T836/T817_7 done) and PUBLIC-14 (T852 done) should surface as
    # re-evaluate candidates now that their related tasks are complete.
    report = agg.build_report("2026-07-09")
    cands = report["remaining_for_ga"]["reevaluate_candidates"]
    assert "PUBLIC-14" in cands


def test_overdue_detection_is_a_list():
    report = agg.build_report("2026-07-09")
    assert isinstance(report["wbs_stats"]["overdue_incomplete"], list)
