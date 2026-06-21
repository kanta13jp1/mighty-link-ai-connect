#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Sync the T808 monthly KPI summary to Google Sheets."""

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
    parser.add_argument("--spreadsheet-id", default=delivery.DEFAULT_SPREADSHEET_ID)
    parser.add_argument("--regenerate-report", action="store_true")
    parser.add_argument("--draft-only", action="store_true", help="Only write the KPI JSON artifact.")
    parser.add_argument("--require-sync", action="store_true", help="Fail if Google Sheets credentials are missing.")
    parser.add_argument("--allow-interactive-oauth", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    today = delivery.today_from_arg(args.today)
    delivery.parse_month(args.month)
    report_file = delivery.ensure_monthly_report(root, args.month, today, force=args.regenerate_report)
    summary = delivery.collect_monthly_summary(root, args.month, today, report_file)
    outputs = delivery.output_paths(root, args.month)
    delivery.write_json(outputs.kpi_json, summary)

    sync_result = delivery.delivery_status("drafted", "KPI JSON artifact written.", artifact=delivery.display_path(root, outputs.kpi_json))
    if not args.draft_only:
        if delivery.google_credentials_configured(root, allow_interactive_oauth=args.allow_interactive_oauth):
            sync_result = delivery.sync_summary_to_sheets(
                root,
                args.spreadsheet_id,
                summary,
                allow_interactive_oauth=args.allow_interactive_oauth,
            )
        elif args.require_sync:
            raise delivery.CredentialMissing("Google Sheets credentials are required for --require-sync.")
        else:
            sync_result = delivery.delivery_status(
                "skipped_missing_credentials",
                "Google Sheets sync skipped because credentials are not configured.",
                artifact=delivery.display_path(root, outputs.kpi_json),
            )

    print(f"[+] {delivery.TASK_ID} monthly KPI {args.month}: {sync_result['status']}")
    print(f"[*] KPI artifact: {outputs.kpi_json}")
    if sync_result.get("spreadsheet_url"):
        print(f"[*] Spreadsheet: {sync_result['spreadsheet_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
