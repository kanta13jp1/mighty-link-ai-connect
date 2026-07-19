"""T900 test spec (written test-first): legal-disclosure integrity guard.

UAT TS-28 (docs/UAT_TEST_SPECIFICATION.md): the statutory disclosure docs
(利用規約 / プライバシーポリシー / 特商法表記 / 課金・返金) carry legally
mandated items and must not contradict one another, yet only a one-off
2026-07-04 report checked them — there was no continuous CI guard. Before the
paid-launch decision (T862), a missing 特商法 item or a cancellation/refund
clause that drifts between docs must fail CI.

This suite pins the pure decision helpers the audit delegates to (so the rule
is unit-testable without file layout), plus an integration check that the
current docs pass the audit.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_legal_disclosures as audit  # noqa: E402


# --------------------------------------------------------------------------- #
# missing_items: each required item is satisfied by any of its alternatives
# --------------------------------------------------------------------------- #
def test_missing_items_detects_absent():
    required = [("解約", ["解約", "退会"]), ("販売価格", ["販売価格", "価格"])]
    assert audit.missing_items("価格は申込画面に表示", required) == ["解約"]


def test_missing_items_empty_when_all_present_via_alternatives():
    required = [("解約", ["解約", "退会"]), ("事業者名", ["事業者名", "事業者情報"])]
    assert audit.missing_items("退会はマイページから。事業者情報あり", required) == []


# --------------------------------------------------------------------------- #
# both_cover: a consistency item must appear in BOTH documents
# --------------------------------------------------------------------------- #
def test_both_cover_true_when_in_both():
    assert audit.both_cover("解約はこちら", "解約方法を表示", ["解約", "退会"]) is True


def test_both_cover_true_via_alternative_keyword():
    # One doc says 解約, the other says 退会 — same concept, still consistent.
    assert audit.both_cover("解約できます", "退会手続き", ["解約", "退会"]) is True


def test_both_cover_false_when_missing_in_one():
    assert audit.both_cover("解約できます", "返金は原則不可", ["解約", "退会"]) is False


# --------------------------------------------------------------------------- #
# placeholder_count: unconfirmed markers to resolve before paid launch
# --------------------------------------------------------------------------- #
def test_placeholder_count_counts_markers():
    assert audit.placeholder_count("株式会社Mighty Link（仮）／責任者（予定）") == 2


def test_placeholder_count_zero_on_confirmed_text():
    assert audit.placeholder_count("確定済みの正式文言です") == 0


def test_placeholder_count_counts_legal_review_markers():
    # 【要法務確認】/【要確認】 are unconfirmed items to resolve before paid launch.
    assert audit.placeholder_count("正式商号は【要法務確認】、登記情報は【要確認】") == 2


def test_placeholder_count_counts_inline_colon_marker_form():
    # The inline 【要法務確認: …】 form (e.g. 上限額・告知期間) must count too.
    assert audit.placeholder_count("上限は【要法務確認: 期間・上限額】、告知は【要法務確認: 30日前】") == 2


# --------------------------------------------------------------------------- #
# Integration: the current statutory docs must pass the audit
# --------------------------------------------------------------------------- #
def test_current_docs_pass_audit():
    report = audit.run_audit()
    failed = [h["id"] for h in report["hypotheses"] if not h["passed"]]
    assert report["all_passed"], f"failing hypotheses: {failed}"


def test_report_records_placeholder_count():
    report = audit.run_audit()
    assert "placeholder_count" in report
    assert isinstance(report["placeholder_count"], int)
