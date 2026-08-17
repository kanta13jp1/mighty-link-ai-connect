import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.yield_pricing_optimizer import YieldPricingOptimizer


def test_yield_pricing_optimizer_premium_skills():
    optimizer = YieldPricingOptimizer()
    res = optimizer.optimize_pricing(
        base_rate_man_yen=80,
        engineer_skills=["AI", "Rust", "Kubernetes"],
        client_budget_max_man_yen=100,
        is_direct_client=True
    )

    assert res.optimal_yield_rate_man_yen >= 85
    assert res.rate_increase_man_yen >= 5
    assert res.estimated_annual_margin_gain_man_yen > 0
    assert res.win_probability_at_optimal_rate >= 0.80
    assert "単価設定の根拠" in res.client_justification_text


def test_yield_pricing_optimizer_budget_cap():
    optimizer = YieldPricingOptimizer()
    res = optimizer.optimize_pricing(
        base_rate_man_yen=75,
        engineer_skills=["Python", "FastAPI"],
        client_budget_max_man_yen=80,
        is_direct_client=False
    )
    assert res.optimal_yield_rate_man_yen <= 80
