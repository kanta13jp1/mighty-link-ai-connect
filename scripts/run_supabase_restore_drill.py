#!/usr/bin/env python3
"""Run a Supabase restore drill without touching production data.

This implements WBS T771 by validating the restore path, runbooks, workflow
contract, and redacted restore command. Real restores still require the
human-gated ``restore_supabase_database.py --confirm-restore`` path.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from backup_supabase_database import format_command, redact_command
from restore_supabase_database import (
    DRY_RUN_DB_URL,
    REQUIRED_FILES,
    build_restore_command,
    validate_snapshot_dir,
)


TASK_ID = "T771"
DEFAULT_JSON = Path("exports") / "supabase_restore_drill_2026-07-01.json"
DEFAULT_MD = Path("exports") / "supabase_restore_drill_2026-07-01.md"
SECRET_TERMS = ("password", "secret", "token", "apikey", "api_key")


@dataclass(frozen=True)
class DrillCheck:
    name: str
    status: str
    detail: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def display_path(path: Path, root: Path | None = None) -> str:
    base = (root or Path.cwd()).resolve()
    try:
        return path.resolve().relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def create_synthetic_snapshot(base_dir: Path, timestamp: str) -> Path:
    snapshot_dir = base_dir / timestamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "roles.sql": "-- T771 restore drill synthetic roles file; no production data.\n",
        "schema.sql": "-- T771 restore drill synthetic schema file; no production data.\n",
        "data.sql": "-- T771 restore drill synthetic data file; no production data.\n",
    }
    for name, content in files.items():
        (snapshot_dir / name).write_text(content, encoding="utf-8")
    return snapshot_dir


def check_contains(path: Path, required: tuple[str, ...], root: Path | None = None) -> DrillCheck:
    content = read_text(path)
    missing = [needle for needle in required if needle not in content]
    status = "pass" if not missing else "fail"
    detail = "all required markers present" if not missing else "missing: " + ", ".join(missing)
    return DrillCheck(name=display_path(path, root), status=status, detail=detail)


def check_restore_command(snapshot_dir: Path, db_url: str) -> tuple[DrillCheck, str]:
    validate_snapshot_dir(snapshot_dir)
    command = build_restore_command(snapshot_dir, db_url)
    redacted = format_command(redact_command(command, db_url))
    required = ("--single-transaction", "ON_ERROR_STOP=1", "session_replication_role", "***")
    missing = [needle for needle in required if needle not in redacted]
    leaked = db_url in redacted
    status = "pass" if not missing and not leaked else "fail"
    detail = "restore command is single-transaction and redacted"
    if missing:
        detail = "missing command markers: " + ", ".join(missing)
    if leaked:
        detail = "database URL was not redacted"
    return DrillCheck(name="restore_dry_run_command", status=status, detail=detail), redacted


def check_no_secret_values(payload: dict) -> DrillCheck:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    findings = [term for term in SECRET_TERMS if term in serialized and "***" not in serialized]
    status = "pass" if not findings else "fail"
    detail = "no unredacted secret markers in report" if not findings else "review terms: " + ", ".join(findings)
    return DrillCheck(name="secret_redaction", status=status, detail=detail)


def build_report(
    *,
    root: Path,
    snapshot_dir: Path,
    restore_command: str,
    checks: list[DrillCheck],
    source: str,
) -> dict:
    snapshot_path = str(snapshot_dir.resolve())
    if source == "synthetic_snapshot":
        snapshot_path = f"<synthetic_snapshot>/{snapshot_dir.name}"
        restore_command = restore_command.replace(str(snapshot_dir), snapshot_path)

    report = {
        "task_id": TASK_ID,
        "generated_at_utc": utc_now().isoformat(),
        "status": "pass" if all(check.status == "pass" for check in checks) else "fail",
        "source": source,
        "snapshot": {
            "path": snapshot_path,
            "required_files": list(REQUIRED_FILES),
            "production_data_included": False,
        },
        "restore_dry_run": {
            "command": restore_command,
            "real_restore_performed": False,
            "real_restore_gate": "Use scripts/restore_supabase_database.py --confirm-restore only after human Go/No-Go.",
        },
        "rpo_rto": {
            "rpo_target": "24h",
            "rto_target": "2h for P1",
            "validated_against": [
                "docs/SUPABASE_BACKUP_RESTORE_RUNBOOK.md",
                "docs/DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md",
                "docs/PRODUCTION_ROLLBACK_RUNBOOK.md",
            ],
        },
        "checks": [asdict(check) for check in checks],
        "next_real_drill": [
            "Create a new Supabase project under the company account.",
            "Restore a non-production snapshot into that project.",
            "Run RLS/API/public-demo checks before any production restore decision.",
            "Record PITR target, owner, approval, and post-restore verification in GitHub/Sheets.",
        ],
    }
    report["checks"].append(asdict(check_no_secret_values(report)))
    report["status"] = "pass" if all(check["status"] == "pass" for check in report["checks"]) else "fail"
    return report


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Supabase リストア訓練レポート (T771)\n\n",
        f"- 生成日時(UTC): {report['generated_at_utc']}\n",
        f"- 判定: `{report['status']}`\n",
        f"- 実DB復元: {report['restore_dry_run']['real_restore_performed']}\n",
        f"- RPO目標: {report['rpo_rto']['rpo_target']}\n",
        f"- RTO目標: {report['rpo_rto']['rto_target']}\n\n",
        "## 復元dry-run\n\n",
        "```powershell\n",
        report["restore_dry_run"]["command"],
        "\n```\n\n",
        "## チェック結果\n\n",
        "| チェック | 状態 | 詳細 |\n",
        "| --- | --- | --- |\n",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {check['detail']} |\n")
    lines.extend(
        [
            "\n## 次の実機訓練\n\n",
            "- 会社アカウント配下に新規Supabase projectを作る。\n",
            "- productionへ直接戻す前に、非本番snapshotを新規projectへ復元する。\n",
            "- RLS/API/public demo guardを通し、PITR時刻、承認者、復元担当者を記録する。\n",
            "- secret、DB URL、OAuth token、個人データ実値はGitHub/Sheets/docs/NotebookLMへ記録しない。\n",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the T771 Supabase restore drill.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--timestamp", default="20260701T000000Z")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    args = parse_args(argv)
    env = env if env is not None else os.environ
    root = args.root.resolve()
    json_output = args.json_output if args.json_output.is_absolute() else root / args.json_output
    md_output = args.md_output if args.md_output.is_absolute() else root / args.md_output
    db_url = env.get("SUPABASE_RESTORE_DB_URL") or env.get("SUPABASE_DB_URL") or DRY_RUN_DB_URL

    with tempfile.TemporaryDirectory(prefix="t771-restore-drill-") as temp_dir:
        snapshot_dir = args.snapshot_dir or create_synthetic_snapshot(Path(temp_dir), args.timestamp)
        snapshot_dir = snapshot_dir.resolve()
        command_check, restore_command = check_restore_command(snapshot_dir, db_url)
        checks = [
            command_check,
            check_contains(
                root / "docs" / "SUPABASE_BACKUP_RESTORE_RUNBOOK.md",
                ("RPO", "RTO", "restore_supabase_database.py", "PITR"),
                root=root,
            ),
            check_contains(
                root / "docs" / "DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md",
                ("RPO", "RTO", "バックアップからのリストア実機訓練"),
                root=root,
            ),
            check_contains(
                root / "docs" / "PRODUCTION_ROLLBACK_RUNBOOK.md",
                ("backup/PITR", "Supabase migration version", "verify_public_demo.py"),
                root=root,
            ),
            check_contains(
                root / ".github" / "workflows" / "supabase-backup.yml",
                ("schedule:", "workflow_dispatch:", "SUPABASE_DB_URL", "SUPABASE_BACKUP_GCS_URI"),
                root=root,
            ),
        ]
        report = build_report(
            root=root,
            snapshot_dir=snapshot_dir,
            restore_command=restore_command,
            checks=checks,
            source="synthetic_snapshot" if args.snapshot_dir is None else "provided_snapshot",
        )
        write_json(json_output, report)
        write_markdown(md_output, report)

    print(f"[+] T771 restore drill {report['status']}: {json_output}")
    print(f"[*] Markdown: {md_output}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
