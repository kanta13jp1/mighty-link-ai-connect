"""IMAP sales email connector for real email ingestion (T910 / T817).

This module retrieves raw emails from IMAP folders (such as INBOX and Trash)
and converts them into RawSalesEmail objects for pipeline processing.
"""

from __future__ import annotations

import os
import ssl
import imaplib
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import List, Sequence

from sales_email_ingest import RawSalesEmail, _message_body


def load_env_file():
    """Load variables from .env file into os.environ if present."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition("=")
            if sep:
                val = value.strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                os.environ.setdefault(key.strip(), val)


def fetch_imap_emails(
    host: str | None = None,
    port: int | None = None,
    use_ssl: bool | None = None,
    username: str | None = None,
    password: str | None = None,
    folders: Sequence[str] | None = None,
    max_messages: int | None = None,
) -> list[RawSalesEmail]:
    """Fetch emails from IMAP server across specified folders.

    If arguments are None, values are read from environment variables.
    """
    load_env_file()

    host = host or os.getenv("IMAP_HOST", os.getenv("POP3_HOST"))
    port_str = os.getenv("IMAP_PORT", "993")
    port = port or (int(port_str) if port_str else 993)

    use_ssl_str = os.getenv("IMAP_USE_SSL", "true").lower()
    use_ssl = use_ssl if use_ssl is not None else (use_ssl_str == "true")

    username = username or os.getenv("IMAP_USERNAME", os.getenv("POP3_USERNAME"))
    password = password or os.getenv("IMAP_PASSWORD", os.getenv("POP3_PASSWORD"))

    if folders is None:
        env_folders = os.getenv("IMAP_FOLDERS", "INBOX,Trash").split(",")
        folders = [f.strip() for f in env_folders if f.strip()]

    if max_messages is None:
        max_messages_str = os.getenv("SALES_EMAIL_PARSE_MAX_MESSAGES", "1000")
        max_messages = int(max_messages_str) if max_messages_str else 1000

    if not host or not username or not password:
        raise ValueError("IMAP host, username, and password must be configured in environment or passed directly.")

    emails: list[RawSalesEmail] = []
    print(f"Connecting to IMAP server {host}:{port} (SSL: {use_ssl}) for user '{username}'...")

    if use_ssl:
        context = ssl.create_default_context()
        client = imaplib.IMAP4_SSL(host, port, ssl_context=context)
    else:
        client = imaplib.IMAP4(host, port)

    try:
        client.login(username, password)

        for folder in folders:
            try:
                res, _ = client.select(f'"{folder}"', readonly=True)
                if res != "OK":
                    print(f"[-] Could not select IMAP folder '{folder}' (status: {res})")
                    continue

                typ, data = client.search(None, "ALL")
                if not data or not data[0]:
                    print(f"[*] Folder '{folder}' is empty.")
                    continue

                mids = data[0].split()
                print(f"[*] Folder '{folder}': found {len(mids)} messages.")

                # Take newest up to max_messages per folder/batch
                if max_messages and len(mids) > max_messages:
                    mids = mids[-max_messages:]

                for mid in reversed(mids):
                    try:
                        _, msg_data = client.fetch(mid, "(RFC822)")
                        if not msg_data or not msg_data[0]:
                            continue

                        raw_bytes = msg_data[0][1]
                        if not isinstance(raw_bytes, bytes):
                            continue

                        msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
                        mid_str = mid.decode("utf-8", errors="ignore")

                        emails.append(
                            RawSalesEmail(
                                source_path=f"imap://{host}/{folder}/{mid_str}",
                                source_type="imap",
                                sender=str(msg.get("From", "")),
                                subject=str(msg.get("Subject", f"IMAP message {mid_str}")),
                                received_at=str(msg.get("Date", "")),
                                message_id=str(msg.get("Message-ID", "")),
                                body=_message_body(msg),
                            )
                        )
                    except Exception as msg_err:
                        print(f"[-] Error fetching IMAP message {mid}: {msg_err}")

            except Exception as folder_err:
                print(f"[-] Error searching folder '{folder}': {folder_err}")

    finally:
        try:
            client.logout()
        except Exception:
            pass

    print(f"[+] Total IMAP emails fetched: {len(emails)}")
    return emails
