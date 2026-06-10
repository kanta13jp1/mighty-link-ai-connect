import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_staging_environment_config as verifier


def write_minimal_firebase_config(project_root: Path) -> None:
    (project_root / ".firebaserc").write_text(
        json.dumps({"projects": {"default": "mighty-link-prod"}}, indent=2),
        encoding="utf-8",
    )
    (project_root / "firebase.json").write_text(
        json.dumps({"hosting": {"site": "mighty-link-prod", "public": "."}}, indent=2),
        encoding="utf-8",
    )


def separated_env() -> dict[str, str]:
    return {
        "FIREBASE_PROJECT_ID": "mighty-link-prod",
        "FIREBASE_STAGING_PROJECT_ID": "mighty-link-staging",
        "FIREBASE_HOSTING_PREVIEW_CHANNEL": "staging",
        "SUPABASE_STAGING_URL": "https://staging.supabase.co",
        "SUPABASE_PROD_URL": "https://prod.supabase.co",
        "SUPABASE_STAGING_ANON_KEY": "anon-staging",
        "SUPABASE_PROD_ANON_KEY": "anon-prod",
        "SUPABASE_STAGING_JWT_SECRET_FINGERPRINT": "sha256:staging",
        "SUPABASE_PROD_JWT_SECRET_FINGERPRINT": "sha256:prod",
        "SUPABASE_STAGING_SERVICE_ROLE_KEY": "service-staging",
        "SUPABASE_PROD_SERVICE_ROLE_KEY": "service-prod",
    }


def check_by_key(report: dict, key: str) -> dict:
    return next(check for check in report["checks"] if check["key"] == key)


def test_build_report_accepts_separated_staging_and_prod(tmp_path):
    write_minimal_firebase_config(tmp_path)

    report = verifier.build_report(tmp_path, separated_env())

    assert report["status"] == "ok"
    assert check_by_key(report, "firebase.preview_channel")["state"] == "ok"
    assert check_by_key(report, "supabase.jwt_secret_fingerprint")["state"] == "ok"


def test_build_report_flags_supabase_same_url_and_jwt_fingerprint(tmp_path):
    write_minimal_firebase_config(tmp_path)
    env = separated_env()
    env["SUPABASE_STAGING_URL"] = env["SUPABASE_PROD_URL"]
    env["SUPABASE_STAGING_JWT_SECRET_FINGERPRINT"] = env["SUPABASE_PROD_JWT_SECRET_FINGERPRINT"]

    report = verifier.build_report(tmp_path, env)

    assert report["status"] == "critical"
    assert check_by_key(report, "supabase.url")["state"] == "critical"
    assert check_by_key(report, "supabase.jwt_secret_fingerprint")["state"] == "critical"


def test_build_report_warns_when_staging_env_is_missing(tmp_path):
    write_minimal_firebase_config(tmp_path)

    report = verifier.build_report(tmp_path, {})

    assert report["status"] == "warning"
    assert check_by_key(report, "firebase.staging_project")["state"] == "warning"
    assert check_by_key(report, "supabase.url")["state"] == "warning"


def test_build_report_rejects_production_like_preview_channel(tmp_path):
    write_minimal_firebase_config(tmp_path)
    env = separated_env()
    env["FIREBASE_HOSTING_PREVIEW_CHANNEL"] = "production"

    report = verifier.build_report(tmp_path, env)

    assert report["status"] == "critical"
    assert check_by_key(report, "firebase.preview_channel")["state"] == "critical"


def test_build_report_rejects_functions_deploy_without_allowlist(tmp_path):
    write_minimal_firebase_config(tmp_path)
    env = separated_env()
    env["FIREBASE_FUNCTIONS_DEPLOY_ENABLED"] = "true"

    report = verifier.build_report(tmp_path, env)

    assert report["status"] == "critical"
    assert check_by_key(report, "firebase.functions_deploy")["state"] == "critical"
