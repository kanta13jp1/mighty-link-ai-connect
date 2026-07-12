"""T889 guard (written test-first): WBS lifecycle-coverage & schedule integrity.

The WBS (`data/WBS.tsv`) must cover the whole delivery lifecycle (企画→設計→実装→
テスト→リリース→実運用→保守) over the confirmed stack (お名前.com / Firebase /
Supabase), keep statuses/columns clean, and never invert a schedule
(開始日 > 終了予定日). This suite pins the ten hypotheses the audit harness
(scripts/audit_wbs_lifecycle_coverage.py) verifies: a synthetic well-formed
baseline passes all ten, each injected defect trips exactly its hypothesis, and
the real WBS is gap-free.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_wbs_lifecycle_coverage as audit  # noqa: E402


# --------------------------------------------------------------------------- #
# Synthetic well-formed baseline + per-hypothesis defect injection
# --------------------------------------------------------------------------- #
def _row(tid, name, status="完了", start="2026-07-01", end="2026-07-02",
         phase="8. 本番運用・品質管理", sub="", engine="VSCode + Claude Code",
         owner="Claude Code", action=""):
    return {
        "タスクID": tid, "大フェーズ": phase, "小フェーズ": sub, "タスク名": name,
        "担当": owner, "実行エンジン": engine, "Sheets Live 連携アクション": action,
        "ステータス": status, "開始日": start, "終了予定日": end,
    }


def _good_rows():
    rows = []
    stage_kw = {"企画": "企画", "設計": "設計", "実装": "実装", "テスト": "テスト",
                "リリース": "リリース", "実運用": "運用監視", "保守": "保守"}
    for i, (_stage, kw) in enumerate(stage_kw.items()):
        rows.append(_row(f"T{100 + i}", f"{kw}タスク"))
    for i, kw in enumerate(["お名前.com", "Firebase", "Supabase"]):
        rows.append(_row(f"T{200 + i}", f"{kw}対応タスク"))
    rows.append(_row("T300", "開発完了総合判定ゲート"))
    # one valid unfinished task so H7 is exercised on real dates
    rows.append(_row("T301", "実運用の監視タスク", status="未着手", start="2026-08-01", end="2026-08-02"))
    while len(rows) < 55:
        rows.append(_row(f"T{500 + len(rows)}", "汎用の実装タスク"))
    return rows


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def test_good_baseline_passes_all_ten():
    hyps = audit.evaluate(audit.EXPECTED_HEADER, _good_rows())
    assert len(hyps) == 10
    failing = [h["id"] for h in hyps if not h["passed"]]
    assert failing == [], failing


def test_h1_flags_too_few_tasks():
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, _good_rows()[:10]))
    assert hyps["H1"]["passed"] is False


def test_h1_flags_wrong_header():
    hyps = _ids(audit.evaluate(["wrong", "header"], _good_rows()))
    assert hyps["H1"]["passed"] is False


def test_h2_flags_duplicate_id():
    rows = _good_rows()
    rows[1]["タスクID"] = rows[0]["タスクID"]
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H2"]["passed"] is False


def test_h3_flags_missing_lifecycle_stage():
    rows = [r for r in _good_rows() if "設計" not in r["タスク名"]]
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H3"]["passed"] is False
    assert "設計" in audit.uncovered_stages(rows)


def test_h4_flags_missing_stack_component():
    rows = [r for r in _good_rows() if "Firebase" not in r["タスク名"]]
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H4"]["passed"] is False


def test_h5_flags_blank_required_column():
    rows = _good_rows()
    rows[0]["担当"] = ""
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H5"]["passed"] is False


def test_h6_flags_unknown_status():
    rows = _good_rows()
    rows[0]["ステータス"] = "保留"
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H6"]["passed"] is False


def test_h7_flags_unfinished_task_missing_dates():
    rows = _good_rows()
    rows.append(_row("T999", "未着手だが日付欠落", status="未着手", start="", end=""))
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H7"]["passed"] is False


def test_h8_flags_inverted_schedule():
    rows = _good_rows()
    rows.append(_row("T998", "日程逆転タスク", start="2026-07-05", end="2026-07-04"))
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H8"]["passed"] is False
    assert any("T998" in x for x in audit.inverted_schedule_rows(rows))


def test_h9_flags_missing_completion_gate():
    rows = [r for r in _good_rows() if "完了" not in r["タスク名"]]
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H9"]["passed"] is False


def test_h10_flags_any_prior_drift():
    rows = _good_rows()
    rows[0]["ステータス"] = "保留"  # trips H6 -> H10 must also fail
    hyps = _ids(audit.evaluate(audit.EXPECTED_HEADER, rows))
    assert hyps["H10"]["passed"] is False


# --------------------------------------------------------------------------- #
# Loader + integration against the real repository
# --------------------------------------------------------------------------- #
def test_load_rows_parses_header_and_dicts(tmp_path):
    f = tmp_path / "wbs.tsv"
    f.write_text("\t".join(audit.EXPECTED_HEADER) + "\r\n"
                 + "\t".join(["T1", "1. 企画・設計", "", "企画", "Claude Code",
                              "VSCode + Claude Code", "", "完了", "2026-07-01", "2026-07-02"]) + "\r\n",
                 encoding="utf-8")
    header, rows = audit.load_rows(f)
    assert header == audit.EXPECTED_HEADER
    assert len(rows) == 1 and rows[0]["タスクID"] == "T1"


def test_real_wbs_is_lifecycle_complete_and_schedule_consistent():
    report = audit.run_audit()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
    assert report["uncovered_stages"] == []
    assert report["uncovered_stack"] == []
    assert report["inverted_schedule"] == []
