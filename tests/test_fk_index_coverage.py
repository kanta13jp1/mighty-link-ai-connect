"""T881 test spec (written test-first): foreign-key index coverage guard.

PostgreSQL does not auto-create indexes on foreign-key columns (only on PK /
UNIQUE), so unindexed FKs are a classic performance defect: joins fall back to
sequential scans and — critically for this project — ON DELETE CASCADE/SET NULL
parent deletes must full-scan every child table (the data-retention/deletion
flow, T847). Supabase's Database Performance Advisor flags "unindexed foreign
keys" for exactly this reason and recommends a btree index per FK column.

This suite pins the ten hypotheses the audit harness
(scripts/audit_fk_index_coverage.py) must verify and drives the fix migration
(supabase/migrations/20260709000000_fk_covering_indexes.sql): after it is added,
every product-schema FK column is covered and the drift guard is green.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_fk_index_coverage as audit  # noqa: E402


# --------------------------------------------------------------------------- #
# Parser unit tests
# --------------------------------------------------------------------------- #
def test_parse_fk_columns_inline_and_constraint_styles():
    sql = """
    CREATE TABLE public.child (
        id BIGSERIAL PRIMARY KEY,
        parent_id BIGINT REFERENCES public.parent(id) ON DELETE CASCADE,
        other_id BIGINT,
        CONSTRAINT fk_other FOREIGN KEY (other_id) REFERENCES public.other(id)
    );
    """
    fk = audit.parse_fk_columns(sql)
    assert fk["child"] == {"parent_id", "other_id"}


def test_parse_btree_leftmost_excludes_gin_and_expressions():
    sql = """
    CREATE INDEX idx_a ON public.t (parent_id, created_at DESC);
    CREATE INDEX idx_gin ON public.t USING gin (payload);
    CREATE INDEX idx_fn ON public.t (lower(name));
    """
    left = audit.parse_btree_leftmost(sql)
    assert "parent_id" in left["t"]      # leftmost of a composite btree
    assert "payload" not in left.get("t", set())   # gin is not FK-covering
    assert "name" not in left.get("t", set())      # functional index is not plain-col


def test_parse_unique_and_pk_single_columns():
    sql = """
    CREATE TABLE public.t (
        id BIGSERIAL PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL UNIQUE,
        note TEXT
    );
    """
    uniq = audit.parse_unique_single_columns(sql)
    assert uniq["t"] == {"id", "user_id"}


# --------------------------------------------------------------------------- #
# Evaluator unit tests (synthetic consistent baseline + injected drift)
# --------------------------------------------------------------------------- #
def _coverage_ok():
    fk = set(audit.EXPECTED_TARGET_GAPS) | {
        ("matches", "user_id"),
        ("usage_ledgers", "user_id"),
        ("sales_email_entities", "message_id"),
    }
    return {
        "fk_columns": set(fk),
        "covered": set(fk),
        "gaps": set(),
        "btree_leftmost": {},
        "new_migration_indexes": [
            {"table": t, "col": c, "if_not_exists": True, "is_btree": True}
            for (t, c) in audit.EXPECTED_TARGET_GAPS
        ],
    }


def _ids(hyps):
    return {h["id"]: h for h in hyps}


def test_evaluate_all_pass_on_consistent_coverage():
    hyps = audit.evaluate(_coverage_ok())
    assert len(hyps) == 10
    failing = [h["id"] for h in hyps if not h["passed"]]
    assert failing == [], failing


def test_h2_flags_incomplete_partition():
    cov = _coverage_ok()
    stray = next(iter(cov["fk_columns"]))
    cov["covered"].discard(stray)  # now in neither covered nor gaps
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H2"]["passed"] is False


def test_h3_requires_composite_leftmost_coverage():
    cov = _coverage_ok()
    cov["covered"].discard(("sales_email_entities", "message_id"))
    cov["gaps"].add(("sales_email_entities", "message_id"))
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H3"]["passed"] is False


def test_h4_requires_unique_and_btree_fk_coverage():
    cov = _coverage_ok()
    cov["covered"].discard(("usage_ledgers", "user_id"))
    cov["gaps"].add(("usage_ledgers", "user_id"))
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H4"]["passed"] is False


def test_h5_requires_audits_match_id_covered():
    cov = _coverage_ok()
    cov["covered"].discard(("audits", "match_id"))
    cov["gaps"].add(("audits", "match_id"))
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H5"]["passed"] is False


def test_h6_flags_any_remaining_gap():
    cov = _coverage_ok()
    cov["covered"].discard(("email_match_feedback", "match_result_id"))
    cov["gaps"].add(("email_match_feedback", "match_result_id"))
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H6"]["passed"] is False


def test_h7_flags_uncovered_target():
    cov = _coverage_ok()
    target = audit.EXPECTED_TARGET_GAPS[0]
    cov["covered"].discard(target)
    cov["gaps"].add(target)
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H7"]["passed"] is False


def test_h8_flags_non_btree_new_index():
    cov = _coverage_ok()
    cov["new_migration_indexes"][0]["is_btree"] = False
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H8"]["passed"] is False


def test_h9_flags_non_idempotent_new_index():
    cov = _coverage_ok()
    cov["new_migration_indexes"][0]["if_not_exists"] = False
    hyps = _ids(audit.evaluate(cov))
    assert hyps["H9"]["passed"] is False


# --------------------------------------------------------------------------- #
# Integration: run the audit against the real repository (post-migration green)
# --------------------------------------------------------------------------- #
def test_real_repository_has_no_fk_index_gaps():
    report = audit.run_audit()
    assert report["gap_count"] == 0, report["gaps"]
    assert report["all_passed"] is True, [
        h["id"] for h in report["hypotheses"] if not h["passed"]
    ]


def test_real_repository_covers_every_known_target():
    coverage = audit.collect_index_coverage()
    missing = [t for t in audit.EXPECTED_TARGET_GAPS if t not in coverage["covered"]]
    assert missing == [], missing


def test_fix_migration_is_additive_and_idempotent():
    coverage = audit.collect_index_coverage()
    idxs = coverage["new_migration_indexes"]
    assert idxs, "fix migration defines no indexes"
    assert all(i["if_not_exists"] for i in idxs)
    assert all(i["is_btree"] for i in idxs)
