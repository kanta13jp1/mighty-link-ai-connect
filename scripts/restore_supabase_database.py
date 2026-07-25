#!/usr/bin/env python3
"""Restore a Supabase PostgreSQL logical backup snapshot for T741."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from backup_supabase_database import format_command, redact_command, redact_db_url


TASK_ID = "T741"
REQUIRED_FILES = ("roles.sql", "schema.sql", "data.sql")
DRY_RUN_DB_URL = "postgresql://postgres:dry-run@example.invalid:5432/postgres"


def validate_snapshot_dir(snapshot_dir: Path) -> list[Path]:
    missing = [snapshot_dir / name for name in REQUIRED_FILES if not (snapshot_dir / name).exists()]
    if missing:
        missing_list = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing required restore files: {missing_list}")
    return [snapshot_dir / name for name in REQUIRED_FILES]


def verify_snapshot_checksums(snapshot_dir: Path) -> None:
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checksums = manifest.get("checksums_sha256")
    if not checksums:
        return

    missing = sorted(set(REQUIRED_FILES) - set(checksums))
    if missing:
        raise ValueError(f"Manifest is missing checksums for: {', '.join(missing)}")

    for name in REQUIRED_FILES:
        digest = hashlib.sha256((snapshot_dir / name).read_bytes()).hexdigest()
        if digest != checksums[name]:
            raise ValueError(f"Checksum mismatch for backup file: {name}")


def build_restore_command(
    snapshot_dir: Path,
    db_url: str,
    psql_bin: str = "psql",
) -> tuple[str, ...]:
    return (
        psql_bin,
        "--single-transaction",
        "--variable",
        "ON_ERROR_STOP=1",
        "--file",
        str(snapshot_dir / "roles.sql"),
        "--file",
        str(snapshot_dir / "schema.sql"),
        "--command",
        "SET session_replication_role = replica",
        "--file",
        str(snapshot_dir / "data.sql"),
        "--dbname",
        db_url,
    )


def write_restore_manifest(snapshot_dir: Path, db_url: str, command: tuple[str, ...]) -> None:
    manifest = {
        "task_id": TASK_ID,
        "restored_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot_dir.name,
        "database_url": redact_db_url(db_url),
        "command": format_command(redact_command(command, db_url)),
        "status": "restored",
    }
    (snapshot_dir / "restore_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restore a Supabase database backup snapshot."
    )
    parser.add_argument("snapshot_dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Print the restore command only.")
    parser.add_argument(
        "--confirm-restore",
        action="store_true",
        help="Required for real restore execution.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    args = parse_args(argv)
    env = env if env is not None else os.environ
    snapshot_dir = args.snapshot_dir

    validate_snapshot_dir(snapshot_dir)
    verify_snapshot_checksums(snapshot_dir)

    db_url = env.get("SUPABASE_RESTORE_DB_URL") or env.get("SUPABASE_DB_URL")
    if not db_url:
        if args.dry_run:
            db_url = DRY_RUN_DB_URL
        else:
            print("[-] SUPABASE_RESTORE_DB_URL or SUPABASE_DB_URL is required.", file=sys.stderr)
            return 2

    if not args.dry_run and not args.confirm_restore:
        print("[-] Refusing real restore without --confirm-restore.", file=sys.stderr)
        return 3

    psql_bin = env.get("PSQL_BIN", "psql")
    command = build_restore_command(snapshot_dir, db_url, psql_bin=psql_bin)
    print(f"[*] {format_command(redact_command(command, db_url))}")
    if args.dry_run:
        return 0

    subprocess.run(command, check=True)
    write_restore_manifest(snapshot_dir, db_url, command)
    print(f"[+] Restore completed from snapshot: {snapshot_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
