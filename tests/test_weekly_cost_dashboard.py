# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_weekly_cost_dashboard as dashboard


def write_jsonl(path: Path, rows: list[dict | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(row if isinstance(row, str) else json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def sample_budgets(path: Path) -> None:
    write_tsv(
        path,
        [
            {
                "cost_center": "ai_api_seedance",
                "owner_lane": "Antigravity + Gemini",
                "category": "AI API",
                "monthly_budget_usd": "10.00",
                "warning_ratio": "0.80",
                "critical_ratio": "1.00",
                "source": "BytePlus ModelArk",
                "notes": "test",
            },
            {
                "cost_center": "ai_api_gemini",
                "owner_lane": "Antigravity + Gemini",
                "category": "AI API",
                "monthly_budget_usd": "20.00",
                "warning_ratio": "0.80",
                "critical_ratio": "1.00",
                "source": "Google AI usage",
                "notes": "test",
            },
        ],
    )


def test_dashboard_aggregates_weekly_usage_and_budget_status(tmp_path):
    ledger = tmp_path / "data" / "external_api_usage.jsonl"
    budgets = tmp_path / "data" / "budgets.tsv"
    actuals = tmp_path / "data" / "actuals.tsv"
    sample_budgets(budgets)
    write_jsonl(
        ledger,
        [
            {"day": "2026-06-10", "provider": "seedance_api", "operation": "generation_create", "billable": True, "outcome": "success"},
            {"day": "2026-06-10", "provider": "seedance_api", "operation": "generation_create", "billable": True, "outcome": "success"},
            {"day": "2026-06-11", "provider": "gemini_api", "operation": "parse", "billable": False, "outcome": "blocked", "reported_total_tokens": 0},
            {"day": "2026-06-01", "provider": "seedance_api", "operation": "generation_create", "billable": True, "outcome": "success"},
        ],
    )
    write_tsv(
        actuals,
        [
            {
                "period_start": "2026-06-09",
                "period_end": "2026-06-15",
                "cost_center": "ai_api_seedance",
                "amount_usd": "9.00",
                "source": "BytePlus console",
                "notes": "test",
            }
        ],
    )

    report = dashboard.build_dashboard(
        dashboard.load_budgets(budgets),
        dashboard.summarize_usage(dashboard.load_jsonl(ledger), dt.date(2026, 6, 9), dt.date(2026, 6, 15)),
        dashboard.load_actuals(actuals, dt.date(2026, 6, 9), dt.date(2026, 6, 15)),
        dt.date(2026, 6, 9),
        dt.date(2026, 6, 15),
    )

    seedance = next(row for row in report["cost_centers"] if row["cost_center"] == "ai_api_seedance")
    gemini = next(row for row in report["cost_centers"] if row["cost_center"] == "ai_api_gemini")
    assert report["overall_status"] == "warning"
    assert seedance["weekly_actual_usd"] == 9.0
    assert seedance["status"] == "warning"
    assert seedance["billable_events"] == 2
    assert gemini["blocked_events"] == 1


def test_cli_writes_artifacts_without_notification_secrets(tmp_path):
    sample_budgets(tmp_path / "data" / "budgets.tsv")
    write_jsonl(
        tmp_path / "data" / "external_api_usage.jsonl",
        [{"day": "2026-06-10", "provider": "seedance_api", "operation": "generation_create", "billable": False, "outcome": "blocked"}],
    )

    exit_code = dashboard.main(
        [
            "--root",
            str(tmp_path),
            "--start-date",
            "2026-06-09",
            "--end-date",
            "2026-06-15",
            "--ledger",
            "data/external_api_usage.jsonl",
            "--budgets",
            "data/budgets.tsv",
            "--actuals",
            "data/missing_actuals.tsv",
            "--json-report",
            "exports/cost.json",
            "--markdown-report",
            "exports/cost.md",
            "--email-draft",
            "exports/email.md",
            "--slack-draft",
            "exports/slack.json",
            "--slack-webhook-url",
            "https://example.invalid/slack-webhook",
            "--smtp-password",
            "smtp-secret",
        ]
    )

    combined = "\n".join(
        [
            (tmp_path / "exports" / "cost.json").read_text(encoding="utf-8"),
            (tmp_path / "exports" / "cost.md").read_text(encoding="utf-8"),
            (tmp_path / "exports" / "email.md").read_text(encoding="utf-8"),
            (tmp_path / "exports" / "slack.json").read_text(encoding="utf-8"),
        ]
    )
    assert exit_code == 0
    assert "hooks.slack.com/services/T000" not in combined
    assert "smtp-secret" not in combined


def test_fail_on_alert_uses_warning_and_critical_exit_codes(tmp_path):
    sample_budgets(tmp_path / "data" / "budgets.tsv")
    write_jsonl(
        tmp_path / "data" / "external_api_usage.jsonl",
        [{"day": "2026-06-10", "provider": "seedance_api", "operation": "generation_create", "billable": True, "outcome": "success"}],
    )

    warning_code = dashboard.main(
        [
            "--root",
            str(tmp_path),
            "--start-date",
            "2026-06-09",
            "--end-date",
            "2026-06-15",
            "--ledger",
            "data/external_api_usage.jsonl",
            "--budgets",
            "data/budgets.tsv",
            "--json-report",
            "exports/warning.json",
            "--markdown-report",
            "exports/warning.md",
            "--email-draft",
            "exports/warning-email.md",
            "--slack-draft",
            "exports/warning-slack.json",
            "--fail-on-alert",
        ]
    )
    assert warning_code == 1

    write_tsv(
        tmp_path / "data" / "actuals.tsv",
        [
            {
                "period_start": "2026-06-09",
                "period_end": "2026-06-15",
                "cost_center": "ai_api_seedance",
                "amount_usd": "11.00",
                "source": "BytePlus console",
                "notes": "test",
            }
        ],
    )
    critical_code = dashboard.main(
        [
            "--root",
            str(tmp_path),
            "--start-date",
            "2026-06-09",
            "--end-date",
            "2026-06-15",
            "--ledger",
            "data/external_api_usage.jsonl",
            "--budgets",
            "data/budgets.tsv",
            "--actuals",
            "data/actuals.tsv",
            "--json-report",
            "exports/critical.json",
            "--markdown-report",
            "exports/critical.md",
            "--email-draft",
            "exports/critical-email.md",
            "--slack-draft",
            "exports/critical-slack.json",
            "--fail-on-alert",
        ]
    )
    assert critical_code == 2
