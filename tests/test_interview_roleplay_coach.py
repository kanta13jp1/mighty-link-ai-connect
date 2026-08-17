import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.interview_roleplay_coach import InterviewRoleplayCoach


def test_interview_roleplay_coach_prep():
    coach = InterviewRoleplayCoach()
    pkg = coach.generate_prep_package("FastAPI AI基盤開発", ["FastAPI", "Python", "AWS"])

    assert len(pkg.technical_questions) >= 2
    assert len(pkg.killer_reverse_questions) >= 3
    assert "FastAPI" in pkg.technical_questions[0]["question"]


def test_interview_roleplay_coach_evaluation():
    coach = InterviewRoleplayCoach()
    q = "FastAPIのパフォーマンス改善で工夫した点を教えてください。"
    ans = "前職プロジェクトでSQLAlchemyのN+1問題を特定し、joinedloadによるクエリ最適化を実施した経験があります。これによりAPI応答速度を45%改善しました。"

    res = coach.evaluate_engineer_answer(q, ans)
    assert res.score >= 85
    assert len(res.strengths) >= 1
    assert "joinedload" in res.engineer_answer or "N+1" in res.engineer_answer
