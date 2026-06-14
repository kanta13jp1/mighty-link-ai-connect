import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_supabase_query_performance_review as review


REQUIRED_PROBES = (
    "extension_status",
    "top_queries_by_total_time",
    "top_queries_by_mean_time",
    "sequential_scan_pressure",
    "unused_indexes",
    "large_indexes",
    "vacuum_analyze_lag",
)


def write_performance_report(path: Path, *, probes: tuple[str, ...] = REQUIRED_PROBES) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": "T750",
        "status": "planned",
        "dry_run": True,
        "database_url": "postgresql://postgres:***@example.invalid:5432/postgres",
        "probes": [{"name": name, "purpose": f"{name} purpose", "sql": "select 1;"} for name in probes],
        "api_results": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_dry_run_report_generates_ready_dashboard_review(tmp_path):
    source_report = tmp_path / "exports" / "supabase_performance_report.json"
    review_json = tmp_path / "exports" / "review.json"
    review_md = tmp_path / "exports" / "review.md"
    write_performance_report(source_report)

    exit_code = review.main(
        [
            "--root",
            str(tmp_path),
            "--performance-report",
            str(source_report),
            "--review-json",
            str(review_json),
            "--review-md",
            str(review_md),
            "--fail-on-critical",
        ]
    )
    payload = json.loads(review_json.read_text(encoding="utf-8"))
    markdown = review_md.read_text(encoding="utf-8")

    assert exit_code == 0
    assert payload["task_id"] == "T761"
    assert payload["overall_status"] == "ready"
    assert payload["summary"]["critical"] == 0
    assert "Query Performance" in markdown
    assert "Index Advisor" in markdown
    assert "supabase inspect db outliers" in markdown


def test_missing_performance_report_is_critical(tmp_path):
    exit_code = review.main(
        [
            "--root",
            str(tmp_path),
            "--performance-report",
            str(tmp_path / "exports" / "missing.json"),
            "--review-json",
            str(tmp_path / "exports" / "review.json"),
            "--review-md",
            str(tmp_path / "exports" / "review.md"),
            "--fail-on-critical",
        ]
    )
    payload = json.loads((tmp_path / "exports" / "review.json").read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["overall_status"] == "critical"
    assert payload["checks"][0]["key"] == "performance_report"


def test_missing_required_probe_is_critical(tmp_path):
    source_report = tmp_path / "exports" / "supabase_performance_report.json"
    write_performance_report(source_report, probes=REQUIRED_PROBES[:-1])

    exit_code = review.main(
        [
            "--root",
            str(tmp_path),
            "--performance-report",
            str(source_report),
            "--review-json",
            str(tmp_path / "exports" / "review.json"),
            "--review-md",
            str(tmp_path / "exports" / "review.md"),
            "--fail-on-critical",
        ]
    )
    payload = json.loads((tmp_path / "exports" / "review.json").read_text(encoding="utf-8"))

    assert exit_code == 2
    assert payload["overall_status"] == "critical"
    assert "vacuum_analyze_lag" in payload["checks"][1]["evidence"]


def test_secret_like_text_is_redacted_from_rendered_output(tmp_path):
    report = {
        "task_id": "T761",
        "generated_at_utc": "2026-06-15T00:00:00Z",
        "overall_status": "ready",
        "summary": {"ok": 0, "ready": 1, "warning": 0, "critical": 0},
        "dashboard_checklist": [],
        "checks": [
            {
                "key": "secret_sample",
                "status": "ready",
                "source": "unit-test",
                "action": "Do not leak postgres URLs or auth tokens.",
                "evidence": "postgresql://postgres:very-secret@example.com:5432/postgres Bearer abc.def",
            }
        ],
        "inspect_commands": [],
        "tuning_rules": [],
    }

    output = tmp_path / "review.md"
    review.write_text(output, review.render_markdown(report))
    text = output.read_text(encoding="utf-8")

    assert "very-secret" not in text
    assert "abc.def" not in text
    assert text.count("<redacted>") == 2
