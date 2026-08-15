"""Test suite for Interview Scheduler module (T968)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from interview_scheduler import (
    generate_interview_candidate_slots,
    build_google_calendar_url,
    create_interview_schedule_package
)

def test_generate_interview_candidate_slots():
    slots = generate_interview_candidate_slots("2026-09-05")
    assert len(slots) == 3
    assert "2026-09-05" in slots[0]
    assert "Google Meet" in slots[0]

def test_build_google_calendar_url():
    url = build_google_calendar_url(
        title="【面談】Pythonエンジニア（田中様）",
        start_iso="2026-09-05 14:00:00",
        end_iso="2026-09-05 15:00:00",
        description="詳細な案件面談"
    )
    assert "calendar.google.com" in url
    assert "TEMPLATE" in url
    assert "20260905T140000" in url

def test_create_interview_schedule_package():
    pkg = create_interview_schedule_package(
        job_title="バックエンド開発",
        client_name="株式会社クライアント",
        engineer_name="山田 太郎",
        proposed_date="2026-09-10"
    )
    assert pkg["status"] == "success"
    assert "google_calendar_url" in pkg
    assert len(pkg["candidate_slots"]) >= 3
