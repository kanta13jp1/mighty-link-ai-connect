from __future__ import annotations

import mailbox
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from recover_thunderbird_sales_emails import load_mbox_emails, parse_since


def append_message(path: Path, *, date: str, subject: str, message_id: str) -> None:
    message = EmailMessage()
    message["From"] = "partner@example.com"
    message["Date"] = date
    message["Subject"] = subject
    message["Message-ID"] = message_id
    message.set_content("Java AWS project details")
    inbox = mailbox.mbox(str(path), create=True)
    try:
        inbox.add(message)
        inbox.flush()
    finally:
        inbox.close()


def test_load_mbox_emails_filters_by_received_date_and_preserves_source(tmp_path):
    mbox_path = tmp_path / "INBOX"
    append_message(
        mbox_path,
        date="Fri, 25 Jul 2026 09:00:00 +0900",
        subject="old",
        message_id="<old@example.com>",
    )
    append_message(
        mbox_path,
        date="Fri, 07 Aug 2026 17:30:00 +0900",
        subject="new project",
        message_id="<new@example.com>",
    )

    emails, invalid_dates = load_mbox_emails(
        mbox_path,
        since=datetime(2026, 7, 26, tzinfo=timezone.utc),
    )

    assert invalid_dates == 0
    assert len(emails) == 1
    assert emails[0].subject == "new project"
    assert emails[0].source_path.startswith("thunderbird-mbox://INBOX/")
    assert emails[0].source_type == "thunderbird_mbox"
    assert emails[0].body.strip() == "Java AWS project details"


def test_load_mbox_emails_skips_invalid_dates_and_limits_to_newest(tmp_path):
    mbox_path = tmp_path / "INBOX"
    append_message(mbox_path, date="invalid", subject="bad", message_id="<bad@example.com>")
    append_message(
        mbox_path,
        date="Thu, 06 Aug 2026 09:00:00 +0000",
        subject="first",
        message_id="<first@example.com>",
    )
    append_message(
        mbox_path,
        date="Fri, 07 Aug 2026 09:00:00 +0000",
        subject="second",
        message_id="<second@example.com>",
    )

    emails, invalid_dates = load_mbox_emails(
        mbox_path,
        since=parse_since("2026-08-01"),
        max_messages=1,
    )

    assert invalid_dates == 1
    assert [email.subject for email in emails] == ["second"]
