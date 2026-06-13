#!/usr/bin/env python3
"""Create a Supabase PostgreSQL logical backup for T741.

The script intentionally covers the Supabase database only. Supabase Storage
objects and generated media need their own backup path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


TASK_ID = "T741"
SNAPSHOT_RE = re.compile(r"^\d{8}T\d{6}Z$")
DEFAULT_BACKUP_DIR = Path("backups") / "supabase"
DEFAULT_RETENTION = 7
DEFAULT_EXCLUDED_TABLES = ("storage.buckets_vectors", "storage.vector_indexes")
DRY_RUN_DB_URL = "postgresql://postgres:dry-run@example.invalid:5432/postgres"


@dataclass(frozen=True)
class BackupPlan:
    snapshot_dir: Path
    files: tuple[str, ...]
    commands: tuple[tuple[str, ...], ...]


def utc_timestamp(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_timestamp(value: str) -> str:
    if not SNAPSHOT_RE.match(value):
        raise argparse.ArgumentTypeError("timestamp must match YYYYMMDDTHHMMSSZ")
    return value


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
    return [redacted if part == db_url else part for part in command]


def format_command(command: tuple[str, ...] | list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in command])


def build_dump_commands(
    db_url: str,
    snapshot_dir: Path,
    supabase_cli: str = "supabase",
    excluded_tables: tuple[str, ...] = DEFAULT_EXCLUDED_TABLES,
) -> tuple[tuple[str, ...], ...]:
    roles = (
        supabase_cli,
        "db",
        "dump",
        "--db-url",
        db_url,
        "-f",
        str(snapshot_dir / "roles.sql"),
        "--role-only",
    )
    schema = (
        supabase_cli,
        "db",
        "dump",
        "--db-url",
        db_url,
        "-f",
        str(snapshot_dir / "schema.sql"),
    )
    data = [
        supabase_cli,
        "db",
        "dump",
        "--db-url",
        db_url,
        "-f",
        str(snapshot_dir / "data.sql"),
        "--use-copy",
        "--data-only",
    ]
    for table in excluded_tables:
        data.extend(["-x", table])
    return (roles, schema, tuple(data))


def build_plan(
    backup_dir: Path,
    db_url: str,
    timestamp: str | None = None,
    supabase_cli: str = "supabase",
) -> BackupPlan:
    snapshot_name = timestamp or utc_timestamp()
    snapshot_dir = backup_dir / snapshot_name
    return BackupPlan(
        snapshot_dir=snapshot_dir,
        files=("roles.sql", "schema.sql", "data.sql"),
        commands=build_dump_commands(db_url, snapshot_dir, supabase_cli=supabase_cli),
    )


def safe_snapshot_dirs(backup_dir: Path) -> list[Path]:
    if not backup_dir.exists():
        return []
    return sorted(
        path
        for path in backup_dir.iterdir()
        if path.is_dir() and SNAPSHOT_RE.match(path.name)
    )


def assert_child_path(parent: Path, child: Path) -> None:
    parent_resolved = parent.resolve()
    child_resolved = child.resolve()
    if child_resolved == parent_resolved or parent_resolved not in child_resolved.parents:
        raise ValueError(f"Refusing to operate outside backup dir: {child}")


def prune_old_snapshots(backup_dir: Path, retention: int, dry_run: bool = False) -> list[Path]:
    if retention < 1:
        raise ValueError("retention must be >= 1")
    snapshots = safe_snapshot_dirs(backup_dir)
    stale = snapshots[:-retention]
    for snapshot in stale:
        assert_child_path(backup_dir, snapshot)
        if not dry_run:
            shutil.rmtree(snapshot)
    return stale


def run_command(command: tuple[str, ...], dry_run: bool, db_url: str) -> None:
    print(f"[*] {format_command(redact_command(command, db_url))}")
    if dry_run:
        return
    subprocess.run(command, check=True)


def build_gcs_command(snapshot_dir: Path, gcs_uri: str, gsutil: str = "gsutil") -> tuple[str, ...]:
    destination = gcs_uri.rstrip("/") + "/"
    return (gsutil, "-m", "cp", "-r", str(snapshot_dir), destination)


def write_manifest(snapshot_dir: Path, manifest: dict) -> None:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_manifest(
    plan: BackupPlan,
    db_url: str,
    retention: int,
    dry_run: bool,
    gcs_uri: str | None,
    upload_command: tuple[str, ...] | None,
    pruned: list[Path] | None = None,
    status: str | None = None,
) -> dict:
    return {
        "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": plan.snapshot_dir.name,
        "status": status or ("dry-run" if dry_run else "created"),
        "database_url": redact_db_url(db_url),
        "retention_generations": retention,
        "scope": "Supabase PostgreSQL logical dump only. Supabase Storage objects are out of scope.",
        "files": list(plan.files),
        "commands": [
            format_command(redact_command(command, db_url)) for command in plan.commands
        ],
        "gcs_uri": gcs_uri,
        "upload_command": format_command(upload_command) if upload_command else None,
        "pruned_snapshots": [path.name for path in pruned or []],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Supabase database backup snapshot."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Backup root directory. Defaults to SUPABASE_BACKUP_DIR or backups/supabase.",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=None,
        help="Local snapshot generations to keep. Defaults to SUPABASE_BACKUP_RETENTION or 7.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan without running external commands.")
    parser.add_argument("--skip-upload", action="store_true", help="Do not upload to GCS.")
    parser.add_argument("--timestamp", type=parse_timestamp, default=None, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    args = parse_args(argv)
    env = env if env is not None else os.environ

    db_url = env.get("SUPABASE_DB_URL")
    if not db_url:
        if args.dry_run:
            db_url = DRY_RUN_DB_URL
        else:
            print("[-] SUPABASE_DB_URL is required for a real backup.", file=sys.stderr)
            return 2

    backup_dir = args.output_dir or Path(env.get("SUPABASE_BACKUP_DIR", DEFAULT_BACKUP_DIR))
    retention = args.retention or int(env.get("SUPABASE_BACKUP_RETENTION", DEFAULT_RETENTION))
    supabase_cli = env.get("SUPABASE_CLI", "supabase")
    gsutil = env.get("GSUTIL", "gsutil")
    gcs_uri = None if args.skip_upload else env.get("SUPABASE_BACKUP_GCS_URI")

    plan = build_plan(backup_dir, db_url, timestamp=args.timestamp, supabase_cli=supabase_cli)
    upload_command = build_gcs_command(plan.snapshot_dir, gcs_uri, gsutil) if gcs_uri else None
    manifest = build_manifest(
        plan=plan,
        db_url=db_url,
        retention=retention,
        dry_run=args.dry_run,
        gcs_uri=gcs_uri,
        upload_command=upload_command,
        status="planned" if args.dry_run else "started",
    )

    write_manifest(plan.snapshot_dir, manifest)
    try:
        for command in plan.commands:
            run_command(command, args.dry_run, db_url)

        if upload_command:
            print(f"[*] {format_command(upload_command)}")
            if not args.dry_run:
                subprocess.run(upload_command, check=True)
        elif not args.skip_upload:
            print("[!] SUPABASE_BACKUP_GCS_URI is not set; keeping local backup only.")

        pruned = prune_old_snapshots(backup_dir, retention=retention, dry_run=args.dry_run)
        final_manifest = build_manifest(
            plan=plan,
            db_url=db_url,
            retention=retention,
            dry_run=args.dry_run,
            gcs_uri=gcs_uri,
            upload_command=upload_command,
            pruned=pruned,
        )
        write_manifest(plan.snapshot_dir, final_manifest)
    except Exception as exc:
        failed_manifest = build_manifest(
            plan=plan,
            db_url=db_url,
            retention=retention,
            dry_run=args.dry_run,
            gcs_uri=gcs_uri,
            upload_command=upload_command,
            status=f"failed: {type(exc).__name__}",
        )
        write_manifest(plan.snapshot_dir, failed_manifest)
        raise

    print(f"[+] Backup snapshot prepared: {plan.snapshot_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
