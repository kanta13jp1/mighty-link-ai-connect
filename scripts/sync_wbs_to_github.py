"""Synchronize selected WBS tasks to GitHub Issues and Project #1.

The command is deliberately targeted: callers must name each WBS task ID.
This prevents a routine closeout from publishing every historical WBS row to a
public repository. Existing human-written issue content is preserved; only a
marker-delimited status block is managed by this script.

Usage:
    python scripts/sync_wbs_to_github.py T893
    python scripts/sync_wbs_to_github.py T888 T889 T890 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WBS_PATH = ROOT / "data" / "WBS.tsv"
DEFAULT_REPO = "kanta13jp1/mighty-link-ai-connect"
DEFAULT_PROJECT_OWNER = "kanta13jp1"
DEFAULT_PROJECT_NUMBER = 1

WBS_HEADERS = [
    "タスクID",
    "大フェーズ",
    "小フェーズ",
    "タスク名",
    "担当",
    "実行エンジン",
    "Sheets Live 連携アクション",
    "ステータス",
    "開始日",
    "終了予定日",
]

STATUS_MAPPING = {
    "未着手": ("OPEN", "Todo"),
    "実行中": ("OPEN", "In Progress"),
    "完了": ("CLOSED", "Done"),
}
REQUIRED_LABELS = ("wbs", "github-project")


class SyncError(RuntimeError):
    """Raised when local or remote state cannot be synchronized safely."""


@dataclass(frozen=True)
class WbsTask:
    task_id: str
    phase: str
    sub_phase: str
    name: str
    owner: str
    engine: str
    status: str
    start_date: str
    target_date: str


@dataclass(frozen=True)
class IssueSnapshot:
    number: int
    title: str
    body: str
    state: str
    url: str
    labels: frozenset[str]


@dataclass(frozen=True)
class ProjectField:
    field_id: str
    field_type: str
    options: dict[str, str]


@dataclass(frozen=True)
class ProjectMetadata:
    project_id: str
    fields: dict[str, ProjectField]


@dataclass(frozen=True)
class ProjectItemSnapshot:
    item_id: str
    issue_url: str
    values: dict[str, str]


def _validated_date(value: str, *, task_id: str, field_name: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise SyncError(f"Invalid {field_name} for {task_id}: {value!r}") from exc
    return value


def load_wbs_tasks(path: Path = DEFAULT_WBS_PATH) -> dict[str, WbsTask]:
    if not path.exists():
        raise SyncError(f"WBS file not found: {path}")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != WBS_HEADERS:
            raise SyncError(
                "Unexpected WBS header. "
                f"Expected {WBS_HEADERS!r}, got {reader.fieldnames!r}"
            )

        tasks: dict[str, WbsTask] = {}
        for line_number, row in enumerate(reader, start=2):
            task_id = (row.get("タスクID") or "").strip()
            if not task_id:
                continue
            if task_id in tasks:
                raise SyncError(f"Duplicate WBS task ID at line {line_number}: {task_id}")

            required = {
                name: (row.get(name) or "").strip()
                for name in ("大フェーズ", "タスク名", "担当", "実行エンジン", "ステータス", "開始日", "終了予定日")
            }
            blank = [name for name, value in required.items() if not value]
            if blank:
                raise SyncError(f"Blank required WBS field(s) for {task_id}: {', '.join(blank)}")
            if required["ステータス"] not in STATUS_MAPPING:
                raise SyncError(
                    f"Unsupported WBS status for {task_id}: {required['ステータス']!r}"
                )

            start_date = _validated_date(
                required["開始日"], task_id=task_id, field_name="開始日"
            )
            target_date = _validated_date(
                required["終了予定日"], task_id=task_id, field_name="終了予定日"
            )
            if start_date > target_date:
                raise SyncError(
                    f"Inverted WBS schedule for {task_id}: {start_date} > {target_date}"
                )

            tasks[task_id] = WbsTask(
                task_id=task_id,
                phase=required["大フェーズ"],
                sub_phase=(row.get("小フェーズ") or "").strip(),
                name=required["タスク名"],
                owner=required["担当"],
                engine=required["実行エンジン"],
                status=required["ステータス"],
                start_date=start_date,
                target_date=target_date,
            )

    return tasks


def start_marker(task_id: str) -> str:
    return f"<!-- mighty-link-wbs:{task_id}:start -->"


def end_marker(task_id: str) -> str:
    return f"<!-- mighty-link-wbs:{task_id}:end -->"


def normalize_issue_body(body: str) -> str:
    """Normalize GitHub CLI/API newline variants before marker comparison."""
    return re.sub(r"\r+\n", "\n", body).replace("\r", "\n")


def issue_bodies_match(left: str, right: str) -> bool:
    return normalize_issue_body(left).rstrip() == normalize_issue_body(right).rstrip()


def render_managed_block(task: WbsTask, repo: str) -> str:
    source_url = f"https://github.com/{repo}/blob/main/data/WBS.tsv"
    docs_url = f"https://github.com/{repo}/blob/main/docs/WBS.md"
    return "\n".join(
        [
            start_marker(task.task_id),
            "## WBS同期情報",
            "",
            f"- タスクID: `{task.task_id}`",
            f"- フェーズ: {task.phase} / {task.sub_phase or '-'}",
            f"- 担当: {task.owner}",
            f"- 実行レーン: {task.engine}",
            f"- WBS状態: `{task.status}`",
            f"- 予定: `{task.start_date}` から `{task.target_date}`",
            f"- 正本: [data/WBS.tsv]({source_url}) / [docs/WBS.md]({docs_url})",
            "",
            "> この範囲は同期スクリプトが管理します。secretやWBSの長文詳細は転記しません。",
            end_marker(task.task_id),
        ]
    )


def merge_managed_block(existing_body: str, block: str, task_id: str) -> str:
    existing_body = normalize_issue_body(existing_body)
    start = start_marker(task_id)
    end = end_marker(task_id)
    has_start = start in existing_body
    has_end = end in existing_body
    if has_start != has_end:
        raise SyncError(
            f"Issue body has an incomplete managed marker pair for {task_id}; refusing to overwrite"
        )
    if has_start:
        prefix, remainder = existing_body.split(start, 1)
        _old, suffix = remainder.split(end, 1)
        return f"{prefix}{block}{suffix}"
    if not existing_body.strip():
        return block
    return f"{existing_body.rstrip()}\n\n{block}\n"


def build_new_issue_body(task: WbsTask, repo: str) -> str:
    intro = (
        "このIssueはWBS正本の進捗をGitHub Projectへ同期するために作成されました。"
        "実装・検証の詳細はリポジトリ内の証跡を参照してください。"
    )
    return merge_managed_block(intro, render_managed_block(task, repo), task.task_id)


def build_issue_title(task: WbsTask) -> str:
    title = f"[{task.task_id}] {task.name}"
    return title if len(title) <= 240 else f"{title[:237]}..."


def _title_matches_task(title: str, task_id: str) -> bool:
    pattern = rf"^(?:\[{re.escape(task_id)}\]|{re.escape(task_id)})(?=\s|[:：-])"
    return re.search(pattern, title, flags=re.IGNORECASE) is not None


def find_issue(issues: Iterable[IssueSnapshot], task_id: str) -> IssueSnapshot | None:
    issue_list = list(issues)
    marker_matches = [issue for issue in issue_list if start_marker(task_id) in issue.body]
    if len(marker_matches) > 1:
        numbers = ", ".join(f"#{issue.number}" for issue in marker_matches)
        raise SyncError(f"Multiple managed Issues found for {task_id}: {numbers}")
    if marker_matches:
        return marker_matches[0]

    title_matches = [issue for issue in issue_list if _title_matches_task(issue.title, task_id)]
    if len(title_matches) > 1:
        numbers = ", ".join(f"#{issue.number}" for issue in title_matches)
        raise SyncError(f"Multiple title-matched Issues found for {task_id}: {numbers}")
    return title_matches[0] if title_matches else None


def _require_project_fields(
    metadata: ProjectMetadata, project_statuses: Iterable[str]
) -> None:
    missing = [name for name in ("Status", "Start date", "Target date") if name not in metadata.fields]
    if missing:
        raise SyncError(f"GitHub Project is missing required field(s): {', '.join(missing)}")
    status_field = metadata.fields["Status"]
    missing_options = [name for name in project_statuses if name not in status_field.options]
    if missing_options:
        raise SyncError(
            "GitHub Project Status is missing option(s): " + ", ".join(sorted(set(missing_options)))
        )


def _planned_actions_for_missing_task(task: WbsTask) -> list[str]:
    issue_state, project_status = STATUS_MAPPING[task.status]
    actions = ["create_issue"]
    if issue_state == "CLOSED":
        actions.append("close_issue")
    actions.extend(
        [
            "add_project_item",
            f"set_project_status:{project_status}",
            f"set_project_start_date:{task.start_date}",
            f"set_project_target_date:{task.target_date}",
        ]
    )
    return actions


def sync_tasks(
    tasks: dict[str, WbsTask],
    task_ids: Iterable[str],
    gateway: Any,
    *,
    repo: str,
    dry_run: bool,
) -> list[dict[str, Any]]:
    selected_ids = list(dict.fromkeys(task_ids))
    if not selected_ids:
        raise SyncError("At least one WBS task ID is required")
    for task_id in selected_ids:
        if task_id not in tasks:
            raise SyncError(f"Unknown WBS task ID: {task_id}")

    selected = [tasks[task_id] for task_id in selected_ids]
    issues = gateway.list_issues()
    metadata = gateway.get_project_metadata()
    _require_project_fields(
        metadata, (STATUS_MAPPING[task.status][1] for task in selected)
    )
    project_items = gateway.list_project_items()
    item_by_url = {item.issue_url: item for item in project_items if item.issue_url}

    report: list[dict[str, Any]] = []
    for task in selected:
        issue = find_issue(issues, task.task_id)
        actions: list[str] = []

        if dry_run and issue is None:
            actions = _planned_actions_for_missing_task(task)
            report.append(
                {
                    "task_id": task.task_id,
                    "wbs_status": task.status,
                    "issue_number": None,
                    "issue_url": None,
                    "actions": actions,
                    "dry_run": True,
                }
            )
            continue

        if issue is None:
            issue = gateway.create_issue(
                build_issue_title(task),
                build_new_issue_body(task, repo),
                REQUIRED_LABELS,
            )
            issues.append(issue)
            actions.append("create_issue")
        else:
            managed = render_managed_block(task, repo)
            desired_body = merge_managed_block(issue.body, managed, task.task_id)
            if not issue_bodies_match(desired_body, issue.body):
                actions.append("update_managed_block")
                if not dry_run:
                    issue = gateway.update_issue_body(issue, desired_body)

            missing_labels = sorted(set(REQUIRED_LABELS) - set(issue.labels))
            if missing_labels:
                actions.append(f"add_labels:{','.join(missing_labels)}")
                if not dry_run:
                    issue = gateway.add_issue_labels(issue, missing_labels)

        desired_issue_state, desired_project_status = STATUS_MAPPING[task.status]
        if issue.state.upper() != desired_issue_state:
            action = "close_issue" if desired_issue_state == "CLOSED" else "reopen_issue"
            actions.append(action)
            if not dry_run:
                issue = gateway.set_issue_state(issue, desired_issue_state)

        item = item_by_url.get(issue.url)
        if item is None:
            actions.append("add_project_item")
            if not dry_run:
                item = gateway.add_project_item(issue.url)
                item_by_url[issue.url] = item

        desired_fields = {
            "Status": desired_project_status,
            "Start date": task.start_date,
            "Target date": task.target_date,
        }
        for field_name, desired_value in desired_fields.items():
            current_value = item.values.get(field_name) if item is not None else None
            if current_value == desired_value:
                continue
            action_name = {
                "Status": "set_project_status",
                "Start date": "set_project_start_date",
                "Target date": "set_project_target_date",
            }[field_name]
            actions.append(f"{action_name}:{desired_value}")
            if dry_run:
                continue
            if item is None:
                raise SyncError(f"Project item was not created for {task.task_id}")
            field = metadata.fields[field_name]
            if field_name == "Status":
                gateway.set_project_single_select(
                    item.item_id,
                    field.field_id,
                    field.options[desired_value],
                )
            else:
                gateway.set_project_date(item.item_id, field.field_id, desired_value)

        report.append(
            {
                "task_id": task.task_id,
                "wbs_status": task.status,
                "issue_number": issue.number,
                "issue_url": issue.url,
                "actions": actions,
                "dry_run": dry_run,
            }
        )

    return report


class GitHubCLI:
    def __init__(self, repo: str, project_owner: str, project_number: int):
        self.repo = repo
        self.project_owner = project_owner
        self.project_number = project_number
        self._project_metadata: ProjectMetadata | None = None

    def _run(self, args: list[str], *, input_text: str | None = None) -> str:
        env = os.environ.copy()
        env["GH_PAGER"] = "cat"
        env["NO_COLOR"] = "1"
        result = subprocess.run(
            ["gh", *args],
            cwd=ROOT,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise SyncError(f"gh {' '.join(args[:3])} failed: {detail}")
        return result.stdout.strip()

    def _json(self, args: list[str]) -> dict[str, Any]:
        raw = self._run(args)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SyncError(f"gh returned invalid JSON for {' '.join(args[:3])}") from exc
        if not isinstance(value, dict):
            raise SyncError(f"gh returned an unexpected JSON shape for {' '.join(args[:3])}")
        return value

    def check_prerequisites(self) -> None:
        self._run(["--version"])
        self._run(["auth", "status"])
        payload = self._json(["repo", "view", self.repo, "--json", "nameWithOwner"])
        if payload.get("nameWithOwner") != self.repo:
            raise SyncError(
                f"Authenticated repository mismatch: expected {self.repo}, got {payload.get('nameWithOwner')}"
            )

    def list_issues(self) -> list[IssueSnapshot]:
        payload = self._run(
            [
                "issue",
                "list",
                "--repo",
                self.repo,
                "--state",
                "all",
                "--limit",
                "1000",
                "--json",
                "number,title,body,state,url,labels",
            ]
        )
        try:
            rows = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise SyncError("gh issue list returned invalid JSON") from exc
        issues = []
        for row in rows:
            labels = frozenset(
                label.get("name", "")
                for label in (row.get("labels") or [])
                if label.get("name")
            )
            issues.append(
                IssueSnapshot(
                    number=int(row["number"]),
                    title=row.get("title") or "",
                    body=row.get("body") or "",
                    state=(row.get("state") or "OPEN").upper(),
                    url=row["url"],
                    labels=labels,
                )
            )
        return issues

    def create_issue(self, title: str, body: str, labels: Iterable[str]) -> IssueSnapshot:
        args = ["issue", "create", "--repo", self.repo, "--title", title, "--body-file", "-"]
        for label in labels:
            args.extend(["--label", label])
        url = self._run(args, input_text=body).splitlines()[-1].strip()
        try:
            number = int(url.rstrip("/").rsplit("/", 1)[1])
        except (IndexError, ValueError) as exc:
            raise SyncError(f"Could not parse created Issue URL: {url!r}") from exc
        return IssueSnapshot(number, title, body, "OPEN", url, frozenset(labels))

    def update_issue_body(self, issue: IssueSnapshot, body: str) -> IssueSnapshot:
        self._run(
            ["issue", "edit", str(issue.number), "--repo", self.repo, "--body-file", "-"],
            input_text=body,
        )
        return replace(issue, body=body)

    def add_issue_labels(
        self, issue: IssueSnapshot, labels: Iterable[str]
    ) -> IssueSnapshot:
        labels = tuple(labels)
        args = ["issue", "edit", str(issue.number), "--repo", self.repo]
        for label in labels:
            args.extend(["--add-label", label])
        self._run(args)
        return replace(issue, labels=issue.labels | frozenset(labels))

    def set_issue_state(self, issue: IssueSnapshot, desired_state: str) -> IssueSnapshot:
        if desired_state == "CLOSED":
            self._run(
                [
                    "issue",
                    "close",
                    str(issue.number),
                    "--repo",
                    self.repo,
                    "--reason",
                    "completed",
                ]
            )
        elif desired_state == "OPEN":
            self._run(["issue", "reopen", str(issue.number), "--repo", self.repo])
        else:
            raise SyncError(f"Unsupported Issue state: {desired_state}")
        return replace(issue, state=desired_state)

    def get_project_metadata(self) -> ProjectMetadata:
        if self._project_metadata is not None:
            return self._project_metadata
        project = self._json(
            [
                "project",
                "view",
                str(self.project_number),
                "--owner",
                self.project_owner,
                "--format",
                "json",
            ]
        )
        fields_payload = self._json(
            [
                "project",
                "field-list",
                str(self.project_number),
                "--owner",
                self.project_owner,
                "--format",
                "json",
            ]
        )
        fields = {}
        for raw in fields_payload.get("fields", []):
            options = {
                option["name"]: option["id"]
                for option in raw.get("options", [])
                if option.get("name") and option.get("id")
            }
            fields[raw["name"]] = ProjectField(raw["id"], raw.get("type", ""), options)
        self._project_metadata = ProjectMetadata(project["id"], fields)
        return self._project_metadata

    def list_project_items(self) -> list[ProjectItemSnapshot]:
        metadata = self.get_project_metadata()
        payload = self._json(
            [
                "project",
                "item-list",
                str(self.project_number),
                "--owner",
                self.project_owner,
                "--limit",
                "1000",
                "--format",
                "json",
            ]
        )
        canonical = {name.casefold(): name for name in metadata.fields}
        items = []
        for raw in payload.get("items", []):
            content = raw.get("content") or {}
            issue_url = content.get("url") or ""
            if not issue_url:
                continue
            values: dict[str, str] = {}
            for key, value in raw.items():
                field_name = canonical.get(str(key).casefold())
                if not field_name:
                    continue
                if isinstance(value, dict):
                    value = value.get("name") or value.get("value") or ""
                if value is not None:
                    values[field_name] = str(value)
            items.append(ProjectItemSnapshot(raw["id"], issue_url, values))
        return items

    def add_project_item(self, issue_url: str) -> ProjectItemSnapshot:
        payload = self._json(
            [
                "project",
                "item-add",
                str(self.project_number),
                "--owner",
                self.project_owner,
                "--url",
                issue_url,
                "--format",
                "json",
            ]
        )
        item_id = payload.get("id")
        if not item_id:
            raise SyncError(f"gh project item-add returned no item id for {issue_url}")
        return ProjectItemSnapshot(item_id, issue_url, {})

    def set_project_single_select(
        self, item_id: str, field_id: str, option_id: str
    ) -> None:
        metadata = self.get_project_metadata()
        self._run(
            [
                "project",
                "item-edit",
                "--id",
                item_id,
                "--project-id",
                metadata.project_id,
                "--field-id",
                field_id,
                "--single-select-option-id",
                option_id,
            ]
        )

    def set_project_date(self, item_id: str, field_id: str, value: str) -> None:
        metadata = self.get_project_metadata()
        self._run(
            [
                "project",
                "item-edit",
                "--id",
                item_id,
                "--project-id",
                metadata.project_id,
                "--field-id",
                field_id,
                "--date",
                value,
            ]
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_ids", nargs="+", help="WBS task IDs to synchronize")
    parser.add_argument("--wbs-path", type=Path, default=DEFAULT_WBS_PATH)
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", DEFAULT_REPO))
    parser.add_argument("--project-owner", default=DEFAULT_PROJECT_OWNER)
    parser.add_argument("--project-number", type=int, default=DEFAULT_PROJECT_NUMBER)
    parser.add_argument("--dry-run", action="store_true", help="Plan without GitHub mutations")
    parser.add_argument("--report", type=Path, help="Optional JSON evidence report path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args(argv)
    try:
        tasks = load_wbs_tasks(args.wbs_path)
        gateway = GitHubCLI(args.repo, args.project_owner, args.project_number)
        gateway.check_prerequisites()
        results = sync_tasks(
            tasks,
            args.task_ids,
            gateway,
            repo=args.repo,
            dry_run=args.dry_run,
        )
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repository": args.repo,
            "project_owner": args.project_owner,
            "project_number": args.project_number,
            "dry_run": args.dry_run,
            "results": results,
        }
        if args.report:
            report_path = args.report if args.report.is_absolute() else ROOT / args.report
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"[+] Wrote report: {report_path.relative_to(ROOT)}")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except SyncError as exc:
        print(f"[-] GitHub WBS sync failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
