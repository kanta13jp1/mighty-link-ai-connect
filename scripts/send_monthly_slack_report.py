#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Send or draft the T808 monthly quality report Slack notification."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import monthly_quality_delivery as delivery


def parse_args(argv: list[str]) -> argparse.Namespace:
    today = delivery.today_from_arg(None)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=delivery.PROJECT_ROOT)
    parser.add_argument("--month", default=delivery.default_target_month(today))
    parser.add_argument("--today", default=None, help="Override today's date YYYY-MM-DD.")
    parser.add_argument("--regenerate-report", action="store_true")
    parser.add_argument("--draft-only", action="store_true")
    parser.add_argument("--send", action="store_true", help="Fail if SLACK_WEBHOOK_URL is missing.")
    parser.add_argument("--notion-url", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    today = delivery.today_from_arg(args.today)
    delivery.parse_month(args.month)
    report_file = delivery.ensure_monthly_report(root, args.month, today, force=args.regenerate_report)
    summary = delivery.collect_monthly_summary(root, args.month, today, report_file)
    outputs = delivery.output_paths(root, args.month)
    payload = delivery.build_slack_payload(summary, notion_url=args.notion_url)
    delivery.write_json(outputs.slack_payload, payload)

    if args.draft_only:
        status = delivery.delivery_status(
            "drafted",
            "Slack payload artifact written.",
            artifact=delivery.display_path(root, outputs.slack_payload),
        )
    elif delivery.slack_configured():
        status = delivery.send_to_slack(payload)
    elif args.send:
        raise delivery.CredentialMissing("SLACK_WEBHOOK_URL is required for --send.")
    else:
        status = delivery.delivery_status(
            "skipped_missing_credentials",
            "Slack send skipped because SLACK_WEBHOOK_URL is not configured.",
            artifact=delivery.display_path(root, outputs.slack_payload),
        )
    delivery.write_json(outputs.slack_status, status)

    print(f"[+] {delivery.TASK_ID} Slack report {args.month}: {status['status']}")
    print(f"[*] Payload artifact: {outputs.slack_payload}")
    print(f"[*] Status artifact: {outputs.slack_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
