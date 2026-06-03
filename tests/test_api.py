import os
import sys
import shutil
import pytest

# Ensure src directory is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import app
from fastapi.testclient import TestClient

# Configure app to use isolated testing directory
app.DATA_DIR = os.path.join(PROJECT_ROOT, "data_test")
app.AUDIT_DIR = os.path.join(app.DATA_DIR, "audit")
app.EXTERNAL_API_USAGE_LOG_FILE = os.path.join(app.DATA_DIR, "external_api_usage.jsonl")

# Ensure AI live mode does not run during tests by setting mocks
app.AI_FORCE_MOCK = True
app.GEMINI_READY = False

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Setup clean testing directory
    if os.path.exists(app.DATA_DIR):
        shutil.rmtree(app.DATA_DIR)
    os.makedirs(app.DATA_DIR, exist_ok=True)
    os.makedirs(app.AUDIT_DIR, exist_ok=True)
    
    # Initialize test database
    app.init_db()
    
    yield
    
    # Cleanup after testing completes
    if os.path.exists(app.DATA_DIR):
        shutil.rmtree(app.DATA_DIR)

@pytest.fixture
def client():
    return TestClient(app.app)

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_basic_auth_protection(client):
    # Public route
    response = client.get("/")
    assert response.status_code == 200
    
    # Secure route - /admin
    response = client.get("/admin")
    assert response.status_code == 401
    
    response = client.get("/admin", auth=("wrong_user", "wrong_pass"))
    assert response.status_code == 401
    
    response = client.get("/admin", auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD))
    assert response.status_code == 200

    # Secure route - /api/audit/recent
    response = client.get("/api/audit/recent")
    assert response.status_code == 401

    response = client.get("/api/audit/recent", auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD))
    assert response.status_code == 200

def test_parse_and_database_persistence(client):
    # 1. Parse Engineer Resume
    resume_text = "氏名: 山田太郎\nスキル: Python, FastAPI, SQLite\n目標: フルスタック開発者"
    response = client.post(
        "/api/parse",
        data={"text": resume_text, "doc_type": "engineer"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "db_id" in res_data
    eng_db_id = res_data["db_id"]
    assert eng_db_id > 0

    # 2. Parse Job Description
    job_text = "職種: Pythonエンジニア\n必須要件: Python, Web API開発\n勤務地: リモート"
    response = client.post(
        "/api/parse",
        data={"text": job_text, "doc_type": "job"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "db_id" in res_data
    job_db_id = res_data["db_id"]
    assert job_db_id > 0

    # 3. Verify they are listed via authenticated endpoints
    # Engineers list without auth
    response = client.get("/api/engineers")
    assert response.status_code == 401

    # Engineers list with auth
    response = client.get("/api/engineers", auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD))
    assert response.status_code == 200
    eng_list = response.json()["engineers"]
    assert len(eng_list) > 0
    assert any(eng["id"] == eng_db_id for eng in eng_list)

    # Jobs list with auth
    response = client.get("/api/jobs", auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD))
    assert response.status_code == 200
    job_list = response.json()["jobs"]
    assert len(job_list) > 0
    assert any(job["id"] == job_db_id for job in job_list)

def test_match_and_database_persistence(client):
    engineer_content = "氏名: 山田太郎\nスキル: Python, FastAPI, SQLite"
    job_content = "職種: Pythonエンジニア\n必須要件: Python, Web API開発"
    
    # Evaluate matching
    response = client.post(
        "/api/match",
        json={"engineer_content": engineer_content, "job_content": job_content}
    )
    assert response.status_code == 200
    match_data = response.json()
    assert "db_match_id" in match_data
    db_match_id = match_data["db_match_id"]
    assert db_match_id > 0

    # Verify matching is listed via authenticated endpoint
    response = client.get("/api/matches", auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD))
    assert response.status_code == 200
    matches_list = response.json()["matches"]
    assert len(matches_list) > 0
    assert any(m["id"] == db_match_id for m in matches_list)
