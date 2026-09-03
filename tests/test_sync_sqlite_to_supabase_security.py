"""Regression tests for secure Supabase publishing from the sales-email sync."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import sync_sqlite_to_supabase as sync_module


VALID_DB_URL = (
    "postgresql://postgres.abcdefghijklmnopqrst:super-secret@"
    "aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
)


def test_secure_connect_rejects_raw_reserved_password_before_driver_call(monkeypatch):
    malformed_url = (
        "postgresql://postgres.abcdefghijklmnopqrst:synthetic@credential-fragment@"
        "aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    connection_attempted = False

    def must_not_connect(_url):
        nonlocal connection_attempted
        connection_attempted = True
        raise AssertionError("database driver must not be called")

    monkeypatch.setattr(sync_module.psycopg2, "connect", must_not_connect)

    with pytest.raises(sync_module.SupabaseSyncError) as exc_info:
        sync_module._connect_postgres_secure(malformed_url)

    rendered = str(exc_info.value)
    assert connection_attempted is False
    assert "invalid_database_url" in rendered
    assert "credential-fragment" not in rendered
    assert malformed_url not in rendered


def test_secure_connect_suppresses_database_driver_exception_text(monkeypatch):
    leaked_fragment = "synthetic-secret-fragment"

    def fail_connection(_url):
        raise RuntimeError(f"could not connect using {leaked_fragment}")

    monkeypatch.setattr(sync_module.psycopg2, "connect", fail_connection)

    with pytest.raises(sync_module.SupabaseSyncError) as exc_info:
        sync_module._connect_postgres_secure(VALID_DB_URL)

    rendered = str(exc_info.value)
    assert "database_connection_failed" in rendered
    assert leaked_fragment not in rendered
    assert VALID_DB_URL not in rendered


def test_main_suppresses_unhandled_sync_exception_text(monkeypatch, capsys):
    leaked_fragment = "synthetic-secret-fragment"

    def fail_sync():
        raise RuntimeError(f"unexpected database failure: {leaked_fragment}")

    monkeypatch.setattr(sync_module, "sync_tables", fail_sync)

    assert sync_module.main() == 1

    output = capsys.readouterr()
    rendered = output.out + output.err
    assert "database_sync_failed" in rendered
    assert leaked_fragment not in rendered
