#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/external_platform_hub.py
外部協調プラットフォーム連携ハブ (T989)。
マッチング成立・リスク検知・契約ドラフト生成イベントを Slack / Microsoft Teams / Notion / Canva 向けに
フォーマット変換し、API Webhook ペイロードやドキュメントを生成する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json


@dataclass
class PlatformEvent:
    event_type: str  # "match_found", "retention_alert", "contract_ready"
    entity_id: str
    title: str
    details: Dict[str, Any]
    severity: str = "info"  # "info", "warning", "critical"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PlatformNotificationPayload:
    platform: str  # "slack", "teams", "notion", "canva"
    payload: Dict[str, Any]
    target_channel_or_db: str
    formatted_summary: str


class ExternalPlatformHub:
    """外部プラットフォームへの通知・連携データを生成するハブクラス。"""

    def format_slack_payload(self, event: PlatformEvent, channel: str = "#ses-matching-alerts") -> PlatformNotificationPayload:
        """Slack Incoming Webhook (Block Kit 互換) ペイロードを生成。"""
        color_map = {
            "info": "#36a64f",
            "warning": "#ecb22e",
            "critical": "#e01e5a",
        }
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"【Mighty Link AI】{event.title}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*種別:* `{event.event_type}`"},
                    {"type": "mrkdwn", "text": f"*重要度:* `{event.severity.upper()}`"},
                    {"type": "mrkdwn", "text": f"*対象ID:* `{event.entity_id}`"},
                    {"type": "mrkdwn", "text": f"*発生日時:* {event.created_at}"},
                ],
            },
        ]
        if event.details:
            detail_lines = "\n".join([f"• *{k}:* {v}" for k, v in event.details.items()])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": detail_lines},
            })

        return PlatformNotificationPayload(
            platform="slack",
            payload={"channel": channel, "attachments": [{"color": color_map.get(event.severity, "#36a64f"), "blocks": blocks}]},
            target_channel_or_db=channel,
            formatted_summary=f"Slack通知: {event.title}",
        )

    def format_teams_payload(self, event: PlatformEvent) -> PlatformNotificationPayload:
        """Microsoft Teams (Adaptive Card) ペイロードを生成。"""
        facts = [{"title": k, "value": str(v)} for k, v in event.details.items()]
        card_content = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {"type": "TextBlock", "text": f"【Mighty Link】{event.title}", "weight": "Bolder", "size": "Medium"},
                {"type": "FactSet", "facts": facts},
            ],
        }
        return PlatformNotificationPayload(
            platform="teams",
            payload={"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": card_content}]},
            target_channel_or_db="general-channel",
            formatted_summary=f"Teams通知: {event.title}",
        )

    def format_notion_page_properties(self, event: PlatformEvent, database_id: str = "notion_ses_db_001") -> PlatformNotificationPayload:
        """Notion API (Pages/Databases) 互換のプロパティ辞書を生成。"""
        properties = {
            "Title": {"title": [{"text": {"content": event.title}}]},
            "EventType": {"select": {"name": event.event_type}},
            "Severity": {"select": {"name": event.severity}},
            "EntityID": {"rich_text": [{"text": {"content": event.entity_id}}]},
        }
        return PlatformNotificationPayload(
            platform="notion",
            payload={"parent": {"database_id": database_id}, "properties": properties},
            target_channel_or_db=database_id,
            formatted_summary=f"Notionレコード: {event.title}",
        )

    def format_canva_deck_spec(self, event: PlatformEvent) -> PlatformNotificationPayload:
        """Canva MCP / プレゼンテーションスライド生成用のスキーマデータを生成。"""
        deck_data = {
            "template": "sales_proposal_corporate",
            "title": event.title,
            "subtitle": f"Generated via Mighty Link AI at {event.created_at}",
            "slides": [
                {
                    "layout": "title_and_metrics",
                    "header": "案件・人材サマリー",
                    "metrics": event.details,
                }
            ],
        }
        return PlatformNotificationPayload(
            platform="canva",
            payload=deck_data,
            target_channel_or_db="canva_workspace",
            formatted_summary=f"Canvaスライド構成: {event.title}",
        )
