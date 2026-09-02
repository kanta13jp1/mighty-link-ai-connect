#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_external_platform_hub.py
テストスイート: 外部協調プラットフォーム連携ハブ (T989)。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.external_platform_hub import (
    ExternalPlatformHub,
    PlatformEvent,
    PlatformNotificationPayload,
)


def test_external_platform_hub_slack_format():
    hub = ExternalPlatformHub()
    event = PlatformEvent(
        event_type="match_found",
        entity_id="match_9901",
        title="新規高スコアマッチング成立 (92点)",
        details={"案件名": "金融系次世代基盤開発", "候補者": "山田 太郎", "月額単価": "88万円"},
        severity="info",
    )
    payload = hub.format_slack_payload(event, channel="#dev-alerts")
    assert isinstance(payload, PlatformNotificationPayload)
    assert payload.platform == "slack"
    assert payload.target_channel_or_db == "#dev-alerts"
    assert "attachments" in payload.payload
    assert len(payload.payload["attachments"][0]["blocks"]) >= 2


def test_external_platform_hub_teams_and_notion_format():
    hub = ExternalPlatformHub()
    event = PlatformEvent(
        event_type="retention_alert",
        entity_id="can_7701",
        title="離職リスク検知アラート",
        details={"エンジニア": "佐藤 健一", "リスク度": "高 (0.85)", "主な要因": "稼働時間急増"},
        severity="warning",
    )
    teams_payload = hub.format_teams_payload(event)
    assert teams_payload.platform == "teams"
    assert "AdaptiveCard" in str(teams_payload.payload)

    notion_payload = hub.format_notion_page_properties(event, database_id="db_retention_risk")
    assert notion_payload.platform == "notion"
    assert notion_payload.payload["parent"]["database_id"] == "db_retention_risk"
    assert "Title" in notion_payload.payload["properties"]


def test_external_platform_hub_canva_deck_spec():
    hub = ExternalPlatformHub()
    event = PlatformEvent(
        event_type="contract_ready",
        entity_id="cnt_5501",
        title="SES個別契約書ドラフト確定",
        details={"発注企業": "株式会社メガバンク", "契約金額": "90万円/月", "契約期間": "2026/09〜2026/12"},
        severity="info",
    )
    canva_payload = hub.format_canva_deck_spec(event)
    assert canva_payload.platform == "canva"
    assert canva_payload.payload["template"] == "sales_proposal_corporate"
    assert len(canva_payload.payload["slides"]) == 1
