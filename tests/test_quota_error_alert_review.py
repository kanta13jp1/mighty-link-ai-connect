import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_quota_error_alert_review as review


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def write_budgets(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "cost_center\towner_lane\tcategory\tmonthly_budget_usd\twarning_ratio\tcritical_ratio\tsource\tnotes",
                "firebase_google_cloud\tVSCode + Codex\tInfra\t10.00\t0.80\t1.00\tCloud Billing\tFirebase/GCP budget",
                "supabase_db\tVSCode + Codex\tDB\t25.00\t0.80\t1.00\tSupabase dashboard\tSupabase budget",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_required_inputs(root: Path, *, query_status: str = "ready") -> dict[str, Path]:
    exports = root / "exports"
    paths = {
        "infra": exports / "infra_monitoring_dashboard.json",
        "cost": exports / "weekly_cost_dashboard.json",
        "uptime": exports / "uptime_monitor_report.json",
        "query": exports / "supabase_query_performance_review.json",
        "budgets": root / "data" / "cost_allocation_budgets.tsv",
    }
    write_json(paths["infra"], {"task_id": "T755", "overall_status": "ok", "checks": []})
    write_json(paths["cost"], {"task_id": "T757", "overall_status": "ok", "cost_centers": []})
    write_json(paths["uptime"], {"task_id": "T743", "overall_status": "ok", "targets": []})
    write_json(paths["query"], {"task_id": "T761", "overall_status": query_status, "summary": {"critical": 0}})
    write_budgets(paths["budgets"])
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "DISASTER_RECOVERY_AND_ESCALATION_RUNBOOK.md").write_text("# DR\n", encoding="utf-8")
    (root / "docs" / "INCIDENT_POSTMORTEM_RUNBOOK.md").write_text("# Incident\n", encoding="utf-8")
    return paths


def test_ready_report_contains_firebase_and_supabase_checks(tmp_path):
    paths = write_required_inputs(tmp_path)
    review_json = tmp_path / "exports" / "quota.json"
    review_md = tmp_path / "exports" / "quota.md"

    exit_code = review.main(
        [
            "--root",
            str(tmp_path),
            "--infra-report",
            str(paths["infra"]),
            "--cost-report",
            str(paths["cost"]),
            "--uptime-report",
            str(paths["uptime"]),
            "--query-review",
            str(paths["query"]),
            "--budgets",
            str(paths["budgets"]),
            "--json-report",
            str(review_json),
            "--markdown-report",
            str(review_md),
            "--fail-on-critical",
        ]
    )
    payload = json.loads(review_json.read_text(encoding="utf-8"))
    markdown = review_md.read_text(encoding="utf-8")

    assert exit_code == 0
    assert payload["task_id"] == "T761_1"
    assert payload["overall_status"] == "ready"
    assert payload["summary"]["critical"] == 0
    assert {check["provider"] for check in payload["checks"]} >= {"Firebase / Google Cloud", "Firebase", "Supabase"}
    assert "Cloud Monitoring" in markdown
    assert "Supabase Metrics API" in markdown


def test_critical_query_review_fails_when_requested(tmp_path):
    paths = write_required_inputs(tmp_path, query_status="critical")

    exit_code = review.main(
        [
            "--root",
            str(tmp_path),
            "--infra-report",
            str(paths["infra"]),
            "--cost-report",
            str(paths["cost"]),
            "--uptime-report",
            str(paths["uptime"]),
            "--query-review",
            str(paths["query"]),
            "--budgets",
            str(paths["budgets"]),
            "--json-report",
            str(tmp_path / "exports" / "quota.json"),
            "--markdown-report",
            str(tmp_path / "exports" / "quota.md"),
            "--fail-on-critical",
        ]
    )
    payload = json.loads((tmp_path / "exports" / "quota.json").read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["overall_status"] == "critical"
    assert any(check["key"] == "supabase_db_saturation_alert" for check in payload["checks"])


def test_secret_like_text_is_redacted_from_outputs(tmp_path):
    output = tmp_path / "exports" / "redacted.md"
    review.write_text(
        output,
        "postgresql://postgres:secret@example.com:5432/postgres "
        "Bearer abc.def https://hooks.slack.com/services/T/B/C api_key=supersecret",
    )
    rendered = output.read_text(encoding="utf-8")

    assert "secret@example.com" not in rendered
    assert "abc.def" not in rendered
    assert "secret@example.com" not in rendered
    assert "hooks.slack.com/services" not in rendered
    assert "api_key=supersecret" not in rendered
    assert "<redacted>" in rendered


def test_missing_budget_rows_are_warnings_not_critical(tmp_path):
    paths = write_required_inputs(tmp_path)
    paths["budgets"].write_text(
        "cost_center\towner_lane\tcategory\tmonthly_budget_usd\twarning_ratio\tcritical_ratio\tsource\tnotes\n",
        encoding="utf-8",
    )

    exit_code = review.main(
        [
            "--root",
            str(tmp_path),
            "--infra-report",
            str(paths["infra"]),
            "--cost-report",
            str(paths["cost"]),
            "--uptime-report",
            str(paths["uptime"]),
            "--query-review",
            str(paths["query"]),
            "--budgets",
            str(paths["budgets"]),
            "--json-report",
            str(tmp_path / "exports" / "quota.json"),
            "--markdown-report",
            str(tmp_path / "exports" / "quota.md"),
            "--fail-on-critical",
        ]
    )
    payload = json.loads((tmp_path / "exports" / "quota.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["overall_status"] == "warning"
    assert payload["summary"]["warning"] >= 1
