import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.placement_velocity_predictor import PlacementVelocityPredictor


def test_placement_velocity_predictor_hot_deal():
    predictor = PlacementVelocityPredictor()
    pred = predictor.predict(
        project_title="【AI/Rust】高頻度取引基盤",
        skills=["Rust", "AI", "Kubernetes"],
        monthly_rate=120,
        is_remote=True
    )

    assert pred.skill_rarity_score >= 85.0
    assert pred.estimated_days_to_fill <= 3.5
    assert pred.urgency_level in ["CRITICAL_IMMEDIATE", "HIGH"]
    assert pred.competition_ratio > 3.0
    assert pred.win_probability >= 0.75


def test_placement_velocity_predictor_standard_deal():
    predictor = PlacementVelocityPredictor()
    pred = predictor.predict(
        project_title="【PHP】ECサイト改修",
        skills=["PHP"],
        monthly_rate=65,
        is_remote=False
    )

    assert pred.urgency_level in ["NORMAL", "HIGH"]
    assert pred.estimated_days_to_fill >= 2.0
