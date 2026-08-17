import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.sales_autopilot_engine import SalesAutopilotEngine


def test_sales_autopilot_engine_overnight_batch():
    engine = SalesAutopilotEngine()

    emails = [
        {"id": "P1", "title": "【Python/FastAPI】AI案件", "skills": ["Python", "FastAPI"], "client_name": "A社"},
        {"id": "P2", "title": "【Go】マイクロサービス", "skills": ["Go", "Kubernetes"], "client_name": "B社"},
    ]

    talent = [
        {"id": "E1", "name": "佐藤 賢太", "skills": ["Python", "FastAPI", "AWS"]},
        {"id": "E2", "name": "田中 太郎", "skills": ["Go", "Docker", "Kubernetes"]},
    ]

    report = engine.run_overnight_batch(emails, talent)
    assert report.processed_emails_count == 2
    assert report.matched_queue_items_count == 2
    assert report.average_fit_score >= 80.0
    assert len(engine.dispatch_queue) == 2
    assert "佐藤 賢太" in engine.dispatch_queue[0].matched_engineer_name
