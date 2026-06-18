# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "manage_db_migrations.py"


def load_module():
    spec = importlib.util.spec_from_file_location("manage_db_migrations", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_project_migration_directories():
    module = load_module()
    for engine in ("sqlite", "postgres", "supabase"):
        migrations = module.load_migrations(module.default_migration_dir(engine))
        assert migrations
        assert migrations == sorted(migrations, key=lambda migration: migration.version)


def test_sqlite_apply_is_idempotent(tmp_path):
    module = load_module()
    db_path = tmp_path / "mighty-test.db"

    assert module.main(["apply", "--engine", "sqlite", "--sqlite-path", str(db_path)]) == 0
    assert module.main(["apply", "--engine", "sqlite", "--sqlite-path", str(db_path)]) == 0

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        ledger = conn.execute("SELECT version, name FROM schema_migrations").fetchall()

    assert {
        "engineers",
        "jobs",
        "match_results",
        "feedback_events",
        "support_requests",
        "sales_mailbox_sources",
        "sales_email_messages",
        "sales_email_entities",
        "project_requirements",
        "talent_profiles_from_email",
        "requirement_skill_tags",
        "email_parse_runs",
        "email_match_results",
        "email_match_feedback",
        "schema_migrations",
    }.issubset(tables)
    assert ledger == [
        ("20260614000000", "app_core_schema"),
        ("20260616000000", "feedback_events"),
        ("20260616000001", "support_requests"),
        ("20260618000000", "sales_email_matching_schema"),
    ]


def test_duplicate_migration_version_is_rejected(tmp_path):
    module = load_module()
    (tmp_path / "20260614000000_first.sql").write_text("CREATE TABLE first_table(id INTEGER);\n", encoding="utf-8")
    (tmp_path / "20260614000000_second.sql").write_text("CREATE TABLE second_table(id INTEGER);\n", encoding="utf-8")

    with pytest.raises(module.MigrationError, match="Duplicate migration version"):
        module.load_migrations(tmp_path)


def test_sql_splitter_handles_postgres_dollar_quoted_functions():
    module = load_module()
    sql = """
    CREATE OR REPLACE FUNCTION trigger_set_timestamp()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TABLE example(id INTEGER PRIMARY KEY);
    """

    statements = module.split_sql_statements(sql)

    assert len(statements) == 2
    assert "RETURN NEW;" in statements[0]
    assert statements[1].startswith("CREATE TABLE example")
