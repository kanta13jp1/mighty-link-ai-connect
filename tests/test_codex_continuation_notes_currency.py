"""T905 test spec (written test-first): Codex continuation notes currency.

UAT TS-35 (docs/UAT_TEST_SPECIFICATION.md): docs/CODEX_CONTINUATION_NOTES.md had
grown to 993 lines — the largest doc in the repo — of which ~925 were dated
2026-05-21/22 session work logs, while its opening 背景 still presented an
already-passed 2026/5/27 Gemini quota refresh as the current premise. AGENTS.md
requires stale docs be rewritten aggressively rather than kept append-only.
This suite pins the cleaned-up shape: no passed-date premise, no dated work-log
sections, the still-useful operational sections retained, and a size cap so the
file cannot silently re-bloat.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC = PROJECT_ROOT / "docs" / "CODEX_CONTINUATION_NOTES.md"

# Sections that remain useful as current operating guidance.
REQUIRED_SECTIONS = [
    "運用方針",
    "切り替え手順",
    "quota-safe 起動",
    "確認方法",
    "Gemini 復帰時",
]

MAX_LINES = 150

# The obsolete premise: a specific quota refresh timestamp that has long passed.
_PASSED_QUOTA_RE = re.compile(r"baseline quota will refresh on|2026/5/27\s*18:48")
# Dated work-log section headings, e.g. "## 2026-05-21 作業ログ: ...".
_WORKLOG_HEADING_RE = re.compile(r"^#{2,3}\s*20\d{2}-\d{2}-\d{2}.*", re.M)


def read_doc() -> str:
    assert DOC.exists(), f"continuation notes missing: {DOC}"
    return DOC.read_text(encoding="utf-8")


def test_no_passed_quota_premise():
    text = read_doc()
    assert not _PASSED_QUOTA_RE.search(text), (
        "the already-passed 2026/5/27 quota refresh must not be stated as the current premise"
    )


def test_no_dated_worklog_sections():
    text = read_doc()
    found = _WORKLOG_HEADING_RE.findall(text)
    assert not found, f"dated work-log sections must be removed (Git/WBS hold history): {found[:3]}"


def test_retains_current_operational_sections():
    text = read_doc()
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    assert not missing, f"current operating guidance missing: {missing}"


def test_points_at_the_real_history_sources():
    text = read_doc()
    assert "Git" in text or "git" in text
    assert "WBS" in text, "the doc must say where task history actually lives"


def test_size_cap_prevents_rebloat():
    lines = read_doc().splitlines()
    assert len(lines) <= MAX_LINES, (
        f"doc re-bloated to {len(lines)} lines (cap {MAX_LINES}); "
        "append session history to Git/WBS, not to this file"
    )


def test_still_documents_force_mock_switch():
    # The practical value of this doc: how to run without burning Gemini quota.
    text = read_doc()
    assert "AI_FORCE_MOCK" in text
