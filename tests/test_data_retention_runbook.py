from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


EXPECTED_RETENTION_TARGETS = [
    "profiles",
    "matches",
    "audits",
    "usage_ledgers",
    "feedback_events",
    "support_requests",
    "sales_mailbox_sources",
    "sales_email_messages",
    "sales_email_entities",
    "project_requirements",
    "talent_profiles_from_email",
    "requirement_skill_tags",
    "email_parse_runs",
    "email_match_results",
    "email_match_feedback",
    "employee_assessment_responses",
    "attendance_punch_events",
    "attendance_timesheet_imports",
]


RLS_REQUIRED_TABLES = [
    "public.profiles",
    "public.matches",
    "public.audits",
    "public.usage_ledgers",
    "public.feedback_events",
    "public.support_requests",
    "public.sales_mailbox_sources",
    "public.sales_email_messages",
    "public.sales_email_entities",
    "public.project_requirements",
    "public.talent_profiles_from_email",
    "public.requirement_skill_tags",
    "public.email_parse_runs",
    "public.email_match_results",
    "public.email_match_feedback",
    "public.employee_assessment_responses",
    "public.attendance_punch_events",
    "public.attendance_timesheet_imports",
]


REVOKE_REQUIRED_TABLES = [
    "sales_mailbox_sources",
    "sales_email_messages",
    "sales_email_entities",
    "project_requirements",
    "talent_profiles_from_email",
    "requirement_skill_tags",
    "email_parse_runs",
    "email_match_results",
    "email_match_feedback",
    "employee_assessment_responses",
    "attendance_punch_events",
    "attendance_timesheet_imports",
]


def read_text(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def all_migrations_sql() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((PROJECT_ROOT / "supabase" / "migrations").glob("*.sql"))
    )


def test_t847_retention_runbook_covers_all_current_tables():
    runbook = read_text("docs/DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md")

    for table in EXPECTED_RETENTION_TARGETS:
        assert table in runbook, f"{table} is missing from T847 retention matrix"

    required_controls = [
        "メール本文全文",
        "CSV原本",
        "secret",
        "RLS",
        "anon/authenticated",
        "GET /api/user-data/export",
        "scripts/rotate_runtime_logs.py",
    ]
    for control in required_controls:
        assert control in runbook


def test_t847_existing_deletion_and_log_runbooks_link_to_matrix():
    for relative_path in [
        "docs/USER_DATA_DELETION_FLOW.md",
        "docs/LOG_ROTATION_AND_RETENTION_RUNBOOK.md",
    ]:
        content = read_text(relative_path)
        assert "DATA_RETENTION_DELETION_ANONYMIZATION_RUNBOOK.md" in content
        assert "T847" in content


def test_all_t847_tables_enable_rls_in_migrations():
    sql = all_migrations_sql().lower()
    normalized = " ".join(sql.split())

    for table in RLS_REQUIRED_TABLES:
        assert f"alter table {table.lower()} enable row level security" in normalized


def test_high_sensitivity_t847_tables_revoke_direct_rest_roles():
    sql = all_migrations_sql().lower()
    normalized = " ".join(sql.split())

    for table in REVOKE_REQUIRED_TABLES:
        combined_revoke = f"revoke all on table public.{table} from anon, authenticated"
        split_revoke = (
            f"revoke all on table public.{table} from anon" in normalized
            and f"revoke all on table public.{table} from authenticated" in normalized
        )
        assert combined_revoke in normalized or split_revoke
