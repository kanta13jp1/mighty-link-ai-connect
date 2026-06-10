#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Audit the local external API usage ledger and report daily guard status.

The source ledger is intentionally local and gitignored:
data/external_api_usage.jsonl

This script is used by WBS T736 to make the existing FastAPI circuit breakers
auditable from the command line, CI, and daily operations.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = PROJECT_ROOT / "data" / "external_api_usage.jsonl"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def today_key() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                events.append(
                    {
                        "provider": "ledger",
                        "operation": "parse",
                        "outcome": "invalid_json",
                        "billable": False,
                        "line_number": line_number,
                    }
                )
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def event_day(event: dict[str, Any]) -> str | None:
    if event.get("day"):
        return str(event["day"])
    timestamp = str(event.get("timestamp") or "")
    if len(timestamp) >= 10:
        return timestamp[:10]
    return None


def configured_guards() -> dict[str, dict[str, int]]:
    return {
        "seedance_api:generation_create": {
            "daily_call_limit": env_int("SEEDANCE_DAILY_GENERATION_LIMIT", 1),
            "daily_reported_token_limit": env_int("SEEDANCE_DAILY_REPORTED_TOKEN_LIMIT", 0),
        },
        "gemini_api:parse": {
            "daily_call_limit": env_int("GEMINI_DAILY_CALL_LIMIT", 20),
            "daily_reported_token_limit": env_int("GEMINI_DAILY_REPORTED_TOKEN_LIMIT", 100000),
        },
        "gemini_api:match": {
            "daily_call_limit": env_int("GEMINI_DAILY_CALL_LIMIT", 20),
            "daily_reported_token_limit": env_int("GEMINI_DAILY_REPORTED_TOKEN_LIMIT", 100000),
        },
    }


def summarize_events(events: list[dict[str, Any]], target_day: str) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for event in events:
        if event_day(event) != target_day:
            continue
        provider = str(event.get("provider") or "unknown")
        operation = str(event.get("operation") or "unknown")
        key = f"{provider}:{operation}"
        row = summary.setdefault(
            key,
            {
                "provider": provider,
                "operation": operation,
                "events": 0,
                "billable_calls": 0,
                "blocked_calls": 0,
                "exception_calls": 0,
                "invalid_json_rows": 0,
                "reported_total_tokens": 0,
            },
        )
        row["events"] += 1
        if event.get("billable"):
            row["billable_calls"] += 1
        if event.get("outcome") == "blocked":
            row["blocked_calls"] += 1
        if event.get("outcome") == "exception":
            row["exception_calls"] += 1
        if event.get("outcome") == "invalid_json":
            row["invalid_json_rows"] += 1
        row["reported_total_tokens"] += int(event.get("reported_total_tokens") or 0)
    return summary


def guard_state(row: dict[str, Any], limits: dict[str, int], warn_ratio: float) -> tuple[str, str]:
    call_limit = int(limits.get("daily_call_limit", 0))
    token_limit = int(limits.get("daily_reported_token_limit", 0))
    billable_calls = int(row.get("billable_calls", 0))
    tokens = int(row.get("reported_total_tokens", 0))

    if call_limit <= 0:
        return "disabled", "daily call limit is 0"
    if billable_calls > call_limit:
        return "critical", f"billable calls exceed limit ({billable_calls}/{call_limit})"
    if token_limit > 0 and tokens > token_limit:
        return "critical", f"reported tokens exceed limit ({tokens}/{token_limit})"
    if billable_calls == call_limit:
        return "warning", f"billable calls reached limit ({billable_calls}/{call_limit}); next live call will be blocked"
    if token_limit > 0 and tokens == token_limit:
        return "warning", f"reported tokens reached limit ({tokens}/{token_limit}); next live call will be blocked"
    if billable_calls >= max(1, int(call_limit * warn_ratio)):
        return "warning", f"billable calls near limit ({billable_calls}/{call_limit})"
    if token_limit > 0 and tokens >= max(1, int(token_limit * warn_ratio)):
        return "warning", f"reported tokens near limit ({tokens}/{token_limit})"
    return "ok", "within daily limits"


def build_report(
    events: list[dict[str, Any]],
    target_day: str,
    warn_ratio: float = 0.8,
    guards: dict[str, dict[str, int]] | None = None,
) -> dict[str, Any]:
    guards = guards or configured_guards()
    summary = summarize_events(events, target_day)
    guard_rows: dict[str, dict[str, Any]] = {}
    alerts: list[dict[str, Any]] = []

    for key, limits in guards.items():
        provider, operation = key.split(":", 1)
        row = summary.get(
            key,
            {
                "provider": provider,
                "operation": operation,
                "events": 0,
                "billable_calls": 0,
                "blocked_calls": 0,
                "exception_calls": 0,
                "invalid_json_rows": 0,
                "reported_total_tokens": 0,
            },
        ).copy()
        row.update(limits)
        state, message = guard_state(row, limits, warn_ratio)
        row["state"] = state
        row["message"] = message
        guard_rows[key] = row
        if state in {"warning", "critical"}:
            alerts.append({"guard": key, "severity": state, "message": message})

    for key, row in summary.items():
        if key not in guard_rows:
            guard_rows[key] = {
                **row,
                "daily_call_limit": None,
                "daily_reported_token_limit": None,
                "state": "unconfigured",
                "message": "no configured circuit-breaker threshold",
            }

    invalid_rows = sum(1 for event in events if event.get("outcome") == "invalid_json")
    if invalid_rows:
        alerts.append(
            {
                "guard": "ledger:parse",
                "severity": "warning",
                "message": f"{invalid_rows} invalid JSONL row(s) ignored",
            }
        )

    status = "critical" if any(a["severity"] == "critical" for a in alerts) else "warning" if alerts else "ok"
    return {
        "status": status,
        "day": target_day,
        "ledger_events_for_day": sum(row["events"] for row in summary.values()),
        "guards": guard_rows,
        "alerts": alerts,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def print_console_report(report: dict[str, Any]) -> None:
    print(f"External API usage audit: {report['day']} [{report['status']}]")
    print("-" * 78)
    print("guard                              state      billable  blocked  tokens")
    print("-" * 78)
    for key in sorted(report["guards"]):
        row = report["guards"][key]
        print(
            f"{key[:34]:34} {row['state'][:9]:9} "
            f"{int(row['billable_calls']):8} {int(row['blocked_calls']):8} "
            f"{int(row['reported_total_tokens']):7}"
        )
    if report["alerts"]:
        print("-" * 78)
        for alert in report["alerts"]:
            print(f"[{alert['severity']}] {alert['guard']}: {alert['message']}")


def write_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--date", default=today_key(), help="Audit date in YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--output", type=Path, help="Write JSON report to this path.")
    parser.add_argument("--write-default-report", action="store_true", help="Write reports/daily_usage_audit_<date>.json.")
    parser.add_argument("--warn-ratio", type=float, default=0.8)
    parser.add_argument("--fail-on-alert", action="store_true", help="Exit non-zero on warning or critical alerts.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    events = load_jsonl(args.ledger)
    report = build_report(events, args.date, args.warn_ratio)
    print_console_report(report)

    if args.output:
        write_report(report, args.output)
    if args.write_default_report:
        write_report(report, DEFAULT_REPORT_DIR / f"daily_usage_audit_{args.date}.json")

    if args.fail_on_alert and report["status"] in {"warning", "critical"}:
        return 2 if report["status"] == "critical" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
