import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.app import app
from src import structured_ai


@pytest.fixture
def client():
    return TestClient(app)


def test_pydantic_schemas_instantiation():
    proj = structured_ai.ProjectRequirementSchema(
        title="Frontend Developer",
        summary="Vue/React frontend position",
        required_skills=["TypeScript", "React"],
        nice_to_have_skills=["Next.js"],
        rate_min=600000,
        rate_max=800000,
    )
    assert proj.title == "Frontend Developer"
    assert "TypeScript" in proj.required_skills
    assert proj.rate_min == 600000

    talent = structured_ai.TalentProfileSchema(
        title="Full Stack Engineer",
        summary="5 years experience in Python & TS",
        skills=["Python", "TypeScript", "Docker"],
        experience_years=5.0,
        desired_rate=850000,
    )
    assert talent.experience_years == 5.0

    fit = structured_ai.FitEvaluationSchema(
        skill_fit_score=90.0,
        culture_fit_score=85.0,
        growth_fit_score=88.0,
        readiness_score=92.0,
        final_score=88.75,
        summary="High match for backend position",
        strengths=["Strong Python expertise"],
        gaps=["Needs AWS certification"],
        roadmap_week1_4=["Week 1: Setup", "Week 2: Dev"],
    )
    assert fit.final_score == 88.75


def test_generate_mock_structured_data():
    proj_mock = structured_ai.generate_mock_structured_data(structured_ai.ProjectRequirementSchema)
    assert isinstance(proj_mock, structured_ai.ProjectRequirementSchema)
    assert len(proj_mock.required_skills) > 0

    talent_mock = structured_ai.generate_mock_structured_data(structured_ai.TalentProfileSchema)
    assert isinstance(talent_mock, structured_ai.TalentProfileSchema)

    fit_mock = structured_ai.generate_mock_structured_data(structured_ai.FitEvaluationSchema)
    assert isinstance(fit_mock, structured_ai.FitEvaluationSchema)
    assert fit_mock.final_score > 0.0


def test_extract_structured_data_fallback():
    # Without API key, extract_structured_data should safely return deterministic fallback
    res = structured_ai.extract_structured_data(
        prompt="Sample job prompt for Python developer",
        schema_cls=structured_ai.ProjectRequirementSchema,
        api_key=None,
    )
    assert isinstance(res, structured_ai.ProjectRequirementSchema)
    assert res.title != ""


def test_api_extract_structured_endpoint_project(client):
    res = client.post(
        "/api/ai/extract/structured",
        json={"text": "Python FastAPI backend developer needed for Shibuya office", "target_type": "project"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["target_type"] == "project"
    assert "title" in data["data"]


def test_api_extract_structured_endpoint_talent(client):
    res = client.post(
        "/api/ai/extract/structured",
        json={"text": "Senior Python developer with 5 years experience", "target_type": "talent"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["target_type"] == "talent"
    assert "skills" in data["data"]


def test_api_extract_structured_endpoint_fit(client):
    res = client.post(
        "/api/ai/extract/structured",
        json={"text": "Evaluate candidate fit for lead Python backend role", "target_type": "fit"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["target_type"] == "fit"
    assert "final_score" in data["data"]


def test_api_extract_structured_validation_failures(client):
    # Short text
    res1 = client.post("/api/ai/extract/structured", json={"text": "a", "target_type": "project"})
    assert res1.status_code == 400
    assert "at least 3 characters" in res1.json()["detail"]

    # Invalid target type
    res2 = client.post("/api/ai/extract/structured", json={"text": "Valid text prompt", "target_type": "unknown"})
    assert res2.status_code == 400
    assert "must be project, talent, or fit" in res2.json()["detail"]


def test_parse_mikiwame_csv_text():
    csv_sample = """id,ストレス耐性,協調性,統率力,適応力,論理的思考
ENG-01,80,85,65,90,75
ENG-02,70,60,80,65,85
"""
    results = structured_ai.parse_mikiwame_csv_text(csv_sample)
    assert len(results) == 2
    assert results[0].pseudonym_id == "ENG-01"
    assert results[0].stress_tolerance == 80.0
    assert results[0].culture_fit_score > 0.0
    assert "協調性スコア" in results[0].interview_advice

