import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import validate_firebase_hosting_headers as header_review


def test_current_firebase_config_has_required_security_headers():
    config = header_review.load_json(PROJECT_ROOT / "firebase.json")
    report = header_review.review_headers(config)

    assert report["status"] == "pass"
    assert report["reviewed_sources"] == ["**"]
    headers = report["headers"]
    assert headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "camera=()" in headers["permissions-policy"]


def test_missing_global_header_rule_fails():
    report = header_review.review_headers({"hosting": {"headers": []}})

    assert report["status"] == "fail"
    checks = {finding["check"] for finding in report["findings"]}
    assert "firebase_hosting_global_headers" in checks
    assert "content-security-policy" in checks
    assert "x-content-type-options" in checks


def test_cli_writes_json_and_markdown_reports(tmp_path):
    firebase_json = tmp_path / "firebase.json"
    json_report = tmp_path / "review.json"
    markdown_report = tmp_path / "review.md"
    firebase_json.write_text((PROJECT_ROOT / "firebase.json").read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = header_review.main(
        [
            "--root",
            str(tmp_path),
            "--firebase-json",
            "firebase.json",
            "--json-report",
            "review.json",
            "--markdown-report",
            "review.md",
        ]
    )

    assert exit_code == 0
    payload = json.loads(json_report.read_text(encoding="utf-8"))
    assert payload["task_id"] == "T835"
    assert payload["status"] == "pass"
    assert "Firebase Hosting Security Headers Review" in markdown_report.read_text(encoding="utf-8")
