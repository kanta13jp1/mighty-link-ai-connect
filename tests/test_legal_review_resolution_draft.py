"""T798_2 test spec (written test-first): legal-review resolution draft.

T798 (利用規約・プライバシーポリシーの法務確認と本文確定) cannot be closed by an
AI lane: 法務確認 needs a qualified reviewer (R36 外部弁護士) and four of the
markers need the company's own registration records. What CAN be produced is a
decision-ready pack so the lawyer/社長 only has to approve or amend.

This suite pins two things that make that pack safe to use:

1. Coverage — every 社内GA必須 row of data/legal_review_signoff.tsv has a section
   with a draft answer, a basis, and a statement of what input still closes it.
2. Honesty — the pack must declare it is NOT a substitute for legal review, and
   must NOT invent corporate facts (registered name, address, representative,
   PII officer). Those stay as explicit placeholders; a fabricated address or
   postal code in a legal document is a real-world harm, so it fails CI.
"""

import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRAFT = PROJECT_ROOT / "docs" / "LEGAL_REVIEW_RESOLUTION_DRAFT.md"
TRACKER = PROJECT_ROOT / "data" / "legal_review_signoff.tsv"

PLACEHOLDER = "【会社記録から入力】"
# Markers whose answer is a company record Claude must never invent.
COMPANY_FACT_IDS = {"T798-01", "T798-09", "T798-10", "T798-11"}
ALLOWED_CATEGORIES = {
    "会社事実の提供が必要",
    "弁護士確認が必要",
    "社内決定で確定可",
}


def _draft() -> str:
    return DRAFT.read_text(encoding="utf-8")


def _ga_rows() -> list[dict]:
    with TRACKER.open(encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if r["フェーズゲート"] == "社内GA必須"]


def _section(text: str, marker_id: str) -> str:
    start = text.index(f"### {marker_id}")
    nxt = text.find("\n### ", start + 1)
    return text[start: nxt if nxt != -1 else len(text)]


def test_draft_exists():
    assert DRAFT.exists(), f"missing {DRAFT}"


def test_declares_it_is_not_a_substitute_for_legal_review():
    text = _draft()
    assert "法務確認の代替ではありません" in text
    assert "R36" in text, "must point at the external-lawyer review issue"


def test_every_ga_marker_has_a_section():
    text = _draft()
    missing = [r["台帳ID"] for r in _ga_rows() if f"### {r['台帳ID']}" not in text]
    assert not missing, f"GA markers without a draft section: {missing}"


def test_each_section_declares_an_allowed_category():
    text = _draft()
    for row in _ga_rows():
        section = _section(text, row["台帳ID"])
        found = [c for c in ALLOWED_CATEGORIES if c in section]
        assert found, f"{row['台帳ID']} declares no 区分"


def test_each_section_carries_draft_basis_and_required_input():
    text = _draft()
    for row in _ga_rows():
        section = _section(text, row["台帳ID"])
        for cue in ("ドラフト回答", "根拠", "確定に必要な入力"):
            assert cue in section, f"{row['台帳ID']} missing '{cue}'"


def test_company_fact_markers_stay_placeholders():
    """The four registration facts must be left blank for the company to fill."""
    text = _draft()
    for marker_id in COMPANY_FACT_IDS:
        section = _section(text, marker_id)
        assert PLACEHOLDER in section, f"{marker_id} must keep the input placeholder"
        assert "会社事実の提供が必要" in section, f"{marker_id} miscategorised"


def test_no_fabricated_corporate_identifiers():
    """A invented address/representative in a legal draft is a real-world harm."""
    text = _draft()
    forbidden = {
        "postal code": r"〒\s*\d{3}-?\d{4}",
        "street address": r"\d+丁目\d+番",
        "registration number": r"法人番号\s*[:：]?\s*\d{8,}",
    }
    hits = [name for name, pattern in forbidden.items() if re.search(pattern, text)]
    assert not hits, f"draft must not contain invented corporate facts: {hits}"


def test_lists_the_company_inputs_needed_in_one_place():
    """The human should see exactly what to supply without reading every section."""
    text = _draft()
    assert "会社から提供が必要な事実" in text
    for marker_id in sorted(COMPANY_FACT_IDS):
        assert marker_id in text.split("会社から提供が必要な事実")[1][:1500], (
            f"{marker_id} not listed in the consolidated input list"
        )


def test_paid_launch_markers_are_not_presented_as_ga_scope():
    """The four T862-gated markers stay out of the GA sign-off set."""
    text = _draft()
    assert "T862" in text
    for marker_id in ("T798-17", "T798-18", "T798-19", "T798-20"):
        assert f"### {marker_id}" not in text, f"{marker_id} is paid-launch scope, not GA"
