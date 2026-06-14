#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate the Firebase and Supabase quota/error alert review for T761_1.

The review aggregates existing monitoring artifacts and turns them into an
operator checklist for Cloud Monitoring, Firebase, Supabase Metrics API, and
notification routing. It is intentionally safe for CI: production credentials
are optional and secret-like strings are redacted before artifacts are written.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "T761_1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INFRA_REPORT = Path("exports") / "infra_monitoring_dashboard.json"
DEFAULT_COST_REPORT = Path("exports") / "weekly_cost_dashboard.json"
DEFAULT_UPTIME_REPORT = Path("exports") / "uptime_monitor_report.json"
DEFAULT_QUERY_REVIEW = Path("exports") / "supabase_query_performance_review.json"
DEFAULT_BUDGETS = Path("data") / "cost_allocation_budgets.tsv"
DEFAULT_JSON_REPORT = Path("exports") / "quota_error_alert_review.json"
DEFAULT_MD_REPORT = Path("exports") / "quota_error_alert_review.md"
STATUS_ORDER = {"ok": 0, "ready": 1, "warning": 2, "critical": 3}
SECRET_PATTERNS = (
    re.compile(r"postgres(?:ql)?://[^\s`\"']+", re.IGNORECASE),
    re.compile(r"Bearer\s+(?=[A-Za-z0-9._=-]*[._=-])[A-Za-z0-9._=-]{6,}", re.IGNORECASE),
    re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+", re.IGNORECASE),
    re.compile(r"sb_(?:secret|publishable|service_role)_[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|token|password|secret)=([A-Za-z0-9._=-]+)", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
)


@dataclass(frozen=True)
class AlertCheck:
    key: str
    provider: str
    status: str
    signal: str
    threshold: str
    action: str
    notification: str
    source: str
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
        redacted = pattern.sub(lambda match: match.group(0).split("=")[0] + "=<redacted>" if "=" in match.group(0) else "<redacted>", redacted)
    return redacted


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact_secret_like_text(text), encoding="utf-8", newline="\n")


def read_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"invalid JSON: {exc}"
    if not isinstance(loaded, dict):
        return {}, "JSON root is not an object"
    return loaded, None


def load_budgets(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    budgets: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            center = (row.get("cost_center") or "").strip()
            if center:
                budgets[center] = {key: (value or "").strip() for key, value in row.items()}
    return budgets


def normalize_status(value: Any, error: str | None = None) -> str:
    if error:
        return "warning"
    status = str(value or "").strip().lower()
    if not status:
        return "ready"
    if status in {"critical", "failed", "failure", "error"} or status.startswith("failed"):
        return "critical"
    if status in {"warning", "warn"}:
        return "warning"
    if status in {"ok", "success", "healthy", "pass", "passed"}:
        return "ok"
    if status in {"ready", "planned", "unknown", "dry-run", "dry_run"}:
        return "ready"
    return "ready"


def report_status(report: dict[str, Any], error: str | None) -> str:
    return normalize_status(report.get("overall_status") or report.get("status"), error)


def worst_status(*statuses: str) -> str:
    return max(statuses, key=lambda status: STATUS_ORDER.get(status, 1))


def budget_evidence(center: str, budgets: dict[str, dict[str, str]]) -> tuple[str, str]:
    row = budgets.get(center)
    if not row:
        return "warning", f"{center} budget row is missing"
    budget = row.get("monthly_budget_usd") or "0"
    warning = row.get("warning_ratio") or "n/a"
    critical = row.get("critical_ratio") or "n/a"
    return "ready", f"{center} monthly_budget_usd={budget}, warning_ratio={warning}, critical_ratio={critical}"


def build_checks(
    root: Path,
    reports: dict[str, tuple[Path, dict[str, Any], str | None]],
    budgets: dict[str, dict[str, str]],
) -> list[AlertCheck]:
    infra_path, infra, infra_error = reports["infra"]
    cost_path, cost, cost_error = reports["cost"]
    uptime_path, uptime, uptime_error = reports["uptime"]
    query_path, query, query_error = reports["query"]

    infra_status = report_status(infra, infra_error)
    cost_status = report_status(cost, cost_error)
    uptime_status = report_status(uptime, uptime_error)
    query_status = report_status(query, query_error)
    firebase_budget_status, firebase_budget_evidence = budget_evidence("firebase_google_cloud", budgets)
    supabase_budget_status, supabase_budget_evidence = budget_evidence("supabase_db", budgets)
    notification_status = "ok" if os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("COST_ALERT_EMAIL_TO") else "ready"
    supabase_metrics_status = "ok" if os.environ.get("SUPABASE_METRICS_URL") else "ready"
    incident_runbooks_present = (
        (root / "docs" / "DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md").exists()
        and (root / "docs" / "INCIDENT_POSTMORTEM_RUNBOOK.md").exists()
    )

    checks = [
        AlertCheck(
            key="firebase_billing_budget_alert",
            provider="Firebase / Google Cloud",
            status=worst_status(firebase_budget_status, cost_status if cost_status == "critical" else firebase_budget_status),
            signal="Cloud Billing actual spend, Firebase plan usage, Hosting/Functions cost center",
            threshold="Warning at 80% and critical at 100% of firebase_google_cloud monthly budget",
            action="Create or verify a Cloud Billing budget alert and keep billed actuals in the weekly cost dashboard.",
            notification="Budget email notification plus optional Slack relay through existing cost alert draft",
            source=f"{display_path(root, cost_path)}; data/cost_allocation_budgets.tsv; Cloud Billing Budgets",
            evidence=f"{firebase_budget_evidence}; cost_report={cost_status if not cost_error else cost_error}",
        ),
        AlertCheck(
            key="firebase_hosting_functions_quota",
            provider="Firebase / Google Cloud",
            status=worst_status("ready", infra_status if infra_status == "critical" else "ready"),
            signal="Firebase Hosting transfer/storage, Functions/Cloud Run invocations, memory, timeout, and quota usage",
            threshold="Warning when dashboard usage exceeds 80%; critical when provider quota or deployment limit is reached",
            action="Review Firebase Usage and Cloud Run/Functions quotas weekly; convert repeated warnings to Cloud Monitoring policies.",
            notification="Ops Slack/Email after manual threshold confirmation; no provider token is stored in artifacts",
            source=f"{display_path(root, infra_path)}; Firebase Usage dashboard; Cloud Monitoring",
            evidence=f"infra_report={infra_status if not infra_error else infra_error}",
        ),
        AlertCheck(
            key="firebase_error_log_alert",
            provider="Firebase / Google Cloud",
            status=worst_status(uptime_status, infra_status if infra_status == "critical" else "ready"),
            signal="HTTPS uptime failures, 5xx responses, Cloud Functions/Cloud Run error logs, TLS certificate failures",
            threshold="Critical on public demo outage, custom domain strict TLS failure, or repeated 5xx/log-based error spikes",
            action="Create a Cloud Logging logs-based metric and Cloud Monitoring alert policy for 5xx and function error logs.",
            notification="Slack webhook or email notification, then follow DR and incident postmortem runbooks",
            source=f"{display_path(root, uptime_path)}; Cloud Logging; Cloud Monitoring alert policies",
            evidence=f"uptime_report={uptime_status if not uptime_error else uptime_error}; infra_report={infra_status}",
        ),
        AlertCheck(
            key="firebase_performance_alert",
            provider="Firebase",
            status="ready",
            signal="Firebase Performance Monitoring latency, network errors, and custom trace degradation",
            threshold="Warning on sustained p95 latency regression; critical when user-visible flows breach SLA thresholds",
            action="Define Performance Monitoring alert events for key user journeys after live traffic exists.",
            notification="Firebase alert trigger to Cloud Functions or operator email, then GitHub Issue for recurring degradation",
            source="Firebase Performance Monitoring; Firebase alert triggers",
            evidence="No production traffic baseline yet; keep as ready gate until enough samples exist",
        ),
        AlertCheck(
            key="supabase_usage_budget_alert",
            provider="Supabase",
            status=supabase_budget_status,
            signal="Supabase spend, egress, database size, storage, auth MAU, and plan usage",
            threshold="Warning at 80% and critical at 100% of supabase_db monthly budget or provider quota",
            action="Check Supabase billing/usage dashboard weekly and record actuals without project IDs or secrets.",
            notification="Weekly cost dashboard alert draft plus operator escalation for paid-plan changes",
            source=f"{display_path(root, cost_path)}; data/cost_allocation_budgets.tsv; Supabase billing dashboard",
            evidence=supabase_budget_evidence,
        ),
        AlertCheck(
            key="supabase_metrics_api_alert",
            provider="Supabase",
            status=supabase_metrics_status,
            signal="Prometheus-compatible database health metrics from Supabase Metrics API",
            threshold="Warning on missing scrape; critical on connection saturation, disk pressure, WAL backlog, or error burst",
            action="Add SUPABASE_METRICS_URL and SUPABASE_METRICS_BEARER_TOKEN as CI/environment secrets before live alerting.",
            notification="Grafana/Datadog/Cloud Monitoring bridge or GitHub Actions summary; token values never enter reports",
            source=f"{display_path(root, infra_path)}; Supabase Metrics API",
            evidence="SUPABASE_METRICS_URL configured" if os.environ.get("SUPABASE_METRICS_URL") else "metrics endpoint not configured in this environment",
        ),
        AlertCheck(
            key="supabase_db_saturation_alert",
            provider="Supabase",
            status=worst_status(query_status, "ready"),
            signal="Slow query review, connection pressure, CPU, memory, disk, locks, WAL, cache hit rate, and index advisor findings",
            threshold="Warning at 80% resource pressure or repeated p95 query latency > 1s; critical on blocking locks or failed diagnostics",
            action="Use Query Performance / Performance Advisor / Index Advisor review before opening DDL or pool-size changes.",
            notification="GitHub Issue plus WBS follow-up; production DDL requires migration safety gate",
            source=f"{display_path(root, query_path)}; Supabase Dashboard; supabase inspect",
            evidence=f"query_review={query_status if not query_error else query_error}",
        ),
        AlertCheck(
            key="notification_channel_routing",
            provider="Operations",
            status=notification_status,
            signal="Slack webhook, email destination, GitHub Actions failure, and Issue/Project escalation",
            threshold="Critical alerts must reach a human-owned channel; warning alerts may stay in scheduled report artifacts",
            action="Store SLACK_WEBHOOK_URL and email settings only as GitHub/CI secrets; never write them to docs, Sheets, or Issues.",
            notification="Slack, email, GitHub Issue comment, and Calendar/WBS closeout",
            source="GitHub Actions secrets; weekly cost alert draft; uptime monitor workflow",
            evidence="notification env present" if notification_status == "ok" else "notification secrets not configured locally; CI can inject them",
        ),
        AlertCheck(
            key="incident_escalation_gate",
            provider="Operations",
            status="ok" if incident_runbooks_present else "warning",
            signal="Critical alert handoff, DR escalation, postmortem creation, and WBS follow-up",
            threshold="Any critical production availability/data-loss/billing runaway alert starts incident handling",
            action="Open/close GitHub Issue with WBS reference and attach follow-up actions to issues_tracker.tsv and qa_tracker.tsv.",
            notification="Human operator, GitHub Issue #97, Project #1, and Google Workspace WBS sync",
            source="docs/DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md; docs/INCIDENT_POSTMORTEM_RUNBOOK.md",
            evidence="runbooks present" if incident_runbooks_present else "one or more incident runbooks missing",
        ),
    ]
    return checks


def summarize_checks(checks: list[AlertCheck]) -> dict[str, int]:
    counter = Counter(check.status for check in checks)
    return {status: int(counter.get(status, 0)) for status in ("ok", "ready", "warning", "critical")}


def overall_status(checks: list[AlertCheck]) -> str:
    if not checks:
        return "warning"
    return max((check.status for check in checks), key=lambda status: STATUS_ORDER.get(status, 1))


def operator_checklist() -> list[dict[str, str]]:
    return [
        {
            "area": "Cloud Billing",
            "action": "Verify Firebase/GCP budget alert recipients and thresholds before enabling paid expansion.",
            "evidence": "Weekly cost dashboard row for firebase_google_cloud plus Cloud Billing budget policy screenshot/export.",
        },
        {
            "area": "Cloud Monitoring",
            "action": "Create alert policies for HTTPS 5xx/log-based errors, Functions/Cloud Run errors, and TLS failures.",
            "evidence": "Alert policy name, notification channel, and GitHub Issue link.",
        },
        {
            "area": "Firebase",
            "action": "Review Hosting/Functions usage and Performance Monitoring alert events after production traffic starts.",
            "evidence": "Firebase usage dashboard and Performance Monitoring alert settings.",
        },
        {
            "area": "Supabase",
            "action": "Enable Metrics API/Grafana-style scraping and watch connection, CPU, disk, WAL, cache, and slow query signals.",
            "evidence": "Metrics scrape status plus Supabase Query Performance review artifact.",
        },
        {
            "area": "Escalation",
            "action": "Route critical alerts to a human-owned channel and open a WBS-linked Issue for follow-up.",
            "evidence": "Issue/Project status, Sheets sync, and Calendar cleanup for completed WBS rows.",
        },
    ]


def build_report(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    infra_path = resolve_project_path(root, args.infra_report)
    cost_path = resolve_project_path(root, args.cost_report)
    uptime_path = resolve_project_path(root, args.uptime_report)
    query_path = resolve_project_path(root, args.query_review)
    budgets_path = resolve_project_path(root, args.budgets)
    reports = {
        "infra": (infra_path, *read_json(infra_path)),
        "cost": (cost_path, *read_json(cost_path)),
        "uptime": (uptime_path, *read_json(uptime_path)),
        "query": (query_path, *read_json(query_path)),
    }
    checks = build_checks(root, reports, load_budgets(budgets_path))
    return {
        "task_id": TASK_ID,
        "generated_at_utc": utc_timestamp(),
        "overall_status": overall_status(checks),
        "summary": summarize_checks(checks),
        "sources": {
            "infra_report": display_path(root, infra_path),
            "cost_report": display_path(root, cost_path),
            "uptime_report": display_path(root, uptime_path),
            "supabase_query_review": display_path(root, query_path),
            "budgets": display_path(root, budgets_path),
            "runbook": "docs/FIREBASE_SUPABASE_QUOTA_ERROR_ALERT_RUNBOOK.md",
        },
        "checks": [asdict(check) for check in checks],
        "operator_checklist": operator_checklist(),
        "escalation_rules": [
            "Do not store Slack webhooks, Supabase bearer tokens, database URLs, or billing account identifiers in artifacts.",
            "Treat Cloud Billing budget alerts as notifications, not automatic spend caps.",
            "Convert repeated warning alerts into WBS tasks with GitHub Issues and Project status.",
            "Escalate critical availability, quota exhaustion, or data-loss risk through the DR and incident runbooks.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Firebase and Supabase Quota/Error Alert Review",
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
            "## Alert Checks",
            "",
            "| Key | Provider | Status | Signal | Threshold | Action | Notification | Evidence |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for check in report["checks"]:
        lines.append(
            "| {key} | {provider} | {status} | {signal} | {threshold} | {action} | {notification} | {evidence} |".format(
                key=str(check["key"]).replace("|", "\\|"),
                provider=str(check["provider"]).replace("|", "\\|"),
                status=str(check["status"]).replace("|", "\\|"),
                signal=str(check["signal"]).replace("|", "\\|"),
                threshold=str(check["threshold"]).replace("|", "\\|"),
                action=str(check["action"]).replace("|", "\\|"),
                notification=str(check["notification"]).replace("|", "\\|"),
                evidence=str(check["evidence"]).replace("|", "\\|"),
            )
        )

    lines.extend(
        [
            "",
            "## Operator Checklist",
            "",
            "| Area | Action | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for item in report["operator_checklist"]:
        lines.append(f"| {item['area']} | {item['action']} | {item['evidence']} |")

    lines.extend(["", "## Escalation Rules", ""])
    for rule in report["escalation_rules"]:
        lines.append(f"- {rule}")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--infra-report", type=Path, default=DEFAULT_INFRA_REPORT)
    parser.add_argument("--cost-report", type=Path, default=DEFAULT_COST_REPORT)
    parser.add_argument("--uptime-report", type=Path, default=DEFAULT_UPTIME_REPORT)
    parser.add_argument("--query-review", type=Path, default=DEFAULT_QUERY_REVIEW)
    parser.add_argument("--budgets", type=Path, default=DEFAULT_BUDGETS)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--fail-on-critical", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    json_report = resolve_project_path(root, args.json_report)
    markdown_report = resolve_project_path(root, args.markdown_report)
    report = build_report(root, args)
    write_text(json_report, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    write_text(markdown_report, render_markdown(report))

    print(
        f"[+] {TASK_ID} quota/error alert review {report['overall_status']}: "
        f"ok={report['summary']['ok']} ready={report['summary']['ready']} "
        f"warning={report['summary']['warning']} critical={report['summary']['critical']}"
    )
    print(f"[*] JSON: {json_report}")
    print(f"[*] Markdown: {markdown_report}")
    if args.fail_on_critical and report["overall_status"] == "critical":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
