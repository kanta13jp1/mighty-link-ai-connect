#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Audit issue and QA tracker rows for unresolved development blockers."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ISSUES = PROJECT_ROOT / "data" / "issues_tracker.tsv"
DEFAULT_QA = PROJECT_ROOT / "data" / "qa_tracker.tsv"
DEFAULT_JSON = PROJECT_ROOT / "exports" / "issue_qa_blocker_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "issue_qa_blocker_audit.md"

ISSUE_BLOCKER_STATES = {"open"}
QA_ALLOWED_STATES = {"回答済", "想定済", "resolved", "closed"}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def build_report(issues: list[dict[str, str]], qa_rows: list[dict[str, str]]) -> dict[str, Any]:
    issue_status_counts = Counter(row.get("状態", "") for row in issues)
    qa_status_counts = Counter(row.get("状態", "") for row in qa_rows)
    issue_blockers = [
        {
            "id": row.get("ID", ""),
            "severity": row.get("重要度", ""),
            "category": row.get("カテゴリ", ""),
            "title": row.get("タイトル", ""),
            "related_wbs": row.get("関連 WBS", ""),
            "related_issue": row.get("関連 Issue", ""),
        }
        for row in issues
        if row.get("状態", "") in ISSUE_BLOCKER_STATES
    ]
    qa_blockers = [
        {
            "id": row.get("ID", ""),
            "category": row.get("カテゴリ", ""),
            "question": row.get("質問", ""),
            "state": row.get("状態", ""),
            "related_topic": row.get("関連論点", ""),
        }
        for row in qa_rows
        if row.get("状態", "") not in QA_ALLOWED_STATES
    ]
    status = "pass" if not issue_blockers and not qa_blockers else "blocked"
    return {
        "status": status,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "issue_total": len(issues),
        "qa_total": len(qa_rows),
        "issue_status_counts": dict(sorted(issue_status_counts.items())),
        "qa_status_counts": dict(sorted(qa_status_counts.items())),
        "issue_blocker_count": len(issue_blockers),
        "qa_blocker_count": len(qa_blockers),
        "issue_blockers": issue_blockers,
        "qa_blockers": qa_blockers,
    }


def write_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "- none"
    return "\n".join(f"- {key or '(blank)'}: {value}" for key, value in counts.items())


def write_markdown(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 課題管理表・QA表 開発ブロッカー監査",
        "",
        f"- 生成日時: {report['generated_at']}",
        f"- 判定: `{report['status']}`",
        f"- 課題行数: {report['issue_total']}",
        f"- QA行数: {report['qa_total']}",
        f"- 課題ブロッカー数: {report['issue_blocker_count']}",
        f"- QAブロッカー数: {report['qa_blocker_count']}",
        "",
        "## 課題ステータス",
        "",
        format_counts(report["issue_status_counts"]),
        "",
        "## QAステータス",
        "",
        format_counts(report["qa_status_counts"]),
        "",
    ]
    if report["issue_blockers"]:
        lines.extend(["## 課題ブロッカー", ""])
        for row in report["issue_blockers"]:
            lines.append(f"- {row['id']} [{row['severity']}] {row['title']} ({row['related_wbs']})")
        lines.append("")
    if report["qa_blockers"]:
        lines.extend(["## QAブロッカー", ""])
        for row in report["qa_blockers"]:
            lines.append(f"- {row['id']} [{row['state']}] {row['question']}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issues", type=Path, default=DEFAULT_ISSUES)
    parser.add_argument("--qa", type=Path, default=DEFAULT_QA)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    parser.add_argument("--fail-on-blockers", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report(read_tsv(args.issues), read_tsv(args.qa))
    write_json(report, args.json_output)
    write_markdown(report, args.md_output)
    print(
        "Issue/QA blocker audit: "
        f"{report['status']} "
        f"(issues={report['issue_blocker_count']}, qa={report['qa_blocker_count']})"
    )
    if args.fail_on_blockers and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
