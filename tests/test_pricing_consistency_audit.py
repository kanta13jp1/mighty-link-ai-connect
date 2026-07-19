"""T901 test spec (written test-first): pricing-consistency guard.

UAT TS-30 (docs/UAT_TEST_SPECIFICATION.md): the paid-launch decision (T862)
depends on plan prices (Free ¥0 / Standard ¥9,800 / Pro ¥29,800, tax-inclusive
¥10,780 / ¥32,780) that are quoted across several docs (the canonical
PRICING_PLAN_PROVISIONAL table, the decision pack, the CEO meeting agendas).
If one doc's price is edited but the others drift, the CEO-facing materials
disagree. This suite pins the guard's pure functions: the canonical monthly
amounts are extracted from the pricing table, plan-context amounts are read
from arbitrary docs, drift is the set difference from canonical, and a
Free-with-a-nonzero-price is caught.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_pricing_consistency as guard  # noqa: E402

CANONICAL_ROW = "| 月額 | ¥0 | ¥9,800（税込 ¥10,780） | ¥29,800（税込 ¥32,780） | 個別見積 |"
CANON = {9800, 10780, 29800, 32780}


def test_canonical_monthly_amounts_from_table_row():
    got = guard.canonical_monthly_amounts(CANONICAL_ROW)
    assert got == CANON, got


def test_canonical_ignores_free_and_overage_scale():
    # ¥0 (Free) and ¥50/¥30 (per-run overage) must NOT enter the monthly set.
    text = CANONICAL_ROW + "\n込み超過時の従量単価 ¥50/回 ¥30/回、Free ¥0"
    assert guard.canonical_monthly_amounts(text) == CANON


def test_plan_price_amounts_reads_only_plan_restatement_lines():
    text = (
        "料金プランは仮決定（Free ¥0 / Standard ¥9,800月 / Pro ¥29,800月）\n"
        "月額コスト上限 ¥10,000 / ¥30,000 / ¥50,000 のどれにするか\n"  # budget, no plan tiers
        "Standard 1契約（¥8,800/月）で回収\n"  # single tier only -> not a restatement
    )
    got = guard.plan_price_amounts(text)
    assert 9800 in got and 29800 in got
    assert 10000 not in got and 30000 not in got and 50000 not in got, \
        "AI-tool cost budgets must not be read as plan prices"
    assert 8800 not in got, "a single-tier line is not a plan restatement"


def test_plan_price_amounts_catches_uncomma_and_tax_inclusive_on_one_line():
    text = "Standard ¥9,800（税込 ¥10,780） / Pro ¥29800（税込 ¥32,780）"
    got = guard.plan_price_amounts(text)
    assert {9800, 10780, 29800, 32780} <= got


def test_drift_amounts_is_empty_when_consistent():
    text = "Free ¥0 / Standard ¥9,800 / Pro ¥29,800（税込 ¥32,780 / ¥10,780）"
    assert guard.drift_amounts(CANON, text) == set()


def test_drift_amounts_flags_a_changed_price():
    text = "Standard ¥8,800月 / Pro ¥29,800月"  # Standard drifted
    assert guard.drift_amounts(CANON, text) == {8800}


def test_free_nonzero_mentions_clean_when_free_is_zero():
    assert guard.free_nonzero_mentions("Free ¥0 / Standard ¥9,800") == []


def test_free_nonzero_mentions_flags_priced_free():
    # Free must never carry a price; ¥1,980 attached to Free is a defect.
    assert guard.free_nonzero_mentions("Free ¥1,980 / Standard ¥9,800") == [1980]


def test_placeholder_count_detects_provisional_markers():
    assert guard.placeholder_count("価格は（仮）。年額は（予定）。") == 2
    assert guard.placeholder_count("確定済み。") == 0


def test_evaluate_passes_on_the_real_repo():
    results = guard.evaluate()
    assert isinstance(results, list) and len(results) == 10
    failed = [r["id"] for r in results if not r["passed"]]
    assert not failed, f"pricing-consistency hypotheses failing on real repo: {failed}"
