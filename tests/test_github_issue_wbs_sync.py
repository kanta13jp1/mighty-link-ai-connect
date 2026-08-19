"""T849_3 test spec (written test-first): GitHub issue ↔ WBS reconciliation.

T849 (GAリリース閉鎖) requires "GitHub Issues/Project 未完了0". Because
sync_wbs_to_github.py is deliberately targeted (`sync_wbs_to_github.py TXXX`),
a lane that completes a task without syncing leaves its issue open forever. On
2026-07-20 that had produced two stale issues — #158 (T866) and #139 (T852) —
both for tasks long since 完了, inflating the closure criterion with work that
was actually done.

This suite pins the pure classification so the reconciler can be trusted:
which open issues belong to 完了 tasks (stale → close), and which belong to
genuinely incomplete work (legitimately open).

The reconciler itself needs `gh` and network, so it is an on-demand tool rather
than a preflight guard; these tests cover its logic without either.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_github_issue_wbs_sync as recon  # noqa: E402


# --------------------------------------------------------------------------- #
# extract_wbs_ids
# --------------------------------------------------------------------------- #
def test_extracts_bracketed_and_bare_task_ids():
    assert recon.extract_wbs_ids("[T898] 7/22(水)13:00 社長定例の実施・議事録反映") == {"T898"}
    assert recon.extract_wbs_ids("T866: DBスキーマ管理の再発防止") == {"T866"}


def test_extracts_subtask_ids_and_multiple():
    got = recon.extract_wbs_ids("T811/T837完了: 監査でR116/R117を発見 (T798_1 参照)")
    assert got == {"T811", "T837", "T798_1"}


def test_ignores_non_task_tokens():
    # issue/QA ids and bare numbers must not be read as WBS tasks
    assert recon.extract_wbs_ids("R116 / QA-108 / #162 / 2026-07-20") == set()


# --------------------------------------------------------------------------- #
# classify_open_issues
# --------------------------------------------------------------------------- #
STATUS = {
    "T866": "完了",
    "T852": "完了",
    "T849": "未着手",
    "T870": "未着手",
    "T811": "完了",
    "T837": "完了",
}


def test_issue_whose_tasks_are_all_done_is_stale():
    issues = [{"number": 158, "title": "T866: DBスキーマ管理の再発防止"}]
    result = recon.classify_open_issues(issues, STATUS)
    assert [i["number"] for i in result["stale"]] == [158]
    assert result["legitimate"] == []


def test_issue_with_an_incomplete_task_is_legitimate():
    issues = [{"number": 136, "title": "[T849] サイト開発完了総合判定"}]
    result = recon.classify_open_issues(issues, STATUS)
    assert result["stale"] == []
    assert [i["number"] for i in result["legitimate"]] == [136]


def test_mixed_issue_is_legitimate_when_any_task_is_open():
    """#162 names completed T811/T837 but tracks the still-open T870 work —
    an issue is only stale when EVERY task it references is done."""
    issues = [{"number": 162, "title": "T811/T837完了: R116発見", "body": "対応は T870 で実施"}]
    result = recon.classify_open_issues(issues, STATUS)
    assert result["stale"] == []
    assert [i["number"] for i in result["legitimate"]] == [162]


def test_issue_referencing_no_task_is_unlinked_not_stale():
    """An issue with no WBS reference must never be auto-closed."""
    issues = [{"number": 99, "title": "typo in README"}]
    result = recon.classify_open_issues(issues, STATUS)
    assert result["stale"] == []
    assert [i["number"] for i in result["unlinked"]] == [99]


def test_unknown_task_id_is_unlinked_not_stale():
    """A task id that is not in the WBS must not be treated as complete."""
    issues = [{"number": 100, "title": "[T999] does not exist"}]
    result = recon.classify_open_issues(issues, STATUS)
    assert result["stale"] == []
    assert [i["number"] for i in result["unlinked"]] == [100]


# --------------------------------------------------------------------------- #
# real WBS load
# --------------------------------------------------------------------------- #
def test_load_wbs_status_reads_the_real_tsv():
    status = recon.load_wbs_status()
    assert len(status) > 300
    assert status.get("T866") == "完了"
    assert status.get("T988") == "完了"
