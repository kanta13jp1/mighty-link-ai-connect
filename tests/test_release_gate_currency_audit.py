"""T908 test spec (written test-first): release-gate currency guard.

UAT TS-41 (docs/UAT_TEST_SPECIFICATION.md): the 21-row release gate ledger
(data/release_go_no_go_criteria.tsv) drives the public-launch verdict, but its
current_state is maintained by hand. Measured on 2026-07-20, three gates were
still BLOCKED/WARNING although every related WBS task had completed
(PUBLIC-06 after T752, PUBLIC-11 after the T817 series, PUBLIC-14 after T852);
two had not been re-checked for 13 days. The overall NO_GO therefore mixed real
blockers with stale bookkeeping.

This suite pins the guard's pure functions: gates are read from the ledger,
"stale" is the set of non-PASS gates whose related WBS are all complete,
"inverse drift" is a PASS gate with incomplete WBS (the more dangerous
direction), and staleness must be acknowledged in notes with a re-evaluation
marker. The guard reports; it must never flip a gate to PASS, because the
decision authority is a human (開発責任者 / CEO / 会社管理者).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_release_gate_currency as guard  # noqa: E402

WBS = {"T1": "完了", "T2": "完了", "T3": "未着手"}


def _gate(gid, state, wbs, notes=""):
    return {
        "criterion_id": gid,
        "current_state": state,
        "related_wbs": wbs,
        "notes": notes,
        "owner": "Codex",
        "decision_authority": "開発責任者",
        "last_checked": "2026-07-20",
    }


def test_related_wbs_ids_splits_semicolon_list():
    assert guard.related_wbs_ids(_gate("G", "PASS", "T1;T2")) == ["T1", "T2"]
    assert guard.related_wbs_ids(_gate("G", "PASS", "")) == []


def test_all_related_complete_detects_completion():
    assert guard.all_related_complete(_gate("G", "BLOCKED", "T1;T2"), WBS) is True
    assert guard.all_related_complete(_gate("G", "BLOCKED", "T1;T3"), WBS) is False
    # a gate with no related WBS is not "complete" — nothing backs it
    assert guard.all_related_complete(_gate("G", "BLOCKED", ""), WBS) is False


def test_stale_gates_are_nonpass_with_all_work_done():
    gates = [
        _gate("A", "BLOCKED", "T1;T2"),   # stale
        _gate("B", "BLOCKED", "T3"),      # genuinely blocked
        _gate("C", "PASS", "T1"),         # fine
    ]
    assert guard.stale_gates(gates, WBS) == ["A"]


def test_unannotated_stale_requires_the_reevaluation_marker():
    gates = [
        _gate("A", "BLOCKED", "T1", notes="理由なし"),
        _gate("B", "WARNING", "T2", notes=f"{guard.REEVAL_MARKER} 実機確認待ち】"),
    ]
    assert guard.unannotated_stale(gates, WBS) == ["A"]


def test_inverse_drift_flags_pass_with_open_work():
    gates = [_gate("A", "PASS", "T1;T3"), _gate("B", "PASS", "T1")]
    assert guard.inverse_drift(gates, WBS) == ["A"]


def test_dangling_wbs_refs_detected():
    gates = [_gate("A", "PASS", "T1;T999")]
    assert guard.dangling_wbs_refs(gates, WBS) == {"A": ["T999"]}


def test_guard_never_auto_passes_a_gate():
    """The guard must be read-only w.r.t. the ledger (human decides state)."""
    source = Path(guard.__file__).read_text(encoding="utf-8")
    for forbidden in ("write_text", "to_csv", "writer(", "current_state\"] =", "current_state'] ="):
        assert forbidden not in source.replace('args.json.write_text', '').replace('args.md.write_text', ''), (
            f"guard must not mutate the gate ledger: {forbidden}"
        )


def test_evaluate_passes_on_the_real_repo():
    results = guard.evaluate()
    assert isinstance(results, list) and len(results) == 10
    failed = [r["id"] for r in results if not r["passed"]]
    assert not failed, f"release-gate hypotheses failing on real repo: {failed}"
