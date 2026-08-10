# -*- coding: utf-8 -*-
import os
import sys
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

import app
import sales_email_pop3
import sync_sales_emails

client = TestClient(app.app)

@patch("sync_sales_emails.sync_sales_emails_pipeline")
def test_sync_sales_emails_endpoint_success(mock_pipeline):
    mock_pipeline.return_value = {
        "status": "success",
        "new_emails_count": 3
    }
    
    # Authorize with basic credentials using auth parameter
    response = client.post(
        "/api/sales-email/sync",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD)
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "new_emails_count": 3
    }
    mock_pipeline.assert_called_once_with(max_messages=None, retry_errors=False)


@patch("sync_sales_emails.sync_sales_emails_pipeline")
def test_sync_sales_emails_endpoint_with_max_messages(mock_pipeline):
    mock_pipeline.return_value = {
        "status": "success",
        "new_emails_count": 1000
    }
    
    response = client.post(
        "/api/sales-email/sync?max_messages=1000",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD)
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "new_emails_count": 1000
    }
    mock_pipeline.assert_called_once_with(max_messages=1000, retry_errors=False)


def test_sync_sales_emails_endpoint_unauthorized():
    response = client.post("/api/sales-email/sync")
    assert response.status_code == 401


def test_pipeline_never_falls_back_to_pop3(monkeypatch):
    class DummyCursor:
        def execute(self, *_args, **_kwargs):
            return None

        def fetchone(self):
            return None

    class DummyConnection:
        def cursor(self):
            return DummyCursor()

    class DummyDb:
        use_supabase = False
        sqlite_conn = DummyConnection()

        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    def fail_pop3_fetch(*_args, **_kwargs):
        pytest.fail("POP3 must not be called by the automatic sync pipeline")

    db = DummyDb()
    monkeypatch.setattr(sync_sales_emails, "DBAdapter", lambda _path: db)
    monkeypatch.setattr(sync_sales_emails, "sync_imap_to_db", lambda *_args, **_kwargs: 0)
    monkeypatch.setattr(sync_sales_emails, "rebuild_extraction_review_json", lambda _db: None)
    monkeypatch.setattr(sync_sales_emails, "rebuild_match_review_json", lambda: None)
    monkeypatch.setattr(sync_sales_emails, "run_parser", lambda _args: pytest.fail("parser should not run"))
    monkeypatch.setattr(sales_email_pop3, "fetch_pop3_emails", fail_pop3_fetch)

    result = sync_sales_emails.sync_sales_emails_pipeline()

    assert result["new_emails_count"] == 0
    assert db.closed is True


def test_pipeline_fails_closed_when_imap_fetch_fails(monkeypatch):
    class DummyDb:
        use_supabase = False
        sqlite_conn = None

        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    db = DummyDb()
    monkeypatch.setattr(sync_sales_emails, "DBAdapter", lambda _path: db)

    def fail_imap_fetch(*_args, **_kwargs):
        raise ConnectionError("authentication failed")

    monkeypatch.setattr(sync_sales_emails, "fetch_imap_emails", fail_imap_fetch)

    with pytest.raises(ConnectionError, match="authentication failed"):
        sync_sales_emails.sync_sales_emails_pipeline()

    assert db.closed is True
