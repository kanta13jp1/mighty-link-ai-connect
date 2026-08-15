"""Read-only POP3 sales email connector.

This module retrieves raw emails from a POP3 server, parses them, and
converts them into RawSalesEmail objects. Server-side deletion is
intentionally unsupported for shared sales mailboxes.
"""

from __future__ import annotations

import os
import poplib
import ssl
from email import policy
from email.parser import BytesParser
from pathlib import Path
# Import from ingest module where RawSalesEmail is defined
from sales_email_ingest import RawSalesEmail, _message_body

_TRUE_VALUES = {"1", "true", "yes", "on"}


def load_env_file():
    """Load variables from .env file into os.environ if it exists."""
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


def _require_leave_on_server(leave_on_server: bool | None) -> None:
    """Reject any configuration that requests server-side deletion."""
    if leave_on_server is None:
        raw_value = os.getenv("POP3_LEAVE_ON_SERVER", "true").strip().lower()
        leave_on_server = True if not raw_value else raw_value in _TRUE_VALUES

    if leave_on_server is not True:
        raise ValueError(
            "Destructive POP3 retrieval is disabled. "
            "POP3_LEAVE_ON_SERVER must be true for shared sales mailboxes."
        )


def fetch_pop3_emails(
    host: str | None = None,
    port: int | None = None,
    use_ssl: bool | None = None,
    username: str | None = None,
    password: str | None = None,
    leave_on_server: bool | None = None,
    max_messages: int | None = None,
) -> list[RawSalesEmail]:
    """POP3 email ingestion is permanently disabled in this system for security and data loss prevention."""
    raise RuntimeError(
        "POP3 email ingestion is permanently disabled in this system to prevent any risk of server-side email deletion. "
        "Please use IMAP read-only mode (sales_email_imap) for receiving sales emails."
    )
