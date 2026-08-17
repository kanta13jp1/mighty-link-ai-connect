import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.browser_extension_bridge import BrowserExtensionBridge, ExtensionMatchRequest


def test_browser_extension_match_request():
    bridge = BrowserExtensionBridge(stripe_meter_enabled=True)
    req = ExtensionMatchRequest(
        page_url="https://mail.google.com/mail/u/0/#inbox/189283",
        extracted_text="急募: FastAPIおよびAWSでのバックエンド開発経験者を探しております。月額85万円〜。",
        source="gmail",
        api_key="sk_live_test_key"
    )

    resp = bridge.process_extension_request(req)
    assert resp.success is True
    assert "FastAPI" in resp.extracted_skills
    assert resp.top_candidate_score >= 90
    assert resp.stripe_meter_event_id is not None
    assert len(bridge.meter_events) == 1


def test_browser_extension_placement_billing():
    bridge = BrowserExtensionBridge()
    billing = bridge.record_successful_placement_billing(
        project_id="PROJ-AI-01",
        candidate_id="ENG-01",
        placement_fee_yen=350000
    )
    assert billing["fee_yen"] == 350000
    assert billing["status"] == "billed"
    assert "placement_fee_" in billing["event_id"]
