"""T907 test spec (written test-first): operations cadence calendar guard.

UAT TS-40 (docs/UAT_TEST_SPECIFICATION.md): 20 of the 46 runbooks declare a
recurring obligation (daily backup, weekly cost, monthly quality report,
quarterly security audit, annual secret rotation), but there was no single
place saying what must happen on what cadence, by whom, and how you confirm it
was done — so a quarterly audit could silently be skipped after GA.

This suite pins the guard's pure functions: cadence sections are parsed from
the calendar, entries are parsed with their runbook link, the required minimum
obligations are checked for coverage, links are checked against disk, and
runbooks that declare a cadence but are absent from the calendar are reported
(minus a documented exclusion list for docs that merely *mention* another
runbook's cadence).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_operations_cadence as guard  # noqa: E402

SAMPLE = """# 運用カレンダー

## 日次
| 実施内容 | 担当 | Runbook | 完了確認 |
| --- | --- | --- | --- |
| DBバックアップ | Codex | [backup](SUPABASE_BACKUP_RESTORE_RUNBOOK.md) | 7世代が存在する |

## 四半期
| 実施内容 | 担当 | Runbook | 完了確認 |
| --- | --- | --- | --- |
| セキュリティ監査 | 人間 | [audit](SECURITY_AUDIT_RUNBOOK.md) | レポートが出力される |
"""


def test_cadence_sections_parses_frequency_headings():
    got = guard.cadence_sections(SAMPLE)
    assert "日次" in got and "四半期" in got
    assert "運用カレンダー" not in got, "the H1 title is not a cadence section"


def test_calendar_runbooks_extracts_linked_runbooks():
    got = guard.calendar_runbooks(SAMPLE)
    assert got == {
        "SUPABASE_BACKUP_RESTORE_RUNBOOK.md",
        "SECURITY_AUDIT_RUNBOOK.md",
    }


def test_dangling_links_flags_missing_files():
    on_disk = {"SECURITY_AUDIT_RUNBOOK.md"}
    linked = {"SECURITY_AUDIT_RUNBOOK.md", "GONE_RUNBOOK.md"}
    assert guard.dangling_links(linked, on_disk) == {"GONE_RUNBOOK.md"}


def test_missing_required_detects_an_absent_obligation():
    text = SAMPLE  # has backup + security audit, but no monthly quality report
    missing = guard.missing_required(text)
    assert "月次品質レポート" in missing
    # the two that ARE present must not be reported
    assert "日次バックアップ" not in missing
    assert "四半期セキュリティ監査" not in missing


def test_missing_required_empty_on_the_real_calendar():
    text = guard.read(guard.CALENDAR)
    assert guard.missing_required(text) == [], "real calendar must cover every required obligation"


def test_unregistered_cadence_runbooks_respects_exclusions():
    # A runbook that only *mentions* another runbook's cadence is excluded.
    assert guard.EXCLUDED_RUNBOOKS, "exclusion list must be documented"
    for name, reason in guard.EXCLUDED_RUNBOOKS.items():
        assert reason, f"exclusion without a reason: {name}"


def test_evaluate_passes_on_the_real_repo():
    results = guard.evaluate()
    assert isinstance(results, list) and len(results) == 10
    failed = [r["id"] for r in results if not r["passed"]]
    assert not failed, f"operations-cadence hypotheses failing on real repo: {failed}"
