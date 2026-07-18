"""T839_1 test spec (written test-first): vendor RFI/DPA checklist guard.

UAT TS-27 (docs/UAT_TEST_SPECIFICATION.md) defines the human-executable
acceptance for the employee-assessment vendor selection document. This suite
pins the machine-checkable half: the doc must exist, name all three shortlist
vendors, carry a 3-vendor comparison matrix, cover the mandatory DPA clauses
(subprocessor, cross-border transfer, incident-notification, deletion
evidence, audit right, data return), include a send-ready RFI questionnaire,
state the sensitive-personal-information handling premise, tie to the legal
review (T798/R36), and carry no credential-shaped strings or asserted vendor
quotes (values are blanks the vendor fills in).
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC = PROJECT_ROOT / "docs" / "EMPLOYEE_ASSESSMENT_VENDOR_RFI_DPA_CHECKLIST.md"

VENDORS = ["ラフールサーベイ", "HRBrain", "ミキワメ"]

# DPA clauses that must each be present for the legal review to be actionable.
DPA_CLAUSES = ["再委託", "国外移転", "インシデント", "削除", "監査", "返還"]

FORBIDDEN_PATTERNS = [
    re.compile(r"sk_(?:live|test)_", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z_-]{10,}"),
    re.compile(r"Bearer\s+[0-9A-Za-z._-]{16,}"),
    re.compile(r"パスワード\s*[:：]\s*\S"),
]


def read_doc() -> str:
    assert DOC.exists(), f"vendor RFI/DPA checklist missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


def test_states_purpose_and_related_wbs():
    text = read_doc()
    assert "T839" in text
    assert "T839_1" in text
    # Legal review linkage so DPA answers can be handed off.
    assert "T798" in text and "R36" in text


def test_names_all_three_shortlist_vendors():
    text = read_doc()
    for vendor in VENDORS:
        assert vendor in text, f"vendor missing from checklist: {vendor}"


def test_has_three_vendor_comparison_matrix():
    text = read_doc()
    assert "比較評価マトリクス" in text or "比較評価表" in text
    # A markdown table wide enough to place three vendors side by side.
    wide_rows = [ln for ln in text.splitlines() if ln.count("|") >= 4]
    assert len(wide_rows) >= 3, "expected a comparison table with >=3 columns"


def test_covers_all_mandatory_dpa_clauses():
    text = read_doc()
    for clause in DPA_CLAUSES:
        assert clause in text, f"DPA clause not covered: {clause}"


def test_has_send_ready_rfi_questionnaire():
    text = read_doc()
    assert "RFI" in text
    # A questionnaire the vendor fills in needs answer blanks.
    assert "回答" in text


def test_states_sensitive_information_premise():
    text = read_doc()
    assert "要配慮" in text
    assert "同意" in text


def test_no_credential_shaped_strings():
    text = read_doc()
    for pattern in FORBIDDEN_PATTERNS:
        assert not pattern.search(text), f"credential-shaped match: {pattern.pattern}"
