"""Analytics and matching must use the same Japanese calendar date."""

import asyncio
import datetime
from types import SimpleNamespace

import pytest

import app as app_module
from sales_email_match import normalize_received_timestamp


def analytics_at(monkeypatch, now, received):
    class Clock(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    clock_module = SimpleNamespace(**vars(datetime))
    clock_module.datetime = Clock
    monkeypatch.setattr(app_module, "datetime", clock_module)
    monkeypatch.setenv("SUPABASE_DB_URL", "test-only-no-network")
    monkeypatch.setattr(app_module, "load_extraction_report_from_postgres", lambda: {
        "extractions": [{"received_at": value, "source_type": "imap"} for value in received],
    })
    return asyncio.run(app_module.get_sales_email_analytics())


@pytest.mark.parametrize("received", [
    "2026-09-19T15:00:00Z",
    "Sat, 19 Sep 2026 15:00:00 +0000",
    "2026-09-20T10:00:00+10:00",
    "2026-09-19T08:00:00-07:00",
    "2026-09-20T00:00:00+09:00",
    "2026-09-20T00:00:00",
    "2026-09-20",
])
def test_daily_analytics_agree_with_matching_dates(monkeypatch, received):
    now = datetime.datetime(2026, 9, 19, 16, tzinfo=datetime.timezone.utc)
    result = analytics_at(monkeypatch, now, [received])
    assert result["daily_counts"] == {normalize_received_timestamp(received)[1]: 1}
    assert result["today_new_count"] == 1
    assert result["source_breakdown"]["today_new"] == 1
    assert result["total_count"] == result["server_direct_count"] == 1


@pytest.mark.parametrize("utc_now, expected", [
    ("2026-09-19T14:59:59+00:00", 1),
    ("2026-09-19T15:00:00+00:00", 2),
    ("2026-09-20T00:00:00+00:00", 2),
    ("2026-09-20T15:00:00+00:00", 0),
])
def test_today_changes_at_jst_midnight(monkeypatch, utc_now, expected):
    result = analytics_at(monkeypatch, datetime.datetime.fromisoformat(utc_now), [
        "2026-09-19T14:59:59Z", "2026-09-19T15:00:00Z", "2026-09-20T01:00:00+09:00",
    ])
    assert result["daily_counts"] == {"2026-09-19": 1, "2026-09-20": 2}
    assert result["today_new_count"] == expected
    assert result["analytics_timezone"] == "Asia/Tokyo"


def test_empty_analytics_declare_same_timezone(monkeypatch, tmp_path):
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.setattr(app_module, "SALES_EMAIL_MATCH_REPORT_FILE", str(tmp_path / "missing.json"))
    result = asyncio.run(app_module.get_sales_email_analytics())
    assert result["total_count"] == 0
    assert result["daily_counts"] == {}
    assert result["analytics_timezone"] == "Asia/Tokyo"
