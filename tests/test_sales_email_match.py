import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import app  # noqa: E402
import sales_email_extract as extract  # noqa: E402
import sales_email_ingest as ingest  # noqa: E402
import sales_email_match as match  # noqa: E402


def sample_extraction_report() -> dict:
    emails = ingest.load_sales_emails([PROJECT_ROOT / "data" / "samples" / "sales_emails"])
    return extract.build_extraction_report(emails)


def sample_extraction_report_with_rate() -> dict:
    report = sample_extraction_report()
    for item in report["extractions"]:
        project = item.get("project_requirement")
        if project:
            item["sender_domain"] = "partner.example.jp"
            project["rate_min"] = 70
            project["rate_max"] = 90
    return report


def test_match_report_builds_project_to_talent_candidates():
    report = match.build_match_report(sample_extraction_report(), match.criteria_from_values(limit=10))

    assert report["task_id"] == "T817_5"
    assert report["project_count"] == 1
    assert report["talent_count"] == 1
    assert report["match_count"] == 1

    row = report["matches"][0]
    assert row["score"] > 0
    assert "Java" in row["matched_skills"]
    assert "SQL" in row["missing_skills"]
    assert row["review_status"] == "pending"
    assert row["score_breakdown"]["required_skill_fit"] > 0


def test_match_report_supports_skill_filters_and_min_score():
    source_report = sample_extraction_report()

    java_report = match.build_match_report(
        source_report,
        match.criteria_from_values(skills="Java", min_score=1, limit=5),
    )
    assert java_report["match_count"] == 1

    missing_report = match.build_match_report(
        source_report,
        match.criteria_from_values(skills="Kubernetes", limit=5),
    )
    assert missing_report["match_count"] == 0


def test_match_report_supports_overlapping_rate_range_filters():
    source_report = sample_extraction_report_with_rate()

    overlapping_report = match.build_match_report(
        source_report,
        match.criteria_from_values(min_rate=80, max_rate=100, limit=5),
    )
    assert overlapping_report["match_count"] == 1

    above_project_ceiling = match.build_match_report(
        source_report,
        match.criteria_from_values(min_rate=91, limit=5),
    )
    assert above_project_ceiling["match_count"] == 0

    below_project_floor = match.build_match_report(
        source_report,
        match.criteria_from_values(max_rate=69, limit=5),
    )
    assert below_project_floor["match_count"] == 0


def test_rate_filter_excludes_projects_without_rate_information():
    report = match.build_match_report(
        sample_extraction_report(),
        match.criteria_from_values(min_rate=50, limit=5),
    )

    assert report["match_count"] == 0


def test_match_report_searches_sender_domain_and_structured_fields():
    source_report = sample_extraction_report_with_rate()

    domain_report = match.build_match_report(
        source_report,
        match.criteria_from_values(search_query="partner.example.jp", limit=5),
    )
    skill_report = match.build_match_report(
        source_report,
        match.criteria_from_values(search_query="Oracle", limit=5),
    )
    missing_report = match.build_match_report(
        source_report,
        match.criteria_from_values(search_query="not-present", limit=5),
    )

    assert domain_report["match_count"] == 1
    assert skill_report["match_count"] == 1
    assert missing_report["match_count"] == 0


def test_match_criteria_rejects_invalid_rate_values():
    with pytest.raises(ValueError, match="min_rate"):
        match.criteria_from_values(min_rate="not-a-number")
    with pytest.raises(ValueError, match="max_rate"):
        match.criteria_from_values(max_rate=-1)
    with pytest.raises(ValueError, match="must not exceed"):
        match.criteria_from_values(min_rate=90, max_rate=70)


def test_match_cli_outputs_sanitized_json_and_markdown(tmp_path):
    extraction_path = tmp_path / "extraction.json"
    json_path = tmp_path / "matches.json"
    markdown_path = tmp_path / "matches.md"
    extract.write_json_report(sample_extraction_report(), extraction_path)

    exit_code = match.main(
        [
            "--input-report",
            str(extraction_path),
            "--json-report",
            str(json_path),
            "--markdown-report",
            str(markdown_path),
            "--skills",
            "Java",
        ]
    )

    assert exit_code == 0
    payload = json_path.read_text(encoding="utf-8")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "raw_email_body_not_loaded" in payload
    assert "candidate@example.com" not in payload
    assert "090-1234-5678" not in payload
    assert "candidate@example.com" not in markdown
    assert "090-1234-5678" not in markdown


def test_sales_email_match_api_uses_sanitized_report(tmp_path):
    extraction_path = tmp_path / "extraction.json"
    extract.write_json_report(sample_extraction_report(), extraction_path)

    old_path = app.SALES_EMAIL_MATCH_REPORT_FILE
    app.SALES_EMAIL_MATCH_REPORT_FILE = str(extraction_path)
    try:
        client = TestClient(app.app)
        response = client.get("/api/sales-email/matches?skills=Java&limit=5")
    finally:
        app.SALES_EMAIL_MATCH_REPORT_FILE = old_path

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["task_id"] == "T817_5"
    assert data["match_count"] == 1
    serialized = json.dumps(data, ensure_ascii=False)
    assert "candidate@example.com" not in serialized
    assert "090-1234-5678" not in serialized


def test_sales_email_match_api_supports_keyword_and_rate_filters(tmp_path):
    extraction_path = tmp_path / "extraction.json"
    extract.write_json_report(sample_extraction_report_with_rate(), extraction_path)

    old_path = app.SALES_EMAIL_MATCH_REPORT_FILE
    app.SALES_EMAIL_MATCH_REPORT_FILE = str(extraction_path)
    try:
        client = TestClient(app.app)
        response = client.get(
            "/api/sales-email/matches",
            params={
                "search_query": "partner.example.jp",
                "min_rate": 80,
                "max_rate": 100,
                "limit": 5,
            },
        )
        invalid_response = client.get(
            "/api/sales-email/matches",
            params={"min_rate": 90, "max_rate": 70},
        )
    finally:
        app.SALES_EMAIL_MATCH_REPORT_FILE = old_path

    assert response.status_code == 200
    data = response.json()
    assert data["match_count"] == 1
    assert data["filters"]["min_rate"] == 80
    assert data["filters"]["max_rate"] == 100
    assert data["filters"]["search_query"] == "partner.example.jp"
    assert invalid_response.status_code == 400
