#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/sales_email_autopilot_bridge.py
SES営業メール受信パイプラインと自律型営業オートパイロットエンジンの統合ブリッジ (T988)。
受信したメールから案件・人材情報を自動検知し、自律提案キューを生成する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re

try:
    from sales_autopilot_engine import (
        AutopilotBatchReport,
        AutopilotDispatchItem,
        SalesAutopilotEngine,
    )
except ImportError:
    from src.sales_autopilot_engine import (
        AutopilotBatchReport,
        AutopilotDispatchItem,
        SalesAutopilotEngine,
    )


@dataclass
class IngestedEmailItem:
    email_id: str
    subject: str
    sender: str
    body: str
    received_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    category: str = "project"  # "project" or "talent"


@dataclass
class BridgeProcessResult:
    processed_count: int
    matched_proposals_count: int
    queue_items: List[AutopilotDispatchItem]
    status: str
    summary: str


class SalesEmailAutopilotBridge:
    """メール受信パイプラインと自律型営業エンジンを連携する統合ブリッジ。"""

    def __init__(self, engine: Optional[SalesAutopilotEngine] = None) -> None:
        self.engine = engine or SalesAutopilotEngine()

    def parse_email_to_project_dict(self, email: IngestedEmailItem) -> Dict[str, Any]:
        """メール本文から案件情報を抽出し、エンジン互換の辞書形式を生成。"""
        budget_match = re.search(r"(\d{2,3})\s*(?:万|万円|0,000円)", email.body)
        max_budget = int(budget_match.group(1)) * 10000 if budget_match else 850000

        skills = []
        for kw in ["Python", "TypeScript", "React", "AWS", "Go", "Java", "Next.js", "Docker", "SQL"]:
            if kw.lower() in email.body.lower():
                skills.append(kw)
        if not skills:
            skills = ["Python"]

        return {
            "id": f"proj_{email.email_id}",
            "title": email.subject.replace("【案件】", "").replace("【急募】", "").strip() or "新規開発支援案件",
            "skills": skills,
            "max_budget": max_budget,
            "client_name": email.sender.split("@")[0],
        }

    def process_incoming_emails(
        self,
        emails: List[IngestedEmailItem],
        available_talents: List[Dict[str, Any]],
    ) -> BridgeProcessResult:
        """受信メール群をバッチ処理し、人材プールとの自律マッチングおよび提案キューを生成。"""
        project_dicts = [
            self.parse_email_to_project_dict(e)
            for e in emails
            if e.category == "project"
        ]

        report = self.engine.run_overnight_batch(
            incoming_project_emails=project_dicts,
            available_talent_pool=available_talents,
        )

        return BridgeProcessResult(
            processed_count=len(emails),
            matched_proposals_count=report.matched_queue_items_count,
            queue_items=report.items,
            status="completed",
            summary=f"受信メール{len(emails)}件を解析し、{report.matched_queue_items_count}件の高精度提案ドラフトを自律生成しました（平均適合度: {report.average_fit_score}点）。",
        )
