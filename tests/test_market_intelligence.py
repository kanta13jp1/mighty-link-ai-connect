"""Test suite for Market Intelligence module (T967)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from market_intelligence import calculate_market_skill_insights

def test_calculate_market_skill_insights_basic():
    sample_emails = [
        {"skills": ["Go", "AWS"], "rate_man_yen": 90},
        {"skills": ["Python", "FastAPI"], "rate_man_yen": 85},
        {"skills": ["Java", "Spring"], "rate_man_yen": 75}
    ]
    res = calculate_market_skill_insights(sample_emails)
    assert res["tier_access"] == "Pro / Enterprise Only"
    assert len(res["market_skill_rankings"]) >= 4
    assert res["highest_paying_skill"] in ["Go", "Python", "AWS"]
    assert res["highest_average_rate"] >= 80.0
