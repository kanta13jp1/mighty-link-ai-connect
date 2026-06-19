import json
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import app  # noqa: E402
import sales_email_extract as extract  # noqa: E402
import sales_email_ingest as ingest  # noqa: E402
import sales_email_match as match  # noqa: E402
import sales_email_review as review  # noqa: E402


def sample_match_report() -> dict:
    emails = ingest.load_sales_emails([PROJECT_ROOT / "data" / "samples" / "sales_emails"])
    extraction_report = extract.build_extraction_report(emails)
    return match.build_match_report(extraction_report, match.criteria_from_values(limit=10))


def write_sample_extraction_report(path: Path) -> dict:
    emails = ingest.load_sales_emails([PROJECT_ROOT / "data" / "samples" / "sales_emails"])
    extraction_report = extract.build_extraction_report(emails)
    extract.write_json_report(extraction_report, path)
    return extraction_report


def test_sales_email_review_cli_outputs_redacted_feedback(tmp_path):
    match_report_path = tmp_path / "match.json"
    review_json_path = tmp_path / "review.json"
    review_md_path = tmp_path / "review.md"
    match_report_path.write_text(json.dumps(sample_match_report(), ensure_ascii=False), encoding="utf-8")

    exit_code = review.main(
        [
            "--match-report",
            str(match_report_path),
            "--json-report",
            str(review_json_path),
            "--markdown-report",
            str(review_md_path),
            "--feedback-status",
            "corrected",
            "--corrected-score",
            "40",
            "--notes",
            "候補はOracle不足。連絡先 candidate@example.com / 090-1234-5678 token=abc123 は保存しない。",
            "--next-action",
            "Oracle経験の追加確認後に再判定",
            "--replace",
        ]
    )

    assert exit_code == 0
    payload = review_json_path.read_text(encoding="utf-8")
    markdown = review_md_path.read_text(encoding="utf-8")
    assert "corrected" in payload
    assert "<email:redacted>" in payload
    assert "<phone:redacted>" in payload
    assert "<secret:redacted>" in payload
    assert "candidate@example.com" not in payload
    assert "090-1234-5678" not in payload
    assert "token=abc123" not in payload
    assert "candidate@example.com" not in markdown
    parsed = json.loads(payload)
    assert parsed["generated_at"].startswith("20")
    assert "<phone:redacted>" not in parsed["generated_at"]
    assert parsed["reviews"][0]["match_key"].startswith("match_")
    assert "<phone:redacted>" not in parsed["reviews"][0]["match_key"]


def test_sales_email_review_api_requires_auth_and_persists_feedback(tmp_path):
    extraction_path = tmp_path / "extraction.json"
    review_json_path = tmp_path / "review-log.json"
    review_md_path = tmp_path / "review-log.md"
    data_dir = tmp_path / "data"
    audit_dir = data_dir / "audit"
    write_sample_extraction_report(extraction_path)
    report = match.build_match_report_from_file(extraction_path, match.criteria_from_values(limit=10))
    row = report["matches"][0]

    old_values = {
        "DATA_DIR": app.DATA_DIR,
        "AUDIT_DIR": app.AUDIT_DIR,
        "AUDIT_LOG_FILE": app.AUDIT_LOG_FILE,
        "SALES_EMAIL_MATCH_REPORT_FILE": app.SALES_EMAIL_MATCH_REPORT_FILE,
        "SALES_EMAIL_REVIEW_LOG_FILE": app.SALES_EMAIL_REVIEW_LOG_FILE,
        "SALES_EMAIL_REVIEW_MARKDOWN_FILE": app.SALES_EMAIL_REVIEW_MARKDOWN_FILE,
        "USE_SUPABASE": app.USE_SUPABASE,
        "DATABASE_URL": app.DATABASE_URL,
        "SUPABASE_SDK_ACTIVE": app.SUPABASE_SDK_ACTIVE,
    }
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True)
    audit_dir.mkdir(parents=True)

    app.DATA_DIR = str(data_dir)
    app.AUDIT_DIR = str(audit_dir)
    app.AUDIT_LOG_FILE = str(audit_dir / "ai_audit.jsonl")
    app.SALES_EMAIL_MATCH_REPORT_FILE = str(extraction_path)
    app.SALES_EMAIL_REVIEW_LOG_FILE = str(review_json_path)
    app.SALES_EMAIL_REVIEW_MARKDOWN_FILE = str(review_md_path)
    app.USE_SUPABASE = False
    app.DATABASE_URL = ""
    app.SUPABASE_SDK_ACTIVE = False
    app.init_db()

    try:
        client = TestClient(app.app)
        unauthorized = client.post(
            "/api/sales-email/reviews",
            json={
                "match_key": review.match_key(row),
                "feedback_status": "accepted",
            },
        )
        assert unauthorized.status_code == 401

        response = client.post(
            "/api/sales-email/reviews",
            auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
            json={
                "match_key": review.match_key(row),
                "feedback_status": "corrected",
                "corrected_score": 41,
                "corrected_notes": "SQL/Oracle不足。candidate@example.com と 090-1234-5678 はログに残さない。",
                "corrected_fields": {"missing_skills": ["SQL", "Oracle"]},
                "next_action": "Oracle経験の証跡を確認する",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["db"]["feedback_id"] > 0
        assert data["review"]["feedback_status"] == "corrected"
        serialized = json.dumps(data, ensure_ascii=False)
        assert "candidate@example.com" not in serialized
        assert "090-1234-5678" not in serialized

        summary_response = client.get(
            "/api/sales-email/reviews/summary",
            auth=(app.BASIC_AUTH_USERNAME, app.BASIC_AUTH_PASSWORD),
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["status"] == "success"
        assert summary["total"] == 1
        assert summary["status_counts"]["corrected"] == 1
        assert summary["file_review_count"] == 1
    finally:
        for key, value in old_values.items():
            setattr(app, key, value)
