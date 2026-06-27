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

def test_app_uses_lifespan_without_deprecated_startup_handlers():
    assert getattr(app.app.router, "on_startup", []) == []
    assert getattr(app.app.router, "lifespan_context", None) is not None

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_rate_limit_exempts_health_and_blocks_expensive_api():
    original_settings = (
        app.RATE_LIMIT_ENABLED,
        app.RATE_LIMIT_WINDOW_SECONDS,
        app.RATE_LIMIT_EXPENSIVE_MAX_REQUESTS,
    )
    app.RATE_LIMIT_ENABLED = True
    app.RATE_LIMIT_WINDOW_SECONDS = 60
    app.RATE_LIMIT_EXPENSIVE_MAX_REQUESTS = 2
    app.api_rate_limiter.reset()

    try:
        with TestClient(app.app) as local_client:
            for _ in range(4):
                assert local_client.get("/api/health").status_code == 200

            payload = {"prompt": "Mighty-Link rate limit smoke test"}
            assert local_client.post("/api/seedance/video-demo", json=payload).status_code == 200
            allowed_response = local_client.post("/api/seedance/video-demo", json=payload)
            assert allowed_response.status_code == 200
            assert allowed_response.headers["X-RateLimit-Limit"] == "2"
            assert allowed_response.headers["X-RateLimit-Remaining"] == "0"

            blocked_response = local_client.post("/api/seedance/video-demo", json=payload)
            assert blocked_response.status_code == 429
            assert blocked_response.headers["Retry-After"]
            assert blocked_response.json()["rate_limit"]["rule"] == "expensive_api"
    finally:
        (
            app.RATE_LIMIT_ENABLED,
            app.RATE_LIMIT_WINDOW_SECONDS,
            app.RATE_LIMIT_EXPENSIVE_MAX_REQUESTS,
        ) = original_settings
        app.api_rate_limiter.reset()

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

    # 3. Verify they are listed (read-only list endpoints allow unauthenticated access)
    # Engineers list without auth (optional auth endpoint: 200)
    response = client.get("/api/engineers")
    assert response.status_code == 200
    eng_list = response.json()["engineers"]
    assert len(eng_list) > 0
    assert any(eng["id"] == eng_db_id for eng in eng_list)

    # Engineers list with auth also works
    response = client.get("/api/engineers", auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD))
    assert response.status_code == 200

    # Jobs list without auth (optional auth endpoint: 200)
    response = client.get("/api/jobs")
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


def test_feedback_submission_and_summary(client):
    engineer_content = "Name: Feedback User\nSkills: Python, FastAPI, Supabase"
    job_content = "Role: Backend Engineer\nRequirements: Python, API development"

    match_response = client.post(
        "/api/match",
        json={"engineer_content": engineer_content, "job_content": job_content},
    )
    assert match_response.status_code == 200
    db_match_id = match_response.json()["db_match_id"]
    assert db_match_id > 0

    feedback_response = client.post(
        "/api/feedback",
        json={
            "match_id": db_match_id,
            "rating": "helpful",
            "nps_score": 9,
            "comment": "Clear score rationale and useful next actions.",
            "source": "diagnosis_report",
            "page_url": "/",
            "session_id": "test-session",
        },
    )
    assert feedback_response.status_code == 200
    assert feedback_response.json()["status"] == "success"
    assert feedback_response.json()["feedback_id"] > 0

    invalid_response = client.post(
        "/api/feedback",
        json={"match_id": db_match_id, "rating": "helpful", "nps_score": 11},
    )
    assert invalid_response.status_code == 400

    unauthorized_summary = client.get("/api/feedback/summary")
    assert unauthorized_summary.status_code == 401

    summary_response = client.get(
        "/api/feedback/summary",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["status"] == "success"
    assert summary["total"] >= 1
    assert summary["rating_counts"]["helpful"] >= 1
    assert summary["nps"]["average"] >= 9
    assert any(item["match_result_id"] == db_match_id for item in summary["recent"])


def test_employee_assessment_response_submission_summary_and_redaction(client):
    response = client.post(
        "/api/employee-assessment/responses",
        json={
            "employee_identifier": "emp-001-yamada",
            "department": "開発本部",
            "motivation_level": 4,
            "culture_level": 5,
            "growth_feedback": (
                "FastAPIの設計レビュー支援が必要です。連絡先 test@example.test、"
                "電話 090-1234-5678、token=secret-value は保存時に消してください。"
            ),
            "consented": True,
            "source": "employee_assessment_form",
            "page_url": "/",
            "session_id": "employee-assessment-test-session",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["response_id"] > 0
    assert data["subject_pseudonym"].startswith("emp-assess-")
    assert "emp-001-yamada" not in data["subject_pseudonym"]
    assert data["privacy_controls"]["raw_identifier_stored"] is False
    assert data["privacy_controls"]["sensitive_text_redacted"] is True

    missing_consent = client.post(
        "/api/employee-assessment/responses",
        json={
            "employee_identifier": "emp-002",
            "department": "営業本部",
            "motivation_level": 3,
            "culture_level": 3,
            "growth_feedback": "同意なしの送信は保存されないことを確認します。",
            "consented": False,
        },
    )
    assert missing_consent.status_code == 400

    invalid_score = client.post(
        "/api/employee-assessment/responses",
        json={
            "employee_identifier": "emp-003",
            "department": "営業本部",
            "motivation_level": 6,
            "culture_level": 3,
            "growth_feedback": "範囲外スコアは保存されないことを確認します。",
            "consented": True,
        },
    )
    assert invalid_score.status_code == 400

    unauthorized_summary = client.get("/api/employee-assessment/responses/summary")
    assert unauthorized_summary.status_code == 401

    summary_response = client.get(
        "/api/employee-assessment/responses/summary",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["status"] == "success"
    assert summary["total"] >= 1
    assert summary["averages"]["motivation_level"] >= 4
    assert summary["department_counts"]["開発本部"] >= 1
    assert summary["privacy_controls"]["raw_identifier_stored"] is False
    recent = summary["recent"][0]
    serialized = str(summary)
    assert "emp-001-yamada" not in serialized
    assert "test@example.test" not in serialized
    assert "090-1234-5678" not in serialized
    assert "token=secret-value" not in serialized
    assert "<email:redacted>" in recent["growth_support_excerpt"]
    assert "<phone:redacted>" in recent["growth_support_excerpt"]
    assert "<secret:redacted>" in recent["growth_support_excerpt"]


def test_attendance_punch_timesheet_parse_approval_and_summary(client):
    punch_response = client.post(
        "/api/attendance/punch",
        json={
            "employee_identifier": "emp-004-attendance",
            "event_type": "in",
            "consented": True,
            "source": "attendance_widget",
            "page_url": "/",
            "session_id": "attendance-test-session",
        },
    )
    assert punch_response.status_code == 200
    punch_data = punch_response.json()
    assert punch_data["status"] == "success"
    assert punch_data["punch_id"] > 0
    assert punch_data["event_type"] == "clock_in"
    assert punch_data["subject_pseudonym"].startswith("att-")
    assert "emp-004-attendance" not in punch_data["subject_pseudonym"]

    missing_consent = client.post(
        "/api/attendance/punch",
        json={"employee_identifier": "emp-004", "event_type": "out", "consented": False},
    )
    assert missing_consent.status_code == 400

    invalid_event = client.post(
        "/api/attendance/punch",
        json={"employee_identifier": "emp-004", "event_type": "vacation", "consented": True},
    )
    assert invalid_event.status_code == 400

    csv_payload = (
        "date,work_hours,overtime_hours,midnight_hours,holiday_work,anomaly\n"
        "2026-06-01,8.0,1.5,0,0,なし\n"
        "2026-06-02,9.0,2.0,0.5,1,打刻漏れ\n"
    ).encode("utf-8")
    parse_response = client.post(
        "/api/attendance/timesheet/parse",
        data={
            "employee_identifier": "emp-004-attendance",
            "consented": "true",
            "consent_version": "MSB-ATTENDANCE-2026-06",
            "source": "attendance_timesheet_upload",
            "page_url": "/",
            "session_id": "attendance-test-session",
        },
        files={"file": ("timesheet-yamada.csv", csv_payload, "text/csv")},
    )
    assert parse_response.status_code == 200
    parse_data = parse_response.json()
    assert parse_data["status"] == "success"
    assert parse_data["import_id"] > 0
    assert parse_data["approval_status"] == "pending_approval"
    assert parse_data["summary"]["work_hours"] == 17.0
    assert parse_data["summary"]["overtime_hours"] == 3.5
    assert parse_data["summary"]["midnight_hours"] == 0.5
    assert parse_data["summary"]["holiday_work_days"] == 1
    assert parse_data["summary"]["anomaly_count"] == 1
    serialized_parse = str(parse_data)
    assert "emp-004-attendance" not in serialized_parse
    assert "timesheet-yamada.csv" not in serialized_parse
    assert parse_data["privacy_controls"]["raw_file_stored"] is False
    assert parse_data["privacy_controls"]["original_filename_stored"] is False

    unauthorized_approval = client.post(
        "/api/attendance/timesheet/approve",
        json={"import_id": parse_data["import_id"], "decision": "approved"},
    )
    assert unauthorized_approval.status_code == 401

    approval_response = client.post(
        "/api/attendance/timesheet/approve",
        json={"import_id": parse_data["import_id"], "decision": "approved"},
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert approval_response.status_code == 200
    approval_data = approval_response.json()
    assert approval_data["status"] == "success"
    assert approval_data["attendance_import"]["status"] == "approved"
    assert approval_data["attendance_import"]["summary"]["overtime_hours"] == 3.5

    unauthorized_summary = client.get("/api/attendance/summary")
    assert unauthorized_summary.status_code == 401

    summary_response = client.get(
        "/api/attendance/summary",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["status"] == "success"
    assert summary["punch_total"] >= 1
    assert summary["import_total"] >= 1
    assert summary["status_counts"]["approved"] >= 1
    assert summary["privacy_controls"]["raw_identifier_stored"] is False
    assert summary["privacy_controls"]["raw_file_stored"] is False
    assert "emp-004-attendance" not in str(summary)
    assert "timesheet-yamada.csv" not in str(summary)


def test_admin_operations_dashboard_requires_auth_aggregates_and_exports_csv(client):
    assessment_response = client.post(
        "/api/employee-assessment/responses",
        json={
            "employee_identifier": "emp-dashboard-001",
            "department": "operations",
            "motivation_level": 5,
            "culture_level": 4,
            "growth_feedback": "Dashboard aggregation smoke test with no raw identifier exposure.",
            "consented": True,
            "source": "employee_assessment_form",
            "page_url": "/",
            "session_id": "dashboard-test-session",
        },
    )
    assert assessment_response.status_code == 200

    csv_payload = (
        "date,work_hours,overtime_hours,midnight_hours,holiday_work,anomaly\n"
        "2026-06-03,8.0,2.0,0,0,\n"
    ).encode("utf-8")
    parse_response = client.post(
        "/api/attendance/timesheet/parse",
        data={
            "employee_identifier": "emp-dashboard-001",
            "consented": "true",
            "source": "attendance_timesheet_upload",
            "page_url": "/",
            "session_id": "dashboard-test-session",
        },
        files={"file": ("dashboard-timesheet.csv", csv_payload, "text/csv")},
    )
    assert parse_response.status_code == 200
    import_id = parse_response.json()["import_id"]
    approval_response = client.post(
        "/api/attendance/timesheet/approve",
        json={"import_id": import_id, "decision": "approved"},
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert approval_response.status_code == 200

    unauthorized = client.get("/api/admin/operations-dashboard")
    assert unauthorized.status_code == 401
    unauthorized_csv = client.get("/api/admin/operations-dashboard/report.csv")
    assert unauthorized_csv.status_code == 401

    response = client.get(
        "/api/admin/operations-dashboard",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["wbs_task"] == "T842"
    assert payload["security"]["admin_summary_requires_basic_auth"] is True
    assert payload["security"]["report_export_requires_basic_auth"] is True
    assert payload["security"]["raw_identifiers_excluded"] is True
    assert payload["kpis"]["employee_assessment_responses"] >= 1
    assert payload["kpis"]["attendance_timesheet_imports"] >= 1
    assert "employee_assessment" in payload["sources"]
    assert "attendance" in payload["sources"]
    assert "sales_email_review" in payload["sources"]
    assert "emp-dashboard-001" not in str(payload)
    assert "dashboard-timesheet.csv" not in str(payload)

    csv_response = client.get(
        "/api/admin/operations-dashboard/report.csv",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    csv_text = csv_response.text
    assert "employee_assessment,responses" in csv_text
    assert "attendance,timesheet_imports" in csv_text
    assert "sales_email_review,reviews" in csv_text
    assert "raw_identifiers_excluded,True" in csv_text
    assert "emp-dashboard-001" not in csv_text
    assert "dashboard-timesheet.csv" not in csv_text


def test_support_request_submission_and_summary(client):
    support_response = client.post(
        "/api/support/request",
        json={
            "category": "technical",
            "contact_email": "support-user@example.test",
            "subject": "診断結果が送信できない",
            "message": "診断結果画面から問い合わせを送信したいが、送信ボタンが反応しません。",
            "source": "support_form",
            "page_url": "/",
            "session_id": "support-test-session",
        },
    )
    assert support_response.status_code == 200
    support_data = support_response.json()
    assert support_data["status"] == "success"
    assert support_data["support_request_id"] > 0
    assert support_data["priority"] == "high"

    invalid_email_response = client.post(
        "/api/support/request",
        json={
            "category": "general",
            "contact_email": "not-an-email",
            "subject": "問い合わせ",
            "message": "問い合わせ本文の最小文字数を満たしています。",
        },
    )
    assert invalid_email_response.status_code == 400

    invalid_message_response = client.post(
        "/api/support/request",
        json={
            "category": "general",
            "contact_email": "support-user@example.test",
            "subject": "短い本文",
            "message": "短い",
        },
    )
    assert invalid_message_response.status_code == 400

    unauthorized_summary = client.get("/api/support/summary")
    assert unauthorized_summary.status_code == 401

    summary_response = client.get(
        "/api/support/summary",
        auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["status"] == "success"
    assert summary["total"] >= 1
    assert summary["category_counts"]["technical"] >= 1
    assert summary["priority_counts"]["high"] >= 1
    assert any(item["contact_email"] == "support-user@example.test" for item in summary["recent"])
