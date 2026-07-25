import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from setup_supabase_backup_ci import generate_setup_plan, main


def test_generate_setup_plan_contains_required_steps():
    plan = generate_setup_plan(
        project_id="my-gcp-proj",
        project_number="987654321",
        pool_id="github-pool",
        provider_id="github-provider",
        sa_email="backup-sa@my-gcp-proj.iam.gserviceaccount.com",
        bucket_name="mightylink-supabase-backup",
        repo="kanta13jp1/mighty-link-ai-connect",
        repository_id="1244319528",
    )
    text = "\n".join(plan)

    assert "roles/iam.workloadIdentityUser" in text
    assert "mightylink-supabase-backup" in text
    assert "github-pool" in text
    assert "github-provider" in text
    assert "assertion.repository_id=='1244319528'" in text
    assert "assertion.ref=='refs/heads/master'" in text
    assert "roles/storage.objectCreator" in text
    assert "roles/storage.objectViewer" in text
    assert "roles/storage.objectAdmin" not in text
    assert "gh secret set GCP_BACKUP_WORKLOAD_IDENTITY_PROVIDER" in text
    assert "gh secret set SUPABASE_DB_URL" in text
    assert "gh workflow run 'Supabase Daily Backup'" in text


def test_setup_script_main_executes_cleanly(capsys):
    ret = main(["--dry-run"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "T870: Supabase Backup CI Recovery Setup Helper" in captured.out
    assert "mighty-link-ai-connect-13d22-supabase-backups" in captured.out
