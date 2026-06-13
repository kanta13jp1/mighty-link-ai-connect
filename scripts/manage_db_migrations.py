#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Validate and apply project database migrations.

This is a small Flyway-style migration runner for the repository's app-level
schema files. Supabase project migrations remain in ``supabase/migrations`` and
are deployed with the Supabase CLI; this script validates those files so CI can
catch filename/order issues before a shared database is touched.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_RE = re.compile(r"^(?P<version>\d{14})_(?P<name>[a-z0-9][a-z0-9_]*).sql$")
VALIDATE_ONLY_ENGINES = {"supabase"}
APPLY_ENGINES = {"sqlite", "postgres"}


class MigrationError(RuntimeError):
    """Raised when migration validation or application fails."""


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path
    checksum: str
    statements: int

    def to_report(self) -> dict[str, Any]:
        row = asdict(self)
        row["path"] = str(self.path.relative_to(PROJECT_ROOT))
        return row


def default_migration_dir(engine: str) -> Path:
    if engine == "supabase":
        return PROJECT_ROOT / "supabase" / "migrations"
    return PROJECT_ROOT / "db" / "migrations" / engine


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def checksum_sql(sql: str) -> str:
    normalized = sql.replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def find_dollar_tag(sql: str, index: int) -> str | None:
    match = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", sql[index:])
    return match.group(0) if match else None


def split_sql_statements(sql: str) -> list[str]:
    """Split SQL on semicolons while respecting quotes and dollar strings."""

    statements: list[str] = []
    buffer: list[str] = []
    i = 0
    in_single = False
    in_double = False
    in_line_comment = False
    in_block_comment = False
    dollar_tag: str | None = None

    while i < len(sql):
        char = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""

        if in_line_comment:
            buffer.append(char)
            if char == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            buffer.append(char)
            if char == "*" and nxt == "/":
                buffer.append(nxt)
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if dollar_tag:
            if sql.startswith(dollar_tag, i):
                buffer.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
            else:
                buffer.append(char)
                i += 1
            continue

        if not in_single and not in_double:
            if char == "-" and nxt == "-":
                buffer.extend([char, nxt])
                in_line_comment = True
                i += 2
                continue
            if char == "/" and nxt == "*":
                buffer.extend([char, nxt])
                in_block_comment = True
                i += 2
                continue
            tag = find_dollar_tag(sql, i)
            if tag:
                buffer.append(tag)
                dollar_tag = tag
                i += len(tag)
                continue

        if char == "'" and not in_double:
            buffer.append(char)
            if in_single and nxt == "'":
                buffer.append(nxt)
                i += 2
                continue
            in_single = not in_single
            i += 1
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            buffer.append(char)
            i += 1
            continue

        if char == ";" and not in_single and not in_double:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            i += 1
            continue

        buffer.append(char)
        i += 1

    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def load_migrations(migration_dir: Path) -> list[Migration]:
    if not migration_dir.exists():
        raise MigrationError(f"Migration directory not found: {migration_dir}")

    migrations: list[Migration] = []
    seen_versions: dict[str, Path] = {}
    for path in sorted(migration_dir.glob("*.sql")):
        match = MIGRATION_RE.fullmatch(path.name)
        if not match:
            raise MigrationError(
                f"Invalid migration filename: {path.name}. Use YYYYMMDDHHMMSS_short_slug.sql"
            )
        sql = path.read_text(encoding="utf-8")
        if not sql.strip():
            raise MigrationError(f"Migration file is empty: {path}")
        version = match.group("version")
        if version in seen_versions:
            raise MigrationError(
                f"Duplicate migration version {version}: {seen_versions[version]} and {path}"
            )
        seen_versions[version] = path
        statements = split_sql_statements(sql)
        if not statements:
            raise MigrationError(f"Migration has no SQL statements: {path}")
        migrations.append(
            Migration(
                version=version,
                name=match.group("name"),
                path=path,
                checksum=checksum_sql(sql),
                statements=len(statements),
            )
        )
    if not migrations:
        raise MigrationError(f"No migration files found in {migration_dir}")
    return migrations


def ledger_sql(engine: str) -> str:
    if engine == "sqlite":
        return """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at_utc TEXT NOT NULL
        )
        """
    return """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        checksum TEXT NOT NULL,
        applied_at_utc TIMESTAMPTZ NOT NULL
    )
    """


def ensure_ledger(conn: Any, engine: str) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(ledger_sql(engine))
        conn.commit()
    finally:
        cursor.close()


def load_applied(conn: Any) -> dict[str, str]:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT version, checksum FROM schema_migrations")
        return {str(row[0]): str(row[1]) for row in cursor.fetchall()}
    finally:
        cursor.close()


def ledger_exists(conn: Any, engine: str) -> bool:
    cursor = conn.cursor()
    try:
        if engine == "sqlite":
            cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
            )
            return cursor.fetchone() is not None
        cursor.execute("SELECT to_regclass('public.schema_migrations') IS NOT NULL")
        row = cursor.fetchone()
        return bool(row and row[0])
    finally:
        cursor.close()


def connect_sqlite(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def connect_sqlite_readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def connect_postgres(database_url: str) -> Any:
    try:
        import psycopg2
    except ImportError as exc:
        raise MigrationError("psycopg2 is required for postgres migration apply") from exc
    return psycopg2.connect(database_url, connect_timeout=10)


def execute_migration(conn: Any, engine: str, migration: Migration) -> None:
    sql = migration.path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql)
    cursor = conn.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
        cursor.execute(
            "INSERT INTO schema_migrations(version, name, checksum, applied_at_utc) VALUES (%s, %s, %s, %s)"
            if engine == "postgres"
            else "INSERT INTO schema_migrations(version, name, checksum, applied_at_utc) VALUES (?, ?, ?, ?)",
            (migration.version, migration.name, migration.checksum, utc_now()),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def build_plan(migrations: Iterable[Migration], applied: dict[str, str] | None = None) -> list[dict[str, Any]]:
    applied = applied or {}
    plan: list[dict[str, Any]] = []
    for migration in migrations:
        status = "pending"
        applied_checksum = applied.get(migration.version)
        if applied_checksum:
            status = "applied" if applied_checksum == migration.checksum else "checksum_mismatch"
        row = migration.to_report()
        row["status"] = status
        plan.append(row)
    return plan


def render_report(command: str, engine: str, migration_dir: Path, plan: list[dict[str, Any]]) -> dict[str, Any]:
    status = "ok"
    if any(row["status"] == "checksum_mismatch" for row in plan):
        status = "critical"
    return {
        "status": status,
        "command": command,
        "engine": engine,
        "migration_dir": str(migration_dir.relative_to(PROJECT_ROOT)),
        "generated_at": utc_now(),
        "summary": {
            "total": len(plan),
            "pending": sum(1 for row in plan if row["status"] == "pending"),
            "applied": sum(1 for row in plan if row["status"] == "applied"),
            "checksum_mismatch": sum(1 for row in plan if row["status"] == "checksum_mismatch"),
        },
        "migrations": plan,
    }


def print_console_report(report: dict[str, Any]) -> None:
    print(f"DB migrations: {report['status']} ({report['engine']})")
    print(f"Directory: {report['migration_dir']}")
    print("-" * 110)
    print("status              version         statements  name")
    print("-" * 110)
    for row in report["migrations"]:
        print(f"{row['status'][:18]:18} {row['version']:14} {row['statements']:10}  {row['name']}")


def write_output(report: dict[str, Any], output: Path | None) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("validate", "plan", "apply"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--engine", choices=sorted(APPLY_ENGINES | VALIDATE_ONLY_ENGINES), required=True)
        sub.add_argument("--migration-dir", type=Path)
        sub.add_argument("--sqlite-path", type=Path, default=PROJECT_ROOT / "data" / "mighty.db")
        sub.add_argument("--database-url", default=os.environ.get("SUPABASE_DB_URL", "").strip())
        sub.add_argument("--dry-run", action="store_true")
        sub.add_argument("--json", action="store_true")
        sub.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    migration_dir = (args.migration_dir or default_migration_dir(args.engine)).resolve()

    try:
        migrations = load_migrations(migration_dir)
        applied: dict[str, str] = {}

        if args.command in {"plan", "apply"} and args.engine == "supabase":
            raise MigrationError("supabase migrations are validate-only here; use the Supabase CLI to apply them")

        if args.command in {"plan", "apply"}:
            if args.engine == "sqlite":
                if args.command == "apply" and not args.dry_run:
                    conn = connect_sqlite(args.sqlite_path)
                elif args.sqlite_path.exists():
                    conn = connect_sqlite_readonly(args.sqlite_path)
                else:
                    conn = None
            else:
                if not args.database_url:
                    raise MigrationError("SUPABASE_DB_URL or --database-url is required for postgres plan/apply")
                conn = connect_postgres(args.database_url)
            try:
                if conn is None:
                    applied = {}
                elif args.command == "apply" and not args.dry_run:
                    ensure_ledger(conn, args.engine)
                    applied = load_applied(conn)
                elif ledger_exists(conn, args.engine):
                    applied = load_applied(conn)
                else:
                    applied = {}
                plan = build_plan(migrations, applied)
                if any(row["status"] == "checksum_mismatch" for row in plan):
                    raise MigrationError("Applied migration checksum mismatch detected")
                if args.command == "apply" and not args.dry_run:
                    pending_versions = {row["version"] for row in plan if row["status"] == "pending"}
                    for migration in migrations:
                        if migration.version in pending_versions:
                            if conn is None:
                                raise MigrationError("Database connection is required to apply migrations")
                            execute_migration(conn, args.engine, migration)
                    applied = load_applied(conn) if conn is not None else {}
                    plan = build_plan(migrations, applied)
            finally:
                if conn is not None:
                    conn.close()
        else:
            plan = build_plan(migrations)

        report = render_report(args.command, args.engine, migration_dir, plan)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_console_report(report)
        write_output(report, args.output)
        return 0 if report["status"] == "ok" else 2
    except MigrationError as exc:
        print(f"DB migration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
