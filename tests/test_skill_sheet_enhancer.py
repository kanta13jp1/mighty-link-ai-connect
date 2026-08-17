import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.skill_sheet_enhancer import SkillSheetEnhancer


def test_skill_sheet_enhancer():
    enhancer = SkillSheetEnhancer()
    res = enhancer.enhance_profile(
        engineer_skills=["Python", "FastAPI", "AWS"],
        raw_self_pr="Pythonでのバックエンド開発経験が3年あります。"
    )

    assert "定量的実績" in res.enhanced_self_pr
    assert res.impact_score_improvement > 0
    assert len(res.key_enhancement_points) >= 3
    assert len(res.recommended_upskill_technologies) >= 2
    assert any("FastAPI" in rec["tech"] for rec in res.recommended_upskill_technologies)
