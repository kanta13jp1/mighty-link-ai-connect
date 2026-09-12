from pathlib import Path
import sys

import pytest
import sqlite3
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import sync_sqlite_to_supabase


VALID_DB_URL = (
    "postgresql://postgres.abcdefghijklmnopqrst:p%40ss%23word@"
    "aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
)


def test_publish_constraint_failure_aborts_instead_of_success(tmp_path, monkeypatch):
    path = tmp_path / 'mail.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE sales_email_messages(id, dedupe_key, message_id_hash, sender_hash, sender_domain, normalized_subject, received_at, body_hash, body_excerpt, source_path, source_type, raw_storage_policy, ingest_status, metadata)')
        conn.execute("INSERT INTO sales_email_messages VALUES(1,'key','hash','sender','example.test','Test',NULL,'body','Excerpt','imap://test','imap','hash_and_redacted_excerpt_only','new','{}')")
    pg = MagicMock()
    cursor = pg.cursor.return_value
    cursor.fetchall.return_value = []
    def execute(sql, *args):
        if 'INSERT INTO sales_email_messages' in sql:
            raise RuntimeError('constraint violation')
    cursor.execute.side_effect = execute
    monkeypatch.setattr(sync_sqlite_to_supabase, 'load_env_file', lambda: None)
    with pytest.raises(RuntimeError, match='transaction rolled back'):
        sync_sqlite_to_supabase.sync_tables(db_url=VALID_DB_URL, connection_factory=lambda _: pg, sqlite_path=path)
    pg.rollback.assert_called_once()
    pg.commit.assert_not_called()


def test_percent_encoded_supavisor_url_is_accepted():
    sync_sqlite_to_supabase.validate_database_url(VALID_DB_URL)


@pytest.mark.parametrize(
    "malformed_url",
    [
        (
            "postgresql://postgres.abcdefghijklmnopqrst:raw@password@"
            "aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        ),
        (
            "postgresql://postgres.abcdefghijklmnopqrst:raw#password@"
            "aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        ),
        (
            "postgresql://postgres.abcdefghijklmnopqrst:raw%ZZpassword@"
            "aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        ),
        (
            "postgresql://postgres.abcdefghijklmnopqrst:password@"
            "attacker.invalid:6543/postgres?sslmode=require"
        ),
        (
            "postgresql://postgres.abcdefghijklmnopqrst:password@"
            "aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
        ),
    ],
)
def test_invalid_url_is_rejected_before_connection(malformed_url: str, monkeypatch):
    # sync_tables() calls load_env_file(), which os.environ.setdefault()s the
    # repo .env. Left unstubbed that writes REAL secrets into the pytest process
    # and leaks into every later test, so stub it out here.
    monkeypatch.setattr(sync_sqlite_to_supabase, "load_env_file", lambda: None)
    connection_attempted = False

    def fail_if_called(_url: str):
        nonlocal connection_attempted
        connection_attempted = True
        pytest.fail("database connection must not be attempted")

    with pytest.raises(ValueError, match="SUPABASE_DB_URL is invalid"):
        sync_sqlite_to_supabase.sync_tables(
            db_url=malformed_url,
            connection_factory=fail_if_called,
        )

    assert connection_attempted is False


def test_driver_error_is_suppressed_from_cli_output(monkeypatch, tmp_path, capsys):
    sqlite_path = tmp_path / "mighty.db"
    sqlite_path.touch()
    leaked_fragment = "credential-derived-fragment"

    monkeypatch.setenv("SUPABASE_DB_URL", VALID_DB_URL)
    monkeypatch.setattr(
        sync_sqlite_to_supabase,
        "PROJECT_ROOT",
        Path(tmp_path),
    )
    monkeypatch.setattr(
        sync_sqlite_to_supabase.psycopg2,
        "connect",
        lambda _url: (_ for _ in ()).throw(
            RuntimeError(f"could not resolve {leaked_fragment} from {VALID_DB_URL}")
        ),
    )

    result = sync_sqlite_to_supabase.main()
    captured = capsys.readouterr()
    rendered = captured.out + captured.err

    assert result == 1
    assert rendered.strip() == sync_sqlite_to_supabase._SAFE_FAILURE_MESSAGE
    assert leaked_fragment not in rendered
    assert VALID_DB_URL not in rendered


def test_missing_url_fails_closed(monkeypatch, capsys):
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.setattr(sync_sqlite_to_supabase, "load_env_file", lambda: None)

    assert sync_sqlite_to_supabase.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == sync_sqlite_to_supabase._SAFE_FAILURE_MESSAGE


def test_env_file_cannot_override_dedicated_database_url(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SUPABASE_DB_URL=postgresql://stale.invalid\nIMAP_HOST=mail.example.test\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sync_sqlite_to_supabase, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("SUPABASE_DB_URL", VALID_DB_URL)
    monkeypatch.delenv("IMAP_HOST", raising=False)

    sync_sqlite_to_supabase.load_env_file()

    assert sync_sqlite_to_supabase.os.environ["SUPABASE_DB_URL"] == VALID_DB_URL
    assert sync_sqlite_to_supabase.os.environ["IMAP_HOST"] == "mail.example.test"
