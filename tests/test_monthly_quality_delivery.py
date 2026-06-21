# -*- coding: utf-8 -*-
"""Tests for T808 monthly quality report delivery helpers."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import monthly_quality_delivery as delivery


def test_default_target_month_uses_last_completed_month():
    assert delivery.default_target_month(dt.date(2026, 7, 1)) == "2026-06"
    assert delivery.default_target_month(dt.date(2026, 1, 15)) == "2025-12"


def test_merge_kpi_values_appends_and_updates_same_month():
    report_file = PROJECT_ROOT / "docs" / "MONTHLY_REPORT_2026-06.md"
    summary = delivery.collect_monthly_summary(PROJECT_ROOT, "2026-06", dt.date(2026, 6, 21), report_file)

    values, row_number, action = delivery.merge_kpi_values([], summary)
    assert values[0] == delivery.KPI_HEADERS
    assert row_number == 2
    assert action == "appended"
    assert values[1][0] == "2026-06"

    summary_updated = json.loads(json.dumps(summary))
    summary_updated["tests"]["pass_pct"] = 98.5
    values, row_number, action = delivery.merge_kpi_values(values, summary_updated)
    assert row_number == 2
    assert action == "updated"
    assert values[1][11] == "98.5"


def test_payloads_do_not_include_notification_secrets(monkeypatch):
    report_file = PROJECT_ROOT / "docs" / "MONTHLY_REPORT_2026-06.md"
    summary = delivery.collect_monthly_summary(PROJECT_ROOT, "2026-06", dt.date(2026, 6, 21), report_file)
    secret_webhook = "https://example.invalid/slack-webhook-test-secret"
    secret_token = "notion-test-token-that-must-not-be-written"
    monkeypatch.setenv("SLACK_WEBHOOK_URL", secret_webhook)
    monkeypatch.setenv("NOTION_API_KEY", secret_token)
    monkeypatch.setenv("NOTION_DATABASE_ID", "database-id")

    slack_payload = delivery.build_slack_payload(summary)
    notion_payload = delivery.build_notion_payload(
        summary,
        delivery.notion_parent_from_env() or {"database_id": "missing"},
    )
    combined = json.dumps(slack_payload, ensure_ascii=False) + json.dumps(notion_payload, ensure_ascii=False)
    assert secret_webhook not in combined
    assert secret_token not in combined
    assert "MONTHLY_REPORT_2026-06.md" in combined


def test_output_artifacts_are_month_scoped(tmp_path):
    outputs = delivery.output_paths(tmp_path, "2026-06")
    delivery.write_json(outputs.slack_status, delivery.delivery_status("drafted", "ok"))
    payload = json.loads(outputs.slack_status.read_text(encoding="utf-8"))
    assert payload["task_id"] == "T808"
    assert outputs.slack_status.name == "monthly_quality_slack_status_2026-06.json"
