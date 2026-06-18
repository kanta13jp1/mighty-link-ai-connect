import re
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import manage_db_migrations as migrations


SUPABASE_MIGRATION = PROJECT_ROOT / "supabase" / "migrations" / "20260618000000_sales_email_matching_schema.sql"
POSTGRES_MIGRATION = PROJECT_ROOT / "db" / "migrations" / "postgres" / "20260618000000_sales_email_matching_schema.sql"
SQLITE_MIGRATION = PROJECT_ROOT / "db" / "migrations" / "sqlite" / "20260618000000_sales_email_matching_schema.sql"
ROLLBACK_SQL = PROJECT_ROOT / "db" / "migrations" / "rollback" / "20260618000000_sales_email_matching_schema_rollback.sql"
SEED_SQL = PROJECT_ROOT / "supabase" / "seed.sql"

REQUIRED_TABLES = [
    "sales_mailbox_sources",
    "sales_email_messages",
    "sales_email_entities",
    "project_requirements",
    "talent_profiles_from_email",
    "requirement_skill_tags",
    "email_parse_runs",
    "email_match_results",
    "email_match_feedback",
]


def test_supabase_sales_email_tables_have_rls_and_no_anon_policies():
    sql = SUPABASE_MIGRATION.read_text(encoding="utf-8")
    normalized = " ".join(sql.split())

    for table in REQUIRED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS public.{table}" in sql
        assert re.search(
            rf"ALTER\s+TABLE\s+public\.{table}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
            normalized,
            re.IGNORECASE,
        ), f"RLS must be enabled for {table}"
        assert re.search(
            rf"REVOKE\s+ALL\s+ON\s+TABLE\s+public\.{table}\s+FROM\s+anon,\s+authenticated",
            normalized,
            re.IGNORECASE,
        ), f"Direct anon/authenticated access must be revoked for {table}"

    assert "CREATE POLICY" not in normalized.upper()
    assert "raw_email_body" not in normalized.lower()
    assert "oauth_token" not in normalized.lower()
    assert "service_role" not in normalized.lower()


def test_sqlite_sales_email_migration_applies_and_enforces_core_constraints(tmp_path):
    db_path = tmp_path / "mighty-sales-email.db"
    assert migrations.main(["apply", "--engine", "sqlite", "--sqlite-path", str(db_path)]) == 0

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        assert set(REQUIRED_TABLES).issubset(tables)

        source_id = conn.execute(
            """
            INSERT INTO sales_mailbox_sources(source_key, display_name, source_type)
            VALUES ('test_source', 'Test Source', 'manual_upload')
            """
        ).lastrowid
        conn.execute(
            """
            INSERT INTO sales_email_messages(
                mailbox_source_id,
                dedupe_key,
                sender_hash,
                normalized_subject,
                body_hash,
                body_excerpt,
                source_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                "a" * 64,
                "b" * 64,
                "SQL Oracle project",
                "c" * 64,
                "Contact: <email:redacted>",
                "manual_upload",
            ),
        )

        try:
            conn.execute(
                """
                INSERT INTO sales_email_messages(
                    mailbox_source_id,
                    dedupe_key,
                    sender_hash,
                    normalized_subject,
                    body_hash,
                    source_type,
                    raw_storage_policy
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    "d" * 64,
                    "e" * 64,
                    "unsafe raw body",
                    "f" * 64,
                    "manual_upload",
                    "raw_body_allowed",
                ),
            )
        except sqlite3.IntegrityError as exc:
            assert "CHECK constraint failed" in str(exc)
        else:
            raise AssertionError("raw body storage policy must be rejected")


def test_seed_and_rollback_are_synthetic_and_complete():
    seed = SEED_SQL.read_text(encoding="utf-8")
    rollback = ROLLBACK_SQL.read_text(encoding="utf-8")

    assert "@ml-mightylink.com" not in seed
    assert "mightylink-app.com" not in seed
    assert "example.test" in seed
    assert "local_synthetic_sales_mailbox" in seed
    assert "local_synthetic_talent_001" in seed

    for table in reversed(REQUIRED_TABLES):
        assert f"DROP TABLE IF EXISTS public.{table}" in rollback


def test_postgres_and_sqlite_migrations_are_present():
    assert POSTGRES_MIGRATION.exists()
    assert SQLITE_MIGRATION.exists()
    assert SUPABASE_MIGRATION.exists()
    assert ROLLBACK_SQL.exists()
