"""Test suite for Proposal Generator module (T964)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from proposal_generator import (
    generate_client_proposal_draft,
    generate_engineer_inquiry_draft
)

def test_generate_client_proposal_draft():
    draft = generate_client_proposal_draft(
        job_title="【フルリモート】Python/FastAPI バックエンド開発",
        client_company_name="株式会社サンプルパートナー",
        engineer_name="山田 太郎",
        experience_summary="・Python実務経験 5年\n・FastAPI/AWS環境でのAPI設計・運用経験多数",
        rate_monthly_man_yen=85,
        available_date="2026年9月1日〜"
    )
    assert draft["type"] == "client_proposal"
    assert "株式会社サンプルパートナー" in draft["body"]
    assert "85万円/月" in draft["body"]
    assert "【要員ご提案】" in draft["subject"]

def test_generate_engineer_inquiry_draft():
    draft = generate_engineer_inquiry_draft(
        job_title="次世代AIマッチング基盤開発",
        engineer_name="佐藤 健",
        project_overview="新規AIサービスのバックエンド開発およびLLM連携基盤の構築",
        rate_monthly_man_yen=90,
        location_and_remote="フルリモート（月1回出社相談）"
    )
    assert draft["type"] == "engineer_inquiry"
    assert "佐藤 健様" in draft["body"]
    assert "〜90万円/月" in draft["body"]
    assert "【案件のご紹介】" in draft["subject"]
