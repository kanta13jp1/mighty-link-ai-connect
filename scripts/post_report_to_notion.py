#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Create the T808 monthly quality report page in Notion."""

from __future__ import annotations

import argparse
import os
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
    parser.add_argument("--send", action="store_true", help="Fail if Notion credentials are missing.")
    parser.add_argument("--title-property", default=os.environ.get("NOTION_TITLE_PROPERTY", "Name"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    today = delivery.today_from_arg(args.today)
    delivery.parse_month(args.month)
    report_file = delivery.ensure_monthly_report(root, args.month, today, force=args.regenerate_report)
    summary = delivery.collect_monthly_summary(root, args.month, today, report_file)
    outputs = delivery.output_paths(root, args.month)

    parent = delivery.notion_parent_from_env() or {"database_id": "NOTION_DATABASE_ID_NOT_CONFIGURED"}
    payload = delivery.build_notion_payload(summary, parent, title_property=args.title_property)
    delivery.write_json(outputs.notion_payload, payload)

    if args.draft_only:
        status = delivery.delivery_status(
            "drafted",
            "Notion payload artifact written.",
            artifact=delivery.display_path(root, outputs.notion_payload),
        )
    elif delivery.notion_credentials_configured():
        status = delivery.post_to_notion(payload)
    elif args.send:
        raise delivery.CredentialMissing(
            "NOTION_API_KEY/NOTION_TOKEN plus NOTION_DATABASE_ID, NOTION_DATA_SOURCE_ID, or NOTION_PARENT_PAGE_ID are required."
        )
    else:
        status = delivery.delivery_status(
            "skipped_missing_credentials",
            "Notion post skipped because credentials or parent ID are not configured.",
            artifact=delivery.display_path(root, outputs.notion_payload),
        )
    delivery.write_json(outputs.notion_status, status)

    print(f"[+] {delivery.TASK_ID} Notion report {args.month}: {status['status']}")
    print(f"[*] Payload artifact: {outputs.notion_payload}")
    print(f"[*] Status artifact: {outputs.notion_status}")
    if status.get("url"):
        print(f"[*] Notion page: {status['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
