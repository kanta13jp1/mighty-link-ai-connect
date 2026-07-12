"""T888 regression guard: the public 営業メールAIマッチング進捗 table must show the
anonymized candidate label on the API success path.

Bug (found via UAT TS-05, QA-118 / R131): the public matching board renders each
row with `m.candidate || m.talent_name`, but sales-email match rows carry neither
field — the anonymized candidate is exposed as `talent_label`. So on the live API
success path the 適合エンジニア column was always blank, and a human running TS-05
could not tell that a candidate had actually been matched.

This suite pins both halves of the contract so it cannot silently regress:

* dynamic  — every match row the API/service emits exposes a non-empty
  `talent_label`, and that label stays anonymized (no real name / email / phone),
* static   — both index.html and src/index.html map `m.talent_label` into the
  candidate column of renderPublicMatchingTable.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import sales_email_extract as extract  # noqa: E402
import sales_email_ingest as ingest  # noqa: E402
import sales_email_match as match  # noqa: E402

HTML_FILES = [PROJECT_ROOT / "index.html", PROJECT_ROOT / "src" / "index.html"]


def sample_report() -> dict:
    emails = ingest.load_sales_emails([PROJECT_ROOT / "data" / "samples" / "sales_emails"])
    return match.build_match_report(
        extract.build_extraction_report(emails),
        match.criteria_from_values(limit=10),
    )


# --------------------------------------------------------------------------- #
# Dynamic: the service exposes an anonymized talent_label per match row
# --------------------------------------------------------------------------- #
def test_every_match_row_exposes_non_empty_talent_label():
    report = sample_report()
    assert report["matches"], "expected at least one candidate match from PoC data"
    for row in report["matches"]:
        assert row.get("talent_label"), f"match row missing talent_label: {row}"


def test_talent_label_stays_anonymized():
    for row in sample_report()["matches"]:
        label = row["talent_label"]
        assert "@" not in label, f"talent_label leaks an email: {label!r}"
        assert not re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", label), (
            f"talent_label leaks a phone number: {label!r}"
        )


def test_talent_label_matches_the_talents_summary():
    report = sample_report()
    known_labels = {t["display_name"] for t in report["talents"]}
    for row in report["matches"]:
        assert row["talent_label"] in known_labels, (
            f"talent_label {row['talent_label']!r} not found in anonymized talents summary"
        )


# --------------------------------------------------------------------------- #
# Static: both public demo HTML files render talent_label in the progress table
# --------------------------------------------------------------------------- #
def test_public_matching_table_maps_talent_label_in_both_html():
    for html_path in HTML_FILES:
        text = html_path.read_text(encoding="utf-8")
        assert "renderPublicMatchingTable" in text, f"{html_path} lost the public table renderer"
        assert "m.talent_label" in text, (
            f"{html_path} no longer maps m.talent_label into the 適合エンジニア column "
            f"(the API-success candidate label would render blank again)"
        )
