import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_supabase_postgres_version as pgcheck


SECRET_DB_URL = "postgresql://postgres:very-secret@db.example.com:5432/postgres"


def test_extract_postgres_major_from_version_string():
    text = "PostgreSQL 15.1 on aarch64-unknown-linux-gnu, compiled by gcc"

    assert pgcheck.extract_postgres_major(text) == 15


def test_assess_version_marks_pg14_critical():
    state, action = pgcheck.assess_version(14)

    assert state == "critical"
    assert "2026-07-01" in action


def test_offline_versions_write_report_without_secrets(tmp_path):
    report_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    exit_code = pgcheck.main(
        [
            "--dry-run",
            "--offline-version",
            "staging=PostgreSQL 15.1 on aarch64-unknown-linux-gnu",
            "--offline-version",
            "production=PostgreSQL 14.12 on x86_64-pc-linux-gnu",
            "--report-path",
            str(report_path),
            "--markdown-path",
            str(markdown_path),
        ],
        env={},
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["status"] == "critical"
    assert {check["target"]: check["major"] for check in report["checks"]} == {
        "production": 14,
        "staging": 15,
    }
    assert "very-secret" not in report_path.read_text(encoding="utf-8")
    assert "Pre-Upgrade Gate" in markdown_path.read_text(encoding="utf-8")


def test_dry_run_redacts_ready_target_url(tmp_path):
    report_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    exit_code = pgcheck.main(
        [
            "--dry-run",
            "--target",
            "production=SUPABASE_PROD_DB_URL",
            "--report-path",
            str(report_path),
            "--markdown-path",
            str(markdown_path),
        ],
        env={"SUPABASE_PROD_DB_URL": SECRET_DB_URL},
    )

    text = report_path.read_text(encoding="utf-8")
    report = json.loads(text)

    assert exit_code == 0
    assert report["status"] == "needs_review"
    assert "very-secret" not in text
    assert "postgres:***@db.example.com:5432/postgres" in text


def test_missing_env_targets_are_reported(tmp_path):
    report_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    exit_code = pgcheck.main(
        [
            "--dry-run",
            "--report-path",
            str(report_path),
            "--markdown-path",
            str(markdown_path),
        ],
        env={},
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["status"] == "needs_credentials"
    assert [check["state"] for check in report["checks"]] == ["missing-env", "missing-env"]
