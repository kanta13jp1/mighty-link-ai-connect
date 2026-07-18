"""T879 test spec (written test-first): 7/22 CEO meeting agenda guard.

UAT TS-24 (docs/UAT_TEST_SPECIFICATION.md) defines the human-executable
acceptance for the 2026-07-22 13:00 CEO meeting: the agenda document must
exist with the meeting date/time and follow-up / decision-request / minutes
sections, every request must be tied to a WBS task id, no secrets may appear,
and the 7/22 calendar slot must stay visible after T879 completes — which the
sync only guarantees if an uncompleted follow-up task (T898) covers 7/22,
because completed rows have their calendar events deleted.

These tests pin the machine-checkable half of that contract.
"""

import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENDA = PROJECT_ROOT / "docs" / "CEO_MEETING_AGENDA_2026-07-22.md"
WBS = PROJECT_ROOT / "data" / "WBS.tsv"

REQUIRED_SECTIONS = [
    "エグゼクティブサマリ",
    "フォローアップ",
    "ご判断・ご対応",
    "議事メモ",
]

# Credential-shaped strings that must never appear in a CEO-facing document.
FORBIDDEN_PATTERNS = [
    re.compile(r"sk_(?:live|test)_", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z_-]{10,}"),
    re.compile(r"Bearer\s+[0-9A-Za-z._-]{16,}"),
    re.compile(r"パスワード\s*[:：]\s*\S"),
]


def read_agenda() -> str:
    assert AGENDA.exists(), f"agenda document missing: {AGENDA}"
    return AGENDA.read_text(encoding="utf-8")


def read_wbs_rows() -> dict[str, dict[str, str]]:
    with WBS.open(encoding="utf-8-sig", newline="") as fh:
        return {row["タスクID"]: row for row in csv.DictReader(fh, delimiter="\t")}


def test_agenda_states_meeting_date_and_time():
    text = read_agenda()
    assert "2026-07-22" in text
    assert "13:00" in text


def test_agenda_has_required_sections():
    text = read_agenda()
    for keyword in REQUIRED_SECTIONS:
        assert keyword in text, f"agenda is missing section keyword: {keyword}"


def test_agenda_ties_requests_to_wbs_tasks():
    text = read_agenda()
    for task_id in ("T898", "T862", "T823", "T831", "T834", "T850"):
        assert task_id in text, f"agenda does not reference {task_id}"


def test_agenda_contains_no_credential_shaped_strings():
    text = read_agenda()
    for pattern in FORBIDDEN_PATTERNS:
        assert not pattern.search(text), f"credential-shaped match: {pattern.pattern}"


def test_wbs_has_t898_follow_up_covering_meeting_day():
    rows = read_wbs_rows()
    assert "T898" in rows, "follow-up task T898 missing from WBS"
    t898 = rows["T898"]
    assert t898["開始日"] == "2026-07-22", "T898 must start on the meeting day"
    assert t898["終了予定日"] >= t898["開始日"]


def test_wbs_t879_is_completed_with_agenda_reference():
    rows = read_wbs_rows()
    t879 = rows["T879"]
    assert t879["ステータス"] == "完了"
    assert "CEO_MEETING_AGENDA_2026-07-22" in t879["Sheets Live 連携アクション"]
