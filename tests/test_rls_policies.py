# -*- coding: utf-8 -*-
"""
Mighty Skill-Bridge: Row Level Security (RLS) Policy Unit Test
Author: Antigravity 2.0 (AI Agent)

This module performs static validation on the Supabase SQL migration files
to ensure that Row Level Security (RLS) is enabled on all critical tables
and that owner-based access policies (auth.firebase_uid() = user_id) are enforced.
"""

import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATION_FILE = os.path.join(PROJECT_ROOT, "supabase", "migrations", "20260606000000_init_schema.sql")

def test_migration_file_exists():
    """Verify that the initial schema migration SQL file exists."""
    assert os.path.exists(MIGRATION_FILE), f"Migration file not found: {MIGRATION_FILE}"

def test_row_level_security_enabled():
    """Verify that RLS is enabled for all critical database tables."""
    with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    critical_tables = [
        "public.profiles",
        "public.matches",
        "public.audits",
        "public.usage_ledgers"
    ]

    for table in critical_tables:
        # Check if ALTER TABLE <table> ENABLE ROW LEVEL SECURITY exists
        pattern = rf"ALTER\s+TABLE\s+{re.escape(table)}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY"
        match = re.search(pattern, sql_content, re.IGNORECASE)
        assert match is not None, f"Row Level Security is not enabled for table: {table}"

def test_owner_security_policies_enforced():
    """Verify that select/update/delete security policies enforce auth.firebase_uid() comparison."""
    with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Normalize whitespace to make matching easier
    normalized_sql = " ".join(sql_content.split())

    # We ensure that policies for tables containing user_id compare auth.firebase_uid()
    policy_checks = [
        ("profiles", r"auth\.firebase_uid\(\)\s*=\s*user_id"),
        ("matches", r"auth\.firebase_uid\(\)\s*=\s*user_id"),
        ("usage_ledgers", r"auth\.firebase_uid\(\)\s*=\s*user_id")
    ]

    for table_name, check_regex in policy_checks:
        # Match all policies for the given public.table_name up to the semicolon
        pattern = rf"CREATE\s+POLICY\s+[^;]*?ON\s+public\.{table_name}\s+[^;]*?;"
        policies = re.findall(pattern, normalized_sql, re.IGNORECASE)
        assert len(policies) > 0, f"No security policies found for table: {table_name}"
        
        # Verify at least one policy restricts access by auth.firebase_uid()
        uid_check_passed = False
        for policy in policies:
            if re.search(check_regex, policy, re.IGNORECASE):
                uid_check_passed = True
                break
        
        assert uid_check_passed, f"Security policies for {table_name} must enforce auth.firebase_uid() = user_id constraint to prevent unauthorized access."
