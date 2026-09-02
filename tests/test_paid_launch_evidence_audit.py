"""Tests for the fail-closed 8/24 paid-launch evidence guard (T988)."""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_paid_launch_evidence as guard  # noqa: E402


def test_snapshot_exposes_missing_measurement_without_secrets():
    snapshot = guard.evidence_snapshot()
    assert snapshot["sales"]["input_count"] == 3143
    assert snapshot["sales"]["fallback_used"] is True
    assert snapshot["monthly"]["kpi"]["availability_pct"] is None
    assert snapshot["cost"]["overall_status"] in {"unknown", "warning"}
    assert snapshot["legal"]["placeholder_count"] == 31


def test_real_decision_pack_passes_all_ten_hypotheses():
    results = guard.evaluate()
    assert len(results) == 10
    assert [result["id"] for result in results] == [f"H{i}" for i in range(1, 11)]
    assert not [result for result in results if not result["passed"]]


def test_false_sales_claim_is_rejected():
    text = guard.read_text(guard.PACK) + "\n精度80%以上を実証"
    h3 = next(result for result in guard.evaluate(pack_text=text) if result["id"] == "H3")
    assert h3["passed"] is False


def test_missing_human_signoff_marker_is_rejected():
    snapshot = deepcopy(guard.evidence_snapshot())
    snapshot["signoff_text"] = snapshot["signoff_text"].replace("要人間確認", "承認済")
    h7 = next(
        result for result in guard.evaluate(snapshot=snapshot) if result["id"] == "H7"
    )
    assert h7["passed"] is False


def test_go_claim_without_closed_gates_is_rejected():
    text = guard.read_text(guard.PACK).replace("現時点の推奨判定: NO-GO", "現時点の推奨判定: Go")
    h10 = next(result for result in guard.evaluate(pack_text=text) if result["id"] == "H10")
    assert h10["passed"] is False
