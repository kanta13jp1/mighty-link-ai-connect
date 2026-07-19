"""T906 test spec (written test-first): service EOL / decommissioning plan.

UAT TS-38 (docs/UAT_TEST_SPECIFICATION.md): the WBS covered 企画→設計→実装→
テスト→リリース→実運用→保守 but had no plan for the terminal stage — actually
winding the service down. T781 built the self-export PoC and
AI_SAAS_SERVICE_FREEZE_RUNBOOK freezes vendor versions at GA; neither says who
does what, in what order, if a shutdown is decided.

This suite pins the properties that make such a plan safe to execute:

1. It is conditional — a plan for *if* shutdown is decided, not an announcement.
2. The eight steps appear in dependency order (notify before delete, export
   window before billing stop, evidence captured before infra teardown).
3. It does NOT invent the notice period: Terms art.15 still carries a
   【要法務確認】 marker, so a hardcoded "30日前" would be a fabricated legal
   commitment. It must defer to the clause and the legal sign-off tracker.
4. Deletion has documented statutory exceptions (books/tax records), so it is
   not an unconditional wipe.
5. A rollback point exists, and no credentials or invented corporate facts leak.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN = PROJECT_ROOT / "docs" / "SERVICE_EOL_DECOMMISSIONING_PLAN.md"

# The decommissioning sequence, in the order they must appear.
STEPS = [
    "終了決定",
    "事前通知",
    "データ持ち出し",
    "課金停止",
    "データ削除",
    "外部サービス",
    "インフラ撤収",
    # step 8's distinctive token: bare "記録" also occurs inside step 1
    # ("終了決定・記録"), which would falsely read as an out-of-order step.
    "証跡保存",
]

# Authoritative sources each step must defer to.
REQUIRED_REFERENCES = [
    "TERMS_OF_SERVICE.md",
    "BILLING_AND_REFUND_POLICY.md",
    "DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md",
    "USER_DATA_SELF_EXPORT_RUNBOOK.md",
]

FORBIDDEN_PATTERNS = [
    re.compile(r"sk_(?:live|test)_", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z_-]{10,}"),
    re.compile(r"パスワード\s*[:：]\s*\S"),
]

# A concrete notice period stated as decided fact would be a fabricated legal
# commitment while Terms art.15 still says 【要法務確認】.
_ASSERTED_NOTICE_RE = re.compile(r"終了日の\s*\d+\s*日前(?!.*要法務確認)")


def read_plan() -> str:
    assert PLAN.exists(), f"EOL plan missing: {PLAN}"
    return PLAN.read_text(encoding="utf-8")


def test_plan_is_conditional_not_an_announcement():
    text = read_plan()
    assert "決定されていません" in text or "決定していません" in text, (
        "the plan must state that no shutdown is currently decided"
    )
    assert "発動" in text, "the plan must define an activation condition"


def _sequence_section(text: str) -> str:
    """The numbered execution-order section.

    Scoped deliberately: the warning callout and §1 mention steps in prose
    ("通知・課金停止・データ削除・解約を実行してはいけません"), so ordering must be
    read from the canonical numbered list, not from the whole document.
    """
    start = text.index("## 2. 実行順序")
    nxt = text.find("\n## ", start + 1)
    return text[start: nxt if nxt != -1 else len(text)]


def test_steps_appear_in_dependency_order():
    section = _sequence_section(read_plan())
    positions = [section.find(s) for s in STEPS]
    missing = [s for s, p in zip(STEPS, positions) if p < 0]
    assert not missing, f"missing decommissioning steps: {missing}"
    assert positions == sorted(positions), (
        f"steps are out of dependency order: {list(zip(STEPS, positions))}"
    )


def test_does_not_fabricate_the_notice_period():
    text = read_plan()
    assert not _ASSERTED_NOTICE_RE.search(text), (
        "notice period is still 【要法務確認】 in Terms art.15; do not assert a number"
    )
    assert "第15条" in text, "must point at the Terms clause that governs notice"
    assert "要法務確認" in text or "legal_review_signoff" in text


def test_references_the_authoritative_docs():
    text = read_plan()
    missing = [r for r in REQUIRED_REFERENCES if r not in text]
    assert not missing, f"missing authoritative references: {missing}"


def test_deletion_has_statutory_exceptions():
    text = read_plan()
    assert "削除の例外" in text or "削除してはならない" in text
    assert "法定保存" in text or "帳簿" in text, (
        "statutory retention (books/tax records) must be carved out of deletion"
    )


def test_defines_a_rollback_point():
    text = read_plan()
    assert "撤回" in text, "the plan must say until which step the decision is reversible"


def test_external_service_cancellation_covers_the_stack():
    text = read_plan()
    for vendor in ["Firebase", "Supabase", "Stripe", "お名前.com"]:
        assert vendor in text, f"external service not covered: {vendor}"


def test_has_human_executable_checklist():
    text = read_plan()
    assert text.count("☐") >= 8, "needs a per-step checkbox checklist a human can tick"


def test_no_credentials_or_invented_company_facts():
    text = read_plan()
    for pattern in FORBIDDEN_PATTERNS:
        assert not pattern.search(text), f"credential-shaped match: {pattern.pattern}"
    # Company registration facts stay as placeholders (same rule as T798_2).
    assert not re.search(r"〒\d{3}-\d{4}", text), "postal code must not be invented"
