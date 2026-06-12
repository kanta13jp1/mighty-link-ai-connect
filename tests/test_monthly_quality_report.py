# -*- coding: utf-8 -*-
"""Tests for scripts/generate_monthly_quality_report.py (T764)."""
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import generate_monthly_quality_report as report


def test_month_bounds_and_prev_month():
    first, next_first = report.month_bounds("2026-06")
    assert first == date(2026, 6, 1)
    assert next_first == date(2026, 7, 1)
    assert report.month_bounds("2026-12")[1] == date(2027, 1, 1)
    assert report.prev_month("2026-06") == "2026-05"
    assert report.prev_month("2026-01") == "2025-12"


def test_parse_date_supports_tsv_formats():
    assert report.parse_date("2026-06-13") == date(2026, 6, 13)
    assert report.parse_date("2026-06-13 10:00") == date(2026, 6, 13)
    assert report.parse_date("") is None
    assert report.parse_date("-") is None


def test_wbs_progress_against_repo_data():
    today = date(2026, 6, 13)
    wbs = report.wbs_progress("2026-06", today)
    assert wbs["total"] > 0
    assert 0 < wbs["done_total"] <= wbs["total"]
    assert wbs["done_this_month"] <= wbs["done_total"]
    assert 0.0 < wbs["completion_pct"] <= 100.0
    # delayed rows must be incomplete and past due
    for row in wbs["delayed"]:
        assert row.get("ステータス") != "完了"
        assert report.parse_date(row.get("終了予定日", "")) < today
    assert len(wbs["upcoming"]) <= 5


def test_render_contains_required_sections():
    content = report.render("2026-06", date(2026, 6, 13))
    for heading in (
        "## 1. WBS 進捗",
        "## 2. サービス品質 KPI",
        "## 3. 外部 API 利用・コスト",
        "## 4. インシデント・課題",
        "## 5. 翌月（または直近）の優先アクション",
        "## 6. 参照リンク",
    ):
        assert heading in content
    # mid-month run must be flagged as interim snapshot
    assert "中間スナップショット" in content
    # final run (1st of following month) must not be flagged
    final = report.render("2026-06", date(2026, 7, 1))
    assert "中間スナップショット" not in final


def test_usage_summary_aggregates_audit_files():
    usage = report.usage_summary("2026-06")
    assert usage["audit_days"] >= 1
    assert "seedance_api:generation_create" in usage["providers"]
    blocked = usage["providers"]["seedance_api:generation_create"]["blocked"]
    assert blocked >= 8
