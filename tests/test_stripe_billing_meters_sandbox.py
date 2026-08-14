"""Unit tests for Stripe Billing Meters Sandbox Verification Harness (T958)."""

from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from verify_stripe_billing_meters_sandbox import (
    build_meter_event_payload,
    validate_meter_event,
    verify_stripe_webhook_signature,
    evaluate,
)


def test_build_and_validate_compliant_meter_event():
    evt = build_meter_event_payload("analysis_run", "cus_test123", value=5)
    assert evt["event_name"] == "analysis_run"
    assert evt["payload"]["stripe_customer_id"] == "cus_test123"
    assert evt["payload"]["value"] == "5"
    
    valid, msg = validate_meter_event(evt)
    assert valid is True, msg


def test_validate_rejects_pii_in_payload():
    bad_evt = {
        "event_name": "analysis_run",
        "payload": {
            "stripe_customer_id": "cus_test123",
            "email": "kanta@example.com",
        },
        "identifier": "idemp_001",
        "timestamp": int(time.time()),
    }
    valid, msg = validate_meter_event(bad_evt)
    assert valid is False
    assert "Forbidden PII key" in msg


def test_webhook_signature_verification_success_and_failure():
    secret = "whsec_test_secret"
    payload = b'{"type": "invoice.paid"}'
    ts = int(time.time())
    
    import hmac
    import hashlib
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"
    
    ok, msg = verify_stripe_webhook_signature(payload, header, secret)
    assert ok is True, msg
    
    bad_ok, bad_msg = verify_stripe_webhook_signature(payload, header, "whsec_wrong")
    assert bad_ok is False
    assert "Signature mismatch" in bad_msg


def test_all_hypotheses_evaluate_to_pass():
    results = evaluate()
    assert len(results) == 10
    failing = [r["id"] for r in results if not r["passed"]]
    assert not failing, f"Failing hypotheses: {failing}"
