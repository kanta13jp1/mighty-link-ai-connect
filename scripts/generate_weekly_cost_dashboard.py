#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate the weekly cost allocation dashboard for WBS T757.

The dashboard combines the local external API usage ledger with optional manual
actuals from provider billing exports. It never stores notification secrets.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import smtplib
import sys
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any


TASK_ID = "T757"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = Path("data") / "external_api_usage.jsonl"
DEFAULT_BUDGETS = Path("data") / "cost_allocation_budgets.tsv"
DEFAULT_ACTUALS = Path("data") / "cost_actuals.tsv"
DEFAULT_JSON_REPORT = Path("exports") / "weekly_cost_dashboard.json"
DEFAULT_MD_REPORT = Path("exports") / "weekly_cost_dashboard.md"
DEFAULT_EMAIL_DRAFT = Path("exports") / "weekly_cost_alert_email.md"
DEFAULT_SLACK_DRAFT = Path("exports") / "weekly_cost_slack_payload.json"
STATUS_ORDER = {"ok": 0, "unknown": 1, "warning": 2, "critical": 3}


@dataclass(frozen=True)
class Budget:
    cost_center: str
    owner_lane: str
    category: str
    monthly_budget_usd: float
    warning_ratio: float
    critical_ratio: float
    source: str
    notes: str


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assert_child_path(root: Path, child: Path) -> None:
    root_resolved = root.resolve()
    child_resolved = child.resolve()
    if child_resolved == root_resolved or root_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {child}")


def resolve_project_path(root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else root / path
    assert_child_path(root, resolved)
    return resolved


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def default_period(today: dt.date | None = None) -> tuple[dt.date, dt.date]:
    end = today or dt.date.today()
    return end - dt.timedelta(days=6), end


def load_budgets(path: Path) -> dict[str, Budget]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        budgets: dict[str, Budget] = {}
        for row in reader:
            key = (row.get("cost_center") or "").strip()
            if not key:
                continue
            budgets[key] = Budget(
                cost_center=key,
                owner_lane=(row.get("owner_lane") or "").strip(),
                category=(row.get("category") or "").strip(),
                monthly_budget_usd=float(row.get("monthly_budget_usd") or 0),
                warning_ratio=float(row.get("warning_ratio") or 0.8),
                critical_ratio=float(row.get("critical_ratio") or 1.0),
                source=(row.get("source") or "").strip(),
                notes=(row.get("notes") or "").strip(),
            )
    return budgets


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            events.append({"provider": "ledger", "operation": "parse", "outcome": "invalid_json", "line": line_number})
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def event_day(event: dict[str, Any]) -> dt.date | None:
    raw_day = event.get("day")
    if raw_day:
        try:
            return parse_date(str(raw_day))
        except ValueError:
            return None
    timestamp = str(event.get("timestamp") or "")
    if len(timestamp) >= 10:
        try:
            return parse_date(timestamp[:10])
        except ValueError:
            return None
    return None


def provider_cost_center(provider: str) -> str:
    provider = provider.lower()
    if "gemini" in provider:
        return "ai_api_gemini"
    if "seedance" in provider or "byteplus" in provider:
        return "ai_api_seedance"
    if "stripe" in provider:
        return "stripe_billing"
    if "firebase" in provider or "google_cloud" in provider or "gcp" in provider:
        return "firebase_google_cloud"
    if "supabase" in provider:
        return "supabase_db"
    if "github" in provider:
        return "github_actions"
    if "slack" in provider:
        return "slack_notifications"
    return f"unallocated_{provider or 'unknown'}"


def summarize_usage(events: list[dict[str, Any]], start: dt.date, end: dt.date) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for event in events:
        day = event_day(event)
        if day is None or day < start or day > end:
            continue
        provider = str(event.get("provider") or "unknown")
        center = provider_cost_center(provider)
        row = summary.setdefault(
            center,
            {
                "events": 0,
                "providers": Counter(),
                "outcomes": Counter(),
                "billable_events": 0,
                "blocked_events": 0,
                "reported_total_tokens": 0,
                "reported_input_tokens": 0,
                "reported_output_tokens": 0,
                "invalid_json_rows": 0,
            },
        )
        row["events"] += 1
        row["providers"][provider] += 1
        outcome = str(event.get("outcome") or "unknown")
        row["outcomes"][outcome] += 1
        if event.get("billable"):
            row["billable_events"] += 1
        if outcome == "blocked":
            row["blocked_events"] += 1
        if outcome == "invalid_json":
            row["invalid_json_rows"] += 1
        row["reported_total_tokens"] += int(event.get("reported_total_tokens") or 0)
        row["reported_input_tokens"] += int(event.get("reported_input_tokens") or 0)
        row["reported_output_tokens"] += int(event.get("reported_output_tokens") or 0)

    normalized: dict[str, dict[str, Any]] = {}
    for center, row in summary.items():
        normalized[center] = {
            **row,
            "providers": dict(row["providers"]),
            "outcomes": dict(row["outcomes"]),
        }
    return normalized


def load_actuals(path: Path, start: dt.date, end: dt.date) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    actuals: dict[str, dict[str, Any]] = defaultdict(lambda: {"amount_usd": 0.0, "sources": [], "notes": []})
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            center = (row.get("cost_center") or "").strip()
            if not center:
                continue
            try:
                row_start = parse_date(str(row.get("period_start") or ""))
                row_end = parse_date(str(row.get("period_end") or ""))
            except ValueError:
                continue
            if row_end < start or row_start > end:
                continue
            amount = float(row.get("amount_usd") or 0)
            actuals[center]["amount_usd"] += amount
            if row.get("source"):
                actuals[center]["sources"].append(str(row["source"]))
            if row.get("notes"):
                actuals[center]["notes"].append(str(row["notes"]))
    return dict(actuals)


def center_status(amount: float | None, budget: Budget | None, billable_events: int, invalid_rows: int) -> str:
    if invalid_rows:
        return "warning"
    if amount is None:
        return "warning" if billable_events else "unknown"
    if budget and budget.monthly_budget_usd > 0:
        if amount >= budget.monthly_budget_usd * budget.critical_ratio:
            return "critical"
        if amount >= budget.monthly_budget_usd * budget.warning_ratio:
            return "warning"
    if billable_events and amount == 0:
        return "warning"
    return "ok"


def build_dashboard(
    budgets: dict[str, Budget],
    usage: dict[str, dict[str, Any]],
    actuals: dict[str, dict[str, Any]],
    start: dt.date,
    end: dt.date,
) -> dict[str, Any]:
    centers = sorted(set(budgets) | set(usage) | set(actuals))
    rows: list[dict[str, Any]] = []
    summary = Counter()
    total_actual = 0.0
    total_billable = 0
    total_blocked = 0
    alerts: list[dict[str, str]] = []

    for center in centers:
        budget = budgets.get(center)
        usage_row = usage.get(center, {})
        actual_row = actuals.get(center)
        amount = float(actual_row["amount_usd"]) if actual_row is not None else None
        if amount is not None:
            total_actual += amount
        billable = int(usage_row.get("billable_events") or 0)
        blocked = int(usage_row.get("blocked_events") or 0)
        total_billable += billable
        total_blocked += blocked
        invalid_rows = int(usage_row.get("invalid_json_rows") or 0)
        status = center_status(amount, budget, billable, invalid_rows)
        summary[status] += 1
        budget_amount = budget.monthly_budget_usd if budget else 0.0
        usage_percent = round((amount / budget_amount) * 100, 2) if amount is not None and budget_amount > 0 else None

        if status in {"warning", "critical"}:
            alerts.append(
                {
                    "cost_center": center,
                    "severity": status,
                    "message": (
                        "billing actual is missing for billable usage"
                        if amount is None and billable
                        else "budget threshold reached or ledger needs attention"
                    ),
                }
            )

        rows.append(
            {
                "cost_center": center,
                "status": status,
                "category": budget.category if budget else "Unallocated",
                "owner_lane": budget.owner_lane if budget else "Unassigned",
                "weekly_actual_usd": amount,
                "monthly_budget_usd": budget_amount,
                "budget_used_percent": usage_percent,
                "events": int(usage_row.get("events") or 0),
                "billable_events": billable,
                "blocked_events": blocked,
                "reported_total_tokens": int(usage_row.get("reported_total_tokens") or 0),
                "providers": usage_row.get("providers") or {},
                "outcomes": usage_row.get("outcomes") or {},
                "source": budget.source if budget else "external ledger",
                "actual_sources": actual_row.get("sources", []) if actual_row else [],
                "notes": budget.notes if budget else "No budget row configured.",
            }
        )

    overall = max((row["status"] for row in rows), key=lambda value: STATUS_ORDER[value], default="ok")
    if overall == "unknown" and any(alert["severity"] == "warning" for alert in alerts):
        overall = "warning"

    return {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "overall_status": overall,
        "summary": {
            "ok": int(summary.get("ok", 0)),
            "unknown": int(summary.get("unknown", 0)),
            "warning": int(summary.get("warning", 0)),
            "critical": int(summary.get("critical", 0)),
            "weekly_actual_usd": round(total_actual, 4),
            "billable_events": total_billable,
            "blocked_events": total_blocked,
        },
        "cost_centers": rows,
        "alerts": alerts,
    }


def build_email_draft(report: dict[str, Any]) -> str:
    period = report["period"]
    summary = report["summary"]
    lines = [
        f"# T757 Weekly Cost Alert Draft ({period['start']} to {period['end']})",
        "",
        f"- Overall status: {report['overall_status']}",
        f"- Weekly actual total: ${summary['weekly_actual_usd']:.2f}",
        f"- Billable events: {summary['billable_events']}",
        f"- Blocked events: {summary['blocked_events']}",
        "",
        "## Alerts",
    ]
    if report["alerts"]:
        for alert in report["alerts"]:
            lines.append(f"- [{alert['severity']}] {alert['cost_center']}: {alert['message']}")
    else:
        lines.append("- No warning or critical alerts.")
    lines.extend(
        [
            "",
            "## Cost Centers",
            "",
            "| Cost center | Status | Weekly actual | Budget | Billable | Blocked |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report["cost_centers"]:
        actual = "unknown" if row["weekly_actual_usd"] is None else f"${row['weekly_actual_usd']:.2f}"
        lines.append(
            f"| {row['cost_center']} | {row['status']} | {actual} | ${row['monthly_budget_usd']:.2f} | "
            f"{row['billable_events']} | {row['blocked_events']} |"
        )
    lines.extend(
        [
            "",
            "Provider consoles remain the source of truth for billed amounts. This draft contains no webhook URL, API key, SMTP password, or provider token.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_slack_payload(report: dict[str, Any]) -> dict[str, Any]:
    period = report["period"]
    summary = report["summary"]
    alert_text = "no alerts"
    if report["alerts"]:
        alert_text = ", ".join(f"{a['severity']}:{a['cost_center']}" for a in report["alerts"][:5])
    return {
        "text": (
            f"T757 weekly cost dashboard {period['start']}..{period['end']} "
            f"[{report['overall_status']}]: actual=${summary['weekly_actual_usd']:.2f}, "
            f"billable={summary['billable_events']}, blocked={summary['blocked_events']}, alerts={alert_text}"
        )
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    period = report["period"]
    summary = report["summary"]
    lines = [
        "# Weekly Cost Allocation Dashboard",
        "",
        f"- Task: {report['task_id']}",
        f"- Generated: {report['generated_at']}",
        f"- Period: {period['start']} to {period['end']}",
        f"- Overall status: {report['overall_status']}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Weekly actual total | ${summary['weekly_actual_usd']:.2f} |",
        f"| Billable events | {summary['billable_events']} |",
        f"| Blocked events | {summary['blocked_events']} |",
        f"| Critical centers | {summary['critical']} |",
        f"| Warning centers | {summary['warning']} |",
        f"| Unknown actual centers | {summary['unknown']} |",
        "",
        "## Cost Centers",
        "",
        "| Cost center | Owner | Status | Weekly actual | Monthly budget | Billable | Blocked | Source |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report["cost_centers"]:
        actual = "unknown" if row["weekly_actual_usd"] is None else f"${row['weekly_actual_usd']:.2f}"
        lines.append(
            f"| {row['cost_center']} | {row['owner_lane']} | {row['status']} | {actual} | "
            f"${row['monthly_budget_usd']:.2f} | {row['billable_events']} | {row['blocked_events']} | {row['source']} |"
        )
    lines.extend(
        [
            "",
            "## Notification",
            "",
            "- Email draft: `exports/weekly_cost_alert_email.md`",
            "- Slack payload draft: `exports/weekly_cost_slack_payload.json`",
            "",
            "## Notes",
            "",
            "- Provider consoles, Cloud Billing export, Supabase billing, and Stripe Dashboard remain the source of truth for billed amounts.",
            "- Missing actuals are intentionally shown as `unknown`; do not invent spend from local logs.",
            "- Notification secrets are read from environment variables only and are not written to artifacts.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def send_slack(webhook_url: str, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status >= 300:
            raise RuntimeError(f"Slack webhook returned HTTP {response.status}")


def send_email(args: argparse.Namespace, body: str, report: dict[str, Any]) -> None:
    if not args.email_to:
        raise ValueError("--email-to is required when --send-email is set")
    smtp_host = args.smtp_host or os.environ.get("SMTP_HOST")
    if not smtp_host:
        raise ValueError("SMTP host is required via --smtp-host or SMTP_HOST")
    smtp_port = int(args.smtp_port or os.environ.get("SMTP_PORT") or 587)
    username = args.smtp_username or os.environ.get("SMTP_USERNAME")
    password = args.smtp_password or os.environ.get("SMTP_PASSWORD")
    sender = args.email_from or os.environ.get("COST_ALERT_EMAIL_FROM") or username
    if not sender:
        raise ValueError("Email sender is required via --email-from or COST_ALERT_EMAIL_FROM")

    message = EmailMessage()
    message["Subject"] = f"T757 weekly cost dashboard [{report['overall_status']}]"
    message["From"] = sender
    message["To"] = args.email_to
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
        smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)


def parse_args(argv: list[str]) -> argparse.Namespace:
    start, end = default_period()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--start-date", default=start.isoformat())
    parser.add_argument("--end-date", default=end.isoformat())
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--budgets", type=Path, default=DEFAULT_BUDGETS)
    parser.add_argument("--actuals", type=Path, default=DEFAULT_ACTUALS)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--markdown-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--email-draft", type=Path, default=DEFAULT_EMAIL_DRAFT)
    parser.add_argument("--slack-draft", type=Path, default=DEFAULT_SLACK_DRAFT)
    parser.add_argument("--send-slack", action="store_true")
    parser.add_argument("--slack-webhook-url", default=os.environ.get("SLACK_WEBHOOK_URL", ""))
    parser.add_argument("--send-email", action="store_true")
    parser.add_argument("--email-to", default=os.environ.get("COST_ALERT_EMAIL_TO", ""))
    parser.add_argument("--email-from", default=os.environ.get("COST_ALERT_EMAIL_FROM", ""))
    parser.add_argument("--smtp-host", default=os.environ.get("SMTP_HOST", ""))
    parser.add_argument("--smtp-port", default=os.environ.get("SMTP_PORT", ""))
    parser.add_argument("--smtp-username", default=os.environ.get("SMTP_USERNAME", ""))
    parser.add_argument("--smtp-password", default=os.environ.get("SMTP_PASSWORD", ""))
    parser.add_argument("--fail-on-alert", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    start = parse_date(args.start_date)
    end = parse_date(args.end_date)
    if end < start:
        raise ValueError("--end-date must be on or after --start-date")

    ledger = resolve_project_path(root, args.ledger)
    budgets_path = resolve_project_path(root, args.budgets)
    actuals_path = resolve_project_path(root, args.actuals)
    json_report = resolve_project_path(root, args.json_report)
    markdown_report = resolve_project_path(root, args.markdown_report)
    email_draft = resolve_project_path(root, args.email_draft)
    slack_draft = resolve_project_path(root, args.slack_draft)

    budgets = load_budgets(budgets_path)
    events = load_jsonl(ledger)
    usage = summarize_usage(events, start, end)
    actuals = load_actuals(actuals_path, start, end)
    report = build_dashboard(budgets, usage, actuals, start, end)
    report["sources"] = {
        "ledger": display_path(root, ledger),
        "budgets": display_path(root, budgets_path),
        "actuals": display_path(root, actuals_path) if actuals_path.exists() else "not configured",
    }

    email_body = build_email_draft(report)
    slack_payload = build_slack_payload(report)
    write_json(json_report, report)
    write_markdown(markdown_report, report)
    email_draft.parent.mkdir(parents=True, exist_ok=True)
    email_draft.write_text(email_body, encoding="utf-8")
    write_json(slack_draft, slack_payload)

    if args.send_slack:
        if not args.slack_webhook_url:
            raise ValueError("--slack-webhook-url or SLACK_WEBHOOK_URL is required when --send-slack is set")
        send_slack(args.slack_webhook_url, slack_payload)
    if args.send_email:
        send_email(args, email_body, report)

    print(
        f"[+] {TASK_ID} weekly cost dashboard {report['overall_status']}: "
        f"actual=${report['summary']['weekly_actual_usd']:.2f} "
        f"billable={report['summary']['billable_events']} blocked={report['summary']['blocked_events']}"
    )
    print(f"[*] JSON: {json_report}")
    print(f"[*] Markdown: {markdown_report}")
    print(f"[*] Email draft: {email_draft}")
    print(f"[*] Slack draft: {slack_draft}")

    if args.fail_on_alert and report["overall_status"] in {"warning", "critical"}:
        return 2 if report["overall_status"] == "critical" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
