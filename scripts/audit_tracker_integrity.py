"""Tracker integrity guard (T890).

The TSV trackers under data/ are the source of truth for the CEO-visible Google
Sheets tabs (課題管理表 / QA表 / テスト結果 / リリース判定). A single ragged row,
duplicate ID, unknown status, malformed date, or dangling cross-reference would
corrupt those Sheets on the next sync — silently. Every lane appends to these
files, so this harness pins ten hypotheses that keep them well-formed and
internally consistent, and fails CI before a bad row reaches the Sheet.

Checks, across issues_tracker / qa_tracker / test_results / release_go_no_go:

* headers match and no row is ragged (H1/H2/H3),
* every ID is unique within its file (H4),
* statuses come from the allowed set (H5),
* dates are YYYY-MM-DD where present (H6),
* every WBS task id referenced by an issue/QA row really exists (H7),
* required cells are non-empty (H8),
* every QA-/R- id a WBS row claims to have recorded exists in its tracker (H9),
* the trackers are drift-free overall (H10).

Output: exports/tracker_integrity_audit.{json,md}. No secrets are emitted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data"
ISSUES = DATA / "issues_tracker.tsv"
QA = DATA / "qa_tracker.tsv"
TESTS = DATA / "test_results.tsv"
RELEASE = DATA / "release_go_no_go_criteria.tsv"
WBS = DATA / "WBS.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "tracker_integrity_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "tracker_integrity_audit.md"

ISSUES_HEADER = ["ID", "カテゴリ", "重要度", "状態", "タイトル", "影響", "緩和策",
                 "オーナー", "起票日", "解決予定日", "関連 WBS", "関連 docs",
                 "関連 Issue", "メモ", "更新日"]
QA_HEADER = ["ID", "カテゴリ", "質問", "回答方針", "保留時の対応", "関連論点",
             "関連 docs", "出典", "状態", "更新日"]
TESTS_HEADER = ["テストID", "機能カテゴリ", "テスト項目", "確認内容", "ステータス",
                "実行エンジン", "合格率", "バグ率", "実行日時"]
RELEASE_HEADER = ["criterion_id", "scope", "category", "criterion", "evidence_source",
                  "required_state", "current_state", "owner", "decision_authority",
                  "related_wbs", "related_issue", "last_checked", "notes"]

ISSUES_STATUS = {"open", "resolved", "accepted_non_blocker", "transferred", "closed"}
QA_STATUS = {"回答済", "想定済"}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_T_RE = re.compile(r"T\d+(?:_\d+)*")
_QA_RE = re.compile(r"QA-\d+")
_R_RE = re.compile(r"R\d+")


def load(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        return [], []
    lines = [ln.rstrip("\r") for ln in path.read_text(encoding="utf-8", errors="replace").split("\n")]
    lines = [ln for ln in lines if ln != ""]
    if not lines:
        return [], []
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def _col(rows: list[list[str]], idx: int) -> list[str]:
    return [r[idx] if idx < len(r) else "" for r in rows]


def wbs_ids() -> set[str]:
    _, rows = load(WBS)
    return {r[0] for r in rows if r}


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def _header_and_width(header, rows, expected):
    header_ok = header == expected
    ragged = []
    for r in rows:
        if len(r) != len(expected):
            ragged.append(f"{(r[0] if r else '?')}({len(r)})")
    return header_ok, ragged


def evaluate() -> list[dict[str, Any]]:
    i_h, i_r = load(ISSUES)
    q_h, q_r = load(QA)
    t_h, t_r = load(TESTS)
    rel_h, rel_r = load(RELEASE)
    known = wbs_ids()
    results: list[dict[str, Any]] = []

    ih_ok, ir = _header_and_width(i_h, i_r, ISSUES_HEADER)
    results.append(_hyp("H1", "課題管理表(issues)のヘッダ15列一致・全行整形",
                        ih_ok and not ir, f"ヘッダ={ih_ok}, ラグド={ir or 'なし'}"))

    qh_ok, qr = _header_and_width(q_h, q_r, QA_HEADER)
    results.append(_hyp("H2", "QA表のヘッダ10列一致・全行整形",
                        qh_ok and not qr, f"ヘッダ={qh_ok}, ラグド={qr or 'なし'}"))

    th_ok, tr = _header_and_width(t_h, t_r, TESTS_HEADER)
    rh_ok, rr = _header_and_width(rel_h, rel_r, RELEASE_HEADER)
    results.append(_hyp("H3", "テスト結果(9列)・リリース判定(13列)のヘッダ一致・全行整形",
                        th_ok and not tr and rh_ok and not rr,
                        f"test(ヘッダ={th_ok},ラグド={tr or 'なし'}) release(ヘッダ={rh_ok},ラグド={rr or 'なし'})"))

    dups = {}
    for name, rows in (("issues", i_r), ("qa", q_r), ("test", t_r), ("release", rel_r)):
        ids = [r[0] for r in rows if r]
        d = sorted({x for x in ids if ids.count(x) > 1})
        if d:
            dups[name] = d
    results.append(_hyp("H4", "全トラッカーのIDが各ファイル内で一意",
                        not dups, f"重複={dups or 'なし'}"))

    bad_status = {}
    bi = sorted({s for s in _col(i_r, 3) if s not in ISSUES_STATUS})
    bq = sorted({s for s in _col(q_r, 8) if s not in QA_STATUS})
    if bi:
        bad_status["issues"] = bi
    if bq:
        bad_status["qa"] = bq
    results.append(_hyp("H5", "状態が許容集合(issues:open/resolved/accepted_non_blocker/transferred/closed, qa:回答済/想定済)",
                        not bad_status, f"不正状態={bad_status or 'なし'}"))

    bad_dates = []
    for tid, d in zip(_col(i_r, 0), _col(i_r, 8)):
        if d and not _DATE_RE.match(d):
            bad_dates.append(f"issues {tid} 起票日={d}")
    for tid, d in zip(_col(i_r, 0), _col(i_r, 14)):
        if d and not _DATE_RE.match(d):
            bad_dates.append(f"issues {tid} 更新日={d}")
    for tid, d in zip(_col(q_r, 0), _col(q_r, 9)):
        if d and not _DATE_RE.match(d):
            bad_dates.append(f"qa {tid} 更新日={d}")
    results.append(_hyp("H6", "日付列(起票日/更新日)がYYYY-MM-DD形式(空許容)",
                        not bad_dates, f"不正日付={bad_dates or 'なし'}"))

    bad_ref = {}
    for tid, refs in zip(_col(i_r, 0), _col(i_r, 10)):
        miss = [t for t in _T_RE.findall(refs) if t not in known and not any(k.startswith(t + "_") for k in known)]
        if miss:
            bad_ref[f"issues:{tid}"] = miss
    for tid, refs in zip(_col(q_r, 0), _col(q_r, 5)):
        miss = [t for t in _T_RE.findall(refs) if t not in known and not any(k.startswith(t + "_") for k in known)]
        if miss:
            bad_ref[f"qa:{tid}"] = miss
    results.append(_hyp("H7", "issues関連WBS・qa関連論点のT参照が全て実在WBS IDに解決",
                        not bad_ref, f"未解決参照={bad_ref or 'なし'}"))

    empties = []
    for r in i_r:
        for idx in (0, 1, 2, 3, 4):  # ID/カテゴリ/重要度/状態/タイトル
            if idx >= len(r) or not r[idx].strip():
                empties.append(f"issues {r[0] if r else '?'}[{ISSUES_HEADER[idx]}]")
    for r in q_r:
        for idx in (0, 1, 2, 8):  # ID/カテゴリ/質問/状態
            if idx >= len(r) or not r[idx].strip():
                empties.append(f"qa {r[0] if r else '?'}[{QA_HEADER[idx]}]")
    results.append(_hyp("H8", "必須セル(issues:ID/カテゴリ/重要度/状態/タイトル, qa:ID/カテゴリ/質問/状態)が非空",
                        not empties, f"空欄={empties[:10] or 'なし'}"))

    issue_ids = {r[0] for r in i_r if r}
    qa_ids = {r[0] for r in q_r if r}
    _, wrows = load(WBS)
    dangling = {"QA": set(), "R": set()}
    for r in wrows:
        detail = r[6] if len(r) > 6 else ""
        for q in _QA_RE.findall(detail):
            if q not in qa_ids:
                dangling["QA"].add(q)
        for rr_ in _R_RE.findall(detail):
            if rr_ not in issue_ids:
                dangling["R"].add(rr_)
    dangling = {k: sorted(v) for k, v in dangling.items() if v}
    results.append(_hyp("H9", "WBS詳細が記録主張するQA-/R- IDが各トラッカーに実在(双方向ドリフト0)",
                        not dangling, f"欠落={dangling or 'なし'}"))

    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp("H10", "全トラッカーが完全・整合(構造/参照ドリフト0)",
                        no_prior_drift, f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))
    return results


def run_audit() -> dict[str, Any]:
    hyps = evaluate()
    _, i_r = load(ISSUES)
    _, q_r = load(QA)
    return {
        "task": "T890",
        "issue_rows": len(i_r),
        "qa_rows": len(q_r),
        "hypotheses": hyps,
        "all_passed": all(h["passed"] for h in hyps),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# トラッカー整合性監査 (T890)",
        "",
        f"- 課題管理表 行数: **{report['issue_rows']}** / QA表 行数: **{report['qa_rows']}**",
        f"- 総合判定: {'✅ PASS (ドリフト0)' if report['all_passed'] else '❌ FAIL'}",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for h in report["hypotheses"]:
        mark = "✅" if h["passed"] else "❌"
        lines.append(f"| {h['id']} | {h['title']} | {mark} | {h['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()
    report = run_audit()
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
