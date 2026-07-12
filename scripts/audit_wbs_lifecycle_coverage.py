"""WBS lifecycle-coverage & schedule-integrity guard (T889).

The project WBS (`data/WBS.tsv`) is the single source of truth for delivery. Its
completeness across the full lifecycle — 企画 → 設計 → 実装 → テスト → リリース →
実運用 → 保守 — used to be checked only by hand (docs/WBS_PROCESS_COVERAGE_AUDIT_*).
This harness automates that review and pins ten hypotheses so a lifecycle gap,
an unknown status, or an inverted schedule (開始日 > 終了予定日) fails CI instead
of silently shipping.

It verifies, over the real confirmed stack (レジストラ=お名前.com / バックエンド=
Firebase / DB=Supabase):

* every canonical lifecycle stage is covered by >=1 task (H3),
* each confirmed stack component is covered by >=1 task (H4),
* required columns are filled and statuses are from the allowed set (H5/H6),
* unfinished tasks carry both dates in YYYY-MM-DD form and no task inverts its
  schedule (H7/H8),
* a development-completion gate exists so the lifecycle actually closes (H9),
* the WBS is drift-free overall (H1/H2/H10).

Output: exports/wbs_lifecycle_coverage_audit.{json,md}. No secrets are emitted.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WBS_PATH = PROJECT_ROOT / "data" / "WBS.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "wbs_lifecycle_coverage_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "wbs_lifecycle_coverage_audit.md"

MIN_TASKS = 50
EXPECTED_HEADER = [
    "タスクID", "大フェーズ", "小フェーズ", "タスク名", "担当",
    "実行エンジン", "Sheets Live 連携アクション", "ステータス", "開始日", "終了予定日",
]
# Columns that must never be blank on any row.
REQUIRED_COLUMNS = ["タスクID", "大フェーズ", "タスク名", "担当", "実行エンジン", "ステータス"]
ALLOWED_STATUS = {"完了", "実行中", "未着手"}

# Canonical delivery lifecycle. Each stage must be covered by >=1 task whose
# phase/name/action blob contains at least one keyword.
LIFECYCLE_STAGES: dict[str, list[str]] = {
    "企画": ["企画", "要件", "ヒアリング", "方向性", "議事録", "PoC", "アンケート設計"],
    "設計": ["設計", "アーキ", "スキーマ", "ワイヤーフレーム", "仕様", "ポリシー"],
    "実装": ["実装", "開発", "機能", "パイプライン", "エンドポイント", "UI", "統合"],
    "テスト": ["テスト", "pytest", "UAT", "受入", "E2E", "検証", "QA", "監査"],
    "リリース": ["デプロイ", "リリース", "ローンチ", "GA", "公開", "Release", "tag", "アナウンス"],
    "実運用": ["運用", "監視", "サポート", "インシデント", "SLA", "バックアップ", "コスト", "DR"],
    "保守": ["保守", "依存更新", "upgrade", "アップグレード", "年次", "棚卸", "追従", "メンテ", "サポート終了"],
}

# Confirmed production stack that must each appear in the WBS.
STACK_COMPONENTS: dict[str, list[str]] = {
    "レジストラ(お名前.com)": ["お名前.com", "レジストラ", "ドメイン", "DNS"],
    "バックエンド(Firebase)": ["Firebase", "firebase"],
    "DB(Supabase)": ["Supabase", "supabase"],
}

# A completion gate that ties the whole delivery together must exist.
COMPLETION_GATE_KEYWORDS = ["完了判定", "総合判定", "開発完了", "GAリリース閉鎖", "完了証跡", "完了宣言"]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_rows(path: Path = WBS_PATH) -> tuple[list[str], list[dict[str, str]]]:
    """Return (header, rows) where each row is a column-name -> value dict."""
    if not path.exists():
        return [], []
    lines = [ln for ln in path.read_text(encoding="utf-8", errors="replace").split("\n")]
    lines = [ln.rstrip("\r") for ln in lines if ln.strip()]
    if not lines:
        return [], []
    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for ln in lines[1:]:
        cells = ln.split("\t")
        rows.append({header[i]: (cells[i] if i < len(cells) else "") for i in range(len(header))})
    return header, rows


def _blob(row: dict[str, str]) -> str:
    return " ".join([
        row.get("大フェーズ", ""), row.get("小フェーズ", ""),
        row.get("タスク名", ""), row.get("Sheets Live 連携アクション", ""),
    ])


def _covered(rows: list[dict[str, str]], keywords: list[str]) -> bool:
    blob = "\n".join(_blob(r) for r in rows)
    return any(kw in blob for kw in keywords)


def uncovered_stages(rows: list[dict[str, str]]) -> list[str]:
    return [s for s, kws in LIFECYCLE_STAGES.items() if not _covered(rows, kws)]


def uncovered_stack(rows: list[dict[str, str]]) -> list[str]:
    return [s for s, kws in STACK_COMPONENTS.items() if not _covered(rows, kws)]


def inverted_schedule_rows(rows: list[dict[str, str]]) -> list[str]:
    bad = []
    for r in rows:
        start, end = r.get("開始日", ""), r.get("終了予定日", "")
        if _DATE_RE.match(start) and _DATE_RE.match(end) and start > end:
            bad.append(f"{r.get('タスクID')}({start}>{end})")
    return bad


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(header: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    results.append(_hyp(
        "H1", f"WBSタスクが{MIN_TASKS}件以上かつヘッダ10列が既定どおり",
        len(rows) >= MIN_TASKS and header == EXPECTED_HEADER,
        f"件数={len(rows)}, ヘッダ一致={header == EXPECTED_HEADER}"))

    ids = [r.get("タスクID", "") for r in rows]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    results.append(_hyp(
        "H2", "タスクIDが一意(重複なし)",
        not dup, f"重複={dup or 'なし'}"))

    miss_stage = uncovered_stages(rows)
    results.append(_hyp(
        "H3", "ライフサイクル7工程(企画/設計/実装/テスト/リリース/実運用/保守)を各≥1タスクで網羅",
        not miss_stage, f"未網羅工程={miss_stage or 'なし'}"))

    miss_stack = uncovered_stack(rows)
    results.append(_hyp(
        "H4", "確定スタック(お名前.com/Firebase/Supabase)を各≥1タスクで網羅",
        not miss_stack, f"未網羅スタック={miss_stack or 'なし'}"))

    blank = {
        r.get("タスクID", "?"): [c for c in REQUIRED_COLUMNS if not r.get(c, "").strip()]
        for r in rows
    }
    blank = {k: v for k, v in blank.items() if v}
    results.append(_hyp(
        "H5", "全行が必須列(ID/大フェーズ/タスク名/担当/実行エンジン/ステータス)を空欄なしで保有",
        not blank, f"空欄={blank or 'なし'}"))

    bad_status = sorted({
        r.get("ステータス", "") for r in rows if r.get("ステータス", "") not in ALLOWED_STATUS
    })
    results.append(_hyp(
        "H6", "全行のステータスが許容値(完了/実行中/未着手)のみ",
        not bad_status, f"不正ステータス={bad_status or 'なし'}"))

    bad_dates = [
        r.get("タスクID", "?") for r in rows
        if r.get("ステータス") != "完了"
        and not (_DATE_RE.match(r.get("開始日", "")) and _DATE_RE.match(r.get("終了予定日", "")))
    ]
    results.append(_hyp(
        "H7", "未完了タスクは開始日・終了予定日をYYYY-MM-DD形式で両方保有",
        not bad_dates, f"日付欠落/不正={bad_dates or 'なし'}"))

    inverted = inverted_schedule_rows(rows)
    results.append(_hyp(
        "H8", "全行で開始日<=終了予定日(日程の逆転なし)",
        not inverted, f"逆転={inverted or 'なし'}"))

    has_gate = _covered(rows, COMPLETION_GATE_KEYWORDS)
    results.append(_hyp(
        "H9", "開発完了の総合判定ゲート(全WBS完了を束ねる最終判定)が存在",
        has_gate, f"完成判定ゲート={'あり' if has_gate else 'なし'}"))

    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp(
        "H10", "WBS全体が完全・整合(ライフサイクル/日程ギャップ0)",
        no_prior_drift, f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))

    return results


def run_audit() -> dict[str, Any]:
    header, rows = load_rows()
    hypotheses = evaluate(header, rows)
    return {
        "task": "T889",
        "wbs_path": str(WBS_PATH.relative_to(PROJECT_ROOT)),
        "task_count": len(rows),
        "uncovered_stages": uncovered_stages(rows),
        "uncovered_stack": uncovered_stack(rows),
        "inverted_schedule": inverted_schedule_rows(rows),
        "hypotheses": hypotheses,
        "all_passed": all(h["passed"] for h in hypotheses),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# WBSライフサイクル網羅性・日程整合監査 (T889)",
        "",
        f"- 対象: `{report['wbs_path']}`",
        f"- タスク数: **{report['task_count']}**",
        f"- 未網羅工程: {report['uncovered_stages'] or 'なし'}",
        f"- 未網羅スタック: {report['uncovered_stack'] or 'なし'}",
        f"- 日程逆転: {report['inverted_schedule'] or 'なし'}",
        f"- 総合判定: {'✅ PASS (ギャップ0)' if report['all_passed'] else '❌ FAIL'}",
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
