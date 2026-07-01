import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import run_supabase_restore_drill as drill


SECRET_DB_URL = "postgresql://postgres:very-secret@db.example.com:5432/postgres"


def test_restore_drill_generates_redacted_pass_report(tmp_path):
    json_output = tmp_path / "restore_drill.json"
    md_output = tmp_path / "restore_drill.md"

    exit_code = drill.main(
        [
            "--root",
            str(PROJECT_ROOT),
            "--json-output",
            str(json_output),
            "--md-output",
            str(md_output),
        ],
        env={"SUPABASE_RESTORE_DB_URL": SECRET_DB_URL},
    )
    report = json.loads(json_output.read_text(encoding="utf-8"))
    markdown = md_output.read_text(encoding="utf-8")

    assert exit_code == 0
    assert report["task_id"] == "T771"
    assert report["status"] == "pass"
    assert report["restore_dry_run"]["real_restore_performed"] is False
    assert "--single-transaction" in report["restore_dry_run"]["command"]
    assert "ON_ERROR_STOP=1" in report["restore_dry_run"]["command"]
    assert "very-secret" not in json_output.read_text(encoding="utf-8")
    assert "very-secret" not in markdown


def test_restore_drill_accepts_existing_snapshot_dir(tmp_path):
    snapshot_dir = tmp_path / "20260701T000000Z"
    snapshot_dir.mkdir()
    for name in ("roles.sql", "schema.sql", "data.sql"):
        (snapshot_dir / name).write_text("-- drill\n", encoding="utf-8")

    exit_code = drill.main(
        [
            "--root",
            str(PROJECT_ROOT),
            "--snapshot-dir",
            str(snapshot_dir),
            "--json-output",
            str(tmp_path / "report.json"),
            "--md-output",
            str(tmp_path / "report.md"),
        ],
        env={},
    )

    assert exit_code == 0


def test_restore_drill_checks_current_runbook_contracts():
    report = drill.build_report(
        root=PROJECT_ROOT,
        snapshot_dir=PROJECT_ROOT,
        restore_command="psql --single-transaction --variable ON_ERROR_STOP=1 ***",
        source="unit",
        checks=[
            drill.check_contains(
                PROJECT_ROOT / "docs" / "SUPABASE_BACKUP_RESTORE_RUNBOOK.md",
                ("RPO", "RTO", "restore_supabase_database.py", "PITR"),
            ),
            drill.check_contains(
                PROJECT_ROOT / ".github" / "workflows" / "supabase-backup.yml",
                ("schedule:", "workflow_dispatch:", "SUPABASE_DB_URL", "SUPABASE_BACKUP_GCS_URI"),
            ),
        ],
    )

    assert report["status"] == "pass"
    assert all(check["status"] == "pass" for check in report["checks"])
