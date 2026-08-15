"""Test suite for Mikiwame AI Integration & Multi-Dimensional Compatibility (T963)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from mikiwame_ai_integration import calculate_multidimensional_score

def test_calculate_multidimensional_score_high_fit():
    res = calculate_multidimensional_score(
        skill_score=90.0,
        mikiwame_trait_type="探求・自律型",
        stress_tolerance_level=4,
        workplace_environment_type="startup_fast_paced"
    )
    assert res["tier_unlocked"] == "Pro / Enterprise"
    assert res["composite_score"] >= 88.0
    assert "自発的なアーキテクチャ提案" in res["team_synergy_advice"]

def test_calculate_multidimensional_score_enterprise_fit():
    res = calculate_multidimensional_score(
        skill_score=85.0,
        mikiwame_trait_type="協調・サポーター型",
        stress_tolerance_level=3,
        workplace_environment_type="enterprise_stable"
    )
    assert res["aptitude_score"] == 95.0
    assert "心理的安全性を確保" in res["team_synergy_advice"]
    # 85*0.6 + 95*0.4 = 51.0 + 38.0 = 89.0
    assert res["composite_score"] == 89.0
