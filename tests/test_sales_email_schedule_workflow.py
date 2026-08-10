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
    assert "--fail-with-body" in workflow
    assert "/api/sales-email/sync?max_messages=100" in workflow
    assert "secrets.SALES_EMAIL_SYNC_USERNAME" in workflow
    assert "secrets.SALES_EMAIL_SYNC_PASSWORD" in workflow
    assert "POP3" not in workflow
    assert "DELE" not in workflow


def test_functions_deploy_removes_stale_imap_keys_before_overlay():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "deploy.yml").read_text(
        encoding="utf-8"
    )

    remove_index = workflow.index("grep -Ev '^(IMAP_HOST|")
    append_index = workflow.index('printf \'\\n%s\\n\' "$SALES_EMAIL_IMAP_ENV"')
    assert remove_index < append_index
