#!/usr/bin/env python3
"""Talent Retention & Churn Risk Predictor Module (T982 - Action 19).

Early detection of engineer burnout, turnover intent, and contract termination risks
using monthly overtime hours and pulse survey sentiment indicators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RetentionRiskAssessment:
    engineer_id: str
    engineer_name: str
    risk_level: str  # "GREEN_SAFE", "YELLOW_WATCH", "RED_CRITICAL_CHURN"
    churn_probability: float  # 0.0 - 1.0
    risk_factors: List[str]
    recommended_sales_action: str
    is_immediate_action_required: bool


class TalentRetentionPredictor:
    def __init__(self) -> None:
        pass

    def evaluate_risk(
        self,
        engineer_id: str,
        engineer_name: str,
        monthly_overtime_hours: float,
        pulse_survey_score: float,  # 1.0 (lowest) to 5.0 (highest)
        months_at_current_client: int = 6
    ) -> RetentionRiskAssessment:
        factors = []
        churn_prob = 0.10

        # Overtime risk evaluation
        if monthly_overtime_hours >= 45.0:
            factors.append(f"月間残業時間が {monthly_overtime_hours} 時間と過重労働水準に達しています（バーンアウト警戒）。")
            churn_prob += 0.45
        elif monthly_overtime_hours >= 30.0:
            factors.append(f"月間残業時間（{monthly_overtime_hours}h）が増加傾向にあります。")
            churn_prob += 0.20
        elif monthly_overtime_hours < 5.0:
            factors.append("稼働時間が極めて少なく、現場でのアサイン不足・モチベーション低下のリスクがあります。")
            churn_prob += 0.15

        # Sentiment / Pulse score evaluation
        if pulse_survey_score <= 2.0:
            factors.append(f"最新の定例パルスサーベイ満足度が {pulse_survey_score}/5.0 と危険水準に低下しています。")
            churn_prob += 0.40
        elif pulse_survey_score <= 3.0:
            factors.append(f"満足度スコア（{pulse_survey_score}/5.0）が低下傾向にあります。")
            churn_prob += 0.15

        churn_prob = min(0.95, round(churn_prob, 2))

        if churn_prob >= 0.65:
            risk_level = "RED_CRITICAL_CHURN"
            action = "🚨 至急: 担当営業およびカウンセラーによる即時1on1面談を実施し、現場環境改善または案件ローテーションの打診を行ってください。"
            immediate = True
        elif churn_prob >= 0.35:
            risk_level = "YELLOW_WATCH"
            action = "⚠️ 注意: 次回定例面談にて残業状況のヒアリングとフォローを実施してください。"
            immediate = False
        else:
            risk_level = "GREEN_SAFE"
            action = "✅ 良好: 安定稼働中です。定期的な感謝のフィードバックを継続してください。"
            immediate = False

        return RetentionRiskAssessment(
            engineer_id=engineer_id,
            engineer_name=engineer_name,
            risk_level=risk_level,
            churn_probability=churn_prob,
            risk_factors=factors,
            recommended_sales_action=action,
            is_immediate_action_required=immediate
        )
