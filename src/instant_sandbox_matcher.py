"""LP Instant Sandbox Matcher & PLG Simulator Module (T969)."""

from typing import Any, Dict, List

ANONYMOUS_JOB_POOL = [
    {
        "job_id": "anon_job_001",
        "title_masked": "【大手プライム】Python / FastAPI バックエンド開発（フルリモート）",
        "rate_range": "80〜95万円/月",
        "required_skills": ["Python", "FastAPI", "AWS"],
        "match_features": "フルリモート、フレックスタイム、モダンスタック"
    },
    {
        "job_id": "anon_job_002",
        "title_masked": "【自社AIサービス】Go / TypeScript マイクロサービス刷新案件",
        "rate_range": "85〜100万円/月",
        "required_skills": ["Go", "TypeScript", "Docker"],
        "match_features": "上場企業直受け、週1出社相談、高単価"
    },
    {
        "job_id": "anon_job_003",
        "title_masked": "【DX推進】React / Next.js フロントエンドアーキテクチャ設計",
        "rate_range": "75〜90万円/月",
        "required_skills": ["React", "Next.js", "TypeScript"],
        "match_features": "私服勤務、私用PC選択可、チーム開発"
    }
]

def simulate_instant_sandbox_match(
    input_skills: List[str],
    desired_rate: int = 80
) -> Dict[str, Any]:
    """Simulate instant job matching for unauthenticated LP visitors."""
    matched_results = []
    input_skills_lower = [s.lower() for s in input_skills]

    for job in ANONYMOUS_JOB_POOL:
        job_skills = [s.lower() for s in job["required_skills"]]
        common = set(input_skills_lower) & set(job_skills)
        score = 70.0 + (len(common) * 12.0)
        score = min(98.0, score)

        matched_results.append({
            "job_id": job["job_id"],
            "title_masked": job["title_masked"],
            "rate_range": job["rate_range"],
            "match_score": round(score, 1),
            "match_skills": [s for s in job["required_skills"] if s.lower() in input_skills_lower],
            "features": job["match_features"]
        })

    matched_results.sort(key=lambda x: x["match_score"], reverse=True)

    estimated_market_rate = max(desired_rate, 75) + 5

    return {
        "status": "success",
        "input_skills": input_skills,
        "estimated_market_rate_man_yen": estimated_market_rate,
        "matched_jobs_count": len(matched_results),
        "top_matched_jobs": matched_results[:3],
        "cta_message": "無料登録で実社名・全案件詳細の閲覧とワンクリック提案文生成が利用可能です。"
    }
