"""Test suite for Interactive Webhook Handler module (T966)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from interactive_webhook import handle_interactive_action

def test_handle_interactive_action_propose():
    res = handle_interactive_action(
        action_type="propose",
        job_id="job_123",
        engineer_id="eng_456",
        user_id="sales_tanaka"
    )
    assert res["status"] == "success"
    assert res["action_type"] == "propose"
    assert "提案キューに登録" in res["status_message"]

def test_handle_interactive_action_keep():
    res = handle_interactive_action(
        action_type="keep",
        job_id="job_123",
        engineer_id="eng_456"
    )
    assert res["status"] == "success"
    assert "キープリストに保存" in res["status_message"]

def test_handle_interactive_action_reject():
    res = handle_interactive_action(
        action_type="reject",
        job_id="job_123",
        engineer_id="eng_456",
        reason="単価がクライアント上限を超過"
    )
    assert res["status"] == "success"
    assert res["reason_recorded"] == "単価がクライアント上限を超過"
    assert "AIフィードバックフライホイール" in res["next_step"]

def test_handle_interactive_action_invalid():
    res = handle_interactive_action(
        action_type="invalid_action",
        job_id="job_123",
        engineer_id="eng_456"
    )
    assert res["status"] == "error"
