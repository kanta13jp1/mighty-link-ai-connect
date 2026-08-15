import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sales_email_pop3 import fetch_pop3_emails


def test_fetch_pop3_emails_is_permanently_disabled():
    """Verify that fetch_pop3_emails raises RuntimeError and refuses execution to prevent server email deletion."""
    with pytest.raises(RuntimeError, match="POP3 email ingestion is permanently disabled"):
        fetch_pop3_emails()
