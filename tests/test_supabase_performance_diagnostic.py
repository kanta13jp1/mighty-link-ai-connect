import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import diagnose_supabase_performance as perf


SECRET_DB_URL = "postgresql://postgres:very-secret@db.example.com:5432/postgres"


def test_redact_db_url_masks_password():
    assert perf.redact_db_url(SECRET_DB_URL) == (
        "postgresql://postgres:***@db.example.com:5432/postgres"
    )


def test_build_sql_bundle_contains_read_only_performance_probes():
    bundle = perf.build_sql_bundle()

    assert "pg_stat_statements" in bundle
    assert "pg_stat_user_indexes" in bundle
    assert "pg_stat_user_tables" in bundle
    assert "create index" not in bundle.lower()
    assert "reindex" not in bundle.lower()


def test_dry_run_writes_report_and_sql_without_secrets(tmp_path):
    report_path = tmp_path / "exports" / "report.json"
    sql_path = tmp_path / "exports" / "diagnostic.sql"

    exit_code = perf.main(
        [
            "--root",
            str(tmp_path),
            "--dry-run",
            "--report-path",
            str(report_path),
            "--sql-path",
            str(sql_path),
        ],
        env={"SUPABASE_DB_URL": SECRET_DB_URL},
    )
    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)

    assert exit_code == 0
    assert report["status"] == "planned"
    assert report["dry_run"] is True
    assert "very-secret" not in report_text
    assert sql_path.exists()
    assert any(probe["name"] == "unused_indexes" for probe in report["probes"])


def test_execute_requires_supabase_db_url(tmp_path, capsys):
    exit_code = perf.main(
        [
            "--root",
            str(tmp_path),
            "--execute",
            "--report-path",
            str(tmp_path / "report.json"),
        ],
        env={},
    )

    assert exit_code == 2
    assert "SUPABASE_DB_URL is required" in capsys.readouterr().err


def test_psql_command_redaction_uses_safe_display():
    command = perf.build_psql_command("psql", SECRET_DB_URL, Path("diagnostic.sql"))
    formatted = perf.format_command(perf.redact_command(command, SECRET_DB_URL))

    assert "very-secret" not in formatted
    assert "postgres:***@db.example.com" in formatted
