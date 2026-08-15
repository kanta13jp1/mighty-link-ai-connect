"""Test suite for AI Feedback Flywheel module (T962)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from ai_feedback_flywheel import aggregate_feedback_logs, generate_tuning_context

def test_aggregate_feedback_logs():
    records = [
        {"action": "accept", "job_title": "案件A", "engineer_name": "山田", "skills": ["Python", "AWS"], "reason": "即戦力"},
        {"action": "accept", "job_title": "案件B", "engineer_name": "佐藤", "skills": ["Python", "FastAPI"], "reason": "スキル一致"},
        {"action": "reject", "job_title": "案件C", "engineer_name": "鈴木", "skills": ["Java"], "reason": "単価上限オーバー"}
    ]
    agg = aggregate_feedback_logs(records)
    assert agg["total_feedback_count"] == 3
    assert agg["accepted_count"] == 2
    assert agg["rejected_count"] == 1
    assert agg["preferred_skills"]["Python"] == 2
    assert "単価上限オーバー" in agg["top_rejected_reasons"]

def test_generate_tuning_context():
    records = [
        {"action": "accept", "job_title": "案件A", "engineer_name": "山田", "skills": ["Python", "FastAPI"], "reason": "即戦力"},
        {"action": "reject", "job_title": "案件B", "engineer_name": "鈴木", "skills": ["PHP"], "reason": "フル出社必須のためNG"}
    ]
    agg = aggregate_feedback_logs(records)
    context = generate_tuning_context(agg)
    assert "自社特化型AI学習フィードバック" in context
    assert "Python" in context
    assert "フル出社必須のためNG" in context

def test_generate_tuning_context_empty():
    agg = aggregate_feedback_logs([])
    context = generate_tuning_context(agg)
    assert "蓄積されたフィードバックはまだありません" in context
