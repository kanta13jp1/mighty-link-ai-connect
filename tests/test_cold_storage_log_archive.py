import json
import sys
import zipfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import archive_audit_logs_to_cold_storage as cold_archive


def test_collect_sources_excludes_secret_files(tmp_path):
    audit_dir = tmp_path / "data" / "audit"
    audit_dir.mkdir(parents=True)
    allowed = audit_dir / "app.jsonl"
    secret = audit_dir / "authorized_user.json"
    allowed.write_text('{"event": "ok"}\n', encoding="utf-8")
    secret.write_text('{"refresh_token": "do-not-store"}\n', encoding="utf-8")

    sources, excluded, warnings = cold_archive.collect_sources(
        root=tmp_path,
        patterns=("data/audit/*",),
    )

    assert [path.name for path in sources] == ["app.jsonl"]
    assert excluded[0].path == "data/audit/authorized_user.json"
    assert excluded[0].reason == "secret filename is never archived"
    assert warnings == []


def test_manifest_and_zip_are_created_with_hashes(tmp_path):
    audit_dir = tmp_path / "data" / "audit"
    audit_dir.mkdir(parents=True)
    log_file = audit_dir / "audit.jsonl"
    log_file.write_text('{"event": "login", "actor": "user-1"}\n', encoding="utf-8")
    security_log = tmp_path / "data" / "security_log.tsv"
    security_log.write_text("date\tresult\n2026-07-01\tPASS\n", encoding="utf-8")

    exit_code = cold_archive.main(
        [
            "--root",
            str(tmp_path),
            "--output-dir",
            "exports/cold_storage",
            "--archive-date",
            "2026-07-01",
            "--pattern",
            "data/audit/*.jsonl",
            "--pattern",
            "data/security_log.tsv",
        ]
    )

    manifest_path = tmp_path / "exports" / "cold_storage" / "cold_storage_manifest_2026-07-01.json"
    archive_path = tmp_path / "exports" / "cold_storage" / "mighty-link-log-archive-2026-07-01.zip"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert manifest["task_id"] == "T773"
    assert len(manifest["sources"]) == 2
    assert all(len(source["sha256"]) == 64 for source in manifest["sources"])
    assert archive_path.exists()
    with zipfile.ZipFile(archive_path) as zf:
        names = set(zf.namelist())
    assert "manifest.json" in names
    assert "data/audit/audit.jsonl" in names
    assert "data/security_log.tsv" in names


def test_manifest_only_skips_zip_but_writes_lifecycle_template(tmp_path):
    log_dir = tmp_path / "data" / "audit"
    log_dir.mkdir(parents=True)
    (log_dir / "audit.jsonl").write_text('{"event": "ok"}\n', encoding="utf-8")

    cold_archive.main(
        [
            "--root",
            str(tmp_path),
            "--output-dir",
            "exports/cold_storage",
            "--archive-date",
            "2026-07-01",
            "--manifest-only",
            "--pattern",
            "data/audit/*.jsonl",
        ]
    )

    output_dir = tmp_path / "exports" / "cold_storage"
    assert (output_dir / "cold_storage_manifest_2026-07-01.json").exists()
    assert (output_dir / "gcs_lifecycle_policy_template.json").exists()
    assert not (output_dir / "mighty-link-log-archive-2026-07-01.zip").exists()


def test_gcs_uri_requires_gs_scheme(tmp_path):
    with pytest.raises(ValueError, match="gcs-uri must start with gs://"):
        cold_archive.main(
            [
                "--root",
                str(tmp_path),
                "--gcs-uri",
                "https://storage.googleapis.com/example",
            ]
        )


def test_t773_runbook_is_linked_from_rotation_runbook():
    runbook = (PROJECT_ROOT / "docs" / "COLD_STORAGE_LOG_ARCHIVE_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    rotation = (PROJECT_ROOT / "docs" / "LOG_ROTATION_AND_RETENTION_RUNBOOK.md").read_text(
        encoding="utf-8"
    )

    assert "T773" in runbook
    assert "scripts/archive_audit_logs_to_cold_storage.py" in runbook
    assert "gcs_lifecycle_policy_template.json" in runbook
    assert "COLD_STORAGE_LOG_ARCHIVE_RUNBOOK.md" in rotation
