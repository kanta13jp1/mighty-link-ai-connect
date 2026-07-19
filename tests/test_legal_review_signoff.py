"""T798_1 test spec (written test-first): legal-review sign-off tracker.

UAT TS-30 (docs/UAT_TEST_SPECIFICATION.md): T798 (利用規約・プライバシー
ポリシーの法務確認と本文確定) leaves 【要法務確認】 markers scattered across the
four statutory docs plus two checklist tables. The 2026-07-04 audit (T869)
counted them once and the T900 CI guard reports the running count, but there was
no single itemised worklist a human/lawyer can sign off row by row — phase-gated
so the internal-GA subset is confirmed first and paid-launch-only points defer
to T862.

This suite pins the tracker's structure and — most importantly — parity with the
docs: every actionable 【要法務確認】 marker in the four docs must have exactly one
tracker row, so a newly added marker fails CI until it is tracked.
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data"
DOCS = PROJECT_ROOT / "docs"
TRACKER = DATA / "legal_review_signoff.tsv"

LEGAL_DOCS = {
    "TERMS_OF_SERVICE": DOCS / "TERMS_OF_SERVICE.md",
    "PRIVACY_POLICY": DOCS / "PRIVACY_POLICY.md",
    "BILLING_AND_REFUND_POLICY": DOCS / "BILLING_AND_REFUND_POLICY.md",
    "TOKUSHOHO_NOTATION": DOCS / "TOKUSHOHO_NOTATION.md",
}
# Both marker styles carry a legal-review question: 【要法務確認】text and the
# inline 【要法務確認: text】 form. Count the core token so neither is missed.
MARKER = "要法務確認"
BANNER_HINT = "マーカーの箇所は"  # the status-banner note line, not an action item

EXPECTED_COLUMNS = [
    "台帳ID", "文書", "条項/セクション", "論点", "マーカー種別",
    "フェーズゲート", "確定要否", "状態", "確定内容/根拠", "確認者", "確認日",
]
VALID_GATE = {"社内GA必須", "有償公開前必須"}
VALID_STATE = {"未確認", "確認中", "確定"}


def _rows():
    with TRACKER.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _actionable_markers(path: Path) -> int:
    """Count 【要法務確認】 occurrences on action lines (exclude the banner note)."""
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if MARKER in line and BANNER_HINT not in line:
            n += line.count(MARKER)
    return n


def test_tracker_exists_with_expected_columns():
    assert TRACKER.exists(), f"missing {TRACKER}"
    with TRACKER.open(encoding="utf-8-sig", newline="") as f:
        header = f.readline().rstrip("\r\n").split("\t")
    assert header == EXPECTED_COLUMNS


def test_every_row_has_valid_gate_state_and_doc():
    rows = _rows()
    assert rows, "tracker has no data rows"
    for r in rows:
        assert r["フェーズゲート"] in VALID_GATE, r
        assert r["状態"] in VALID_STATE, r
        assert r["文書"] in LEGAL_DOCS, r


def test_inline_marker_parity_per_doc():
    rows = _rows()
    for name, path in LEGAL_DOCS.items():
        tracked = sum(
            1 for r in rows if r["文書"] == name and r["マーカー種別"] == "inline"
        )
        expected = _actionable_markers(path)
        assert tracked == expected, (
            f"{name}: tracker inline rows {tracked} != doc markers {expected}"
        )


def test_ga_and_paid_subsets_both_present():
    rows = _rows()
    ga = [r for r in rows if r["フェーズゲート"] == "社内GA必須"]
    paid = [r for r in rows if r["フェーズゲート"] == "有償公開前必須"]
    assert ga, "no internal-GA-blocking rows"
    assert paid, "no paid-launch rows"


def test_paid_rows_defer_to_t862():
    for r in _rows():
        if r["フェーズゲート"] == "有償公開前必須":
            joined = r["確定内容/根拠"] + r["論点"]
            assert "T862" in joined, f"paid-launch row must reference T862: {r}"


def test_ids_are_unique():
    ids = [r["台帳ID"] for r in _rows()]
    assert len(ids) == len(set(ids)), "duplicate 台帳ID"
