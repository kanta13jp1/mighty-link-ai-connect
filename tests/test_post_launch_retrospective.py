"""T801 test spec (written test-first): post-launch retrospective guard.

UAT TS-25 (docs/UAT_TEST_SPECIFICATION.md) defines the human-executable
acceptance for the post-launch retrospective. This suite pins the
machine-checkable half: the retro doc must state its review window and WBS
reference, use a KPT (Keep/Problem/Try) frame, cite the GA-period incidents
(R140/T896 deploy miss, R141/T897 WBS-tool contamination) and an existing
postmortem, triage the open issues into resolved-by-GA vs still-open, tie
each prevention action to a WBS id, feed the next-phase roadmap, and carry no
secrets.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RETRO = (
    PROJECT_ROOT / "docs" / "POST_LAUNCH_RETROSPECTIVE_2026-07-18.md"
    if (PROJECT_ROOT / "docs" / "POST_LAUNCH_RETROSPECTIVE_2026-07-18.md").exists()
    else PROJECT_ROOT / "docs" / "archive" / "historical_reports" / "POST_LAUNCH_RETROSPECTIVE_2026-07-18.md"
)

FORBIDDEN_PATTERNS = [
    re.compile(r"sk_(?:live|test)_", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z_-]{10,}"),
    re.compile(r"Bearer\s+[0-9A-Za-z._-]{16,}"),
    re.compile(r"パスワード\s*[:：]\s*\S"),
]


def read_retro() -> str:
    assert RETRO.exists(), f"retrospective document missing: {RETRO}"
    return RETRO.read_text(encoding="utf-8")


def test_states_window_and_wbs_reference():
    text = read_retro()
    assert "2026-07-08" in text, "GA date must be stated"
    assert "2026-07-18" in text, "review end date must be stated"
    assert "T801" in text


def test_uses_kpt_frame():
    text = read_retro()
    for keyword in ("Keep", "Problem", "Try"):
        assert keyword in text, f"KPT frame missing: {keyword}"


def test_cites_ga_period_incidents_and_a_postmortem():
    text = read_retro()
    assert "R140" in text and "T896" in text, "deploy-miss incident must be cited"
    assert "R141" in text and "T897" in text, "WBS-tool contamination must be cited"
    assert ("R44" in text) or ("R114" in text) or ("POSTMORTEM" in text), (
        "an existing postmortem must be referenced"
    )


def test_triages_open_issues_resolved_vs_ongoing():
    text = read_retro()
    # Stale-by-GA issues acknowledged as resolved.
    for rid in ("R111", "R113", "R120"):
        assert rid in text, f"resolved-by-GA issue not triaged: {rid}"
    # Genuinely open issues acknowledged as ongoing.
    for rid in ("R116", "R122", "R132"):
        assert rid in text, f"ongoing issue not triaged: {rid}"


def test_prevention_actions_tie_to_wbs():
    text = read_retro()
    for task_id in ("T870", "T896", "T894", "T819"):
        assert task_id in text, f"prevention action not tied to {task_id}"


def test_feeds_next_phase_roadmap():
    text = read_retro()
    for task_id in ("T862", "T768", "T752"):
        assert task_id in text, f"roadmap does not carry {task_id}"


def test_contains_no_credential_shaped_strings():
    text = read_retro()
    for pattern in FORBIDDEN_PATTERNS:
        assert not pattern.search(text), f"credential-shaped match: {pattern.pattern}"
