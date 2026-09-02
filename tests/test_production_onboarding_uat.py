"""Regression tests for the secret-safe production onboarding UAT (T1001)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_production_onboarding as uat  # noqa: E402


def test_uat_passes_contract_without_recording_sensitive_values(monkeypatch):
    username = "production-user-value"
    password = "production-password-value"
    run_id = "123456"

    def fake_request(url, *, method="GET", payload=None, auth_header=None, timeout=20):
        if url.endswith("/state") and not auth_header:
            return 401, {"detail": "Unauthorized"}
        if url.endswith("/state"):
            return 200, {
                "flow_version": "MSB-ONBOARDING-TEST",
                "legal_consent_version": "MSB-LEGAL-TEST",
                "required_step_ids": ["account", "legal_consent"],
                "steps": [],
            }
        if url.endswith("/progress"):
            return 200, {"can_activate": True}
        if payload and payload.get("legal_consent_version") == "MSB-LEGAL-STALE-UAT":
            return 400, {"detail": "stale"}
        return 200, {
            "activated": True,
            "auth_status": "authenticated",
            "session_token": "sess_onb_sensitive-token-value",
            "subject_pseudonym": "onb-sensitive-value",
        }

    monkeypatch.setattr(uat, "_request", fake_request)
    report = uat.run_uat("https://mightylink-app.com/", username, password, run_id)

    assert report["passed"] is True
    serialized = json.dumps(report, ensure_ascii=False)
    assert username not in serialized
    assert password not in serialized
    assert "sess_onb_sensitive-token-value" not in serialized
    assert "onb-sensitive-value" not in serialized
    assert f"github-actions-uat-{run_id}" not in serialized
    assert report["sensitive_fields_recorded"] is False


def test_uat_rejects_non_production_or_credential_bearing_urls():
    for value in (
        "http://mightylink-app.com/",
        "https://example.com/",
        "https://user:password@mightylink-app.com/",
        "https://mightylink-app.com/?token=value",
    ):
        try:
            uat._base_url(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe URL accepted: {value}")


def test_workflow_runs_manually_and_always_uploads_report():
    workflow = (
        PROJECT_ROOT / ".github" / "workflows" / "production-onboarding-uat.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "BASIC_AUTH_USERNAME: ${{ secrets.BASIC_AUTH_USERNAME }}" in workflow
    assert "BASIC_AUTH_PASSWORD: ${{ secrets.BASIC_AUTH_PASSWORD }}" in workflow
    assert "python scripts/verify_production_onboarding.py" in workflow
    assert "if: always()" in workflow
    assert "exports/production_onboarding_uat_report.json" in workflow
    assert "actions/upload-artifact@v7" in workflow