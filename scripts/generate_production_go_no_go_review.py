#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate the T746 production Go/No-Go readiness review.

The checklist source of truth is data/release_go_no_go_criteria.tsv. This
script validates the checklist, joins related WBS task statuses, and emits
JSON/Markdown artifacts for Sheets, docs review, and GitHub evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "T746"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CRITERIA = Path("data") / "release_go_no_go_criteria.tsv"
DEFAULT_WBS = Path("data") / "WBS.tsv"
DEFAULT_JSON = Path("exports") / "production_go_no_go_review.json"
DEFAULT_MD = Path("exports") / "production_go_no_go_review.md"
VALID_STATES = {"PASS", "WARNING", "HUMAN_GATE", "BLOCKED", "N/A"}
STATE_ORDER = {"PASS": 0, "N/A": 0, "WARNING": 1, "HUMAN_GATE": 2, "BLOCKED": 3}
REQUIRED_COLUMNS = [
    "criterion_id",
    "scope",
    "category",
    "criterion",
    "evidence_source",
    "required_state",
    "current_state",
    "owner",
    "decision_authority",
    "related_wbs",
    "related_issue",
    "last_checked",
    "notes",
]
SECRET_PATTERNS = (
    re.compile(r"postgres(?:ql)?://[^\s`\"']+", re.IGNORECASE),
    re.compile(r"Bearer\s+(?=[A-Za-z0-9._=-]*[._=-])[A-Za-z0-9._=-]{6,}", re.IGNORECASE),
    re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+", re.IGNORECASE),
    re.compile(r"sb_(?:secret|publishable|service_role)_[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|token|password|secret)=([A-Za-z0-9._=-]+)", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
)


@dataclass(frozen=True)
class Criterion:
    criterion_id: str
    scope: str
    category: str
    criterion: str
    evidence_source: str
    required_state: str
    current_state: str
    owner: str
    decision_authority: str
    related_wbs: str
    related_issue: str
    last_checked: str
    notes: str
    wbs_statuses: dict[str, str]
    missing_evidence: list[str]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assert_child_path(parent: Path, child: Path) -> None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved == parent_resolved or parent_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {child}")


def resolve_project_path(root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else root / path
    assert_child_path(root, resolved)
    return resolved


def display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def redact_secret_like_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(
            lambda match: match.group(0).split("=")[0] + "=<redacted>"
            if "=" in match.group(0)
            else "<redacted>",
            redacted,
        )
    return redacted


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact_secret_like_text(text), encoding="utf-8", newline="\n")


def load_wbs_statuses(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return {
            (row.get("タスクID") or "").strip(): (row.get("ステータス") or "").strip()
            for row in reader
            if (row.get("タスクID") or "").strip()
        }


def split_refs(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;,]", value or "") if part.strip()]


def evidence_exists(root: Path, evidence: str) -> bool:
    if evidence.startswith(("http://", "https://")):
        return True
    path = root / evidence
    return path.exists()


def load_criteria(path: Path, root: Path, wbs_statuses: dict[str, str]) -> list[Criterion]:
    if not path.exists():
        raise ValueError(f"Criteria TSV not found: {path}")
    criteria: list[Criterion] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing_columns:
            raise ValueError(f"Missing criteria columns: {missing_columns}")
        for row in reader:
            criterion_id = (row.get("criterion_id") or "").strip()
            if not criterion_id:
                continue
            if criterion_id in seen:
                raise ValueError(f"Duplicate criterion_id: {criterion_id}")
            seen.add(criterion_id)
            current_state = (row.get("current_state") or "").strip().upper()
            required_state = (row.get("required_state") or "").strip().upper()
            if current_state not in VALID_STATES:
                raise ValueError(f"Invalid current_state for {criterion_id}: {current_state}")
            if required_state not in VALID_STATES:
                raise ValueError(f"Invalid required_state for {criterion_id}: {required_state}")

            related_ids = split_refs(row.get("related_wbs") or "")
            related_statuses = {
                task_id: wbs_statuses.get(task_id, "missing")
                for task_id in related_ids
                if task_id.startswith("T")
            }
            missing_evidence = [
                evidence
                for evidence in split_refs(row.get("evidence_source") or "")
                if evidence.startswith(("docs/", "scripts/", "src/", "data/", "exports/", ".github/", "index.html"))
                and not evidence_exists(root, evidence)
            ]
            criteria.append(
                Criterion(
                    criterion_id=criterion_id,
                    scope=(row.get("scope") or "").strip(),
                    category=(row.get("category") or "").strip(),
                    criterion=(row.get("criterion") or "").strip(),
                    evidence_source=(row.get("evidence_source") or "").strip(),
                    required_state=required_state,
                    current_state=current_state,
                    owner=(row.get("owner") or "").strip(),
                    decision_authority=(row.get("decision_authority") or "").strip(),
                    related_wbs=(row.get("related_wbs") or "").strip(),
                    related_issue=(row.get("related_issue") or "").strip(),
                    last_checked=(row.get("last_checked") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                    wbs_statuses=related_statuses,
                    missing_evidence=missing_evidence,
                )
            )
    if not criteria:
        raise ValueError(f"No release criteria found in {path}")
    return criteria


def recommendation_for(criteria: list[Criterion]) -> str:
    states = {criterion.current_state for criterion in criteria}
    if "BLOCKED" in states:
        return "NO_GO"
    if "HUMAN_GATE" in states:
        return "CONDITIONAL_GO_AFTER_APPROVAL"
    if "WARNING" in states:
        return "GO_WITH_WARNINGS"
    return "GO"


def build_report(root: Path, criteria_path: Path, wbs_path: Path) -> dict[str, Any]:
    wbs_statuses = load_wbs_statuses(wbs_path)
    criteria = load_criteria(criteria_path, root, wbs_statuses)
    by_scope: dict[str, list[Criterion]] = defaultdict(list)
    for criterion in criteria:
        by_scope[criterion.scope].append(criterion)

    scope_reports = {}
    for scope, rows in sorted(by_scope.items()):
        counter = Counter(row.current_state for row in rows)
        worst = max((row.current_state for row in rows), key=lambda state: STATE_ORDER[state])
        scope_reports[scope] = {
            "recommendation": recommendation_for(rows),
            "worst_state": worst,
            "counts": dict(counter),
            "total": len(rows),
        }

    overall = "NO_GO" if any(row.current_state == "BLOCKED" for row in criteria) else recommendation_for(criteria)
    evidence_warnings = [
        {"criterion_id": row.criterion_id, "missing_evidence": row.missing_evidence}
        for row in criteria
        if row.missing_evidence
    ]
    if evidence_warnings and overall == "GO":
        overall = "GO_WITH_WARNINGS"

    return {
        "task_id": TASK_ID,
        "generated_at": utc_timestamp(),
        "criteria_source": display_path(root, criteria_path),
        "wbs_source": display_path(root, wbs_path),
        "overall_recommendation": overall,
        "summary": {
            "total": len(criteria),
            "counts": dict(Counter(row.current_state for row in criteria)),
            "evidence_warnings": len(evidence_warnings),
        },
        "scopes": scope_reports,
        "criteria": [asdict(row) for row in criteria],
        "evidence_warnings": evidence_warnings,
        "approval_process": [
            "Codex/Antigravity/Claude各レーンが担当ゲートの証跡をdocs・exports・Issueへ残す。",
            "T746の判定表をSheetsのリリース判定タブへ同期し、未完了ゲートをCEO/法務/開発責任者へ割り当てる。",
            "public_paid_launch は BLOCKED が0件、HUMAN_GATE がCEO/法務承認済みになるまでNo-Go。",
            "Go判定後も rollback担当者、known-good commit、Firebase release、Cloud Run revision、Supabase backup/PITR時刻を記録してから本番反映する。",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 本番リリース Go/No-Go 判定レビュー (T746)",
        "",
        f"- 生成時刻(UTC): {report['generated_at']}",
        f"- 正本TSV: `{report['criteria_source']}`",
        f"- WBS正本: `{report['wbs_source']}`",
        f"- 総合判定: **{report['overall_recommendation']}**",
        "",
        "## スコープ別判定",
        "",
        "| スコープ | 判定 | 件数 | 状態内訳 |",
        "| :--- | :--- | ---: | :--- |",
    ]
    for scope, row in report["scopes"].items():
        counts = ", ".join(f"{key}:{value}" for key, value in sorted(row["counts"].items()))
        lines.append(f"| {scope} | {row['recommendation']} | {row['total']} | {counts} |")

    lines.extend(
        [
            "",
            "## 判定基準",
            "",
            "| ID | Scope | Category | State | Criterion | Evidence | Related WBS | Authority | Notes |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for criterion in report["criteria"]:
        notes = criterion["notes"].replace("|", "\\|")
        criterion_text = criterion["criterion"].replace("|", "\\|")
        evidence = criterion["evidence_source"].replace("|", "\\|")
        lines.append(
            "| {criterion_id} | {scope} | {category} | {current_state} | {criterion} | {evidence} | {related_wbs} | {decision_authority} | {notes} |".format(
                criterion_id=criterion["criterion_id"],
                scope=criterion["scope"],
                category=criterion["category"],
                current_state=criterion["current_state"],
                criterion=criterion_text,
                evidence=evidence,
                related_wbs=criterion["related_wbs"],
                decision_authority=criterion["decision_authority"],
                notes=notes,
            )
        )

    lines.extend(["", "## 承認プロセス", ""])
    for step in report["approval_process"]:
        lines.append(f"- {step}")

    if report["evidence_warnings"]:
        lines.extend(["", "## Evidence Warnings", ""])
        for warning in report["evidence_warnings"]:
            missing = ", ".join(warning["missing_evidence"])
            lines.append(f"- {warning['criterion_id']}: {missing}")
    lines.append("")
    return "\n".join(lines)


def write_json(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--criteria", type=Path, default=DEFAULT_CRITERIA)
    parser.add_argument("--wbs", type=Path, default=DEFAULT_WBS)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-report", type=Path, default=DEFAULT_MD)
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    criteria_path = resolve_project_path(root, args.criteria)
    wbs_path = resolve_project_path(root, args.wbs)
    json_path = resolve_project_path(root, args.json_report)
    markdown_path = resolve_project_path(root, args.markdown_report)

    try:
        report = build_report(root, criteria_path, wbs_path)
    except ValueError as exc:
        print(f"[-] T746 Go/No-Go review failed: {exc}", file=sys.stderr)
        return 2

    write_json(json_path, report)
    write_text(markdown_path, render_markdown(report))
    print(
        "[+] T746 Go/No-Go review generated: "
        f"{report['overall_recommendation']} "
        f"({report['summary']['counts']})"
    )
    print(f"[*] JSON: {display_path(root, json_path)}")
    print(f"[*] Markdown: {display_path(root, markdown_path)}")

    if args.fail_on_blocked and report["overall_recommendation"] == "NO_GO":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
