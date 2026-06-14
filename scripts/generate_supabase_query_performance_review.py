#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate the Supabase Query Performance dashboard review artifact for T761.

The review turns the T750 diagnostic report into a weekly operator checklist for
Supabase Dashboard Query Performance, Performance Advisor, Index Advisor, and
follow-up migration decisions. It intentionally does not require production
credentials and never writes secret values.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "T761"
DEFAULT_PERFORMANCE_REPORT = Path("exports") / "supabase_performance_report.json"
DEFAULT_REVIEW_JSON = Path("exports") / "supabase_query_performance_review.json"
DEFAULT_REVIEW_MD = Path("exports") / "supabase_query_performance_review.md"
STATUS_ORDER = {"ok": 0, "ready": 1, "warning": 2, "critical": 3}
SECRET_PATTERNS = (
    re.compile(r"postgres(?:ql)?://[^\s`]+", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"sb_secret_[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
)


@dataclass(frozen=True)
class ReviewCheck:
    key: str
    status: str
    source: str
    action: str
    evidence: str


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
        redacted = pattern.sub("<redacted>", redacted)
    return redacted


def read_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"invalid JSON: {exc}"
    return loaded if isinstance(loaded, dict) else {}, None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact_secret_like_text(text), encoding="utf-8", newline="\n")


def dashboard_checklist() -> list[dict[str, str]]:
    return [
        {
            "area": "Query Performance",
            "action": "Open Supabase Dashboard > Database > Query Performance and sort by total time, mean time, and calls.",
            "decision": "Map the top slow queries to API route or UI operation before changing indexes.",
        },
        {
            "area": "Performance Advisor",
            "action": "Open Database > Performance Advisor and rerun checks after fixes.",
            "decision": "Create a GitHub Issue for every warning that affects production reads, writes, locks, or bloat.",
        },
        {
            "area": "Index Advisor",
            "action": "For each slow query, open the Indexes tab and compare suggested indexes with existing indexes.",
            "decision": "Accept only recommendations backed by EXPLAIN evidence and expected production query shape.",
        },
        {
            "area": "SQL / Inspect",
            "action": "Run supabase inspect db outliers, index-usage, unused-indexes, seq-scans, cache-hit, locks, and blocking.",
            "decision": "Use the CLI output to validate Dashboard findings and avoid one-off UI-only decisions.",
        },
        {
            "area": "Migration",
            "action": "Record accepted DDL as a forward migration and prefer CREATE INDEX CONCURRENTLY for production-sized tables.",
            "decision": "Never apply index DDL directly in production without WBS, Issue, rollback note, and staging evidence.",
        },
    ]


def inspect_commands() -> list[str]:
    return [
        "supabase inspect db outliers",
        "supabase inspect db index-usage",
        "supabase inspect db unused-indexes",
        "supabase inspect db seq-scans",
        "supabase inspect db cache-hit",
        "supabase inspect db locks",
        "supabase inspect db blocking",
    ]


def build_checks(root: Path, report_path: Path, report: dict[str, Any], read_error: str | None) -> list[ReviewCheck]:
    checks: list[ReviewCheck] = []
    source = display_path(root, report_path)
    if read_error:
        return [
            ReviewCheck(
                key="performance_report",
                status="critical",
                source=source,
                action="Regenerate the T750 performance diagnostic report before Dashboard review.",
                evidence=read_error,
            )
        ]

    report_status = str(report.get("status") or "unknown")
    dry_run = bool(report.get("dry_run"))
    probes = report.get("probes") if isinstance(report.get("probes"), list) else []
    api_results = report.get("api_results") if isinstance(report.get("api_results"), list) else []

    if report_status.startswith("failed"):
        status = "critical"
        action = "Fix the diagnostic execution failure before tuning indexes."
    elif dry_run:
        status = "ready"
        action = "Use this dry-run bundle for the next live Supabase Dashboard review."
    else:
        status = "ok"
        action = "Review the live diagnostic output alongside Supabase Dashboard before opening index changes."

    checks.append(
        ReviewCheck(
            key="diagnostic_report_status",
            status=status,
            source=source,
            action=action,
            evidence=f"status={report_status}, dry_run={dry_run}, probes={len(probes)}, api_results={len(api_results)}",
        )
    )

    required_probe_names = {
        "extension_status",
        "top_queries_by_total_time",
        "top_queries_by_mean_time",
        "sequential_scan_pressure",
        "unused_indexes",
        "large_indexes",
        "vacuum_analyze_lag",
    }
    observed_probe_names = {str(probe.get("name")) for probe in probes if isinstance(probe, dict)}
    missing = sorted(required_probe_names - observed_probe_names)
    checks.append(
        ReviewCheck(
            key="diagnostic_probe_coverage",
            status="critical" if missing else "ok",
            source=source,
            action="Keep the diagnostic bundle aligned with Supabase pg_stat_statements and index review needs.",
            evidence=f"missing={','.join(missing) if missing else 'none'}",
        )
    )

    checks.append(
        ReviewCheck(
            key="dashboard_review_gate",
            status="ready",
            source="Supabase Dashboard",
            action="Run Query Performance, Performance Advisor, and Index Advisor review before any production index migration.",
            evidence="manual dashboard confirmation required; no production credentials stored in this artifact",
        )
    )

    checks.append(
        ReviewCheck(
            key="migration_safety_gate",
            status="ready",
            source="DB_MIGRATION_MANAGEMENT_RUNBOOK.md",
            action="Use forward migrations, staging verification, and CREATE INDEX CONCURRENTLY where applicable.",
            evidence="direct production DDL is disallowed by project operating rules",
        )
    )

    return checks


def summarize_checks(checks: list[ReviewCheck]) -> dict[str, int]:
    counter = Counter(check.status for check in checks)
    return {status: int(counter.get(status, 0)) for status in ("ok", "ready", "warning", "critical")}


def overall_status(checks: list[ReviewCheck]) -> str:
    if not checks:
        return "warning"
    return max((check.status for check in checks), key=lambda value: STATUS_ORDER.get(value, 1))


def build_report(root: Path, performance_report_path: Path) -> dict[str, Any]:
    report, read_error = read_json(performance_report_path)
    checks = build_checks(root, performance_report_path, report, read_error)
    return {
        "task_id": TASK_ID,
        "generated_at_utc": utc_timestamp(),
        "overall_status": overall_status(checks),
        "summary": summarize_checks(checks),
        "sources": {
            "performance_report": display_path(root, performance_report_path),
            "supabase_dashboard": "Database > Query Performance / Performance Advisor / Index Advisor",
            "runbook": "docs/SUPABASE_QUERY_PERFORMANCE_DASHBOARD_RUNBOOK.md",
        },
        "checks": [asdict(check) for check in checks],
        "dashboard_checklist": dashboard_checklist(),
        "inspect_commands": inspect_commands(),
        "tuning_rules": [
            "Do not add or drop indexes from a single slow-query observation.",
            "Prefer measured query plans from staging and production-like data volume.",
            "Create or update a GitHub Issue before accepted DDL work.",
            "Write accepted index DDL as a forward migration and include rollback notes.",
            "Review unused indexes across at least two reporting cycles before dropping them.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Supabase Query Performance Review",
        "",
        f"- Task: {report['task_id']}",
        f"- Generated: {report['generated_at_utc']}",
        f"- Overall status: {report['overall_status']}",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in report["summary"].items():
        lines.append(f"| {status} | {count} |")

    lines.extend(
        [
            "",
            "## Dashboard Checklist",
            "",
            "| Area | Action | Decision Rule |",
            "| --- | --- | --- |",
        ]
    )
    for item in report["dashboard_checklist"]:
        lines.append(f"| {item['area']} | {item['action']} | {item['decision']} |")

    lines.extend(
        [
            "",
            "## Generated Checks",
            "",
            "| Key | Status | Source | Action | Evidence |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for check in report["checks"]:
        lines.append(
            "| {key} | {status} | {source} | {action} | {evidence} |".format(
                key=str(check["key"]).replace("|", "\\|"),
                status=str(check["status"]).replace("|", "\\|"),
                source=str(check["source"]).replace("|", "\\|"),
                action=str(check["action"]).replace("|", "\\|"),
                evidence=str(check["evidence"]).replace("|", "\\|"),
            )
        )

    lines.extend(["", "## Supabase Inspect Commands", ""])
    for command in report["inspect_commands"]:
        lines.append(f"- `{command}`")

    lines.extend(["", "## Tuning Rules", ""])
    for rule in report["tuning_rules"]:
        lines.append(f"- {rule}")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--performance-report", type=Path, default=DEFAULT_PERFORMANCE_REPORT)
    parser.add_argument("--review-json", type=Path, default=DEFAULT_REVIEW_JSON)
    parser.add_argument("--review-md", type=Path, default=DEFAULT_REVIEW_MD)
    parser.add_argument("--fail-on-critical", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    performance_report_path = resolve_project_path(root, args.performance_report)
    review_json = resolve_project_path(root, args.review_json)
    review_md = resolve_project_path(root, args.review_md)

    report = build_report(root, performance_report_path)
    write_text(review_json, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    write_text(review_md, render_markdown(report))

    print(
        f"[+] T761 Supabase query performance review {report['overall_status']}: "
        f"ok={report['summary']['ok']} ready={report['summary']['ready']} "
        f"critical={report['summary']['critical']}"
    )
    print(f"[*] JSON: {review_json}")
    print(f"[*] Markdown: {review_md}")
    if args.fail_on_critical and report["overall_status"] == "critical":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
