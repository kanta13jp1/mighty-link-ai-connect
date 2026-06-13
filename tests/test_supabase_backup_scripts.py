import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import backup_supabase_database as backup
import restore_supabase_database as restore


SECRET_DB_URL = "postgresql://postgres:very-secret@db.example.com:5432/postgres"


def test_redact_db_url_masks_password():
    redacted = backup.redact_db_url(SECRET_DB_URL)

    assert "very-secret" not in redacted
    assert redacted == "postgresql://postgres:***@db.example.com:5432/postgres"


def test_backup_dry_run_writes_redacted_manifest(tmp_path):
    env = {
        "SUPABASE_DB_URL": SECRET_DB_URL,
        "SUPABASE_BACKUP_DIR": str(tmp_path),
        "SUPABASE_BACKUP_RETENTION": "7",
    }

    exit_code = backup.main(
        ["--dry-run", "--skip-upload", "--timestamp", "20260613T180000Z"],
        env=env,
    )

    manifest_path = tmp_path / "20260613T180000Z" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert manifest["status"] == "dry-run"
    assert manifest["files"] == ["roles.sql", "schema.sql", "data.sql"]
    assert "very-secret" not in manifest_path.read_text(encoding="utf-8")
    assert any("--role-only" in command for command in manifest["commands"])
    assert any("--data-only" in command for command in manifest["commands"])


def test_prune_old_snapshots_keeps_retention_and_ignores_other_dirs(tmp_path):
    for name in (
        "20260610T180000Z",
        "20260611T180000Z",
        "20260612T180000Z",
        "20260613T180000Z",
        "notes",
    ):
        (tmp_path / name).mkdir()

    pruned = backup.prune_old_snapshots(tmp_path, retention=2)

    assert [path.name for path in pruned] == ["20260610T180000Z", "20260611T180000Z"]
    assert not (tmp_path / "20260610T180000Z").exists()
    assert not (tmp_path / "20260611T180000Z").exists()
    assert (tmp_path / "20260612T180000Z").exists()
    assert (tmp_path / "20260613T180000Z").exists()
    assert (tmp_path / "notes").exists()


def test_restore_dry_run_prints_safe_psql_command(tmp_path, capsys):
    snapshot_dir = tmp_path / "20260613T180000Z"
    snapshot_dir.mkdir()
    for name in restore.REQUIRED_FILES:
        (snapshot_dir / name).write_text("-- test\n", encoding="utf-8")

    exit_code = restore.main([str(snapshot_dir), "--dry-run"], env={"SUPABASE_RESTORE_DB_URL": SECRET_DB_URL})
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "--single-transaction" in output
    assert "ON_ERROR_STOP=1" in output
    assert "session_replication_role" in output
    assert "very-secret" not in output
