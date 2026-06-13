# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_infra_monitoring_dashboard as dashboard


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_parse_prometheus_metrics_categorizes_supabase_series():
    text = """
    # HELP supabase_cpu_usage CPU
    supabase_cpu_usage 0.4
    supabase_memory_bytes 123
    supabase_disk_io_bytes 456
    supabase_connection_count 2
    pg_stat_statements_query_time 10
    """

    parsed = dashboard.parse_prometheus_metrics(text)

    assert parsed["samples"] == 5
    assert "cpu" in parsed["categories"]
    assert "memory" in parsed["categories"]
    assert "disk_io" in parsed["categories"]
    assert "connections" in parsed["categories"]
    assert "queries" in parsed["categories"]


def test_local_host_resource_status_caps_critical_by_default(monkeypatch):
    monkeypatch.delenv("INFRA_HOST_RESOURCE_CRITICAL", raising=False)
    assert dashboard.local_host_resource_status(99.0, 80.0, 90.0) == "warning"

    monkeypatch.setenv("INFRA_HOST_RESOURCE_CRITICAL", "1")
    assert dashboard.local_host_resource_status(99.0, 80.0, 90.0) == "critical"


def test_dashboard_writes_reports_without_secret_like_values(tmp_path, monkeypatch):
    write_json(
        tmp_path / "exports" / "uptime.json",
        {
            "summary": {"status": "ok", "ok": 1, "warning": 0, "failed": 0},
            "results": [{"elapsed_ms": 100.0}],
        },
    )
    write_json(
        tmp_path / "exports" / "perf.json",
        {"status": "completed", "dry_run": False, "probes": [{"name": "query"}], "api_results": []},
    )
    write_json(
        tmp_path / "exports" / "logs.json",
        {"candidates": [], "pruned_archives": []},
    )
    usage = tmp_path / "data" / "external_api_usage.jsonl"
    usage.parent.mkdir(parents=True)
    usage.write_text(
        '{"provider":"seedance","outcome":"blocked","billable":false,"reason":"postgresql://user:secret@example/db"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        dashboard,
        "collect_local_resource_checks",
        lambda root: [
            dashboard.TelemetryCheck("disk_usage", "host", "ok", "20% used", "test", "none"),
            dashboard.TelemetryCheck("memory_usage", "host", "ok", "30% used", "test", "none"),
            dashboard.TelemetryCheck("cpu_load", "host", "ok", "0.1", "test", "none"),
        ],
    )

    exit_code = dashboard.main(
        [
            "--root",
            str(tmp_path),
            "--uptime-report",
            "exports/uptime.json",
            "--performance-report",
            "exports/perf.json",
            "--log-rotation-report",
            "exports/logs.json",
            "--external-usage-log",
            "data/external_api_usage.jsonl",
            "--report-path",
            "exports/dashboard.json",
            "--markdown-path",
            "exports/dashboard.md",
        ]
    )

    report_text = (tmp_path / "exports" / "dashboard.json").read_text(encoding="utf-8")
    markdown_text = (tmp_path / "exports" / "dashboard.md").read_text(encoding="utf-8")
    report = json.loads(report_text)

    assert exit_code == 0
    assert report["task_id"] == "T755"
    assert "postgresql://user:secret" not in report_text
    assert "postgresql://user:secret" not in markdown_text
    assert report["summary"]["critical"] == 0


def test_fail_on_critical_returns_nonzero(tmp_path, monkeypatch):
    write_json(
        tmp_path / "exports" / "uptime.json",
        {"summary": {"status": "failed", "ok": 0, "warning": 0, "failed": 1}, "results": []},
    )
    write_json(tmp_path / "exports" / "perf.json", {"status": "completed", "dry_run": False})
    write_json(tmp_path / "exports" / "logs.json", {"candidates": [], "pruned_archives": []})
    usage = tmp_path / "data" / "external_api_usage.jsonl"
    usage.parent.mkdir(parents=True)
    usage.write_text("", encoding="utf-8")
    monkeypatch.setattr(dashboard, "collect_local_resource_checks", lambda root: [])

    exit_code = dashboard.main(
        [
            "--root",
            str(tmp_path),
            "--uptime-report",
            "exports/uptime.json",
            "--performance-report",
            "exports/perf.json",
            "--log-rotation-report",
            "exports/logs.json",
            "--external-usage-log",
            "data/external_api_usage.jsonl",
            "--report-path",
            "exports/dashboard.json",
            "--markdown-path",
            "exports/dashboard.md",
            "--fail-on-critical",
        ]
    )

    assert exit_code == 2


def test_external_usage_summary_counts_billable_and_blocked(tmp_path):
    log_path = tmp_path / "usage.jsonl"
    log_path.write_text(
        '{"provider":"gemini","outcome":"success","billable":true}\n'
        '{"provider":"seedance","outcome":"blocked","billable":false}\n',
        encoding="utf-8",
    )

    summary = dashboard.parse_external_usage(log_path)

    assert summary["events"] == 2
    assert summary["billable_events"] == 1
    assert summary["outcomes"]["blocked"] == 1
