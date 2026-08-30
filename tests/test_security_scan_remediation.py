from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_sla_measurement_report import fetch_view  # noqa: E402
from network_security import (  # noqa: E402
    require_https_or_loopback_url,
    require_https_url,
    require_loopback_http_url,
)
from parse_sales_emails import _validated_sqlite_keys  # noqa: E402


def test_network_destinations_reject_insecure_remote_and_embedded_credentials():
    with pytest.raises(ValueError):
        require_https_url("http://example.com/hook")
    with pytest.raises(ValueError):
        require_https_url("https://user:secret@example.com/hook")
    with pytest.raises(ValueError):
        require_https_or_loopback_url("http://example.com/metrics")


def test_network_destinations_allow_https_and_explicit_loopback_only():
    assert require_https_url("https://example.com/hook") == "https://example.com/hook"
    assert require_https_or_loopback_url("http://127.0.0.1:9090/metrics").startswith("http://127.0.0.1")
    assert require_loopback_http_url("http://localhost:9099/push").endswith("/push")
    with pytest.raises(ValueError):
        require_loopback_http_url("http://192.168.1.20:9099/push")


def test_security_dependency_floor_uses_patched_fastapi_starlette_line():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "fastapi>=0.141.1,<0.142.0" in requirements
    assert "starlette>=1.6.0,<1.7.0" in requirements
    assert "starlette>=1.0.1,<1.1.0" not in requirements


def test_security_workflow_always_preserves_scan_evidence():
    workflow = (ROOT / ".github" / "workflows" / "security-scan.yml").read_text(encoding="utf-8")
    assert "if: always()" in workflow
    assert "reports/bandit_weekly.txt" in workflow
    assert "reports/pip_audit_weekly.json" in workflow
    assert "actions/upload-artifact@v6" in workflow

def test_sql_identifier_allowlists_reject_untrusted_columns_and_views():
    with pytest.raises(ValueError):
        _validated_sqlite_keys(
            "sales_email_messages",
            {"dedupe_key); DROP TABLE sales_email_messages; --": "bad"},
        )

    class CursorMustNotExecute:
        def execute(self, *_args, **_kwargs):
            pytest.fail("SQL must not execute for an unsupported view")

    with pytest.raises(ValueError):
        fetch_view(CursorMustNotExecute(), "kpi_monthly_availability; DROP VIEW x")
