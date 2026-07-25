"""Tests for the fail-closed production UAT write verifier (T845/T921)."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_supabase_uat_writes
from verify_supabase_uat_writes import LIVE_UAT_TABLES, verify_uat_db_writes


EXPECTED_TABLES = {
    "employee_assessment_responses",
    "attendance_punch_events",
    "attendance_timesheet_imports",
    "usage_analytics_events",
    "sales_mailbox_sources",
    "sales_email_messages",
    "sales_email_entities",
    "project_requirements",
    "talent_profiles_from_email",
    "requirement_skill_tags",
    "email_parse_runs",
    "email_match_results",
    "email_match_feedback",
    "feedback_events",
    "support_requests",
}


class FakeCursor:
    def __init__(self, *, fail_on: str | None = None, cleanup_count: int = 0):
        self.fail_on = fail_on
        self.cleanup_count = cleanup_count
        self.executed: list[tuple[str, object]] = []
        self.next_id = 100
        self._fetchone = None

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split())
        self.executed.append((normalized, params))
        if self.fail_on and self.fail_on in normalized:
            raise RuntimeError(f"synthetic failure at {self.fail_on}")
        if normalized.startswith("SHOW server_version_num"):
            self._fetchone = ("170006",)
        elif normalized.startswith("INSERT INTO"):
            self._fetchone = (params[0],)
        elif normalized.startswith("SELECT 1 FROM"):
            self._fetchone = (1,)
        elif normalized.startswith("SELECT ("):
            self._fetchone = (self.cleanup_count,)
        else:
            self._fetchone = None

    def fetchone(self):
        return self._fetchone

    def close(self):
        return None


class FakeConnection:
    def __init__(self, cursor: FakeCursor):
        self.cursor_instance = cursor
        self.rollback_count = 0
        self.commit_count = 0
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def rollback(self):
        self.rollback_count += 1

    def commit(self):
        self.commit_count += 1

    def close(self):
        self.closed = True


def test_offline_guard_validates_schema_without_claiming_live_writes():
    assert audit_supabase_uat_writes.EVIDENCE_PATH is not None

    result = verify_uat_db_writes()

    assert result["status"] == "PASS"
    assert result["mode"] == "offline_schema_contract"
    assert result["live_write_verified"] is False
    assert result["transaction_rolled_back"] is False
    assert set(result["checked_tables"]) == EXPECTED_TABLES
    assert set(LIVE_UAT_TABLES) == EXPECTED_TABLES
    assert all(info["verified"] for info in result["table_status"].values())


def test_execute_mode_fails_closed_without_database_secret():
    result = verify_uat_db_writes(execute=True)

    assert result["status"] == "FAIL"
    assert result["mode"] == "live_transactional_write"
    assert result["live_write_verified"] is False
    assert "required" in result["summary"].lower()


def test_live_probe_inserts_every_table_then_rolls_back_and_checks_cleanup():
    cursor = FakeCursor()
    connection = FakeConnection(cursor)

    result = verify_uat_db_writes(
        db_url="postgresql://user:secret@db.example.test:5432/postgres",
        execute=True,
        connection_factory=lambda _url: connection,
        run_id="t921-test-run",
    )

    inserted_tables = {
        query.split()[2]
        for query, _params in cursor.executed
        if query.startswith("INSERT INTO")
    }
    assert result["status"] == "PASS"
    assert result["mode"] == "live_transactional_write"
    assert result["live_write_verified"] is True
    assert result["transaction_rolled_back"] is True
    assert result["cleanup_verified"] is True
    assert result["persisted_probe_records"] == 0
    assert inserted_tables == {f"public.{table}" for table in EXPECTED_TABLES}
    assert connection.rollback_count >= 2
    assert connection.commit_count == 0
    assert connection.closed is True


def test_live_probe_fails_when_cleanup_finds_persisted_records():
    connection = FakeConnection(FakeCursor(cleanup_count=1))

    result = verify_uat_db_writes(
        db_url="postgresql://user:secret@db.example.test:5432/postgres",
        execute=True,
        connection_factory=lambda _url: connection,
        run_id="t921-cleanup-failure",
    )

    assert result["status"] == "FAIL"
    assert result["live_write_verified"] is False
    assert result["cleanup_verified"] is False
    assert result["persisted_probe_records"] == 1
    assert connection.commit_count == 0


def test_database_errors_are_redacted_and_never_downgraded_to_warning():
    secret_url = "postgresql://user:super-secret@db.example.test:5432/postgres"

    def fail_connection(_url):
        raise RuntimeError(f"could not connect to {secret_url}")

    result = verify_uat_db_writes(
        db_url=secret_url,
        execute=True,
        connection_factory=fail_connection,
    )
    rendered = repr(result)

    assert result["status"] == "FAIL"
    assert result["live_write_verified"] is False
    assert "WARN" not in rendered
    assert secret_url not in rendered
    assert "super-secret" not in rendered


def test_manual_workflow_uses_repository_secret_and_publishes_evidence():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "supabase-uat-write.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "secrets.SUPABASE_DB_URL" in workflow
    assert "verify_supabase_uat_writes.py --execute" in workflow
    assert "actions/checkout@v6" in workflow
    assert "actions/setup-python@v6" in workflow
    assert "actions/upload-artifact@v6" in workflow
    assert "pull_request:" not in workflow


def test_actions_context_makes_live_evidence_traceable(monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "123456")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/repo")

    result = verify_uat_db_writes()

    assert result["github_actions"] == {
        "run_id": "123456",
        "commit_sha": "abc123",
        "run_url": "https://github.com/example/repo/actions/runs/123456",
    }
