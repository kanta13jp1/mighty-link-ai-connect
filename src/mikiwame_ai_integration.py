"""Mikiwame AI Integration & Multi-Dimensional Compatibility Module (T963)."""

from typing import Any, Dict, List, Optional

def calculate_multidimensional_score(
    skill_score: float,
    mikiwame_trait_type: str,
    stress_tolerance_level: int,  # 1 (low) to 5 (high)
    workplace_environment_type: str  # e.g., 'startup_fast_paced', 'enterprise_stable', 'remote_autonomous'
) -> Dict[str, Any]:
    """Calculate multi-dimensional compatibility combining skill score & Mikiwame personality traits."""
    # Compatibility matrix between personality and workplace environment
    trait_env_compatibility = {
        ("探求・自律型", "startup_fast_paced"): 95.0,
        ("探求・自律型", "remote_autonomous"): 90.0,
        ("探求・自律型", "enterprise_stable"): 75.0,
        ("協調・サポーター型", "enterprise_stable"): 95.0,
        ("協調・サポーター型", "startup_fast_paced"): 70.0,
        ("協調・サポーター型", "remote_autonomous"): 80.0,
        ("推進・リーダー型", "startup_fast_paced"): 90.0,
        ("推進・リーダー型", "enterprise_stable"): 85.0,
        ("推進・リーダー型", "remote_autonomous"): 85.0,
    }

    env_match_score = trait_env_compatibility.get(
        (mikiwame_trait_type, workplace_environment_type),
        80.0
    )

    # Stress tolerance adjustment factor
    stress_bonus = (stress_tolerance_level - 3) * 3.0  # -6 to +6

    aptitude_score = max(0.0, min(100.0, env_match_score + stress_bonus))

    # Total composite score: 60% Technical Skills + 40% Aptitude / Team Synergy
    composite_score = (skill_score * 0.6) + (aptitude_score * 0.4)

    # Interview & onboarding advice based on traits
    advice = ""
    if mikiwame_trait_type == "探求・自律型":
        advice = "裁量を持たせたタスクアサインと、自発的なアーキテクチャ提案を促すことで最大のパフォーマンスを発揮します。"
    elif mikiwame_trait_type == "協調・サポーター型":
        advice = "チーム内の定期1on1やペアプログラミング環境を提供し、心理的安全性を確保することで高い定着率を実現します。"
    else:
        advice = "目標ゴールを明確に提示し、マイルストーンごとの達成度を評価することで推進力を最大化できます。"

    return {
        "composite_score": round(composite_score, 1),
        "skill_score": round(skill_score, 1),
        "aptitude_score": round(aptitude_score, 1),
        "mikiwame_trait_type": mikiwame_trait_type,
        "stress_tolerance_level": stress_tolerance_level,
        "workplace_environment_type": workplace_environment_type,
        "team_synergy_advice": advice,
        "tier_unlocked": "Pro / Enterprise"
    }
