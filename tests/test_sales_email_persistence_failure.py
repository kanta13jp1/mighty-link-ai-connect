"""Storage failures must stop the sync instead of reporting zero new mail."""

import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_sales_emails import check_duplicate_key, insert_sales_email_message


def test_constraint_failure_is_fatal_and_connection_is_rolled_back():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sales_email_messages (id INTEGER PRIMARY KEY, source_type TEXT CHECK(source_type = 'api'))")
    db = SimpleNamespace(use_supabase=False, sqlite_conn=conn)
    with pytest.raises(RuntimeError, match="persistence failed"):
        insert_sales_email_message(db, {"source_type": "imap"})
    assert not conn.in_transaction
    assert conn.execute("SELECT count(*) FROM sales_email_messages").fetchone()[0] == 0
    conn.close()


def test_supabase_insert_without_record_is_fatal():
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.return_value.data = []
    db = SimpleNamespace(use_supabase=True, sb_client=client)
    with pytest.raises(RuntimeError, match="persistence failed"):
        insert_sales_email_message(db, {"source_type": "imap"})


def test_duplicate_lookup_failure_is_not_treated_as_new_mail():
    conn = sqlite3.connect(":memory:")
    db = SimpleNamespace(use_supabase=False, sqlite_conn=conn)
    with pytest.raises(RuntimeError, match="duplicate lookup failed"):
        check_duplicate_key(db, "test-key")
    conn.close()


def test_supabase_duplicate_lookup_without_response_is_fatal():
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = None
    db = SimpleNamespace(use_supabase=True, sb_client=client)
    with pytest.raises(RuntimeError, match="duplicate lookup failed"):
        check_duplicate_key(db, "test-key")
