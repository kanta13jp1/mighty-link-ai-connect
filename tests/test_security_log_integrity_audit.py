"""Tests for Security & Log Integrity Audit Guard (T931)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from audit_security_log_integrity import (
    build_hypotheses,
    check_source_modules_exist,
    run_audit,
    scan_for_secret_leaks,
    verify_aptitude_non_persistence,
)


def test_check_source_modules_exist() -> None:
    assert check_source_modules_exist() is True


def test_verify_aptitude_non_persistence() -> None:
    ok, detail = verify_aptitude_non_persistence()
    assert ok is True
    assert "No database imports" in detail


def test_scan_for_secret_leaks_clean_code() -> None:
    clean_code = "def hello():\n    return 'world'\n"
    leaks = scan_for_secret_leaks(clean_code)
    assert len(leaks) == 0


def test_scan_for_secret_leaks_detection() -> None:
    dirty_code = 'password = "SuperSecret12345!"'
    leaks = scan_for_secret_leaks(dirty_code)
    assert len(leaks) > 0


def test_build_hypotheses_all_pass() -> None:
    results, summary = build_hypotheses()
    assert summary["all_passed"] is True
    assert summary["failed_hypotheses"] == 0
    assert len(results) == 10
    for r in results:
        assert r["passed"] is True, f"Hypothesis {r['hypothesis']} failed: {r['detail']}"


def test_run_audit_creates_artifacts(tmp_path: Path) -> None:
    json_path = tmp_path / "security_log_audit.json"
    md_path = tmp_path / "security_log_audit.md"
    
    code = run_audit(json_out=json_path, md_out=md_path)
    assert code == 0
    assert json_path.exists()
    assert md_path.exists()
    
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["summary"]["all_passed"] is True
