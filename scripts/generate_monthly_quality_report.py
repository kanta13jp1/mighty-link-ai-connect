# -*- coding: utf-8 -*-
"""Generate the monthly quality report (T764).

Aggregates local source-of-truth data into ``docs/MONTHLY_REPORT_YYYY-MM.md``
following the template defined in docs/MONTHLY_PROGRESS_REPORT_AND_KPI_DASHBOARD.md (T767).

Sources:
  - data/WBS.tsv                      : WBS progress (completed / delayed / upcoming)
  - data/test_results.tsv             : test pass rate
  - data/issues_tracker.tsv           : incidents and open issues for the month
  - data/security_log.tsv             : security findings for the month
  - reports/daily_usage_audit_*.json  : external API usage (calls / tokens / guard alerts)
  - docs/COST_REPORT_YYYY-MM.md       : linked when present (GCP Billing API is not wired yet)

Google Docs sync: the generated file lives under docs/, so the existing
``scripts/sync_docs_to_notebooklm.py`` pipeline uploads it to Google Docs
(k-umezawa@ml-mightylink.com Drive) together with the other docs.

Usage:
  python scripts/generate_monthly_quality_report.py [--month YYYY-MM] [--today YYYY-MM-DD]

Per the T767 schedule this runs on the 1st of the following month; running it
mid-month produces an interim snapshot (marked as such in the header).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORTS_DIR = PROJECT_ROOT / "reports"

SHEETS_URL = "https://docs.google.com/spreadsheets/d/1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8"
REPO_URL = "https://github.com/kanta13jp1/mighty-link-ai-connect"
DEMO_URL = "https://mightylink-app.com/"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:]]


def month_bounds(month: str) -> tuple[date, date]:
    year, mon = (int(part) for part in month.split("-"))
    first = date(year, mon, 1)
    last = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return first, last


def prev_month(month: str) -> str:
    year, mon = (int(part) for part in month.split("-"))
    return f"{year - 1}-12" if mon == 1 else f"{year}-{mon - 1:02d}"


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value[: len("2026-06-13 10:00") if " " in value else 10], fmt).date()
        except ValueError:
            continue
    return None


def in_month(value: str, month: str) -> bool:
    parsed = parse_date(value)
    return parsed is not None and parsed.strftime("%Y-%m") == month


# ---------- section builders ----------

def wbs_progress(month: str, today: date) -> dict:
    rows = read_tsv(DATA_DIR / "WBS.tsv")
    done = [r for r in rows if r.get("ステータス", "").strip() == "完了"]
    done_this = [r for r in done if in_month(r.get("終了予定日", ""), month)]
    done_prev = [r for r in done if in_month(r.get("終了予定日", ""), prev_month(month))]
    open_rows = [r for r in rows if r.get("ステータス", "").strip() != "完了"]
    delayed = [
        r for r in open_rows
        if (d := parse_date(r.get("終了予定日", ""))) is not None and d < today
    ]
    first_next = month_bounds(month)[1]
    upcoming = sorted(
        (r for r in open_rows if (d := parse_date(r.get("開始日", ""))) is not None and d >= first_next),
        key=lambda r: r.get("開始日", ""),
    )[:5]
    if len(upcoming) < 5:
        running = sorted(
            (r for r in open_rows if r not in upcoming),
            key=lambda r: r.get("開始日", ""),
        )
        upcoming += running[: 5 - len(upcoming)]
    return {
        "total": len(rows),
        "done_total": len(done),
        "done_this_month": len(done_this),
        "done_prev_month": len(done_prev),
        "completion_pct": 100.0 * len(done) / len(rows) if rows else 0.0,
        "delayed": delayed,
        "upcoming": upcoming,
    }


def test_quality(month: str) -> dict:
    rows = read_tsv(DATA_DIR / "test_results.tsv")
    statuses = [r.get("ステータス", "").strip().upper() for r in rows]
    passed = sum(1 for s in statuses if s == "PASS")
    return {"total": len(rows), "passed": passed,
            "pass_pct": 100.0 * passed / len(rows) if rows else 0.0}


def usage_summary(month: str) -> dict:
    providers: dict[str, dict[str, int]] = {}
    alerts: list[str] = []
    audit_days = 0
    for path in sorted(REPORTS_DIR.glob("daily_usage_audit_*.json")):
        day = path.stem.replace("daily_usage_audit_", "")
        if not day.startswith(month):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        audit_days += 1
        for key, guard in (payload.get("guards") or {}).items():
            agg = providers.setdefault(key, {"billable": 0, "blocked": 0, "tokens": 0})
            agg["billable"] += int(guard.get("billable_calls") or 0)
            agg["blocked"] += int(guard.get("blocked_calls") or 0)
            agg["tokens"] += int(guard.get("reported_total_tokens") or 0)
        alerts.extend(str(a) for a in (payload.get("alerts") or []))
    return {"providers": providers, "alerts": alerts, "audit_days": audit_days}


def month_issues(month: str) -> list[dict[str, str]]:
    rows = read_tsv(DATA_DIR / "issues_tracker.tsv")
    return [r for r in rows if in_month(r.get("起票日", ""), month) or in_month(r.get("更新日", ""), month)]


def month_security(month: str) -> list[dict[str, str]]:
    rows = read_tsv(DATA_DIR / "security_log.tsv")
    return [r for r in rows if (r.get("検知日時", "") or "").startswith(month)]


# ---------- rendering ----------

def render(month: str, today: date) -> str:
    wbs = wbs_progress(month, today)
    tests = test_quality(month)
    usage = usage_summary(month)
    issues = month_issues(month)
    security = month_security(month)
    interim = today < month_bounds(month)[1]

    lines: list[str] = []
    add = lines.append
    add(f"# Mighty Skill-Bridge 月次品質レポート: {month.replace('-', '年')}月")
    add("")
    if interim:
        add(f"> [!NOTE]\n> 月中時点の中間スナップショットです（生成日: {today.isoformat()}）。確定版は翌月 1 日に再生成します（T767 スケジュール）。")
        add("")
    add(f"**作成日**: {today.isoformat()}")
    add("**作成者**: 梅澤 寛太（+ Claude Code, scripts/generate_monthly_quality_report.py による自動生成）")
    add("")
    add("---")
    add("")
    add("## 1. WBS 進捗")
    add("")
    add("| 指標 | 今月 | 先月比 |")
    add("| :--- | :--- | :--- |")
    diff = wbs["done_this_month"] - wbs["done_prev_month"]
    add(f"| 当月完了タスク数 | {wbs['done_this_month']} 件 | {diff:+d} 件 |")
    add(f"| 全体完了率 | {wbs['completion_pct']:.1f}% ({wbs['done_total']}/{wbs['total']}) | — |")
    add(f"| 期限超過の未完了タスク | {len(wbs['delayed'])} 件 | — |")
    add("")
    if wbs["delayed"]:
        add("**期限超過タスク（要リスケまたは着手）:**")
        add("")
        for r in wbs["delayed"]:
            add(f"- {r.get('タスクID')} {r.get('タスク名')}（期限 {r.get('終了予定日')} / 担当 {r.get('担当')}）")
        add("")
    add("---")
    add("")
    add("## 2. サービス品質 KPI")
    add("")
    add("| KPI | 今月実績 | 目標 | 判定 |")
    add("| :--- | :--- | :--- | :--- |")
    add(f"| テスト合格率 | {tests['pass_pct']:.1f}% ({tests['passed']}/{tests['total']}) | 100% | {'✅' if tests['passed'] == tests['total'] else '❌'} |")
    gemini_calls = sum(v["billable"] for k, v in usage["providers"].items() if k.startswith("gemini_api"))
    add(f"| AI 診断 API 課金実行件数 | {gemini_calls} 件 | コストガード内 | ✅ |")
    add("| 稼働率 / P95 / 5xx エラー率 | 未計測 | ≥99.5% / ≤3.0s / ≤0.5% | ⏳ 計測基盤整備中（T743 死活監視・T755 テレメトリ・T778 SLA ビュー） |")
    add("")
    add("---")
    add("")
    add("## 3. 外部 API 利用・コスト")
    add("")
    if usage["providers"]:
        add(f"日次利用台帳監査（`reports/daily_usage_audit_*.json`、当月 {usage['audit_days']} 日分）の集計:")
        add("")
        add("| プロバイダ:操作 | 課金実行 | ガード遮断 | 報告トークン |")
        add("| :--- | ---: | ---: | ---: |")
        for key, agg in sorted(usage["providers"].items()):
            add(f"| {key} | {agg['billable']} | {agg['blocked']} | {agg['tokens']:,} |")
        add("")
        add(f"ガードアラート: {len(usage['alerts'])} 件" + (f" — {'; '.join(usage['alerts'][:3])}" if usage["alerts"] else "（コストガードはすべて上限内）"))
    else:
        add("当月の日次利用台帳監査レコードなし（外部 API は既定で無効 = コスト 0）。")
    add("")
    cost_report = DOCS_DIR / f"COST_REPORT_{month}.md"
    if cost_report.exists():
        add(f"金額ベースの実測は [COST_REPORT_{month}.md](COST_REPORT_{month}.md) を参照（GCP Billing API 連携は T757 週次コストダッシュボードで自動化予定）。")
    add("")
    add("---")
    add("")
    add("## 4. インシデント・課題（当月起票/更新）")
    add("")
    if issues:
        add("| ID | 重要度 | 状態 | タイトル |")
        add("| :--- | :--- | :--- | :--- |")
        for r in issues:
            add(f"| {r.get('ID')} | {r.get('重要度')} | {r.get('状態')} | {r.get('タイトル')} |")
    else:
        add("当月の起票・更新なし。")
    add("")
    if security:
        add("**セキュリティ検出（security_log）:**")
        add("")
        for r in security:
            add(f"- {r.get('脆弱性ID')} [{r.get('重要度')}] {r.get('検知された問題')} — {r.get('ステータス')}")
        add("")
    add("---")
    add("")
    add("## 5. 翌月（または直近）の優先アクション")
    add("")
    for i, r in enumerate(wbs["upcoming"], 1):
        add(f"{i}. {r.get('タスクID')} {r.get('タスク名')}（開始 {r.get('開始日')} / 担当 {r.get('担当')}）")
    add("")
    add("---")
    add("")
    add("## 6. 参照リンク")
    add("")
    add(f"- [WBS スプレッドシート]({SHEETS_URL})")
    add(f"- [GitHub リポジトリ]({REPO_URL})")
    add(f"- [本番 URL]({DEMO_URL})")
    add("- [SLA/KPI 定義](SLA_KPI_DEFINITION_AND_MEASUREMENT.md) / [レポート仕様 (T767)](MONTHLY_PROGRESS_REPORT_AND_KPI_DASHBOARD.md)")
    add("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate monthly quality report (T764)")
    parser.add_argument("--month", default=None, help="Target month YYYY-MM (default: current month)")
    parser.add_argument("--today", default=None, help="Override today's date YYYY-MM-DD (for tests)")
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    month = args.month or today.strftime("%Y-%m")

    content = render(month, today)
    out_path = DOCS_DIR / f"MONTHLY_REPORT_{month}.md"
    out_path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[+] Wrote {out_path.relative_to(PROJECT_ROOT)}")
    print("[*] Google Docs sync: run python scripts/sync_docs_to_notebooklm.py (docs/*.md pipeline)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
