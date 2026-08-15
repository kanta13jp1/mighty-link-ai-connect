"""Test suite for Client Credibility Scorer module (T970)."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from client_credibility_scorer import analyze_client_credibility

def test_analyze_client_credibility_direct():
    text = "【エンド直請け】自社開発サービスの新規立ち上げ案件です。支払いサイトは月末締め翌月末払い。"
    res = analyze_client_credibility(text)
    assert res["status"] == "success"
    assert res["chain_score"] == 100.0
    assert "エンド直" in res["chain_depth_type"]
    assert res["credibility_score"] >= 90.0
    assert res["is_safe_to_propose"] is True

def test_analyze_client_credibility_deep_chain():
    text = "大手通信会社向けの多重再委託案件です。支払いサイトは月末締め翌々月末払い（60日）。"
    res = analyze_client_credibility(text)
    assert res["status"] == "success"
    assert res["chain_score"] <= 60.0
    assert len(res["risk_flags"]) >= 1
    assert "60日" in res["payment_terms"]
