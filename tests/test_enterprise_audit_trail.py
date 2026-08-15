"""Test suite for Enterprise Audit Trail module (T971)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from enterprise_audit_trail import (
    generate_audit_entry,
    verify_audit_chain_integrity,
    export_enterprise_audit_report
)

def test_audit_chain_integrity_valid():
    entry1 = generate_audit_entry(user_id="user_admin", action="LOGIN", resource_id="auth", previous_hash="GENESIS")
    entry2 = generate_audit_entry(user_id="user_admin", action="MATCH_RUN", resource_id="job_001", previous_hash=entry1["hash"])
    entry3 = generate_audit_entry(user_id="user_admin", action="EXPORT_CSV", resource_id="report_001", previous_hash=entry2["hash"])

    chain = [entry1, entry2, entry3]
    assert verify_audit_chain_integrity(chain) is True

    report = export_enterprise_audit_report(chain)
    assert report["total_events_count"] == 3
    assert report["chain_integrity_verified"] is True
    assert "SOC2" in report["compliance_standard"]

def test_audit_chain_integrity_tampered():
    entry1 = generate_audit_entry(user_id="user_admin", action="LOGIN", resource_id="auth", previous_hash="GENESIS")
    entry2 = generate_audit_entry(user_id="user_admin", action="MATCH_RUN", resource_id="job_001", previous_hash=entry1["hash"])

    # Tamper entry1 action
    entry1_tampered = dict(entry1)
    entry1_tampered["action"] = "UNAUTHORIZED_ACCESS"

    chain = [entry1_tampered, entry2]
    assert verify_audit_chain_integrity(chain) is False
