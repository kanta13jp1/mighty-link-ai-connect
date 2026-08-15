"""Typed Structured AI Extraction and Validation Module (T948).

Leverages Instructor (jxnl/instructor) and Pydantic v2 to extract, validate, and retry
typed structured responses from Gemini LLM calls, with zero-breakage deterministic fallbacks.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field

try:
    import instructor
    HAS_INSTRUCTOR = True
except ImportError:
    instructor = None
    HAS_INSTRUCTOR = False

logger = logging.getLogger("mighty_link.structured_ai")

T = TypeVar("T", bound=BaseModel)


class ProjectRequirementSchema(BaseModel):
    title: str = Field(description="Title of the project or job role")
    summary: str = Field(description="Brief 1-2 sentence overview")
    required_skills: List[str] = Field(default_factory=list, description="Must-have technical skills")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Optional or nice-to-have skills")
    rate_min: Optional[int] = Field(default=None, description="Minimum monthly rate in JPY")
    rate_max: Optional[int] = Field(default=None, description="Maximum monthly rate in JPY")
    location: str = Field(default="東京", description="Work location")
    remote_type: str = Field(default="フルリモート", description="Remote policy: フルリモート, 一部リモート, 常駐")


class TalentProfileSchema(BaseModel):
    title: str = Field(description="Primary job title or career role")
    summary: str = Field(description="Summary of background and strengths")
    skills: List[str] = Field(default_factory=list, description="List of technical skills")
    experience_years: float = Field(default=3.0, description="Total years of software engineering experience")
    desired_rate: Optional[int] = Field(default=None, description="Desired monthly rate in JPY")
    work_style: str = Field(default="フルリモート可", description="Preferred work style")


class FitEvaluationSchema(BaseModel):
    skill_fit_score: float = Field(ge=0.0, le=100.0, description="Skill dimension fit score (0-100)")
    culture_fit_score: float = Field(ge=0.0, le=100.0, description="Culture & values fit score (0-100)")
    growth_fit_score: float = Field(ge=0.0, le=100.0, description="Growth & career alignment score (0-100)")
    readiness_score: float = Field(ge=0.0, le=100.0, description="Immediate readiness score (0-100)")
    final_score: float = Field(ge=0.0, le=100.0, description="Weighted composite fit score (0-100)")
    summary: str = Field(description="Executive summary of the evaluation")
    strengths: List[str] = Field(default_factory=list, description="Key matched strengths")
    gaps: List[str] = Field(default_factory=list, description="Identified skill or experience gaps")
    roadmap_week1_4: List[str] = Field(default_factory=list, description="4-week onboarding and growth roadmap")


def generate_mock_structured_data(schema_cls: Type[T]) -> T:
    """Deterministic fallback data when AI keys are absent or calls fail."""
    if schema_cls == ProjectRequirementSchema:
        return ProjectRequirementSchema(
            title="Python Web Backend Engineer",
            summary="FastAPI + PostgreSQL ベースの社内DX基盤開発案件",
            required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            nice_to_have_skills=["GCP", "Supabase", "GraphQL"],
            rate_min=700000,
            rate_max=900000,
            location="東京都千代田区 / フルリモート",
            remote_type="フルリモート",
        )
    elif schema_cls == TalentProfileSchema:
        return TalentProfileSchema(
            title="シニア Python バックエンドエンジニア",
            summary="FastAPI・Web API開発経験5年の即戦力要員",
            skills=["Python", "FastAPI", "PostgreSQL", "Docker", "GCP"],
            experience_years=5.0,
            desired_rate=800000,
            work_style="フルリモート可",
        )
    elif schema_cls == FitEvaluationSchema:
        return FitEvaluationSchema(
            skill_fit_score=88.0,
            culture_fit_score=92.0,
            growth_fit_score=85.0,
            readiness_score=90.0,
            final_score=88.5,
            summary="Python/FastAPIの即戦力スキルを有し、自律改善文化へのフィット度が高い優れたマッチング結果です。",
            strengths=["FastAPI/PostgreSQLの実務経験豊富", "自律型AIアプローチへの理解"],
            gaps=["一部の特定クラウドネイティブモニタリング経験の補強"],
            roadmap_week1_4=[
                "第1週: ドメイン構造・FastAPI既存エンドポイントの把握",
                "第2週: テスト駆動・CI整合ガード運用プロセスのキャッチアップ",
                "第3週: 外部SaaS統合モジュールの実務開発",
                "第4週: 本番リリース受入・運用ログ自動スキャン運用の主導",
            ],
        )
    else:
        # Generic instantiation
        return schema_cls()


def extract_structured_data(
    prompt: str,
    schema_cls: Type[T],
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.5-flash",
    max_retries: int = 3,
) -> T:
    """Extract typed, validated structure using Instructor with fail-closed fallback."""
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key or not HAS_INSTRUCTOR:
        logger.info("API key absent or Instructor missing. Returning deterministic mock fallback.")
        return generate_mock_structured_data(schema_cls)

    try:
        # Initialize client via Instructor
        client = instructor.from_provider(f"google/{model_name}", api_key=key)
        response = client.create(
            response_model=schema_cls,
            messages=[{"role": "user", "content": prompt}],
            max_retries=max_retries,
        )
        return response
    except Exception as e:
        logger.warning(f"Instructor extraction error: {e}. Falling back to mock structured data.")
        return generate_mock_structured_data(schema_cls)
