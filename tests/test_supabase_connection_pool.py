import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import app


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.closed = False

    def execute(self, query):
        self.queries.append(query)

    def fetchone(self):
        return (1,)

    def close(self):
        self.closed = True


class FakeRawConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj


class FakePool:
    def __init__(self):
        self.raw_connection = FakeRawConnection()
        self.returned = []
        self.closed_all = False

    def getconn(self):
        return self.raw_connection

    def putconn(self, conn, close=False):
        self.returned.append((conn, close))

    def closeall(self):
        self.closed_all = True


def test_supabase_pooler_mode_detection():
    assert (
        app._database_url_pooler_mode(
            "postgresql://postgres.project:password@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
        )
        == "supavisor_transaction"
    )
    assert (
        app._database_url_pooler_mode(
            "postgresql://postgres.project:password@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
        )
        == "supavisor_session"
    )
    assert (
        app._database_url_pooler_mode(
            "postgresql://postgres:password@db.project.supabase.co:5432/postgres"
        )
        == "direct_ipv6_risk"
    )


def test_supabase_pool_status_does_not_expose_connection_string(monkeypatch):
    monkeypatch.setattr(
        app,
        "DATABASE_URL",
        "postgresql://postgres.project:super-secret@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres",
    )
    monkeypatch.setattr(app, "USE_SUPABASE", True)
    monkeypatch.setattr(app, "POSTGRES_AVAILABLE", True)

    status = app.get_supabase_pool_status()

    assert status["enabled"] is True
    assert status["pooler_mode"] == "supavisor_transaction"
    assert "super-secret" not in repr(status)
    assert "SUPABASE_DB_URL" not in repr(status)


def test_get_db_connection_borrows_and_returns_pooled_connection(monkeypatch):
    fake_pool = FakePool()
    monkeypatch.setattr(app, "DATABASE_URL", "postgresql://example.invalid/postgres")
    monkeypatch.setattr(app, "USE_SUPABASE", True)
    monkeypatch.setattr(app, "POSTGRES_AVAILABLE", True)
    monkeypatch.setattr(app, "SUPABASE_DB_POOL_PRE_PING", True)
    monkeypatch.setattr(app, "_get_or_create_postgres_pool", lambda: fake_pool)

    conn, db_type = app.get_db_connection()

    assert db_type == "postgres"
    assert fake_pool.raw_connection.cursor_obj.queries == ["SELECT 1;"]
    assert fake_pool.returned == []

    conn.close()
    conn.close()

    assert fake_pool.returned == [(fake_pool.raw_connection, False)]

