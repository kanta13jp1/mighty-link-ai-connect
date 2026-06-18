import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import sales_email_extract as extract
import sales_email_ingest as ingest


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_project_requirement_extraction_is_structured_and_redacted(tmp_path):
    write(
        tmp_path / "project.txt",
        "\n".join(
            [
                "From: BP Sales <bp-project@example.com>",
                "Subject: RE: SQL Oracle 案件",
                "Date: Thu, 18 Jun 2026 10:00:00 +0900",
                "",
                "案件名: 基幹システム刷新",
                "必須: SQL、Oracle、Java、基本設計",
                "尚可: AWS、Docker",
                "単価: 75〜90万",
                "勤務地: 東京 リモート併用",
                "稼働: 7月開始 長期",
                "商流: エンド直",
                "面談1回。連絡先 candidate@example.com / 090-1234-5678 / token=abcdef12345",
            ]
        ),
    )

    report = extract.build_extraction_report(ingest.load_sales_emails([tmp_path]))
    payload = json.dumps(report, ensure_ascii=False)
    item = report["extractions"][0]
    project = item["project_requirement"]

    assert report["task_id"] == "T817_4"
    assert report["project_requirement_count"] == 1
    assert report["talent_profile_count"] == 0
    assert item["email_kind"] == "project_intro"
    assert project["rate_min"] == 75
    assert project["rate_max"] == 90
    assert project["remote_type"] == "hybrid"
    assert "SQL" in project["required_skills"]
    assert "Oracle" in project["required_skills"]
    assert "AWS" in project["nice_to_have_skills"]
    assert "candidate@example.com" not in payload
    assert "090-1234-5678" not in payload
    assert "abcdef12345" not in payload
    assert "<email:redacted>" in payload
    assert "<phone:redacted>" in payload
    assert "<secret:redacted>" in payload


def test_talent_profile_extraction_uses_anonymized_identity(tmp_path):
    write(
        tmp_path / "talent.csv",
        "\n".join(
            [
                "sender,subject,body,received_at,message_id",
                (
                    "partner@example.com,要員提案 Java SE,"
                    "要員提案です。Java 5年、Spring、SQL、AWS経験。希望単価80万。"
                    "東京、フルリモート希望。即日稼働可能。本人メール talent@example.com,"
                    "2026-06-18,<talent-1>"
                ),
            ]
        ),
    )

    report = extract.build_extraction_report(ingest.load_sales_emails([tmp_path]))
    payload = json.dumps(report, ensure_ascii=False)
    item = report["extractions"][0]
    talent = item["talent_profile"]

    assert report["talent_profile_count"] == 1
    assert item["email_kind"] == "talent_proposal"
    assert talent["anonymized_talent_key"].startswith("talent_")
    assert talent["experience_years"] == 5.0
    assert talent["desired_rate_min"] == 80
    assert talent["desired_rate_max"] == 80
    assert talent["remote_preference"] == "remote"
    assert {"Java", "Spring", "SQL", "AWS"}.issubset(set(talent["skills"]))
    assert "talent@example.com" not in payload
    assert "本人メール" in payload
    assert "<email:redacted>" in payload


def test_cli_writes_sanitized_json_and_markdown(tmp_path):
    source = tmp_path / "sales.txt"
    json_report = tmp_path / "review.json"
    md_report = tmp_path / "review.md"
    write(
        source,
        "\n".join(
            [
                "From: BP Sales <bp@example.com>",
                "Subject: Python FastAPI 案件",
                "",
                "案件です。必須: Python FastAPI PostgreSQL 連絡 sales@example.com。単価70万。勤務地: 品川。",
            ]
        ),
    )

    exit_code = extract.main(
        [
            "--input",
            str(source),
            "--json-report",
            str(json_report),
            "--markdown-report",
            str(md_report),
        ]
    )

    assert exit_code == 0
    data = json.loads(json_report.read_text(encoding="utf-8"))
    markdown = md_report.read_text(encoding="utf-8")
    assert data["project_requirement_count"] == 1
    assert "Python" in json.dumps(data, ensure_ascii=False)
    assert "sales@example.com" not in json.dumps(data, ensure_ascii=False)
    assert "sales@example.com" not in markdown
    assert "<email:redacted>" in markdown
