import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import audit_external_api_usage as audit


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if isinstance(row, str):
                handle.write(row + "\n")
            else:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_build_report_detects_warning_and_critical_limits(tmp_path):
    ledger = tmp_path / "usage.jsonl"
    write_jsonl(
        ledger,
        [
            {
                "day": "2026-06-10",
                "provider": "seedance_api",
                "operation": "generation_create",
                "billable": True,
                "outcome": "success",
            },
            {
                "day": "2026-06-10",
                "provider": "seedance_api",
                "operation": "generation_create",
                "billable": True,
                "outcome": "success",
            },
            {
                "day": "2026-06-10",
                "provider": "gemini_api",
                "operation": "parse",
                "billable": True,
                "outcome": "success",
                "reported_total_tokens": 81,
            },
            {
                "day": "2026-06-10",
                "provider": "gemini_api",
                "operation": "parse",
                "billable": False,
                "outcome": "blocked",
            },
            {
                "day": "2026-06-09",
                "provider": "gemini_api",
                "operation": "parse",
                "billable": True,
                "outcome": "success",
                "reported_total_tokens": 9999,
            },
        ],
    )

    report = audit.build_report(
        audit.load_jsonl(ledger),
        "2026-06-10",
        guards={
            "seedance_api:generation_create": {
                "daily_call_limit": 1,
                "daily_reported_token_limit": 0,
            },
            "gemini_api:parse": {
                "daily_call_limit": 20,
                "daily_reported_token_limit": 100,
            },
            "gemini_api:match": {
                "daily_call_limit": 20,
                "daily_reported_token_limit": 100,
            },
        },
    )

    assert report["status"] == "critical"
    assert report["ledger_events_for_day"] == 4
    assert report["guards"]["seedance_api:generation_create"]["state"] == "critical"
    assert report["guards"]["gemini_api:parse"]["state"] == "warning"
    assert report["guards"]["gemini_api:parse"]["blocked_calls"] == 1


def test_missing_ledger_is_ok_and_invalid_json_is_warning(tmp_path):
    missing_report = audit.build_report(audit.load_jsonl(tmp_path / "missing.jsonl"), "2026-06-10")
    assert missing_report["status"] == "ok"
    assert missing_report["ledger_events_for_day"] == 0

    ledger = tmp_path / "broken.jsonl"
    write_jsonl(
        ledger,
        [
            '{"day":"2026-06-10","provider":"gemini_api","operation":"match","billable":false,"outcome":"blocked"}',
            "{not json",
        ],
    )

    report = audit.build_report(audit.load_jsonl(ledger), "2026-06-10")

    assert report["status"] == "warning"
    assert any(alert["guard"] == "ledger:parse" for alert in report["alerts"])
