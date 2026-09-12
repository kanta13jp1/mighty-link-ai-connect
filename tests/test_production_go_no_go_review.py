import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_production_go_no_go_review as review


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_wbs(path: Path) -> None:
    write(
        path,
        "\t".join(
            [
                "タスクID",
                "大フェーズ",
                "小フェーズ",
                "タスク名",
                "担当",
                "実行エンジン",
                "Sheets Live 連携アクション",
                "ステータス",
                "開始日",
                "終了予定日",
            ]
        )
        + "\n"
        + "T746\t7. 決定後実行\tリリース\tGo/No-Go\tCodex\tCodex\treview\t完了\t2026-06-16\t2026-06-17\n"
        + "T770\t9. 長期保守・拡張\t品質管理\t負荷テスト\tCodex\tCodex\ttest\t未着手\t2026-06-27\t2026-06-29\n",
    )


def criteria_header() -> str:
    return "\t".join(review.REQUIRED_COLUMNS) + "\n"


def criteria_row(
    criterion_id: str,
    *,
    scope: str = "public_paid_launch",
    state: str = "PASS",
    related_wbs: str = "T746",
    evidence: str = "docs/evidence.md",
) -> str:
    values = {
        "criterion_id": criterion_id,
        "scope": scope,
        "category": "release",
        "criterion": "判定基準",
        "evidence_source": evidence,
        "required_state": "PASS",
        "current_state": state,
        "owner": "Codex",
        "decision_authority": "CEO",
        "related_wbs": related_wbs,
        "related_issue": "#103",
        "last_checked": "2026-06-17",
        "notes": "test",
    }
    return "\t".join(values[column] for column in review.REQUIRED_COLUMNS) + "\n"


def test_build_report_groups_scopes_and_no_go_on_blocked(tmp_path):
    write_wbs(tmp_path / "data" / "WBS.tsv")
    write(tmp_path / "docs" / "evidence.md", "# evidence\n")
    write(
        tmp_path / "data" / "criteria.tsv",
        criteria_header()
        + criteria_row("DEMO-01", scope="controlled_demo", state="PASS", related_wbs="T746")
        + criteria_row("PUBLIC-01", scope="public_paid_launch", state="BLOCKED", related_wbs="T770"),
    )

    report = review.build_report(tmp_path, tmp_path / "data" / "criteria.tsv", tmp_path / "data" / "WBS.tsv")

    assert report["overall_recommendation"] == "NO_GO"
    assert report["scopes"]["controlled_demo"]["recommendation"] == "GO"
    assert report["scopes"]["public_paid_launch"]["recommendation"] == "NO_GO"
    public_row = next(row for row in report["criteria"] if row["criterion_id"] == "PUBLIC-01")
    assert public_row["wbs_statuses"] == {"T770": "未着手"}


def test_human_gate_becomes_conditional_without_blocked(tmp_path):
    write_wbs(tmp_path / "data" / "WBS.tsv")
    write(tmp_path / "docs" / "evidence.md", "# evidence\n")
    write(
        tmp_path / "data" / "criteria.tsv",
        criteria_header() + criteria_row("PUBLIC-04", state="HUMAN_GATE"),
    )

    report = review.build_report(tmp_path, tmp_path / "data" / "criteria.tsv", tmp_path / "data" / "WBS.tsv")

    assert report["overall_recommendation"] == "CONDITIONAL_GO_AFTER_APPROVAL"


def test_duplicate_criterion_id_is_rejected(tmp_path):
    write_wbs(tmp_path / "data" / "WBS.tsv")
    write(tmp_path / "docs" / "evidence.md", "# evidence\n")
    write(
        tmp_path / "data" / "criteria.tsv",
        criteria_header()
        + criteria_row("PUBLIC-01")
        + criteria_row("PUBLIC-01", state="WARNING"),
    )

    try:
        review.build_report(tmp_path, tmp_path / "data" / "criteria.tsv", tmp_path / "data" / "WBS.tsv")
    except ValueError as exc:
        assert "Duplicate criterion_id" in str(exc)
    else:
        raise AssertionError("Expected duplicate criterion_id to be rejected")


def test_main_writes_json_and_redacted_markdown(tmp_path):
    write_wbs(tmp_path / "data" / "WBS.tsv")
    write(tmp_path / "docs" / "evidence.md", "# evidence\n")
    write(
        tmp_path / "data" / "criteria.tsv",
        criteria_header()
        + criteria_row(
            "PUBLIC-01",
            evidence="docs/evidence.md; https://hooks.slack.com/services/T/B/C; api_key=supersecret",
        ),
    )

    exit_code = review.main(
        [
            "--root",
            str(tmp_path),
            "--criteria",
            str(tmp_path / "data" / "criteria.tsv"),
            "--wbs",
            str(tmp_path / "data" / "WBS.tsv"),
            "--json-report",
            str(tmp_path / "exports" / "report.json"),
            "--markdown-report",
            str(tmp_path / "exports" / "report.md"),
        ]
    )
    payload = json.loads((tmp_path / "exports" / "report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "exports" / "report.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert payload["task_id"] == "T746"
    assert payload["overall_recommendation"] == "GO"
    assert "hooks.slack.com/services" not in markdown
    assert "api_key=supersecret" not in markdown
    assert "<redacted>" in markdown
