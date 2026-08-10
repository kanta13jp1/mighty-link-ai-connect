#!/usr/bin/env python3
"""Recover sales emails from a preserved Thunderbird mbox into local SQLite."""

from __future__ import annotations

import argparse
import mailbox
import sys
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from parse_sales_emails import DBAdapter  # noqa: E402
from sales_email_ingest import RawSalesEmail, _message_body  # noqa: E402
from sync_sales_emails import sync_raw_email_list  # noqa: E402


def parse_since(value: str) -> datetime:
    """Parse an ISO date/time and normalize it to UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_mbox_emails(
    mbox_path: Path,
    *,
    since: datetime,
    max_messages: int | None = None,
) -> tuple[list[RawSalesEmail], int]:
    """Read eligible messages without changing the preserved mbox."""
    if not mbox_path.is_file():
        raise FileNotFoundError(f"Thunderbird mbox not found: {mbox_path}")

    recovered: list[tuple[datetime, RawSalesEmail]] = []
    invalid_dates = 0
    inbox = mailbox.mbox(str(mbox_path), create=False)

    for key in inbox.iterkeys():
        raw_bytes = inbox.get_bytes(key, from_=False)
        message = BytesParser(policy=policy.default).parsebytes(raw_bytes)
        try:
            received_at = parsedate_to_datetime(str(message.get("Date", "")))
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
            received_at = received_at.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            invalid_dates += 1
            continue

        if received_at < since:
            continue

        recovered.append(
            (
                received_at,
                RawSalesEmail(
                    source_path=f"thunderbird-mbox://{mbox_path.name}/{key}",
                    source_type="thunderbird_mbox",
                    sender=str(message.get("From", "")),
                    subject=str(message.get("Subject", f"Thunderbird message {key}")),
                    received_at=str(message.get("Date", "")),
                    message_id=str(message.get("Message-ID", "")),
                    body=_message_body(message),
                ),
            )
        )

    recovered.sort(key=lambda item: item[0])
    if max_messages is not None:
        recovered = recovered[-max_messages:]
    return [item[1] for item in recovered], invalid_dates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recover preserved Thunderbird INBOX messages into local SQLite."
    )
    parser.add_argument("--mbox", type=Path, required=True, help="Preserved Thunderbird INBOX mbox path")
    parser.add_argument("--since", required=True, help="Oldest received date/time to recover (ISO 8601)")
    parser.add_argument("--max-messages", type=int, default=None, help="Optional newest-message limit")
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=PROJECT_ROOT / "data" / "mighty.db",
        help="Staging SQLite database",
    )
    parser.add_argument("--dry-run", action="store_true", help="Count recoverable messages without writing SQLite")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_messages is not None and args.max_messages < 1:
        raise ValueError("--max-messages must be at least 1")

    emails, invalid_dates = load_mbox_emails(
        args.mbox,
        since=parse_since(args.since),
        max_messages=args.max_messages,
    )
    print(f"[*] Recoverable Thunderbird messages: {len(emails)}")
    print(f"[*] Messages skipped for invalid Date headers: {invalid_dates}")
    if args.dry_run:
        print("[+] Dry run complete; SQLite was not changed.")
        return 0

    db = DBAdapter(args.sqlite_path)
    if db.use_supabase:
        db.close()
        raise RuntimeError("Thunderbird recovery must stage through SQLite, not Supabase REST.")
    try:
        inserted = sync_raw_email_list(db, emails)
    finally:
        db.close()
    print(f"[+] Inserted {inserted} deduplicated messages into SQLite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
