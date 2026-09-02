"""Tests for Stripe Tax and Invoice Compliance Runbook (T813 preparation)."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS = PROJECT_ROOT / "docs"
RUNBOOK = DOCS / "STRIPE_TAX_AND_INVOICE_COMPLIANCE_RUNBOOK.md"
BILLING_POLICY = DOCS / "BILLING_AND_REFUND_POLICY.md"


def test_runbook_exists():
    assert RUNBOOK.exists(), f"missing {RUNBOOK}"


def test_mandatory_invoice_items_covered():
    content = RUNBOOK.read_text(encoding="utf-8")
    mandatory_keywords = [
        "適格請求書発行事業者",
        "登録番号",
        "取引年月日",
        "取引内容",
        "適用税率",
        "氏名又は名称",
    ]
    for kw in mandatory_keywords:
        assert kw in content, f"missing mandatory invoice item keyword '{kw}' in runbook"


def test_pricing_tax_behavior_and_codes():
    content = RUNBOOK.read_text(encoding="utf-8")
    assert "exclusive" in content, "missing exclusive tax behavior"
    assert "txcd_10000000" in content, "missing Stripe Tax Code txcd_10000000"
    assert "切り捨て" in content, "missing rounding rule"


def test_billing_policy_cross_reference():
    content = RUNBOOK.read_text(encoding="utf-8")
    assert "BILLING_AND_REFUND_POLICY.md" in content, "missing reference to BILLING_AND_REFUND_POLICY.md"
