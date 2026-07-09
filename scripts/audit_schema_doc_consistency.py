"""Schema <-> documentation drift guard (T880).

`docs/database.md` is the canonical data-model document, but it had drifted to
the T102 (2026-05-22) state: three tables (engineers/jobs/match_results) and an
"IndexedDB / browser-completed" narrative, while production now runs Firebase
Auth + Supabase PostgreSQL 17.6 with 23 tables and 6 SLA KPI views defined
across `supabase/migrations` (the Supabase source of truth) and
`db/migrations` (the app-runtime schema).

After R114/R117 (missing production tables caused by migration drift) the risk
this harness guards is the *documentation* silently diverging from the schema
the migrations actually define. It parses every schema source, parses the
machine-readable inventory embedded in `docs/database.md`, and verifies ten
hypotheses. Output: exports/schema_doc_consistency_audit.{json,md}. No secrets.

Canonical rule (Supabase official docs, 2026-07 refresh): migration files are
the single source of truth and every table in an exposed (public) schema must
have RLS enabled.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = PROJECT_ROOT / "docs" / "database.md"
SUPABASE_DIR = PROJECT_ROOT / "supabase" / "migrations"
APP_RUNTIME_DIR = PROJECT_ROOT / "db" / "migrations" / "postgres"
APP_PY = PROJECT_ROOT / "src" / "app.py"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "schema_doc_consistency_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "schema_doc_consistency_audit.md"

# Legacy app-runtime tables that live only in db/migrations (not supabase/migrations).
LEGACY_APP_TABLES = {"engineers", "jobs", "match_results"}

# Objects defined in the repo but not yet applied to the production Supabase DB.
# uptime_checks + the six KPI views are added by 20260705000000_sla_measurement_views
# and applied to prod only when T778's human step (SUPABASE_DB_URL) runs.
PENDING_PROD_OBJECTS = {
    "uptime_checks",
    "kpi_daily_diagnoses",
    "kpi_weekly_active_users",
    "kpi_weekly_anonymous_sessions",
    "kpi_monthly_availability",
    "kpi_daily_response_time",
    "kpi_weekly_diagnosis_accuracy",
}

# Phrases from the stale T102 narrative that must not survive in the current doc.
STALE_MARKERS = [
    "IndexedDB",
    "外部サーバーなしでの爆速動作",
    "ブラウザ完結",
    "超軽量なバックエンド構築を想定",
]

# Canonical schema sources the doc must point readers at.
CANONICAL_SOURCE_REFS = [
    "supabase/migrations",
    "db/migrations",
    "DB_MIGRATION_MANAGEMENT_RUNBOOK",
]

INVENTORY_START = "<!-- SCHEMA-INVENTORY:START -->"
INVENTORY_END = "<!-- SCHEMA-INVENTORY:END -->"

_TABLE_RE = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?([\w.\"'`]+)\s*\(",
    re.IGNORECASE,
)
_VIEW_RE = re.compile(
    r"create\s+(?:or\s+replace\s+)?view\s+([\w.\"'`]+)",
    re.IGNORECASE,
)
_RLS_RE = re.compile(
    r"alter\s+table\s+(?:if\s+exists\s+)?([\w.\"'`]+)\s+enable\s+row\s+level\s+security",
    re.IGNORECASE,
)


def _clean_identifier(raw: str) -> str:
    """Strip quotes/backticks and any schema prefix, returning the bare name."""
    cleaned = raw.replace('"', "").replace("'", "").replace("`", "")
    return cleaned.split(".")[-1].strip().lower()


def parse_sql_tables(sql_text: str) -> set[str]:
    return {_clean_identifier(m) for m in _TABLE_RE.findall(sql_text)}


def parse_sql_views(sql_text: str) -> set[str]:
    return {_clean_identifier(m) for m in _VIEW_RE.findall(sql_text)}


def parse_rls_enabled_tables(sql_text: str) -> set[str]:
    return {_clean_identifier(m) for m in _RLS_RE.findall(sql_text)}


def _read_dir_sql(directory: Path) -> str:
    if not directory.exists():
        return ""
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(directory.glob("*.sql"))
    )


def parse_documented_inventory(md_text: str) -> dict[str, set[str]]:
    r"""Parse the machine-readable inventory block embedded in database.md.

    Only identifiers inside the SCHEMA-INVENTORY markers count. Each markdown
    row is `| \`name\` | 種別 | ... | 本番反映 |`; 種別 selects table vs view and
    a 本番反映 cell containing '適用待ち' marks the object as pending prod.
    """
    tables: set[str] = set()
    views: set[str] = set()
    pending: set[str] = set()

    start = md_text.find(INVENTORY_START)
    end = md_text.find(INVENTORY_END)
    if start == -1 or end == -1 or end < start:
        return {"tables": tables, "views": views, "pending": pending}

    block = md_text[start + len(INVENTORY_START) : end]
    name_re = re.compile(r"`([A-Za-z_][\w]*)`")
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        m = name_re.search(line)
        if not m:
            continue  # header / separator rows carry no backticked identifier
        name = m.group(1).lower()
        is_view = "ビュー" in line
        if is_view:
            views.add(name)
        else:
            tables.add(name)
        if "適用待ち" in line:
            pending.add(name)
    return {"tables": tables, "views": views, "pending": pending}


def collect_authoritative() -> dict[str, Any]:
    """Compute the authoritative schema picture from all migration sources."""
    supabase_sql = _read_dir_sql(SUPABASE_DIR)
    app_runtime_sql = _read_dir_sql(APP_RUNTIME_DIR)
    app_py_text = APP_PY.read_text(encoding="utf-8", errors="replace") if APP_PY.exists() else ""

    supabase_tables = parse_sql_tables(supabase_sql)
    supabase_views = parse_sql_views(supabase_sql)
    app_runtime_tables = parse_sql_tables(app_runtime_sql)
    initdb_tables = parse_sql_tables(app_py_text)
    rls_tables = parse_rls_enabled_tables(
        "\n".join([supabase_sql, app_runtime_sql, app_py_text])
    )

    authoritative_tables = supabase_tables | app_runtime_tables

    return {
        "supabase_tables": supabase_tables,
        "supabase_views": supabase_views,
        "app_runtime_tables": app_runtime_tables,
        "initdb_tables": initdb_tables,
        "rls_tables": rls_tables,
        "authoritative_tables": authoritative_tables,
        "pending": set(PENDING_PROD_OBJECTS),
    }


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(schema: dict[str, Any], documented: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate the ten schema<->doc consistency hypotheses (pure function)."""
    doc_tables = set(documented.get("tables", set()))
    doc_views = set(documented.get("views", set()))
    doc_pending = set(documented.get("pending", set()))
    text = documented.get("text", "")

    results: list[dict[str, Any]] = []

    missing_sb = schema["supabase_tables"] - doc_tables
    results.append(_hyp(
        "H1", "Supabase本番migration定義の全テーブルがdatabase.mdに記載",
        not missing_sb, f"未記載: {sorted(missing_sb) or 'なし'}"))

    legacy = LEGACY_APP_TABLES & schema["app_runtime_tables"]
    missing_legacy = legacy - doc_tables
    results.append(_hyp(
        "H2", "アプリ実行時legacyテーブル(engineers/jobs/match_results)が記載",
        not missing_legacy, f"未記載: {sorted(missing_legacy) or 'なし'}"))

    phantom = doc_tables - schema["authoritative_tables"]
    results.append(_hyp(
        "H3", "database.md記載テーブルは全て実スキーマソースに存在(phantom 0)",
        not phantom, f"phantom: {sorted(phantom) or 'なし'}"))

    missing_views = schema["supabase_views"] - doc_views
    results.append(_hyp(
        "H4", "6つのSLA KPIビュー(kpi_*)が記載",
        not missing_views, f"未記載ビュー: {sorted(missing_views) or 'なし'}"))

    orphan = schema["initdb_tables"] - schema["authoritative_tables"]
    results.append(_hyp(
        "H5", "init_db作成テーブルは全て正規migrationソースにも定義(未管理0)",
        not orphan, f"未管理init_dbテーブル: {sorted(orphan) or 'なし'}"))

    stale = [m for m in STALE_MARKERS if m in text]
    results.append(_hyp(
        "H6", "旧アーキ(IndexedDB等)のstale記述が除去済み",
        not stale, f"残存stale語: {stale or 'なし'}"))

    missing_refs = [r for r in CANONICAL_SOURCE_REFS if r not in text]
    results.append(_hyp(
        "H7", "正本ソース(supabase/migrations・db/migrations・Runbook)を明示参照",
        not missing_refs, f"未参照: {missing_refs or 'なし'}"))

    pending_unmarked = schema["pending"] - doc_pending
    results.append(_hyp(
        "H8", "本番未適用(uptime_checks+6ビュー, T778)が『適用待ち』と明記",
        not pending_unmarked, f"未マーク: {sorted(pending_unmarked) or 'なし'}"))

    rls_undoc = schema["rls_tables"] - doc_tables
    rls_mentioned = ("RLS" in text) or ("Row Level Security" in text)
    results.append(_hyp(
        "H9", "RLS記述があり、RLS有効化された全テーブルが記載(公式: public全表RLS必須)",
        (not rls_undoc) and rls_mentioned,
        f"未記載RLS表: {sorted(rls_undoc) or 'なし'} / RLS言及: {rls_mentioned}"))

    counts_ok = (
        len(doc_tables) == len(schema["authoritative_tables"])
        and len(doc_views) == len(schema["supabase_views"])
    )
    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp(
        "H10",
        "総テーブル数(23)・ビュー数(6)がdocと算出値で一致し、ドリフト0",
        counts_ok and no_prior_drift,
        f"doc表数={len(doc_tables)}/正本={len(schema['authoritative_tables'])}, "
        f"docビュー数={len(doc_views)}/正本={len(schema['supabase_views'])}, "
        f"先行ドリフト={'なし' if no_prior_drift else 'あり'}"))

    return results


def run_audit() -> dict[str, Any]:
    schema = collect_authoritative()
    doc_text = DOC_PATH.read_text(encoding="utf-8", errors="replace") if DOC_PATH.exists() else ""
    documented = parse_documented_inventory(doc_text)
    documented["text"] = doc_text

    hypotheses = evaluate(schema, documented)
    all_passed = all(h["passed"] for h in hypotheses)

    return {
        "task": "T880",
        "doc_path": str(DOC_PATH.relative_to(PROJECT_ROOT)),
        "authoritative_table_count": len(schema["authoritative_tables"]),
        "authoritative_view_count": len(schema["supabase_views"]),
        "documented_table_count": len(documented["tables"]),
        "documented_view_count": len(documented["views"]),
        "pending_prod_objects": sorted(schema["pending"]),
        "authoritative_tables": sorted(schema["authoritative_tables"]),
        "supabase_views": sorted(schema["supabase_views"]),
        "hypotheses": hypotheses,
        "all_passed": all_passed,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# スキーマ⇔ドキュメント整合監査 (T880)",
        "",
        f"- 対象ドキュメント: `{report['doc_path']}`",
        f"- 正本テーブル数: **{report['authoritative_table_count']}** / "
        f"記載: {report['documented_table_count']}",
        f"- 正本ビュー数: **{report['authoritative_view_count']}** / "
        f"記載: {report['documented_view_count']}",
        f"- 本番適用待ち: {', '.join(report['pending_prod_objects'])}",
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    parser.add_argument("--md", default=str(DEFAULT_MD))
    args = parser.parse_args()

    report = run_audit()

    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")

    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
