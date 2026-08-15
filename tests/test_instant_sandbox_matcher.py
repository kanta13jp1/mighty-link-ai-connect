"""Test suite for Instant Sandbox Matcher module (T969)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from instant_sandbox_matcher import simulate_instant_sandbox_match

def test_simulate_instant_sandbox_match_python():
    res = simulate_instant_sandbox_match(input_skills=["Python", "FastAPI"], desired_rate=80)
    assert res["status"] == "success"
    assert res["estimated_market_rate_man_yen"] >= 80
    assert len(res["top_matched_jobs"]) >= 2
    top = res["top_matched_jobs"][0]
    assert top["match_score"] >= 80.0
    assert "無料登録" in res["cta_message"]

def test_simulate_instant_sandbox_match_generic():
    res = simulate_instant_sandbox_match(input_skills=["Java"], desired_rate=70)
    assert res["status"] == "success"
    assert res["matched_jobs_count"] >= 1
