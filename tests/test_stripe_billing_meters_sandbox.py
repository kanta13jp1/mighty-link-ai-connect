"""Regression tests for the fail-closed Stripe meter contract harness (T958)."""

from __future__ import annotations

import hashlib
import hmac
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import verify_stripe_billing_meters_sandbox as guard  # noqa: E402


def signed_header(payload: bytes, secret: str, timestamp: int) -> str:
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def test_builds_valid_meter_event_without_pii():
    event = guard.build_meter_event_payload(
        "analysis_run", "cus_test123", value=2, timestamp=1_800_000_000
    )
    assert guard.validate_meter_event(event) == (True, "Valid")
    assert event["payload"] == {"stripe_customer_id": "cus_test123", "value": "2"}


def test_default_identifiers_are_unique_to_avoid_false_deduplication():
    first = guard.build_meter_event_payload("analysis_run", "cus_test123", timestamp=1_800_000_000)
    second = guard.build_meter_event_payload("analysis_run", "cus_test123", timestamp=1_800_000_000)
    assert first["identifier"] != second["identifier"]


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "1"])
def test_rejects_non_positive_integer_usage(value):
    with pytest.raises(ValueError):
        guard.build_meter_event_payload("analysis_run", "cus_test123", value=value)


def test_rejects_pii_and_unapproved_dimensions():
    event = guard.build_meter_event_payload("analysis_run", "cus_test123")
    event["payload"]["email"] = "person@example.com"
    valid, detail = guard.validate_meter_event(event)
    assert valid is False
    assert "payload" in detail.lower()


def test_rejects_secret_shaped_payload_value():
    event = guard.build_meter_event_payload("analysis_run", "cus_test123")
    event["payload"]["stripe_customer_id"] = "sk_live_not_a_customer"
    assert guard.validate_meter_event(event)[0] is False


def test_webhook_accepts_any_matching_v1_signature_during_rotation():
    payload = b'{"type":"invoice.paid"}'
    secret = "whsec_test_secret"
    timestamp = 1_800_000_000
    good = signed_header(payload, secret, timestamp).split("v1=", 1)[1]
    header = f"t={timestamp},v1=bad,v1={good}"
    assert guard.verify_stripe_webhook_signature(
        payload, header, secret, current_time=timestamp
    )[0]


def test_webhook_rejects_replay_and_zero_tolerance():
    payload = b"{}"
    secret = "whsec_test_secret"
    timestamp = 1_800_000_000
    header = signed_header(payload, secret, timestamp)
    assert not guard.verify_stripe_webhook_signature(
        payload, header, secret, current_time=timestamp + 301
    )[0]
    assert not guard.verify_stripe_webhook_signature(
        payload, header, secret, tolerance_seconds=0, current_time=timestamp
    )[0]


def test_sandbox_environment_fails_closed_for_live_or_unknown_keys():
    assert not guard.sandbox_environment_check({"STRIPE_SECRET_KEY": "sk_live_redacted"})[0]
    assert not guard.sandbox_environment_check({"STRIPE_SECRET_KEY": "opaque"})[0]


def test_sandbox_environment_distinguishes_offline_and_required_modes():
    offline_ok, offline_detail = guard.sandbox_environment_check({})
    assert offline_ok and "no API call" in offline_detail
    assert not guard.sandbox_environment_check({}, require_sandbox_key=True)[0]
    assert guard.sandbox_environment_check(
        {"STRIPE_SECRET_KEY": "sk_test_redacted"}, require_sandbox_key=True
    )[0]


def test_real_repo_evaluation_is_honest_about_offline_scope():
    results = guard.evaluate()
    assert len(results) == 10
    assert all(result["passed"] for result in results)
    h9 = next(result for result in results if result["id"] == "H9")
    h10 = next(result for result in results if result["id"] == "H10")
    assert "API call made" in h9["detail"] or "credential boundary verified" in h9["detail"]
    assert "API未呼び出し" in h10["detail"]
