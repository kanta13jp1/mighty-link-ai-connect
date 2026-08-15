"""Test suite for Figma Design Tokens synchronization audit (T768/T909/T917)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_figma_design_sync import run_figma_sync_audit


def test_figma_design_sync_all_hypotheses_pass():
    """Verify that all 10 hypotheses in audit_figma_design_sync pass without drift."""
    success, findings = run_figma_sync_audit()
    assert success is True, f"Figma design sync audit failed: {findings}"
    assert len(findings) == 10, f"Expected 10 hypotheses, got {len(findings)}"
