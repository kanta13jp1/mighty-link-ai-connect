from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sales_email_sync_workflow_is_scheduled_and_fail_closed():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "sales-email-sync.yml").read_text(
        encoding="utf-8"
    )

    assert 'cron: "*/15 * * * *"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "concurrency:" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "scripts/manage_db_migrations.py apply --engine sqlite" in workflow
    assert "scripts/sync_sales_emails.py --max-messages 100" in workflow
    assert "scripts/sync_sqlite_to_supabase.py" in workflow
    assert "secrets.SALES_EMAIL_IMAP_ENV" in workflow
    assert "secrets.SUPABASE_DB_URL" in workflow
    assert "POP3" not in workflow
    assert "DELE" not in workflow


def test_functions_deploy_removes_stale_imap_keys_before_overlay():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "deploy.yml").read_text(
        encoding="utf-8"
    )

    remove_index = workflow.index("grep -Ev '^(IMAP_HOST|")
    append_index = workflow.index('printf \'\\n%s\\n\' "$SALES_EMAIL_IMAP_ENV"')
    assert remove_index < append_index
