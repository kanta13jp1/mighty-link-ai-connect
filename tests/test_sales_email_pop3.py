import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sales_email_pop3 import fetch_pop3_emails
from sales_email_ingest import RawSalesEmail


@pytest.fixture
def mock_pop3_ssl():
    with patch("poplib.POP3_SSL") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        
        # stat returns (num_messages, total_size)
        mock_client.stat.return_value = (3, 1000)
        mock_client.getwelcome.return_value = b"+OK Pop server ready"
        mock_client.user.return_value = b"+OK User accepted"
        mock_client.pass_.return_value = b"+OK Pass accepted"
        
        # retr returns (response, lines, octets)
        msg1_lines = [
            b"From: test1@example.com",
            b"Subject: Test Subject 1",
            b"Date: Wed, 08 Jul 2026 12:00:00 +0900",
            b"Message-ID: <msg1@example.com>",
            b"",
            b"Body of message 1",
        ]
        msg2_lines = [
            b"From: test2@example.com",
            b"Subject: Test Subject 2",
            b"Date: Wed, 08 Jul 2026 12:10:00 +0900",
            b"Message-ID: <msg2@example.com>",
            b"",
            b"Body of message 2",
        ]
        msg3_lines = [
            b"From: test3@example.com",
            b"Subject: Test Subject 3",
            b"Date: Wed, 08 Jul 2026 12:20:00 +0900",
            b"Message-ID: <msg3@example.com>",
            b"",
            b"Body of message 3",
        ]
        
        # mock client retr behavior
        def mock_retr(idx):
            if idx == 1:
                return (b"+OK", msg1_lines, 200)
            elif idx == 2:
                return (b"+OK", msg2_lines, 200)
            elif idx == 3:
                return (b"+OK", msg3_lines, 200)
            raise ValueError("Invalid index")
            
        mock_client.retr.side_effect = mock_retr
        yield mock_client


def test_fetch_pop3_emails_success(mock_pop3_ssl):
    # Set env vars temporarily
    env_patch = {
        "POP3_HOST": "pop.example.com",
        "POP3_PORT": "995",
        "POP3_USE_SSL": "true",
        "POP3_USERNAME": "test_user",
        "POP3_PASSWORD": "test_password",
        "POP3_LEAVE_ON_SERVER": "true",
    }
    with patch.dict(os.environ, env_patch):
        emails = fetch_pop3_emails()
        
        assert len(emails) == 3
        # Should be ordered newest first (index 3 down to 1)
        assert emails[0].sender == "test3@example.com"
        assert emails[0].subject == "Test Subject 3"
        assert emails[0].body.strip() == "Body of message 3"
        
        assert emails[2].sender == "test1@example.com"
        assert emails[2].subject == "Test Subject 1"
        assert emails[2].body.strip() == "Body of message 1"
        
        # verify no deletion
        mock_pop3_ssl.dele.assert_not_called()
        mock_pop3_ssl.quit.assert_called_once()


def test_fetch_pop3_emails_rejects_deletion(mock_pop3_ssl):
    env_patch = {
        "POP3_HOST": "pop.example.com",
        "POP3_PORT": "995",
        "POP3_USE_SSL": "true",
        "POP3_USERNAME": "test_user",
        "POP3_PASSWORD": "test_password",
        "POP3_LEAVE_ON_SERVER": "false",
    }
    with patch.dict(os.environ, env_patch):
        with pytest.raises(ValueError, match="Destructive POP3 retrieval is disabled"):
            fetch_pop3_emails()

    mock_pop3_ssl.dele.assert_not_called()


def test_fetch_pop3_emails_blank_leave_setting_is_safe(mock_pop3_ssl):
    env_patch = {
        "POP3_HOST": "pop.example.com",
        "POP3_PORT": "995",
        "POP3_USE_SSL": "true",
        "POP3_USERNAME": "test_user",
        "POP3_PASSWORD": "test_password",
        "POP3_LEAVE_ON_SERVER": "",
    }
    with patch.dict(os.environ, env_patch):
        emails = fetch_pop3_emails()

    assert len(emails) == 3
    mock_pop3_ssl.dele.assert_not_called()


def test_fetch_pop3_emails_limit(mock_pop3_ssl):
    env_patch = {
        "POP3_HOST": "pop.example.com",
        "POP3_PORT": "995",
        "POP3_USE_SSL": "true",
        "POP3_USERNAME": "test_user",
        "POP3_PASSWORD": "test_password",
        "POP3_LEAVE_ON_SERVER": "true",
    }
    with patch.dict(os.environ, env_patch):
        # Fetch with max_messages = 2
        emails = fetch_pop3_emails(max_messages=2)
        # Should only get latest 2 messages (indices 3 and 2)
        assert len(emails) == 2
        assert emails[0].subject == "Test Subject 3"
        assert emails[1].subject == "Test Subject 2"


def test_fetch_pop3_emails_1000_scale():
    """Verify POP3 ingest handles 1000-email scale (T910 requirements)."""
    with patch("poplib.POP3_SSL") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        
        # Simulate 1000 messages on server
        mock_client.stat.return_value = (1000, 5000000)
        mock_client.getwelcome.return_value = b"+OK Pop server ready"
        mock_client.user.return_value = b"+OK User accepted"
        mock_client.pass_.return_value = b"+OK Pass accepted"
        
        def mock_retr(idx):
            msg_lines = [
                f"From: sender{idx}@example.com".encode(),
                f"Subject: Sales Email {idx}".encode(),
                b"Date: Wed, 22 Jul 2026 12:00:00 +0900",
                f"Message-ID: <msg{idx}@example.com>".encode(),
                b"",
                f"Body content of sales email {idx}".encode(),
            ]
            return (b"+OK", msg_lines, 500)

        mock_client.retr.side_effect = mock_retr

        env_patch = {
            "POP3_HOST": "pop.example.com",
            "POP3_PORT": "995",
            "POP3_USE_SSL": "true",
            "POP3_USERNAME": "test_user",
            "POP3_PASSWORD": "test_password",
            "POP3_LEAVE_ON_SERVER": "true",
        }
        with patch.dict(os.environ, env_patch):
            emails = fetch_pop3_emails(max_messages=1000)
            assert len(emails) == 1000
            assert emails[0].subject == "Sales Email 1000"
            assert emails[999].subject == "Sales Email 1"
            assert emails[0].source_type == "pop3"
