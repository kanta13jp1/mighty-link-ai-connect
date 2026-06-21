#!/usr/bin/env python3
"""Check Supabase Postgres major versions for the PG14 EOL gate.

The script never writes raw connection strings. Live checks require database
URLs in environment variables; offline checks accept sanitized `version()`
output copied from the Supabase SQL editor.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


TASK_ID = "T828"
RELATED_TASK_ID = "T811"
PG14_EOL_DATE = "2026-07-01"
DEFAULT_REPORT_PATH = Path("exports") / "supabase_postgres_version_check.json"
DEFAULT_MARKDOWN_PATH = Path("exports") / "supabase_postgres_version_check.md"
DEFAULT_TARGETS = (
    "staging=SUPABASE_STAGING_DB_URL",
    "production=SUPABASE_PROD_DB_URL",
)
VERSION_SQL = "select version();"
VERSION_RE = re.compile(r"\bPostgreSQL\s+(\d+)(?:\.(\d+))?\b", re.IGNORECASE)


@dataclass(frozen=True)
class Target:
    name: str
    env_var: str


@dataclass(frozen=True)
class VersionCheck:
    target: str
    source: str
    state: str
    major: int | None
    version_text: str | None
    action: str
    database_url: str | None = None


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_assignment(value: str, *, field_name: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{field_name} must be NAME=VALUE")
    left, right = value.split("=", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise argparse.ArgumentTypeError(f"{field_name} must be NAME=VALUE")
    return left, right


def parse_target(value: str) -> Target:
    name, env_var = parse_assignment(value, field_name="target")
    if not re.fullmatch(r"[A-Z0-9_]+", env_var):
        raise argparse.ArgumentTypeError("target env var must be uppercase snake case")
    return Target(name=name, env_var=env_var)


def redact_db_url(db_url: str) -> str:
    parts = urlsplit(db_url)
    if not parts.scheme or not parts.hostname:
        return "<redacted-db-url>"
    user = parts.username or "user"
    host = parts.hostname
    port = f":{parts.port}" if parts.port else ""
    auth = f"{user}:***@{host}{port}" if parts.password else f"{user}@{host}{port}"
    return urlunsplit((parts.scheme, auth, parts.path, parts.query, parts.fragment))


def extract_postgres_major(version_text: str | None) -> int | None:
    if not version_text:
        return None
    match = VERSION_RE.search(version_text)
    if not match:
        return None
    return int(match.group(1))


def assess_version(major: int | None) -> tuple[str, str]:
    if major is None:
        return (
            "warning",
            "Postgres major version could not be parsed. Re-run `select version();`.",
        )
    if major < 14:
        return (
            "critical",
            f"Postgres {major} is older than the PG14 EOL baseline. Plan an immediate upgrade.",
        )
    if major == 14:
        return (
            "critical",
            f"Postgres 14 must be upgraded before Supabase removes support on {PG14_EOL_DATE}.",
        )
    return (
        "ok",
        f"Postgres {major} is above the PG14 EOL risk threshold. Keep normal upgrade monitoring.",
    )


def check_offline(target: str, version_text: str) -> VersionCheck:
    major = extract_postgres_major(version_text)
    state, action = assess_version(major)
    return VersionCheck(
        target=target,
        source="offline-version",
        state=state,
        major=major,
        version_text=version_text,
        action=action,
    )


def check_missing_env(target: Target) -> VersionCheck:
    return VersionCheck(
        target=target.name,
        source=target.env_var,
        state="missing-env",
        major=None,
        version_text=None,
        action=(
            f"Set {target.env_var} locally or paste sanitized Supabase SQL Editor "
            f"`{VERSION_SQL}` output with --offline-version {target.name}=..."
        ),
    )


def import_psycopg2():
    try:
        import psycopg2  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("psycopg2 is required for --execute") from exc
    return psycopg2


def check_live(target: Target, db_url: str, timeout_seconds: int) -> VersionCheck:
    psycopg2 = import_psycopg2()
    connection = None
    try:
        connection = psycopg2.connect(db_url, connect_timeout=timeout_seconds)
        with connection.cursor() as cursor:
            cursor.execute(VERSION_SQL)
            row = cursor.fetchone()
        version_text = str(row[0]) if row else ""
        major = extract_postgres_major(version_text)
        state, action = assess_version(major)
        return VersionCheck(
            target=target.name,
            source=target.env_var,
            state=state,
            major=major,
            version_text=version_text,
            action=action,
            database_url=redact_db_url(db_url),
        )
    finally:
        if connection is not None:
            connection.close()


def overall_status(checks: list[VersionCheck]) -> str:
    states = {check.state for check in checks}
    if any(state == "critical" for state in states):
        return "critical"
    if checks and all(state == "ok" for state in states):
        return "ok"
    if states <= {"missing-env"}:
        return "needs_credentials"
    return "needs_review"


def build_report(checks: list[VersionCheck], dry_run: bool) -> dict:
    return {
        "task_id": TASK_ID,
        "related_task_id": RELATED_TASK_ID,
        "generated_at_utc": utc_timestamp(),
        "dry_run": dry_run,
        "status": overall_status(checks),
        "pg14_eol_date": PG14_EOL_DATE,
        "version_sql": VERSION_SQL,
        "checks": [asdict(check) for check in checks],
        "pre_upgrade_gate": [
            "Record a fresh Supabase backup or PITR timestamp before changing Postgres major versions.",
            "Run the version check for both staging and production; production must not be upgraded first.",
            "Review extensions before upgrading, especially TimescaleDB, plv8, pg_graphql, pgjwt, and deprecated Postgres 17 extensions.",
            "Check logical replication slots and recreate them after upgrade if used.",
            "Reserve a maintenance window and announce write-impacting downtime before production upgrade.",
            "Run API smoke tests, RLS tests, migration validation, and the public demo guard after staging and production checks.",
        ],
        "secret_policy": (
            "Database URLs and service role keys must stay in local env vars or GitHub Secrets. "
            "Reports contain only redacted URLs and sanitized version strings."
        ),
    }


def write_json(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Supabase Postgres Version Check",
        "",
        f"- Task: {report['task_id']} (related: {report['related_task_id']})",
        f"- Generated: {report['generated_at_utc']}",
        f"- Status: {report['status']}",
        f"- PG14 EOL date: {report['pg14_eol_date']}",
        f"- SQL: `{report['version_sql']}`",
        "",
        "## Results",
        "",
        "| Target | State | Major | Source | Action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for check in report["checks"]:
        major = check["major"] if check["major"] is not None else "-"
        lines.append(
            f"| {check['target']} | {check['state']} | {major} | "
            f"{check['source']} | {check['action']} |"
        )
    lines.extend(["", "## Pre-Upgrade Gate", ""])
    lines.extend(f"- {item}" for item in report["pre_upgrade_gate"])
    lines.extend(["", "## Secret Policy", "", report["secret_policy"], ""])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Supabase Postgres versions for the PG14 EOL gate."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Write a non-connecting plan.")
    mode.add_argument("--execute", action="store_true", help="Connect and run select version().")
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target mapping in NAME=ENV_VAR form. Defaults to staging and production env vars.",
    )
    parser.add_argument(
        "--offline-version",
        action="append",
        default=[],
        help="Sanitized version output in NAME='PostgreSQL ...' form.",
    )
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-path", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--timeout-seconds", type=int, default=10)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    args = parse_args(argv)
    env = env if env is not None else os.environ
    dry_run = not args.execute

    if args.timeout_seconds < 1:
        raise ValueError("timeout-seconds must be >= 1")

    targets = [parse_target(value) for value in (args.target or DEFAULT_TARGETS)]
    offline_versions = dict(
        parse_assignment(value, field_name="offline-version")
        for value in args.offline_version
    )

    checks: list[VersionCheck] = [
        check_offline(target, version_text)
        for target, version_text in sorted(offline_versions.items())
    ]

    offline_target_names = set(offline_versions)
    for target in targets:
        if target.name in offline_target_names:
            continue
        db_url = env.get(target.env_var)
        if not db_url:
            checks.append(check_missing_env(target))
            continue
        if dry_run:
            checks.append(
                VersionCheck(
                    target=target.name,
                    source=target.env_var,
                    state="ready",
                    major=None,
                    version_text=None,
                    database_url=redact_db_url(db_url),
                    action="Run again with --execute to connect and run select version().",
                )
            )
        else:
            checks.append(check_live(target, db_url, args.timeout_seconds))

    report = build_report(checks, dry_run=dry_run)
    write_json(args.report_path, report)
    write_markdown(args.markdown_path, report)
    print(f"[+] Supabase Postgres version check {report['status']}: {args.report_path}")
    if not dry_run and report["status"] in {"critical", "needs_credentials"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
