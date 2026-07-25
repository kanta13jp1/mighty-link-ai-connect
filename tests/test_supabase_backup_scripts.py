import json
import hashlib
import subprocess
import sys
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import backup_supabase_database as backup
import restore_supabase_database as restore


SECRET_DB_URL = "postgresql://postgres:very-secret@db.example.com:5432/postgres"


def test_supabase_cli_major_matches_production_database():
    config = tomllib.loads(
        (PROJECT_ROOT / "supabase" / "config.toml").read_text(encoding="utf-8")
    )

    assert config["db"]["major_version"] == 17


def test_redact_db_url_masks_password():
    redacted = backup.redact_db_url(SECRET_DB_URL)

    assert "very-secret" not in redacted
    assert redacted == "postgresql://postgres:***@db.example.com:5432/postgres"


def test_backup_command_failure_does_not_expose_db_url(monkeypatch):
    command = ("supabase", "db", "dump", "--db-url", SECRET_DB_URL)

    def fail(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(backup.subprocess, "run", fail)

    try:
        backup.run_command(command, dry_run=False, db_url=SECRET_DB_URL)
    except RuntimeError as exc:
        message = str(exc)
        assert "very-secret" not in message
        assert SECRET_DB_URL not in message
        assert "exit code 1" in message
    else:
        raise AssertionError("backup command failure was not raised")


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


def test_gcs_upload_uses_gcloud_storage():
    command = backup.build_gcs_command(
        Path("backups/supabase/20260613T180000Z"),
        "gs://private-bucket/supabase",
    )

    assert command[:4] == ("gcloud", "storage", "cp", "--recursive")
    assert command[-1] == "gs://private-bucket/supabase/"


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


def test_restore_rejects_checksum_mismatch(tmp_path):
    snapshot_dir = tmp_path / "20260613T180000Z"
    snapshot_dir.mkdir()
    checksums = {}
    for name in restore.REQUIRED_FILES:
        content = f"-- {name}\n".encode()
        (snapshot_dir / name).write_bytes(content)
        checksums[name] = hashlib.sha256(content).hexdigest()
    (snapshot_dir / "manifest.json").write_text(
        json.dumps({"checksums_sha256": checksums}),
        encoding="utf-8",
    )
    (snapshot_dir / "data.sql").write_text("-- tampered\n", encoding="utf-8")

    try:
        restore.main(
            [str(snapshot_dir), "--dry-run"],
            env={"SUPABASE_RESTORE_DB_URL": SECRET_DB_URL},
        )
    except ValueError as exc:
        assert "Checksum mismatch" in str(exc)
    else:
        raise AssertionError("restore accepted a tampered backup")
