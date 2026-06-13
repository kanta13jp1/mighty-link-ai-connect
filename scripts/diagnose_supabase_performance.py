#!/usr/bin/env python3
"""Build or run Supabase/Postgres performance diagnostics for T750."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


TASK_ID = "T750"
DEFAULT_REPORT_PATH = Path("exports") / "supabase_performance_report.json"
DEFAULT_SQL_PATH = Path("exports") / "supabase_performance_diagnostic.sql"
DEFAULT_RAW_OUTPUT_PATH = Path("exports") / "supabase_performance_raw.txt"
DEFAULT_TIMEOUT_SECONDS = 45
DRY_RUN_DB_URL = "postgresql://postgres:dry-run@example.invalid:5432/postgres"


@dataclass(frozen=True)
class QueryProbe:
    name: str
    purpose: str
    sql: str


@dataclass(frozen=True)
class ApiProbeResult:
    url: str
    status: str
    elapsed_ms: float | None
    error: str | None = None


SQL_PROBES = (
    QueryProbe(
        name="extension_status",
        purpose="Confirm whether pg_stat_statements, hypopg, and index_advisor are available.",
        sql="""
select extname, extversion
from pg_extension
where extname in ('pg_stat_statements', 'hypopg', 'index_advisor')
order by extname;
""".strip(),
    ),
    QueryProbe(
        name="top_queries_by_total_time",
        purpose="Find high total-time statements that dominate DB work.",
        sql="""
select
  queryid,
  calls,
  round(total_exec_time::numeric, 2) as total_exec_time_ms,
  round(mean_exec_time::numeric, 2) as mean_exec_time_ms,
  rows,
  left(regexp_replace(query, '\\s+', ' ', 'g'), 240) as query_sample
from pg_stat_statements
order by total_exec_time desc
limit 20;
""".strip(),
    ),
    QueryProbe(
        name="top_queries_by_mean_time",
        purpose="Find statements with high per-call latency.",
        sql="""
select
  queryid,
  calls,
  round(mean_exec_time::numeric, 2) as mean_exec_time_ms,
  round(max_exec_time::numeric, 2) as max_exec_time_ms,
  left(regexp_replace(query, '\\s+', ' ', 'g'), 240) as query_sample
from pg_stat_statements
where calls >= 5
order by mean_exec_time desc
limit 20;
""".strip(),
    ),
    QueryProbe(
        name="sequential_scan_pressure",
        purpose="Identify tables where sequential scans dominate indexed scans.",
        sql="""
select
  schemaname,
  relname,
  seq_scan,
  idx_scan,
  n_live_tup,
  n_dead_tup,
  last_analyze,
  last_autoanalyze
from pg_stat_user_tables
where seq_scan > greatest(idx_scan * 2, 50)
order by seq_scan desc
limit 30;
""".strip(),
    ),
    QueryProbe(
        name="unused_indexes",
        purpose="Find non-primary-key indexes with no scans, then review before dropping.",
        sql="""
select
  schemaname,
  relname as table_name,
  indexrelname as index_name,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
from pg_stat_user_indexes
where idx_scan = 0
  and indexrelname not like '%_pkey'
order by pg_relation_size(indexrelid) desc
limit 30;
""".strip(),
    ),
    QueryProbe(
        name="large_indexes",
        purpose="List largest indexes for storage maintenance review.",
        sql="""
select
  schemaname,
  relname as table_name,
  indexrelname as index_name,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
from pg_stat_user_indexes
order by pg_relation_size(indexrelid) desc
limit 30;
""".strip(),
    ),
    QueryProbe(
        name="vacuum_analyze_lag",
        purpose="Find tables that may need vacuum/analyze attention.",
        sql="""
select
  schemaname,
  relname,
  n_live_tup,
  n_dead_tup,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
from pg_stat_user_tables
where n_dead_tup > greatest(n_live_tup * 0.2, 1000)
order by n_dead_tup desc
limit 30;
""".strip(),
    ),
)


MAINTENANCE_GUIDANCE = (
    "Use Supabase Dashboard Query Performance and Index Advisor before adding indexes.",
    "Prefer CREATE INDEX CONCURRENTLY for large production tables to avoid blocking writes.",
    "Do not run CREATE INDEX CONCURRENTLY or REINDEX CONCURRENTLY inside a transaction.",
    "Record every accepted index change as a forward migration before applying it to staging or production.",
    "Review unused indexes for at least two reporting cycles before dropping them.",
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact_db_url(db_url: str) -> str:
    parts = urlsplit(db_url)
    if not parts.scheme or not parts.hostname:
        return "<redacted-db-url>"
    user = parts.username or "user"
    host = parts.hostname
    port = f":{parts.port}" if parts.port else ""
    auth = f"{user}:***@{host}{port}" if parts.password else f"{user}@{host}{port}"
    return urlunsplit((parts.scheme, auth, parts.path, parts.query, parts.fragment))


def redact_command(command: tuple[str, ...] | list[str], db_url: str) -> list[str]:
    redacted = redact_db_url(db_url)
    return [redacted if part == db_url else str(part) for part in command]


def format_command(command: tuple[str, ...] | list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in command])


def build_sql_bundle(probes: tuple[QueryProbe, ...] = SQL_PROBES) -> str:
    chunks = [
        "-- Mighty-Link AI Connect Supabase performance diagnostic bundle",
        f"-- Task: {TASK_ID}",
        "-- Read-only probes. Review generated output before taking maintenance action.",
        "\\pset pager off",
        "\\timing on",
        "",
    ]
    for probe in probes:
        chunks.extend(
            [
                f"\\echo '--- {probe.name}: {probe.purpose}'",
                probe.sql.rstrip(";") + ";",
                "",
            ]
        )
    return "\n".join(chunks)


def assert_child_path(parent: Path, child: Path) -> None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved == parent_resolved or parent_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside project root: {child}")


def resolve_output_path(root: Path, path: Path) -> Path:
    resolved = path if path.is_absolute() else root / path
    assert_child_path(root, resolved)
    return resolved


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def build_psql_command(psql: str, db_url: str, sql_path: Path) -> tuple[str, ...]:
    return (
        psql,
        "--dbname",
        db_url,
        "-X",
        "--set",
        "ON_ERROR_STOP=1",
        "--file",
        str(sql_path),
    )


def run_psql(command: tuple[str, ...], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_seconds,
    )


def measure_api_url(url: str, timeout_seconds: int) -> ApiProbeResult:
    started = time.perf_counter()
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            return ApiProbeResult(
                url=url,
                status=f"HTTP {response.status}",
                elapsed_ms=elapsed_ms,
            )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return ApiProbeResult(
            url=url,
            status="error",
            elapsed_ms=elapsed_ms,
            error=f"{type(exc).__name__}: {exc}",
        )


def build_report(
    *,
    root: Path,
    dry_run: bool,
    status: str,
    db_url: str,
    sql_path: Path,
    raw_output_path: Path,
    psql_command: tuple[str, ...] | None,
    api_results: list[ApiProbeResult],
    notes: list[str] | None = None,
) -> dict:
    return {
        "task_id": TASK_ID,
        "generated_at_utc": utc_timestamp(),
        "status": status,
        "dry_run": dry_run,
        "database_url": redact_db_url(db_url),
        "sql_bundle": display_path(root, sql_path),
        "raw_output": display_path(root, raw_output_path),
        "psql_command": (
            format_command(redact_command(psql_command, db_url)) if psql_command else None
        ),
        "probes": [asdict(probe) for probe in SQL_PROBES],
        "api_results": [asdict(result) for result in api_results],
        "maintenance_guidance": MAINTENANCE_GUIDANCE,
        "notes": notes or [],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare or execute Supabase/Postgres performance diagnostics."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Write the plan only.")
    mode.add_argument("--execute", action="store_true", help="Run psql diagnostics.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--sql-path", type=Path, default=DEFAULT_SQL_PATH)
    parser.add_argument("--raw-output-path", type=Path, default=DEFAULT_RAW_OUTPUT_PATH)
    parser.add_argument("--psql", default="psql")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--api-url",
        action="append",
        default=[],
        help="Optional health or API endpoint to time. Repeat for multiple URLs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    args = parse_args(argv)
    env = env if env is not None else os.environ
    root = args.root.resolve()
    sql_path = resolve_output_path(root, args.sql_path)
    report_path = resolve_output_path(root, args.report_path)
    raw_output_path = resolve_output_path(root, args.raw_output_path)
    dry_run = not args.execute

    if args.timeout_seconds < 1:
        raise ValueError("timeout-seconds must be >= 1")

    db_url = env.get("SUPABASE_DB_URL") or DRY_RUN_DB_URL
    write_text(sql_path, build_sql_bundle())

    api_results = (
        [measure_api_url(url, args.timeout_seconds) for url in args.api_url]
        if args.execute
        else []
    )

    if dry_run:
        report = build_report(
            root=root,
            dry_run=True,
            status="planned",
            db_url=db_url,
            sql_path=sql_path,
            raw_output_path=raw_output_path,
            psql_command=None,
            api_results=api_results,
            notes=["Use --execute with SUPABASE_DB_URL to run live diagnostics."],
        )
        write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(f"[+] T750 diagnostic plan written: {report_path}")
        print(f"[*] SQL bundle: {sql_path}")
        return 0

    if "SUPABASE_DB_URL" not in env:
        print("[-] SUPABASE_DB_URL is required when using --execute.", file=sys.stderr)
        return 2

    command = build_psql_command(args.psql, db_url, sql_path)
    result = run_psql(command, args.timeout_seconds)
    raw_text = result.stdout
    if result.stderr:
        raw_text += "\n--- STDERR ---\n" + result.stderr
    write_text(raw_output_path, raw_text)

    status = "completed" if result.returncode == 0 else f"failed:{result.returncode}"
    report = build_report(
        root=root,
        dry_run=False,
        status=status,
        db_url=db_url,
        sql_path=sql_path,
        raw_output_path=raw_output_path,
        psql_command=command,
        api_results=api_results,
    )
    write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"[+] T750 diagnostic {status}. Report: {report_path}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
