"""T899 test spec (written test-first): calendar orphan-event cleanup.

R142: when a WBS task is renamed, sync_wbs_to_calendar.py leaves the old
summary's event on the calendar because create/update and the existing
cleanup functions match on summary or on completion status only. The
permanent fix is orphan_event_ids(), a pure decision function the API
wrapper delegates to, so the deletion rule is unit-testable without any
Google API call.

Contract pinned here (UAT TS-26):
* an event we synced (carrying wbsIds) whose summary is not in the current
  intended set is an orphan and must be deleted,
* an event whose summary IS intended must be kept,
* an event without wbsIds (e.g. a static event we didn't tag, or a user's
  own event) must never be deleted,
* when the intended set is empty (WBS unreadable / all-complete) the
  function returns nothing — it must never mass-delete.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import sync_wbs_to_calendar as sc  # noqa: E402


def ev(event_id, summary, wbs_ids):
    # A None or empty wbs_ids models an event we did not tag with wbsIds.
    return {"id": event_id, "summary": summary, "wbs_ids": list(wbs_ids) if wbs_ids else []}


def test_detects_renamed_orphan():
    present = [
        ev("e1", "【MSB】T819 旧タイトル", ["T819"]),
        ev("e2", "【MSB】T819 新タイトル", ["T819"]),
    ]
    intended = {"【MSB】T819 新タイトル"}
    assert sc.orphan_event_ids(present, intended) == ["e1"]


def test_keeps_intended_events():
    present = [ev("e1", "keep-me", ["T900"])]
    intended = {"keep-me"}
    assert sc.orphan_event_ids(present, intended) == []


def test_never_deletes_events_without_wbs_ids():
    # Static events we didn't tag, or a user's own calendar entries.
    present = [
        ev("e1", "untagged manual event", []),
        ev("e2", "static without wbsIds", None),
    ]
    intended = {"something else entirely"}
    assert sc.orphan_event_ids(present, intended) == []


def test_empty_intended_set_is_a_safety_noop():
    present = [ev("e1", "anything", ["T1"]), ev("e2", "another", ["T2"])]
    assert sc.orphan_event_ids(present, set()) == []


def test_multiple_orphans_all_returned():
    present = [
        ev("e1", "old-a", ["T1"]),
        ev("e2", "current", ["T2"]),
        ev("e3", "old-b", ["T3"]),
    ]
    intended = {"current"}
    assert sorted(sc.orphan_event_ids(present, intended)) == ["e1", "e3"]


def test_orphan_with_multiple_wbs_ids_still_detected():
    present = [ev("e1", "old multi", ["T1", "T2"])]
    intended = {"new multi"}
    assert sc.orphan_event_ids(present, intended) == ["e1"]
