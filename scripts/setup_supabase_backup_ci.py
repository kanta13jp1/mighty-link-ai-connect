#!/usr/bin/env python3
"""Interactive / dry-run helper to set up GCP WIF & GCS for Supabase Backup CI (T870 / R116).

This script provides dry-run and execution support for T870 following
docs/SUPABASE_BACKUP_CI_RECOVERY_RUNBOOK.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TASK_ID = "T870"
RUNBOOK_PATH = Path("docs") / "SUPABASE_BACKUP_CI_RECOVERY_RUNBOOK.md"
DEFAULT_POOL_ID = "github-pool"
DEFAULT_PROVIDER_ID = "github-provider"
DEFAULT_BUCKET_NAME = "mighty-link-ai-connect-13d22-supabase-backups"
DEFAULT_REPO = "kanta13jp1/mighty-link-ai-connect"
DEFAULT_REPOSITORY_ID = "1244319528"
LIFECYCLE_FILE = ".github/config/supabase-backup-lifecycle.json"


def generate_setup_plan(
    project_id: str = "<PROJECT_ID>",
    project_number: str = "<PROJECT_NUMBER>",
    pool_id: str = DEFAULT_POOL_ID,
    provider_id: str = DEFAULT_PROVIDER_ID,
    sa_email: str = "<SA_EMAIL>",
    bucket_name: str = DEFAULT_BUCKET_NAME,
    repo: str = DEFAULT_REPO,
    repository_id: str = DEFAULT_REPOSITORY_ID,
) -> list[str]:
    """Generate the exact gcloud and gh secret commands for T870 recovery."""
    commands = [
        f"# Step 1: Confirm project ID and ensure project number is not 100664750415",
        f"gcloud config get-value project",
        f"gcloud projects describe {project_id} --format='value(projectNumber)'",
        f"",
        f"# Step 2: Create Workload Identity Pool & Provider",
        f"gcloud iam workload-identity-pools create {pool_id} --project={project_id} --location=global --display-name='GitHub Actions Pool'",
        f"gcloud iam workload-identity-pools providers create-oidc {provider_id} --project={project_id} --location=global --workload-identity-pool={pool_id} --issuer-uri='https://token.actions.githubusercontent.com' --attribute-mapping='google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_id=assertion.repository_id,attribute.ref=assertion.ref' --attribute-condition=\"assertion.repository_id=='{repository_id}' && assertion.ref=='refs/heads/master'\"",
        f"",
        f"# Step 3: Grant roles/iam.workloadIdentityUser to Service Account",
        f"gcloud iam service-accounts add-iam-policy-binding {sa_email} --project={project_id} --role='roles/iam.workloadIdentityUser' --member='principalSet://iam.googleapis.com/projects/{project_number}/locations/global/workloadIdentityPools/{pool_id}/attribute.repository_id/{repository_id}'",
        f"",
        f"# Step 4: Create Private GCS Bucket for Backups",
        f"gcloud storage buckets create gs://{bucket_name} --project={project_id} --location=asia-northeast1 --uniform-bucket-level-access --public-access-prevention",
        f"gcloud storage buckets update gs://{bucket_name} --retention-period=P7D --lifecycle-file={LIFECYCLE_FILE}",
        f"gcloud storage buckets add-iam-policy-binding gs://{bucket_name} --member='serviceAccount:{sa_email}' --role='roles/storage.objectCreator'",
        f"gcloud storage buckets add-iam-policy-binding gs://{bucket_name} --member='serviceAccount:{sa_email}' --role='roles/storage.objectViewer'",
        f"",
        f"# Step 5: Register GitHub Repository Secrets (interactive input)",
        f"gh secret set GCP_BACKUP_WORKLOAD_IDENTITY_PROVIDER --repo {repo}",
        f"gh secret set GCP_BACKUP_SERVICE_ACCOUNT_EMAIL      --repo {repo}",
        f"gh secret set SUPABASE_BACKUP_GCS_URI        --repo {repo}",
        f"gh secret set SUPABASE_DB_URL                --repo {repo}",
        f"",
        f"# Step 6: Trigger and Verify Backup Workflow",
        f"gh workflow run 'Supabase Daily Backup' --repo {repo}",
        f"gh run list --workflow='Supabase Daily Backup' --repo {repo} --limit 1",
    ]
    return commands


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Helper for T870 Supabase Daily Backup CI Recovery."
    )
    parser.add_argument("--project-id", default="<PROJECT_ID>", help="Target GCP project ID.")
    parser.add_argument("--project-number", default="<PROJECT_NUMBER>", help="Target GCP project number.")
    parser.add_argument("--pool-id", default=DEFAULT_POOL_ID, help="WIF pool ID.")
    parser.add_argument("--provider-id", default=DEFAULT_PROVIDER_ID, help="WIF provider ID.")
    parser.add_argument("--sa-email", default="<SA_EMAIL>", help="Service account email.")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET_NAME, help="GCS bucket name.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repository name.")
    parser.add_argument("--repository-id", default=DEFAULT_REPOSITORY_ID, help="Numeric GitHub repository ID.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Print plan without executing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"=== {TASK_ID}: Supabase Backup CI Recovery Setup Helper ===")
    print(f"Runbook: {RUNBOOK_PATH}")
    print(f"Bucket: gs://{args.bucket}")
    print(f"WIF Pool: {args.pool_id}")
    print(f"WIF Provider: {args.provider_id}")
    print(f"Repository: {args.repo}\n")

    plan = generate_setup_plan(
        project_id=args.project_id,
        project_number=args.project_number,
        pool_id=args.pool_id,
        provider_id=args.provider_id,
        sa_email=args.sa_email,
        bucket_name=args.bucket,
        repo=args.repo,
        repository_id=args.repository_id,
    )

    for line in plan:
        print(line)

    print("\n[+] Setup plan generated successfully. Follow instructions interactively or execute gcloud / gh commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
