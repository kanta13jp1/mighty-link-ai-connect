#!/usr/bin/env python3
"""Placement Velocity & Competition Predictor Module (T974 - Action 15).

Predicts deal closure velocity (estimated days to fill) and applicant competition ratio
to optimize sales proposal urgency and pipeline conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VelocityPrediction:
    project_title: str
    estimated_days_to_fill: float  # e.g., 3.2 days
    competition_ratio: float      # e.g., 4.5x candidates per seat
    skill_rarity_score: float     # 1-100 (100 = rarest)
    urgency_level: str            # "CRITICAL_IMMEDIATE", "HIGH", "NORMAL", "LOW"
    recommended_action: str
    win_probability: float        # 0.0 - 1.0


class PlacementVelocityPredictor:
    def __init__(self) -> None:
        self.rarity_map = {
            "ai": 92.0, "agent": 95.0, "fastapi": 85.0, "kubernetes": 88.0, "go": 84.0,
            "rust": 96.0, "next.js": 78.0, "typescript": 72.0, "python": 75.0,
            "java": 60.0, "php": 55.0, "aws": 70.0
        }

    def predict(
        self,
        project_title: str,
        skills: List[str],
        monthly_rate: int,
        is_remote: bool = True
    ) -> VelocityPrediction:
        # Calculate skill rarity
        rarity_scores = [self.rarity_map.get(s.lower(), 65.0) for s in skills]
        rarity = sum(rarity_scores) / len(rarity_scores) if rarity_scores else 65.0

        # High rarity or high rate attracts fast closing
        rate_factor = min(1.3, max(0.8, monthly_rate / 80.0))
        
        # High rarity + high rate = high competition
        competition = round((rarity / 20.0) * rate_factor, 1)
        
        # Estimated days to fill (Hot skills close within 2-4 days)
        base_days = 7.0 - (rarity / 25.0)
        est_days = max(1.5, round(base_days * (0.85 if is_remote else 1.15), 1))

        if est_days <= 3.0:
            urgency = "CRITICAL_IMMEDIATE"
            rec = "🔥 激戦案件: 24時間以内の即時打診・提案送信を強く推奨します。"
            win_prob = 0.88
        elif est_days <= 5.0:
            urgency = "HIGH"
            rec = "⚡ 有力案件: 48時間以内の書類送付および面談日程調整を推奨。"
            win_prob = 0.76
        else:
            urgency = "NORMAL"
            rec = "標準案件: 通常プロセスでの提案・要員選定で充足可能です。"
            win_prob = 0.65

        return VelocityPrediction(
            project_title=project_title,
            estimated_days_to_fill=est_days,
            competition_ratio=competition,
            skill_rarity_score=round(rarity, 1),
            urgency_level=urgency,
            recommended_action=rec,
            win_probability=win_prob,
        )
