"""T880 test spec (written test-first): schema <-> documentation drift guard.

docs/database.md is the canonical data-model document. After R114/R117 (missing
production tables caused by migration drift) the risk we must guard against is
the *documentation* silently diverging from the schema that migrations actually
define. This suite pins the ten hypotheses the audit harness
(scripts/audit_schema_doc_consistency.py) must verify:

* every table defined by a migration source is documented (H1/H2),
* nothing phantom is documented (H3),
* every SLA view is documented (H4),
* init_db never bootstraps a table that no migration owns (H5),
* the stale IndexedDB / browser-only narrative is gone (H6),
* the doc points at the canonical schema sources (H7),
* not-yet-applied prod objects are flagged (H8),
* RLS is documented for every RLS-enabled table (H9),
* counts line up and the audit is drift-free (H10).

The tests exercise the pure parsers/evaluator on synthetic input and then run
the real audit against the repository.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_schema_doc_consistency as audit  # noqa: E402


# --------------------------------------------------------------------------- #
# Parser unit tests
# --------------------------------------------------------------------------- #
def test_parse_sql_tables_handles_if_not_exists_schema_and_quotes():
    sql = """
    CREATE TABLE public.profiles ( id uuid );
    CREATE TABLE IF NOT EXISTS public.matches ( id uuid );
    CREATE TABLE IF NOT EXISTS engineers ( id serial );
    create table "public"."audits" ( id uuid );
    """
    tables = audit.parse_sql_tables(sql)
    assert tables == {"profiles", "matches", "engineers", "audits"}


def test_parse_sql_views_extracts_kpi_view_names():
    sql = """
    CREATE OR REPLACE VIEW public.kpi_daily_diagnoses AS SELECT 1;
    create view public.kpi_monthly_availability as select 1;
    CREATE TABLE public.uptime_checks ( id bigserial );
    """
    assert audit.parse_sql_views(sql) == {
        "kpi_daily_diagnoses",
        "kpi_monthly_availability",
    }
    # A table is not a view.
    assert "uptime_checks" not in audit.parse_sql_views(sql)


def test_parse_rls_enabled_tables():
    sql = """
    ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
    ALTER TABLE engineers ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.matches DISABLE ROW LEVEL SECURITY;
    """
    assert audit.parse_rls_enabled_tables(sql) == {"profiles", "engineers"}


def test_parse_documented_inventory_reads_marked_block_only():
    md = """
    intro text with `not_a_table` outside the markers
    <!-- SCHEMA-INVENTORY:START -->
    | 名前 | 種別 | ドメイン | 定義元 | RLS | 本番反映 |
    | :-- | :-- | :-- | :-- | :-- | :-- |
    | `profiles` | テーブル | コア | supabase | 有 | 適用済 |
    | `uptime_checks` | テーブル | SLA | supabase | 有 | 適用待ち(T778) |
    | `kpi_daily_diagnoses` | ビュー | SLA | supabase | - | 適用待ち(T778) |
    <!-- SCHEMA-INVENTORY:END -->
    """
    inv = audit.parse_documented_inventory(md)
    assert inv["tables"] == {"profiles", "uptime_checks"}
    assert inv["views"] == {"kpi_daily_diagnoses"}
    assert inv["pending"] == {"uptime_checks", "kpi_daily_diagnoses"}
    # Identifiers outside the markers must be ignored.
    assert "not_a_table" not in inv["tables"]


# --------------------------------------------------------------------------- #
# Evaluator unit tests (synthetic consistent baseline + injected drift)
# --------------------------------------------------------------------------- #
def _consistent_schema():
    return {
        "supabase_tables": {"profiles", "matches", "uptime_checks"},
        "supabase_views": {"kpi_daily_diagnoses"},
        "app_runtime_tables": {"engineers", "jobs", "match_results"},
        "initdb_tables": {"engineers", "matches"},
        "rls_tables": {"profiles", "matches", "engineers"},
        "authoritative_tables": {
            "profiles",
            "matches",
            "uptime_checks",
            "engineers",
            "jobs",
            "match_results",
        },
        "pending": {"uptime_checks", "kpi_daily_diagnoses"},
    }


def _consistent_doc():
    return {
        "tables": {
            "profiles",
            "matches",
            "uptime_checks",
            "engineers",
            "jobs",
            "match_results",
        },
        "views": {"kpi_daily_diagnoses"},
        "pending": {"uptime_checks", "kpi_daily_diagnoses"},
        "text": (
            "Firebase Auth + Supabase Postgres 17.6 + Row Level Security (RLS)。"
            "正本は supabase/migrations と db/migrations、"
            "DB_MIGRATION_MANAGEMENT_RUNBOOK を参照。本番適用待ちは T778。"
        ),
    }


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def test_evaluate_all_pass_on_consistent_pair():
    hyps = audit.evaluate(_consistent_schema(), _consistent_doc())
    assert len(hyps) == 10
    failing = [h["id"] for h in hyps if not h["passed"]]
    assert failing == [], failing


def test_h1_flags_missing_supabase_table():
    doc = _consistent_doc()
    doc["tables"].discard("matches")
    hyps = _ids(audit.evaluate(_consistent_schema(), doc))
    assert hyps["H1"]["passed"] is False


def test_h2_flags_missing_legacy_table():
    doc = _consistent_doc()
    doc["tables"].discard("engineers")
    hyps = _ids(audit.evaluate(_consistent_schema(), doc))
    assert hyps["H2"]["passed"] is False


def test_h3_flags_phantom_documented_table():
    doc = _consistent_doc()
    doc["tables"].add("ghost_table")
    hyps = _ids(audit.evaluate(_consistent_schema(), doc))
    assert hyps["H3"]["passed"] is False


def test_h4_flags_missing_view():
    doc = _consistent_doc()
    doc["views"].discard("kpi_daily_diagnoses")
    hyps = _ids(audit.evaluate(_consistent_schema(), doc))
    assert hyps["H4"]["passed"] is False


def test_h5_flags_unmanaged_initdb_table():
    schema = _consistent_schema()
    # init_db bootstraps a table that no migration owns -> R114/R117 style drift.
    schema["initdb_tables"] = schema["initdb_tables"] | {"orphan_table"}
    hyps = _ids(audit.evaluate(schema, _consistent_doc()))
    assert hyps["H5"]["passed"] is False


def test_h6_flags_stale_marker():
    doc = _consistent_doc()
    doc["text"] += " 本プロジェクトは IndexedDB でブラウザ完結する。"
    hyps = _ids(audit.evaluate(_consistent_schema(), doc))
    assert hyps["H6"]["passed"] is False


def test_h7_flags_missing_source_reference():
    doc = _consistent_doc()
    doc["text"] = "Firebase Auth と RLS のみ言及。正本参照なし。"
    hyps = _ids(audit.evaluate(_consistent_schema(), doc))
    assert hyps["H7"]["passed"] is False


def test_h8_flags_unmarked_pending_object():
    doc = _consistent_doc()
    doc["pending"].discard("uptime_checks")
    hyps = _ids(audit.evaluate(_consistent_schema(), doc))
    assert hyps["H8"]["passed"] is False


def test_h9_flags_undocumented_rls_table():
    schema = _consistent_schema()
    schema["rls_tables"] = schema["rls_tables"] | {"secret_rls_table"}
    hyps = _ids(audit.evaluate(schema, _consistent_doc()))
    assert hyps["H9"]["passed"] is False


def test_h10_flags_count_mismatch():
    doc = _consistent_doc()
    doc["tables"].add("extra_undocumented_but_authoritative")
    # Also add to authoritative so H1/H3 still pass but the count invariant trips.
    schema = _consistent_schema()
    schema["authoritative_tables"].add("extra_undocumented_but_authoritative")
    hyps = _ids(audit.evaluate(schema, doc))
    # H10 requires documented == authoritative in count AND all other checks green;
    # here counts match, so construct a real mismatch instead:
    doc2 = _consistent_doc()
    schema2 = _consistent_schema()
    schema2["authoritative_tables"].add("only_in_schema")
    hyps2 = _ids(audit.evaluate(schema2, doc2))
    assert hyps2["H10"]["passed"] is False


# --------------------------------------------------------------------------- #
# Integration: run the audit against the real repository
# --------------------------------------------------------------------------- #
def test_real_repository_audit_is_drift_free():
    report = audit.run_audit()
    failing = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"] is True, failing


def test_real_repository_has_expected_authoritative_counts():
    schema = audit.collect_authoritative()
    # 20 supabase-migration tables + engineers/jobs/match_results (app runtime).
    assert len(schema["authoritative_tables"]) == 23
    assert len(schema["supabase_views"]) == 6
    # uptime_checks + the six KPI views are defined but not yet applied to prod.
    assert schema["pending"] == {
        "uptime_checks",
        "kpi_daily_diagnoses",
        "kpi_weekly_active_users",
        "kpi_weekly_anonymous_sessions",
        "kpi_monthly_availability",
        "kpi_daily_response_time",
        "kpi_weekly_diagnosis_accuracy",
    }


def test_real_repository_initdb_is_fully_migration_managed():
    schema = audit.collect_authoritative()
    orphan = schema["initdb_tables"] - schema["authoritative_tables"]
    assert orphan == set(), orphan
