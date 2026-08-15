"""Test suite for Slack / Teams Webhook notification module (T961)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from slack_teams_notification import (
    build_slack_instant_card,
    build_slack_daily_digest,
    send_webhook_notification
)

def test_build_slack_instant_card():
    card = build_slack_instant_card(
        job_title="【フルリモート】Python/FastAPIバックエンド開発",
        engineer_name="山田 太郎 (Python 5年)",
        score=92.5,
        reason="Python/FastAPI要件に完全合致し、単価・リモート条件もクリアしています。"
    )
    assert "text" in card
    assert "blocks" in card
    assert "92.5%" in card["text"]
    assert len(card["blocks"]) >= 3

def test_build_slack_daily_digest():
    top_matches = [
        {"job_title": "AIエンジニア案件", "engineer_name": "佐藤 健", "score": 95.0},
        {"job_title": "Go言語マイクロサービス", "engineer_name": "鈴木 一郎", "score": 88.0}
    ]
    digest = build_slack_daily_digest(
        date_str="2026-08-15",
        total_emails=1024,
        high_match_count=18,
        top_matches=top_matches
    )
    assert "2026-08-15" in digest["text"]
    assert "1024 件" in digest["blocks"][1]["fields"][0]["text"]
    assert "18 件" in digest["blocks"][1]["fields"][1]["text"]

def test_send_webhook_notification_dry_run():
    # When webhook_url is None or empty, should return dry_run safely
    res = send_webhook_notification(webhook_url=None, payload={"test": 123})
    assert res["status"] == "dry_run"
    assert res["sent"] is False
