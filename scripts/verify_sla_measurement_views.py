"""Offline verification for the T778 SLA measurement views + report logic (T778_1).

T778 built the SLA measurement foundation (uptime_checks table, 6 KPI views,
recorder, report generator). Applying the migration to production Supabase is a
human/credentialed step. This harness owns the *offline verification* half so it
can run in CI without SUPABASE_DB_URL:

1. Schema-drift guard: every column each SLA view depends on must still exist in
   the committed migration schema. This is the exact failure class the project
   already hit (profiles.last_login did not exist -> WAU redesigned; R114/R117
   missing tables), so it must be caught before a prod apply, not after.
2. SLA threshold logic: the report generator's evaluate() (availability >= 99.5%,
   P95 <= 3000ms, helpful >= 70%) is verified against synthetic PASS/FAIL/NO-DATA
   fixtures — it drives the Go/No-Go and monthly quality pipeline.

Outputs: exports/sla_view_verification.{json,md}. No DB, no secrets.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = PROJECT_ROOT / "supabase" / "migrations"
SLA_MIGRATION = MIGRATIONS_DIR / "20260705000000_sla_measurement_views.sql"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "sla_view_verification.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "sla_view_verification.md"

# Declarative contract: each SLA view and the (table -> columns) it depends on.
# Derived from supabase/migrations/20260705000000_sla_measurement_views.sql.
# The schema-drift guard checks every column below still exists in the migrations.
VIEW_DEPENDENCIES: dict[str, dict[str, list[str]]] = {
    "kpi_daily_diagnoses": {"matches": ["created_at", "user_id", "fit_score"]},
    "kpi_weekly_active_users": {"matches": ["created_at", "user_id"]},
    "kpi_weekly_anonymous_sessions": {"usage_analytics_events": ["created_at", "session_pseudonym"]},
    "kpi_monthly_availability": {"uptime_checks": ["checked_at", "target_id", "status"]},
    "kpi_daily_response_time": {"uptime_checks": ["checked_at", "target_id", "response_ms"]},
    "kpi_weekly_diagnosis_accuracy": {"feedback_events": ["created_at", "rating"]},
}


def _load_report_module():
    spec = importlib.util.spec_from_file_location(
        "generate_sla_measurement_report", PROJECT_ROOT / "scripts" / "generate_sla_measurement_report.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_schema_columns() -> dict[str, set[str]]:
    """Build {table: {columns}} from all migration CREATE TABLE / ALTER TABLE ADD."""
    tables: dict[str, set[str]] = {}
    create_re = re.compile(
        r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(?:public\.)?(\w+)\s*\((.*?)\n\)\s*;",
        re.IGNORECASE | re.DOTALL,
    )
    alter_re = re.compile(
        r"ALTER TABLE(?:\s+IF EXISTS)?\s+(?:public\.)?(\w+)\s+ADD COLUMN(?:\s+IF NOT EXISTS)?\s+(\w+)",
        re.IGNORECASE,
    )
    reserved = {
        "constraint", "primary", "foreign", "unique", "check", "create", "using",
        "references", "on", "default",
    }
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        text = sql_file.read_text(encoding="utf-8")
        for table, body in create_re.findall(text):
            cols = tables.setdefault(table.lower(), set())
            for raw_line in body.splitlines():
                line = raw_line.strip().strip(",")
                if not line:
                    continue
                first = line.split()[0].lower()
                if first in reserved or first.startswith("--"):
                    continue
                if re.match(r"^[a-z_][a-z0-9_]*$", first):
                    cols.add(first)
        for table, column in alter_re.findall(text):
            tables.setdefault(table.lower(), set()).add(column.lower())
    return tables


def build_hypotheses(schema: dict[str, set[str]], report_mod) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def record(hid: str, statement: str, check: Callable[[], tuple[bool, str]]) -> None:
        try:
            passed, detail = check()
        except Exception as exc:
            passed, detail = False, f"例外: {type(exc).__name__}: {exc}"
        results.append({"id": hid, "hypothesis": statement, "passed": passed, "detail": detail})

    # H1-H6: each view's dependency columns exist in the committed schema.
    view_items = list(VIEW_DEPENDENCIES.items())
    for i, (view, deps) in enumerate(view_items, start=1):
        def make_check(view=view, deps=deps):
            def check() -> tuple[bool, str]:
                missing = []
                for table, cols in deps.items():
                    have = schema.get(table, set())
                    if not have:
                        missing.append(f"{table}(テーブル未定義)")
                        continue
                    for col in cols:
                        if col not in have:
                            missing.append(f"{table}.{col}")
                ok = not missing
                dep_str = ", ".join(f"{t}({'/'.join(c)})" for t, c in deps.items())
                return ok, f"{dep_str} → {'全列存在' if ok else '欠落: ' + ', '.join(missing)}"

            return check

        record(f"H{i}", f"ビュー {view} が参照する列がスキーマに存在する", make_check())

    # H7: evaluate() PASSes when all metrics meet targets.
    def h7() -> tuple[bool, str]:
        views = {
            "kpi_monthly_availability": [{"availability_pct": 99.9}, {"availability_pct": 99.6}],
            "kpi_daily_response_time": [{"p95_ms": 1200.0}, {"p95_ms": 2800.0}],
            "kpi_weekly_diagnosis_accuracy": [{"helpful_pct": 82.0}],
        }
        checks = report_mod.evaluate(views)
        by = {c["metric"].split()[0]: c for c in checks}
        ok = all(c["pass"] is True for c in checks)
        return ok, f"availability={by['availability_pct']['pass']} p95={by['p95_ms']['pass']} helpful={by['helpful_pct']['pass']}"

    record("H7", "evaluate(): 全指標が目標達成のときPASS判定になる", h7)

    # H8: evaluate() FAILs on any breach (availability<99.5, p95>3000, helpful<70).
    def h8() -> tuple[bool, str]:
        views = {
            "kpi_monthly_availability": [{"availability_pct": 99.9}, {"availability_pct": 98.0}],
            "kpi_daily_response_time": [{"p95_ms": 1200.0}, {"p95_ms": 3500.0}],
            "kpi_weekly_diagnosis_accuracy": [{"helpful_pct": 61.0}],
        }
        checks = report_mod.evaluate(views)
        fails = {c["metric"].split()[0] for c in checks if c["pass"] is False}
        ok = fails == {"availability_pct", "p95_ms", "helpful_pct"}
        return ok, f"FAIL検出={sorted(fails)}（3指標全てFAIL期待）"

    record("H8", "evaluate(): 目標未達（可用性/遅延/精度）を全てFAILとして検出する", h8)

    # H9: evaluate() handles empty views as NO-DATA (pass is None), not a crash.
    def h9() -> tuple[bool, str]:
        checks = report_mod.evaluate({})
        ok = len(checks) == 3 and all(c["pass"] is None for c in checks)
        return ok, f"NO-DATA件数={sum(1 for c in checks if c['pass'] is None)}/3"

    record("H9", "evaluate(): データ無しでも例外にならずNO-DATAを返す", h9)

    # H10: report generator refuses to run without SUPABASE_DB_URL, and its
    # targets match the pilot SLA definition.
    def h10() -> tuple[bool, str]:
        import os

        prev = os.environ.pop("SUPABASE_DB_URL", None)
        try:
            rc = report_mod.main()
        finally:
            if prev is not None:
                os.environ["SUPABASE_DB_URL"] = prev
        targets = report_mod.TARGETS
        ok = rc == 1 and targets["availability_pct_pilot"] == 99.5 and targets["p95_ms"] == 3000 and targets["helpful_pct"] == 70.0
        return ok, f"SUPABASE_DB_URL無しの戻り値={rc}(1期待) targets={targets}"

    record("H10", "レポート生成は認証情報無しで安全に停止し、目標値がpilot SLA定義と一致する", h10)

    return results


def build_report(checked_at: str) -> dict[str, Any]:
    schema = parse_schema_columns()
    report_mod = _load_report_module()
    hypotheses = build_hypotheses(schema, report_mod)
    passed = sum(1 for h in hypotheses if h["passed"])
    return {
        "report_id": "SLA_VIEW_VERIFICATION_T778_1",
        "checked_at": checked_at,
        "status": "ok" if passed == len(hypotheses) else "attention",
        "hypotheses_total": len(hypotheses),
        "hypotheses_passed": passed,
        "hypotheses": hypotheses,
        "tables_parsed": {t: sorted(c) for t, c in sorted(schema.items())},
        "scope_note": "オフラインのビュー/レポート検証。本番Supabaseへのmigration適用と実データでのビュー検証はSUPABASE_DB_URL必須の人間工程（T778本体）。",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# SLA計測ビュー オフライン検証ログ (T778_1)",
        "",
        f"- レポートID: `{report['report_id']}`",
        f"- 実施日: {report['checked_at']}",
        f"- 判定: **{report['status']}** ({report['hypotheses_passed']}/{report['hypotheses_total']} 仮説PASS)",
        f"- スコープ: {report['scope_note']}",
        "",
        "## 10仮説検証",
        "",
        "| # | 仮説 | 結果 | 根拠 |",
        "| --- | --- | --- | --- |",
    ]
    for h in report["hypotheses"]:
        mark = "PASS" if h["passed"] else "FAIL"
        lines.append(f"| {h['id']} | {h['hypothesis']} | {mark} | {h['detail'].replace('|', '/')} |")
    lines += [
        "",
        "## 残作業（T778本体・人間/認証情報依存）",
        "",
        "- 本番Supabaseへの `supabase/migrations/20260705000000_sla_measurement_views.sql` 適用（`SUPABASE_DB_URL` 必須の運用者工程）。",
        "- 実データでの `python scripts/generate_sla_measurement_report.py` 実行とSLA/KPIレポートのSheets同期（T764/T808パイプライン）。",
        "- `scripts/check_uptime_targets.py --record-db` による稼働サンプルの継続蓄積。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline SLA view + report verification (T778_1)")
    parser.add_argument("--checked-at", default="2026-07-08")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--fail-on-attention", action="store_true")
    args = parser.parse_args()

    report = build_report(args.checked_at)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"[*] Wrote {args.json_out}")
    print(f"[*] Wrote {args.md_out}")
    print(
        f"[{'+' if report['status'] == 'ok' else '!'}] SLA view verification {report['status']}: "
        f"{report['hypotheses_passed']}/{report['hypotheses_total']} hypotheses passed"
    )
    if args.fail_on_attention and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
