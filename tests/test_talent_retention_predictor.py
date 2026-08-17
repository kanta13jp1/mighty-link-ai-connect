import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.talent_retention_predictor import TalentRetentionPredictor


def test_talent_retention_predictor_safe():
    predictor = TalentRetentionPredictor()
    res = predictor.evaluate_risk(
        engineer_id="ENG-01",
        engineer_name="田中 太郎",
        monthly_overtime_hours=15.0,
        pulse_survey_score=4.5
    )

    assert res.risk_level == "GREEN_SAFE"
    assert res.churn_probability <= 0.30
    assert res.is_immediate_action_required is False


def test_talent_retention_predictor_critical():
    predictor = TalentRetentionPredictor()
    res = predictor.evaluate_risk(
        engineer_id="ENG-02",
        engineer_name="山田 花子",
        monthly_overtime_hours=55.0,
        pulse_survey_score=1.5
    )

    assert res.risk_level == "RED_CRITICAL_CHURN"
    assert res.churn_probability >= 0.65
    assert res.is_immediate_action_required is True
    assert len(res.risk_factors) >= 2
    assert "至急" in res.recommended_sales_action
