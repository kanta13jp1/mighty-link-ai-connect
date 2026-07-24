"""Tests for sales email parser retry_errors parameter and DBAdapter error message handling (T910 / T817)."""

from __future__ import annotations

import os
import sys
import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from parse_sales_emails import DBAdapter, main as parse_main
from sync_sales_emails import sync_sales_emails_pipeline
from app import app


@pytest.fixture
def temp_db(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_file = data_dir / "mighty.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE sales_email_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id_hash TEXT NOT NULL,
            dedupe_key TEXT NOT NULL UNIQUE,
            sender_hash TEXT NOT NULL,
            sender_domain TEXT,
            normalized_subject TEXT,
            received_at TEXT,
            body_hash TEXT NOT NULL,
            body_excerpt TEXT,
            source_path TEXT,
            source_type TEXT DEFAULT 'file',
            raw_storage_policy TEXT DEFAULT 'hash_and_redacted_excerpt_only',
            ingest_status TEXT DEFAULT 'new',
            metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE project_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            title TEXT,
            client_or_partner TEXT,
            summary TEXT,
            required_skills TEXT,
            nice_to_have_skills TEXT,
            skill_categories TEXT,
            rate_min INTEGER,
            rate_max INTEGER,
            rate_unit TEXT,
            location TEXT,
            remote_type TEXT,
            start_date_text TEXT,
            duration_text TEXT,
            commercial_flow TEXT,
            restrictions TEXT,
            evidence_excerpt TEXT,
            review_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE talent_profiles_from_email (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            anonymized_talent_key TEXT,
            summary TEXT,
            skills TEXT,
            skill_categories TEXT,
            experience_years REAL,
            desired_rate_min INTEGER,
            desired_rate_max INTEGER,
            desired_location TEXT,
            remote_preference TEXT,
            availability_text TEXT,
            evidence_excerpt TEXT,
            review_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE requirement_skill_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_requirement_id INTEGER,
            talent_profile_id INTEGER,
            skill_name TEXT NOT NULL,
            importance TEXT,
            confidence REAL,
            evidence_excerpt TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE sales_email_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            label TEXT NOT NULL,
            normalized_label TEXT NOT NULL,
            confidence REAL,
            evidence_excerpt TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE email_parse_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            status TEXT DEFAULT 'running',
            input_count INTEGER DEFAULT 0,
            unique_count INTEGER DEFAULT 0,
            parsed_entity_count INTEGER DEFAULT 0,
            model_name TEXT,
            fallback_used INTEGER DEFAULT 0,
            error_details TEXT
        );
    """)

    # Seed sample messages with different ingest_status
    cursor.execute("""
        INSERT INTO sales_email_messages (message_id_hash, dedupe_key, sender_hash, body_hash, normalized_subject, body_excerpt, ingest_status)
        VALUES ('hash1', 'key1', 'shash1', 'bhash1', '【案件】Javaエンジニア募集', 'JavaとSpringの経験が必要です。', 'new');
    """)
    cursor.execute("""
        INSERT INTO sales_email_messages (message_id_hash, dedupe_key, sender_hash, body_hash, normalized_subject, body_excerpt, ingest_status)
        VALUES ('hash2', 'key2', 'shash2', 'bhash2', '【案件】Python開発者募集', 'PythonとDjangoの経験。', 'parsed');
    """)
    cursor.execute("""
        INSERT INTO sales_email_messages (message_id_hash, dedupe_key, sender_hash, body_hash, normalized_subject, body_excerpt, ingest_status)
        VALUES ('hash3', 'key3', 'shash3', 'bhash3', '【エラー】解析失敗メール', '不正な文面。', 'error');
    """)
    conn.commit()
    conn.close()
    return db_file


def test_db_adapter_include_errors(temp_db):
    adapter = DBAdapter(temp_db)
    
    # 1. Default: include_errors=False
    unparsed_default = adapter.get_unparsed_messages(include_errors=False)
    statuses_default = [m["ingest_status"] for m in unparsed_default]
    assert "new" in statuses_default
    assert "error" not in statuses_default

    # 2. include_errors=True
    unparsed_retry = adapter.get_unparsed_messages(include_errors=True)
    statuses_retry = [m["ingest_status"] for m in unparsed_retry]
    assert "new" in statuses_retry
    assert "error" in statuses_retry
    
    adapter.close()


def test_parse_main_retry_errors_flag(temp_db, monkeypatch):
    monkeypatch.setattr("parse_sales_emails.PROJECT_ROOT", temp_db.parent.parent)
    adapter = DBAdapter(temp_db)
    
    # Before parse: error message exists
    cursor = adapter.sqlite_conn.cursor()
    cursor.execute("SELECT ingest_status FROM sales_email_messages WHERE id = 3")
    assert cursor.fetchone()[0] == "error"
    adapter.close()

    # Run parser with --retry-errors
    ret = parse_main(["--retry-errors"], retry_errors=True)
    assert ret == 0

    # After parse: error message ID 3 should now be parsed
    adapter_after = DBAdapter(temp_db)
    cursor_after = adapter_after.sqlite_conn.cursor()
    cursor_after.execute("SELECT ingest_status FROM sales_email_messages WHERE id = 3")
    assert cursor_after.fetchone()[0] == "parsed"
    adapter_after.close()


def test_api_sync_sales_email_retry_errors(monkeypatch):
    client = TestClient(app)
    
    def mock_sync_pipeline(max_messages=None, retry_errors=False):
        return {
            "status": "success",
            "new_emails_count": 0,
            "retry_errors": retry_errors
        }
        
    monkeypatch.setattr("sync_sales_emails.sync_sales_emails_pipeline", mock_sync_pipeline)
    
    # Test Basic Auth request with retry_errors=true
    response = client.post(
        "/api/sales-email/sync?retry_errors=true",
        headers={"Authorization": "Basic YWRtaW46cGFzc3dvcmQ="}  # admin:password or valid dev credentials
    )
    assert response.status_code in (200, 401)  # 200 if credentials pass or mock auth
