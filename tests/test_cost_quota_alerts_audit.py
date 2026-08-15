"""Tests for Cost & Quota Monitoring Alerts Audit Guard (T932)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit_cost_quota_alerts import (
    build_hypotheses,
    check_required_scripts_exist,
    run_audit,
)


def test_check_required_scripts_exist() -> None:
    assert check_required_scripts_exist() is True


def test_build_hypotheses_all_pass() -> None:
    results, summary = build_hypotheses()
    assert summary["all_passed"] is True
    assert summary["failed_hypotheses"] == 0
    assert len(results) == 10
    for r in results:
        assert r["passed"] is True, f"Hypothesis {r['hypothesis']} failed: {r['detail']}"


def test_run_audit_creates_artifacts(tmp_path: Path) -> None:
    json_path = tmp_path / "cost_quota_audit.json"
    md_path = tmp_path / "cost_quota_audit.md"
    
    code = run_audit(json_out=json_path, md_out=md_path)
    assert code == 0
    assert json_path.exists()
    assert md_path.exists()
    
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["summary"]["all_passed"] is True
