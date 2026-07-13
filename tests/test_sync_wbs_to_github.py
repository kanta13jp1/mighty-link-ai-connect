"""T893: targeted WBS -> GitHub Issues/Project synchronization."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import sync_wbs_to_github as sync  # noqa: E402


def _task(task_id: str = "T893", status: str = "完了") -> sync.WbsTask:
    return sync.WbsTask(
        task_id=task_id,
        phase="8. 本番運用・品質管理",
        sub_phase="品質管理",
        name="GitHub WBS同期ガード",
        owner="Codex",
        engine="VSCode + Codex + GitHub CLI",
        status=status,
        start_date="2026-07-13",
        target_date="2026-07-13",
    )


class FakeGateway:
    def __init__(self, issues=None, items=None):
        self.issues = list(issues or [])
        self.items = list(items or [])
        self.calls = []
        self.project = sync.ProjectMetadata(
            project_id="PVT_project",
            fields={
                "Status": sync.ProjectField(
                    field_id="status_field",
                    field_type="ProjectV2SingleSelectField",
                    options={"Todo": "todo", "In Progress": "doing", "Done": "done"},
                ),
                "Start date": sync.ProjectField("start_field", "ProjectV2Field", {}),
                "Target date": sync.ProjectField("target_field", "ProjectV2Field", {}),
            },
        )

    def list_issues(self):
        return list(self.issues)

    def create_issue(self, title, body, labels):
        self.calls.append(("create_issue", title, tuple(labels)))
        issue = sync.IssueSnapshot(
            number=190,
            title=title,
            body=body,
            state="OPEN",
            url="https://github.com/acme/repo/issues/190",
            labels=frozenset(labels),
        )
        self.issues.append(issue)
        return issue

    def update_issue_body(self, issue, body):
        self.calls.append(("update_issue_body", issue.number))
        updated = replace(issue, body=body)
        self.issues[self.issues.index(issue)] = updated
        return updated

    def add_issue_labels(self, issue, labels):
        self.calls.append(("add_issue_labels", issue.number, tuple(labels)))
        updated = replace(issue, labels=issue.labels | frozenset(labels))
        self.issues[self.issues.index(issue)] = updated
        return updated

    def set_issue_state(self, issue, desired_state):
        self.calls.append(("set_issue_state", issue.number, desired_state))
        updated = replace(issue, state=desired_state)
        self.issues[self.issues.index(issue)] = updated
        return updated

    def get_project_metadata(self):
        return self.project

    def list_project_items(self):
        return list(self.items)

    def add_project_item(self, issue_url):
        self.calls.append(("add_project_item", issue_url))
        item = sync.ProjectItemSnapshot(
            item_id="PVTI_new",
            issue_url=issue_url,
            values={},
        )
        self.items.append(item)
        return item

    def set_project_single_select(self, item_id, field_id, option_id):
        self.calls.append(("set_project_single_select", item_id, field_id, option_id))

    def set_project_date(self, item_id, field_id, value):
        self.calls.append(("set_project_date", item_id, field_id, value))


def _managed_issue(task: sync.WbsTask, body_prefix: str = "") -> sync.IssueSnapshot:
    block = sync.render_managed_block(task, "acme/repo")
    return sync.IssueSnapshot(
        number=189,
        title=f"[{task.task_id}] {task.name}",
        body=sync.merge_managed_block(body_prefix, block, task.task_id),
        state="CLOSED" if task.status == "完了" else "OPEN",
        url="https://github.com/acme/repo/issues/189",
        labels=frozenset(sync.REQUIRED_LABELS),
    )


def test_load_wbs_tasks_reads_utf8_bom_and_validates_columns(tmp_path):
    path = tmp_path / "WBS.tsv"
    path.write_text(
        "\t".join(sync.WBS_HEADERS)
        + "\n"
        + "\t".join(
            [
                "T893",
                "8. 本番運用・品質管理",
                "品質管理",
                "GitHub同期",
                "Codex",
                "VSCode + Codex",
                "同期する",
                "完了",
                "2026-07-13",
                "2026-07-13",
            ]
        )
        + "\n",
        encoding="utf-8-sig",
    )

    tasks = sync.load_wbs_tasks(path)

    assert tasks["T893"].status == "完了"
    assert tasks["T893"].target_date == "2026-07-13"


def test_load_wbs_tasks_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "WBS.tsv"
    row = ["T893", "8", "品質", "同期", "Codex", "Codex", "", "完了", "2026-07-13", "2026-07-13"]
    path.write_text(
        "\t".join(sync.WBS_HEADERS) + "\n" + "\t".join(row) + "\n" + "\t".join(row) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(sync.SyncError, match="Duplicate WBS task ID"):
        sync.load_wbs_tasks(path)


@pytest.mark.parametrize(
    ("status", "issue_state", "project_status"),
    [
        ("未着手", "OPEN", "Todo"),
        ("実行中", "OPEN", "In Progress"),
        ("完了", "CLOSED", "Done"),
    ],
)
def test_status_mapping_is_explicit(status, issue_state, project_status):
    assert sync.STATUS_MAPPING[status] == (issue_state, project_status)


def test_find_issue_uses_exact_marker_before_title_fallback():
    task = _task()
    marker_issue = _managed_issue(task)
    similarly_named = replace(
        marker_issue,
        number=188,
        title="[T893_1] 別タスク",
        body="",
        url="https://github.com/acme/repo/issues/188",
    )

    assert sync.find_issue([similarly_named, marker_issue], "T893") == marker_issue


def test_merge_managed_block_preserves_human_written_issue_body():
    task = _task()
    original = "## 人間が記録した証跡\n\nこの段落は保持する。"
    merged = sync.merge_managed_block(
        original, sync.render_managed_block(task, "acme/repo"), task.task_id
    )

    assert original in merged
    assert merged.count(sync.start_marker("T893")) == 1
    assert merged.count(sync.end_marker("T893")) == 1


def test_sync_creates_closes_and_adds_completed_task_to_project():
    gateway = FakeGateway()

    report = sync.sync_tasks(
        {"T893": _task()}, ["T893"], gateway, repo="acme/repo", dry_run=False
    )

    names = [call[0] for call in gateway.calls]
    assert names.count("create_issue") == 1
    assert ("set_issue_state", 190, "CLOSED") in gateway.calls
    assert names.count("add_project_item") == 1
    assert ("set_project_single_select", "PVTI_new", "status_field", "done") in gateway.calls
    assert ("set_project_date", "PVTI_new", "start_field", "2026-07-13") in gateway.calls
    assert ("set_project_date", "PVTI_new", "target_field", "2026-07-13") in gateway.calls
    assert report[0]["issue_number"] == 190


def test_sync_is_idempotent_when_issue_and_project_values_match():
    task = _task()
    issue = _managed_issue(task)
    item = sync.ProjectItemSnapshot(
        item_id="PVTI_existing",
        issue_url=issue.url,
        values={"Status": "Done", "Start date": "2026-07-13", "Target date": "2026-07-13"},
    )
    gateway = FakeGateway([issue], [item])

    report = sync.sync_tasks(
        {task.task_id: task}, [task.task_id], gateway, repo="acme/repo", dry_run=False
    )

    assert gateway.calls == []
    assert report[0]["actions"] == []


def test_sync_is_idempotent_with_github_crlf_issue_body():
    task = _task()
    issue = _managed_issue(task)
    github_issue = replace(issue, body=issue.body.replace("\n", "\r\r\n"))
    item = sync.ProjectItemSnapshot(
        item_id="PVTI_existing",
        issue_url=issue.url,
        values={"Status": "Done", "Start date": "2026-07-13", "Target date": "2026-07-13"},
    )
    gateway = FakeGateway([github_issue], [item])

    report = sync.sync_tasks(
        {task.task_id: task}, [task.task_id], gateway, repo="acme/repo", dry_run=False
    )

    assert gateway.calls == []
    assert report[0]["actions"] == []


def test_sync_updates_open_task_to_in_progress_without_recreating_issue():
    task = _task(status="実行中")
    stale = _managed_issue(replace(task, status="未着手"), body_prefix="既存証跡")
    item = sync.ProjectItemSnapshot(
        item_id="PVTI_existing",
        issue_url=stale.url,
        values={"Status": "Todo", "Start date": "2026-07-13", "Target date": "2026-07-13"},
    )
    gateway = FakeGateway([stale], [item])

    sync.sync_tasks({task.task_id: task}, [task.task_id], gateway, repo="acme/repo", dry_run=False)

    names = [call[0] for call in gateway.calls]
    assert "create_issue" not in names
    assert ("update_issue_body", 189) in gateway.calls
    assert ("set_issue_state", 189, "OPEN") not in gateway.calls
    assert ("set_project_single_select", "PVTI_existing", "status_field", "doing") in gateway.calls


def test_dry_run_plans_changes_without_mutating_github():
    gateway = FakeGateway()

    report = sync.sync_tasks(
        {"T893": _task()}, ["T893"], gateway, repo="acme/repo", dry_run=True
    )

    assert gateway.calls == []
    assert report[0]["issue_number"] is None
    assert "create_issue" in report[0]["actions"]


def test_unknown_task_id_fails_before_any_remote_mutation():
    gateway = FakeGateway()

    with pytest.raises(sync.SyncError, match="Unknown WBS task ID: T999"):
        sync.sync_tasks({"T893": _task()}, ["T999"], gateway, repo="acme/repo", dry_run=False)

    assert gateway.calls == []
