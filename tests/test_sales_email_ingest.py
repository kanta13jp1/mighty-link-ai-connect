import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import sales_email_ingest as ingest


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_eml_and_txt_duplicates_are_detected_without_raw_body_output(tmp_path):
    body = (
        "SQL / Oracle engineer is required. Contact candidate@example.com "
        "or 090-1234-5678. Bearer abc.def_ghi"
    )
    write(
        tmp_path / "project.eml",
        "\n".join(
            [
                "From: BP Sales <bp@example.com>",
                "Subject: RE: SQL Oracle project",
                "Date: Wed, 17 Jun 2026 10:00:00 +0900",
                "Message-ID: <message-1@example.com>",
                "Content-Type: text/plain; charset=utf-8",
                "",
                body,
            ]
        ),
    )
    write(
        tmp_path / "duplicate.txt",
        "\n".join(
            [
                "From: BP Sales <bp@example.com>",
                "Subject: SQL Oracle project",
                "Date: Wed, 17 Jun 2026 10:01:00 +0900",
                "",
                body,
            ]
        ),
    )

    emails = ingest.load_sales_emails([tmp_path])
    report = ingest.build_ingest_report(emails)
    serialized = json.dumps(report, ensure_ascii=False)

    assert report["input_count"] == 2
    assert report["unique_count"] == 1
    assert report["duplicate_count"] == 1
    assert any(message["duplicate"] for message in report["messages"])
    assert "candidate@example.com" not in serialized
    assert "090-1234-5678" not in serialized
    assert "abc.def_ghi" not in serialized
    assert "<email:redacted>" in serialized
    assert "<phone:redacted>" in serialized
    assert "<secret:redacted>" in serialized


def test_csv_aliases_and_markdown_report_are_sanitized(tmp_path):
    csv_path = tmp_path / "sales.csv"
    write(
        csv_path,
        "\n".join(
            [
                "sender,subject,body,received_at,message_id",
                "partner@example.com,Java remote project,Java and AWS needed. mail: sales@example.com,2026-06-17,<csv-1>",
            ]
        ),
    )
    json_report = tmp_path / "review.json"
    md_report = tmp_path / "review.md"

    exit_code = ingest.main(
        [
            "--input",
            str(csv_path),
            "--json-report",
            str(json_report),
            "--markdown-report",
            str(md_report),
        ]
    )

    payload = json.loads(json_report.read_text(encoding="utf-8"))
    markdown = md_report.read_text(encoding="utf-8")
    assert exit_code == 0
    assert payload["input_count"] == 1
    assert payload["unique_count"] == 1
    assert payload["messages"][0]["sender_domain"] == "example.com"
    assert "sales@example.com" not in markdown
    assert "<email:redacted>" in markdown


def test_unsupported_input_is_rejected(tmp_path):
    write(tmp_path / "bad.pdf", "not a supported source")

    try:
        ingest.load_sales_emails([tmp_path / "bad.pdf"])
    except FileNotFoundError as exc:
        assert "Unsupported or missing input path" in str(exc)
    else:
        raise AssertionError("Expected unsupported files to be rejected")


def test_pop3_cli_option_is_rejected():
    with pytest.raises(SystemExit) as exc_info:
        ingest.main(["--pop3"])

    assert exc_info.value.code == 2
