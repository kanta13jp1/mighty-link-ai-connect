"""Foreign-key index coverage guard (T881).

PostgreSQL creates indexes automatically only for PRIMARY KEY and UNIQUE
constraints — never for foreign-key columns. Unindexed FKs are a well-known
performance defect: joins fall back to sequential scans, and ON DELETE
CASCADE / SET NULL parent deletes must full-scan every referencing child table
(directly affecting this project's data-retention/deletion flow, T847).

Supabase's Database Performance Advisor flags "unindexed foreign keys" and
recommends a btree index per FK column (2026-07 docs refresh:
`create index ix_child_parent_id on child(parent_id)`).

Scope: the Supabase product schema (`supabase/migrations`), which holds the
RLS-protected, actively-joined tables (core diagnosis + sales-email matching +
HR + analytics). The legacy app-runtime tables (engineers/jobs/match_results in
`db/migrations`) are low-traffic PoC-compat tables and out of scope here.

The harness parses FK columns and btree/UNIQUE/PK index coverage, verifies ten
hypotheses, and confirms the fix migration
(supabase/migrations/20260709000000_fk_covering_indexes.sql) closes every gap
additively and idempotently. Output: exports/fk_index_coverage_audit.{json,md}.
No secrets.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPABASE_DIR = PROJECT_ROOT / "supabase" / "migrations"
FK_INDEX_MIGRATION = SUPABASE_DIR / "20260709000000_fk_covering_indexes.sql"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "fk_index_coverage_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "fk_index_coverage_audit.md"

# The FK columns that had no covering index before T881 (the fix targets).
EXPECTED_TARGET_GAPS = [
    ("audits", "match_id"),
    ("sales_email_messages", "mailbox_source_id"),
    ("sales_email_messages", "duplicate_of_id"),
    ("project_requirements", "message_id"),
    ("talent_profiles_from_email", "message_id"),
    ("requirement_skill_tags", "project_requirement_id"),
    ("requirement_skill_tags", "talent_profile_id"),
    ("email_parse_runs", "mailbox_source_id"),
    ("email_match_results", "project_requirement_id"),
    ("email_match_results", "talent_profile_id"),
    ("email_match_feedback", "match_result_id"),
]

_CREATE_TABLE_RE = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?[\"']?(\w+)[\"']?\s*\((.*?)\n\s*\)\s*;",
    re.IGNORECASE | re.DOTALL,
)
_INDEX_RE = re.compile(
    r"create\s+index\s+(if\s+not\s+exists\s+)?(\w+)\s+on\s+(?:public\.)?(\w+)\s*"
    r"(?:using\s+(\w+)\s*)?\(([^)]*)\)",
    re.IGNORECASE,
)
_FK_CONSTRAINT_RE = re.compile(r"foreign\s+key\s*\(\s*(\w+)", re.IGNORECASE)
_SKIP_LINE_PREFIXES = ("constraint", "foreign", "primary", "unique", "check")


def _read_supabase_sql() -> str:
    if not SUPABASE_DIR.exists():
        return ""
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(SUPABASE_DIR.glob("*.sql"))
    )


def _iter_table_blocks(sql_text: str):
    for m in _CREATE_TABLE_RE.finditer(sql_text):
        yield m.group(1).lower(), m.group(2)


def parse_fk_columns(sql_text: str) -> dict[str, set[str]]:
    """Extract FK columns per table (both inline REFERENCES and CONSTRAINT styles)."""
    fk: dict[str, set[str]] = {}
    for table, body in _iter_table_blocks(sql_text):
        cols: set[str] = set()
        for raw in body.splitlines():
            line = raw.strip()
            if "references" not in line.lower():
                continue
            constraint = _FK_CONSTRAINT_RE.search(line)
            if constraint:
                cols.add(constraint.group(1).lower())
            elif not line.lower().startswith(_SKIP_LINE_PREFIXES):
                token = re.match(r"(\w+)", line)
                if token:
                    cols.add(token.group(1).lower())
        if cols:
            fk[table] = cols
    return fk


def parse_index_statements(sql_text: str) -> list[dict[str, Any]]:
    """Parse each CREATE INDEX into name/table/leftmost/if_not_exists/using/is_plain."""
    out: list[dict[str, Any]] = []
    for m in _INDEX_RE.finditer(sql_text):
        ine = bool(m.group(1))
        name = m.group(2).lower()
        table = m.group(3).lower()
        using = (m.group(4) or "btree").lower()
        first = m.group(5).split(",")[0].strip()
        first = re.sub(r"\s+(asc|desc)$", "", first, flags=re.IGNORECASE).strip()
        is_plain = bool(re.fullmatch(r"\w+", first))
        out.append({
            "name": name,
            "table": table,
            "leftmost": first.lower() if is_plain else first,
            "if_not_exists": ine,
            "using": using,
            "is_plain": is_plain,
            "is_btree": using == "btree" and is_plain,
        })
    return out


def parse_btree_leftmost(sql_text: str) -> dict[str, set[str]]:
    """Leftmost plain-column of every btree index (GIN/GiST and expressions excluded)."""
    left: dict[str, set[str]] = {}
    for idx in parse_index_statements(sql_text):
        if idx["using"] == "btree" and idx["is_plain"]:
            left.setdefault(idx["table"], set()).add(idx["leftmost"])
    return left


def parse_unique_single_columns(sql_text: str) -> dict[str, set[str]]:
    """Single-column UNIQUE and single-column PRIMARY KEY definitions (implicit indexes)."""
    uniq: dict[str, set[str]] = {}
    for table, body in _iter_table_blocks(sql_text):
        cols: set[str] = set()
        for raw in body.splitlines():
            line = raw.strip()
            low = line.lower()
            if low.startswith(_SKIP_LINE_PREFIXES):
                continue  # table-level PRIMARY KEY (a,b) / UNIQUE (a,b) are not single-col
            token = re.match(r"(\w+)", line)
            if not token:
                continue
            if re.search(r"\bprimary\s+key\b", low) or re.search(r"\bunique\b", low):
                cols.add(token.group(1).lower())
        if cols:
            uniq[table] = cols
    return uniq


def collect_index_coverage() -> dict[str, Any]:
    sql = _read_supabase_sql()
    fk = parse_fk_columns(sql)
    btree = parse_btree_leftmost(sql)
    uniq = parse_unique_single_columns(sql)

    fk_columns = {(t, c) for t, cs in fk.items() for c in cs}
    covered = {
        (t, c)
        for (t, c) in fk_columns
        if c in btree.get(t, set()) or c in uniq.get(t, set())
    }
    gaps = fk_columns - covered

    fix_sql = (
        FK_INDEX_MIGRATION.read_text(encoding="utf-8", errors="replace")
        if FK_INDEX_MIGRATION.exists()
        else ""
    )
    new_migration_indexes = [
        {
            "table": i["table"],
            "col": i["leftmost"],
            "if_not_exists": i["if_not_exists"],
            "is_btree": i["is_btree"],
        }
        for i in parse_index_statements(fix_sql)
    ]

    return {
        "fk_columns": fk_columns,
        "covered": covered,
        "gaps": gaps,
        "btree_leftmost": btree,
        "unique_columns": uniq,
        "new_migration_indexes": new_migration_indexes,
    }


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    fk = set(coverage["fk_columns"])
    covered = set(coverage["covered"])
    gaps = set(coverage["gaps"])
    newidx = list(coverage["new_migration_indexes"])
    targets = list(EXPECTED_TARGET_GAPS)

    results: list[dict[str, Any]] = []

    results.append(_hyp(
        "H1", "FK列抽出が健全(>=12件・主要FK在)",
        len(fk) >= 12
        and ("sales_email_messages", "mailbox_source_id") in fk
        and ("audits", "match_id") in fk,
        f"FK列数={len(fk)}"))

    partition_ok = (covered | gaps) == fk and not (covered & gaps)
    results.append(_hyp(
        "H2", "被覆判定が完全な分割(covered∪gaps==fk, 重複なし)",
        partition_ok, f"covered={len(covered)}, gaps={len(gaps)}, fk={len(fk)}"))

    results.append(_hyp(
        "H3", "複合indexのleftmostがFKを被覆(sales_email_entities.message_id)",
        ("sales_email_entities", "message_id") in covered,
        "message_idはidx(message_id,entity_type)で被覆"))

    results.append(_hyp(
        "H4", "UNIQUE/btree単独indexがFKを被覆(usage_ledgers.user_id, matches.user_id)",
        ("usage_ledgers", "user_id") in covered and ("matches", "user_id") in covered,
        "user_idはUNIQUE/idx_matches_user_createdで被覆"))

    results.append(_hyp(
        "H5", "監査ログFK(audits.match_id, ON DELETE SET NULL)が被覆",
        ("audits", "match_id") in covered, "削除カスケード性能"))

    results.append(_hyp(
        "H6", "FKインデックスギャップ0(公式Supabase advisor推奨に整合)",
        not gaps, f"残ギャップ: {sorted(gaps) or 'なし'}"))

    uncovered_targets = [t for t in targets if t not in covered]
    results.append(_hyp(
        "H7", "既知の要対応FK11件が全て被覆",
        not uncovered_targets, f"未被覆target: {uncovered_targets or 'なし'}"))

    results.append(_hyp(
        "H8", "fix migrationのindexは全てbtree・単一plain列",
        bool(newidx) and all(i["is_btree"] for i in newidx),
        f"index数={len(newidx)}, 非btree={[i['col'] for i in newidx if not i['is_btree']] or 'なし'}"))

    results.append(_hyp(
        "H9", "fix migrationのindexは全てIF NOT EXISTS(冪等・追加のみ)",
        bool(newidx) and all(i["if_not_exists"] for i in newidx),
        f"非冪等={[i['col'] for i in newidx if not i['if_not_exists']] or 'なし'}"))

    no_prior_drift = all(h["passed"] for h in results)
    results.append(_hyp(
        "H10", "総合ドリフト0(全FK被覆かつ全チェックgreen)",
        no_prior_drift and not gaps,
        f"先行ドリフト={'なし' if no_prior_drift else 'あり'}, ギャップ={len(gaps)}"))

    return results


def run_audit() -> dict[str, Any]:
    coverage = collect_index_coverage()
    hypotheses = evaluate(coverage)
    return {
        "task": "T881",
        "scope": "supabase/migrations (product schema)",
        "fk_count": len(coverage["fk_columns"]),
        "covered_count": len(coverage["covered"]),
        "gap_count": len(coverage["gaps"]),
        "gaps": sorted(coverage["gaps"]),
        "fix_migration": FK_INDEX_MIGRATION.name,
        "new_index_count": len(coverage["new_migration_indexes"]),
        "hypotheses": hypotheses,
        "all_passed": all(h["passed"] for h in hypotheses),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 外部キー・インデックス被覆監査 (T881)",
        "",
        f"- 対象範囲: {report['scope']}",
        f"- FK列数: {report['fk_count']} / 被覆: {report['covered_count']} / "
        f"ギャップ: **{report['gap_count']}**",
        f"- 修正migration: `{report['fix_migration']}` (追加index {report['new_index_count']}件)",
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
    Path(args.json).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    Path(args.md).write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
