"""Unit tests for sales email source breakdown, dynamic analytics API, and UI integration."""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from app import app
from sync_sales_emails import determine_source_type


def test_determine_source_type_classification():
    """Verify source_path strings map to the correct source_type."""
    assert determine_source_type("imap://imap2.gmoserver.jp/INBOX/123") == "imap"
    assert determine_source_type("pop3://pop2.gmoserver.jp/7") == "pop3"
    assert determine_source_type("thunderbird/local/archive_2025.eml") == "thunderbird_local"
    assert determine_source_type("data/sales_emails_archive/mail_001.txt") == "thunderbird_local"
    assert determine_source_type("mbox://local/inbox") == "thunderbird_local"


def test_sales_email_analytics_endpoint_structure():
    """Verify /api/sales-email/analytics returns dynamic counts and source breakdown."""
    client = TestClient(app)
    res = client.get("/api/sales-email/analytics")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "success"
    
    assert "total_count" in data
    assert "server_direct_count" in data
    assert "local_restored_count" in data
    assert "today_new_count" in data
    assert "source_breakdown" in data
    
    sb = data["source_breakdown"]
    assert "imap" in sb
    assert "pop3" in sb
    assert "thunderbird_local" in sb
    
    # Verify no double counting: server_direct_count is sum of imap + pop3
    assert data["server_direct_count"] == sb["imap"] + sb["pop3"]
    # Verify total_count equals server_direct + local_restored
    assert data["total_count"] == data["server_direct_count"] + data["local_restored_count"]


def test_index_html_labels_and_no_hardcoded_counts():
    """Verify index.html contains proper UI labels and no hardcoded hero values."""
    index_path = PROJECT_ROOT / "index.html"
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")
    
    # Required dynamic labels
    assert "総解析データ" in content
    assert "メールサーバー直接取得履歴" in content
    assert "Thunderbird復旧データ" in content
    assert "本日の新着" in content
    
    # Verify hardcoded counts are eliminated from hero cards
    assert 'id="analytics-hero-total">691' not in content
    assert 'id="analytics-hero-total">694' not in content
    assert 'id="analytics-hero-server">691' not in content
    assert 'id="analytics-hero-server">694' not in content
