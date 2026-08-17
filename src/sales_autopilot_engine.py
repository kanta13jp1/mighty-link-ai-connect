#!/usr/bin/env python3
"""Autonomous Sales Autopilot Engine Module (T985 - Action 22).

Processes incoming overnight project emails in background, automatically scores talent-project fit,
and compiles a ready-to-send proposal dispatch queue for sales reps at 9:00 AM.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AutopilotDispatchItem:
    queue_id: str
    project_id: str
    project_title: str
    client_name: str
    matched_engineer_id: str
    matched_engineer_name: str
    fit_score: float
    generated_proposal_draft: str
    created_at: int
    is_approved_by_sales: bool = False


@dataclass
class AutopilotBatchReport:
    batch_id: str
    processed_emails_count: int
    matched_queue_items_count: int
    average_fit_score: float
    items: List[AutopilotDispatchItem]


class SalesAutopilotEngine:
    def __init__(self) -> None:
        self.dispatch_queue: List[AutopilotDispatchItem] = []

    def run_overnight_batch(
        self,
        incoming_project_emails: List[Dict[str, Any]],
        available_talent_pool: List[Dict[str, Any]]
    ) -> AutopilotBatchReport:
        items = []

        for p in incoming_project_emails:
            req_skills = [s.lower() for s in p.get("skills", ["Python"])]
            
            # Find best talent
            best_match = None
            best_score = 0.0

            for eng in available_talent_pool:
                eng_skills = [s.lower() for s in eng.get("skills", [])]
                overlap = set(req_skills) & set(eng_skills)
                score = 65.0 + (len(overlap) * 15.0)
                score = min(98.0, score)

                if score > best_score and score >= 80.0:
                    best_score = score
                    best_match = eng

            if best_match:
                qid = f"AUTO-Q-{int(time.time())}-{len(items) + 1}"
                draft = (
                    f"【即時ご提案】{p['title']} 向け要員（{best_match['name']}）のご案内\n"
                    f"貴社の「{p['title']}」に対し、適合度 {best_score:.1f}% の即戦力エンジニアをご提案いたします。"
                )

                item = AutopilotDispatchItem(
                    queue_id=qid,
                    project_id=p["id"],
                    project_title=p["title"],
                    client_name=p.get("client_name", "クライアント企業様"),
                    matched_engineer_id=best_match["id"],
                    matched_engineer_name=best_match["name"],
                    fit_score=round(best_score, 1),
                    generated_proposal_draft=draft,
                    created_at=int(time.time()),
                    is_approved_by_sales=False
                )
                items.append(item)
                self.dispatch_queue.append(item)

        avg_score = round(sum(i.fit_score for i in items) / len(items), 1) if items else 0.0

        return AutopilotBatchReport(
            batch_id=f"BATCH-AP-{int(time.time())}",
            processed_emails_count=len(incoming_project_emails),
            matched_queue_items_count=len(items),
            average_fit_score=avg_score,
            items=items
        )
