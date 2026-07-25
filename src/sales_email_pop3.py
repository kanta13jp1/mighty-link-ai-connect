"""POP3 sales email connector.

This module retrieves raw emails from a POP3 server, parses them, and
converts them into RawSalesEmail objects.
"""

from __future__ import annotations

import os
import poplib
import ssl
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Sequence

# Import from ingest module where RawSalesEmail is defined
from sales_email_ingest import RawSalesEmail, _message_body


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


def fetch_pop3_emails(
    host: str | None = None,
    port: int | None = None,
    use_ssl: bool | None = None,
    username: str | None = None,
    password: str | None = None,
    leave_on_server: bool | None = None,
    max_messages: int | None = None,
) -> list[RawSalesEmail]:
    """Fetch emails from POP3 server and parse them.

    If arguments are None, values are read from environment variables.
    """
    load_env_file()
    # Environment variable fallbacks
    host = host or os.getenv("POP3_HOST")
    port_str = os.getenv("POP3_PORT", "995")
    port = port or (int(port_str) if port_str else 995)
    
    use_ssl_str = os.getenv("POP3_USE_SSL", "true").lower()
    use_ssl = use_ssl if use_ssl is not None else (use_ssl_str == "true")
    
    username = username or os.getenv("POP3_USERNAME")
    password = password or os.getenv("POP3_PASSWORD")
    
    # HARD SAFETY ENFORCEMENT: Never delete messages from POP3 server (Read-Only Safety)
    leave_on_server = True
    
    # Load limit for safety (default to 1000 for daily 1000-email ingest scale)
    if max_messages is None:
        max_messages_str = os.getenv("SALES_EMAIL_PARSE_MAX_MESSAGES", "1000")
        max_messages = int(max_messages_str) if max_messages_str else 1000

    if not host or not username or not password:
        raise ValueError("POP3 host, username, and password must be configured in environment or passed directly.")

    emails: list[RawSalesEmail] = []
    
    print(f"Connecting to POP3 server {host}:{port} (SSL: {use_ssl}) [READ-ONLY SAFETY ENFORCED]...")
    
    if use_ssl:
        context = ssl.create_default_context()
        client = poplib.POP3_SSL(host, port, context=context)
    else:
        client = poplib.POP3(host, port)
        
    try:
        client.getwelcome()
        client.user(username)
        client.pass_(password)
        
        num_messages, _ = client.stat()
        print(f"Total messages on server: {num_messages}")
        
        # Load newest first
        start_idx = max(1, num_messages - max_messages + 1)
        
        print(f"Fetching messages from index {start_idx} to {num_messages}...")
        for i in range(num_messages, start_idx - 1, -1):
            try:
                _, lines, _ = client.retr(i)
                raw_content = b"\n".join(lines)
                
                # Parse
                message = BytesParser(policy=policy.default).parsebytes(raw_content)
                
                emails.append(
                    RawSalesEmail(
                        source_path=f"pop3://{host}/{i}",
                        source_type="pop3",
                        sender=str(message.get("From", "")),
                        subject=str(message.get("Subject", f"POP3 message {i}")),
                        received_at=str(message.get("Date", "")),
                        message_id=str(message.get("Message-ID", "")),
                        body=_message_body(message),
                    )
                )
                # NEVER issue DELE command - strictly read-only
            except Exception as msg_err:
                print(f"Error fetching message {i}: {msg_err}")
                
    finally:
        client.quit()
        
    return emails
