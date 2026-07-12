"""T890 guard (written test-first): TSV tracker integrity.

The data/ trackers feed the CEO-visible Google Sheets tabs. This suite pins the
ten hypotheses the audit (scripts/audit_tracker_integrity.py) verifies: a
synthetic well-formed set of all four trackers passes all ten, each injected
defect trips exactly its hypothesis, and the real repository trackers are clean.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_tracker_integrity as audit  # noqa: E402


def _tsv(header, rows):
    return "\r\n".join(["\t".join(header)] + ["\t".join(r) for r in rows]) + "\r\n"


def _good():
    issues = [
        ["R900", "quality", "LOW", "resolved", "タイトル", "影響", "緩和策",
         "Claude Code", "2026-07-12", "2026-07-12", "T900", "docs/x.md", "-", "メモ", "2026-07-12"],
        ["R901", "quality", "MED", "open", "タイトル2", "影響2", "緩和策2",
         "Codex", "2026-07-12", "", "T900", "docs/y.md", "-", "メモ2", "2026-07-12"],
    ]
    qa = [
        ["QA-900", "quality", "質問？", "回答", "保留", "T900", "docs/x.md", "出典", "回答済", "2026-07-12"],
        ["QA-901", "quality", "質問2？", "回答2", "保留2", "R900;T900", "docs/y.md", "出典2", "想定済", "2026-07-12"],
    ]
    tests = [["TS-900", "cat", "項目", "確認", "PASS", "Claude Code", "100%", "0%", "2026-07-12"]]
    release = [["PUB-900", "internal", "cat", "基準", "evidence", "PASS", "PASS",
                "owner", "auth", "T900", "-", "2026-07-12", "notes"]]
    wbs = [["T900", "8. 本番運用・品質管理", "品質管理", "タスク", "Claude Code",
            "VSCode + Claude Code", "QA-900/R900記録の詳細", "完了", "2026-07-12", "2026-07-12"]]
    return {"issues": issues, "qa": qa, "tests": tests, "release": release, "wbs": wbs}


def _install(tmp_path, monkeypatch, data):
    files = {
        "issues": (tmp_path / "issues.tsv", audit.ISSUES_HEADER, data["issues"]),
        "qa": (tmp_path / "qa.tsv", audit.QA_HEADER, data["qa"]),
        "tests": (tmp_path / "tests.tsv", audit.TESTS_HEADER, data["tests"]),
        "release": (tmp_path / "release.tsv", audit.RELEASE_HEADER, data["release"]),
        "wbs": (tmp_path / "wbs.tsv",
                ["タスクID", "大フェーズ", "小フェーズ", "タスク名", "担当", "実行エンジン",
                 "Sheets Live 連携アクション", "ステータス", "開始日", "終了予定日"], data["wbs"]),
    }
    for _key, (path, header, rows) in files.items():
        path.write_bytes(_tsv(header, rows).encode("utf-8"))
    monkeypatch.setattr(audit, "ISSUES", files["issues"][0])
    monkeypatch.setattr(audit, "QA", files["qa"][0])
    monkeypatch.setattr(audit, "TESTS", files["tests"][0])
    monkeypatch.setattr(audit, "RELEASE", files["release"][0])
    monkeypatch.setattr(audit, "WBS", files["wbs"][0])


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def test_good_baseline_passes_all_ten(tmp_path, monkeypatch):
    _install(tmp_path, monkeypatch, _good())
    hyps = audit.evaluate()
    assert len(hyps) == 10
    failing = [h["id"] for h in hyps if not h["passed"]]
    assert failing == [], failing


def test_h1_flags_ragged_issue_row(tmp_path, monkeypatch):
    d = _good()
    d["issues"][0] = d["issues"][0][:-1]  # drop last column -> 14 cols
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H1"]["passed"] is False


def test_h2_flags_ragged_qa_row(tmp_path, monkeypatch):
    d = _good()
    d["qa"][0] = d["qa"][0] + ["extra"]  # 11 cols
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H2"]["passed"] is False


def test_h3_flags_ragged_release_row(tmp_path, monkeypatch):
    d = _good()
    d["release"][0] = d["release"][0][:-2]
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H3"]["passed"] is False


def test_h4_flags_duplicate_id(tmp_path, monkeypatch):
    d = _good()
    d["issues"][1][0] = d["issues"][0][0]  # duplicate R900
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H4"]["passed"] is False


def test_h5_flags_unknown_status(tmp_path, monkeypatch):
    d = _good()
    d["issues"][0][3] = "保留中"  # not in allowed set
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H5"]["passed"] is False


def test_h6_flags_bad_date(tmp_path, monkeypatch):
    d = _good()
    d["issues"][0][8] = "2026/07/12"  # wrong format
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H6"]["passed"] is False


def test_h7_flags_dangling_wbs_reference(tmp_path, monkeypatch):
    d = _good()
    d["issues"][0][10] = "T404"  # not present in synthetic WBS
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H7"]["passed"] is False


def test_h8_flags_empty_required_cell(tmp_path, monkeypatch):
    d = _good()
    d["qa"][0][2] = ""  # empty 質問
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H8"]["passed"] is False


def test_h9_flags_wbs_claiming_missing_tracker_id(tmp_path, monkeypatch):
    d = _good()
    d["wbs"][0][6] = "QA-999記録"  # QA-999 not in qa tracker
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H9"]["passed"] is False


def test_h10_flags_any_prior_drift(tmp_path, monkeypatch):
    d = _good()
    d["issues"][1][0] = d["issues"][0][0]  # dup -> H4 fails -> H10 fails
    _install(tmp_path, monkeypatch, d)
    assert _ids(audit.evaluate())["H10"]["passed"] is False


# --------------------------------------------------------------------------- #
# Integration: the real repository trackers
# --------------------------------------------------------------------------- #
def test_real_trackers_are_integrity_clean():
    report = audit.run_audit()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing
