"""Test for verify_supabase_uat_writes.py (T845)."""
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from verify_supabase_uat_writes import verify_uat_db_writes, REQUIRED_UAT_TABLES

def test_verify_uat_db_writes_fallback():
    res = verify_uat_db_writes(db_url=None)
    assert res["status"] in ("PASS", "WARN")
    assert res["has_db_connection"] is False
    assert len(res["checked_tables"]) == 7
    for tbl in REQUIRED_UAT_TABLES:
        assert tbl in res["table_status"]
        assert res["table_status"][tbl]["verified"] is True
