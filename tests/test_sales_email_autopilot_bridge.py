#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_sales_email_autopilot_bridge.py
テストスイート: 自律型営業メール統合ブリッジ (T988)。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.sales_autopilot_engine import SalesAutopilotEngine
from src.sales_email_autopilot_bridge import (
    BridgeProcessResult,
    IngestedEmailItem,
    SalesEmailAutopilotBridge,
)


def test_sales_email_autopilot_bridge_parse():
    bridge = SalesEmailAutopilotBridge()
    email = IngestedEmailItem(
        email_id="em_001",
        subject="【急募】Python/React フルリモート案件（85万円/月）",
        sender="partner@example.com",
        body="フルリモートで稼働可能なPythonおよびReact経験者を募集します。単価85万円、即日開始可能です。",
        category="project",
    )
    p_dict = bridge.parse_email_to_project_dict(email)
    assert p_dict["id"] == "proj_em_001"
    assert "Python" in p_dict["skills"]
    assert "React" in p_dict["skills"]
    assert p_dict["max_budget"] == 850000
    assert p_dict["client_name"] == "partner"


def test_sales_email_autopilot_bridge_batch_matching():
    bridge = SalesEmailAutopilotBridge()
    emails = [
        IngestedEmailItem(
            email_id="em_101",
            subject="【案件】Go/AWS マイクロサービス開発",
            sender="agency@example.com",
            body="Go言語とAWS環境でのAPI開発案件です。単価90万円。",
            category="project",
        ),
        IngestedEmailItem(
            email_id="em_102",
            subject="【案件】TypeScript / React フロントエンド開発",
            sender="startup@example.com",
            body="TypeScriptとReactのフロントエンド開発。単価80万円。",
            category="project",
        ),
    ]
    talents = [
        {
            "id": "can_01",
            "name": "田中 太郎",
            "skills": ["TypeScript", "React", "Python"],
        },
        {
            "id": "can_02",
            "name": "鈴木 一郎",
            "skills": ["Go", "AWS", "Docker"],
        },
    ]

    result = bridge.process_incoming_emails(emails, talents)
    assert isinstance(result, BridgeProcessResult)
    assert result.processed_count == 2
    assert result.matched_proposals_count >= 2
    assert len(result.queue_items) >= 2
    assert result.status == "completed"
    assert "高精度提案ドラフトを自律生成しました" in result.summary
