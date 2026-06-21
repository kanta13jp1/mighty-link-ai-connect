import os
import sys

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import app
from stripe_customer_portal import (
    StripePortalError,
    build_customer_portal_payload,
    create_customer_portal_session,
    sanitized_payload,
)


class FakeStripeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def client():
    return TestClient(app.app)


def test_build_customer_portal_payload_for_subscription_cancel():
    payload = build_customer_portal_payload(
        customer_id="cus_test_123456",
        return_url="https://mightylink-app.com/billing",
        configuration_id="bpc_test_123",
        flow_type="subscription_cancel",
        subscription_id="sub_test_456789",
        locale="ja",
    )

    assert payload["customer"] == "cus_test_123456"
    assert payload["return_url"] == "https://mightylink-app.com/billing"
    assert payload["configuration"] == "bpc_test_123"
    assert payload["locale"] == "ja"
    assert payload["flow_data[type]"] == "subscription_cancel"
    assert payload["flow_data[subscription_cancel][subscription]"] == "sub_test_456789"
    assert payload["flow_data[after_completion][type]"] == "redirect"


def test_subscription_flow_requires_subscription_id():
    with pytest.raises(ValueError, match="subscription_id is required"):
        build_customer_portal_payload(
            customer_id="cus_test_123456",
            return_url="https://mightylink-app.com/billing",
            flow_type="subscription_update",
        )


def test_sanitized_payload_masks_customer_and_subscription_ids():
    payload = build_customer_portal_payload(
        customer_id="cus_test_123456",
        return_url="https://mightylink-app.com/billing",
        flow_type="subscription_cancel",
        subscription_id="sub_test_456789",
    )
    safe_payload = sanitized_payload(payload)

    assert safe_payload["customer"] == "cus_...3456"
    assert safe_payload["flow_data[subscription_cancel][subscription]"] == "sub_...6789"
    assert "cus_test_123456" not in str(safe_payload)
    assert "sub_test_456789" not in str(safe_payload)


def test_create_customer_portal_session_posts_form_payload():
    calls = {}

    def fake_post(url, data, headers, timeout):
        calls["url"] = url
        calls["data"] = data
        calls["headers"] = headers
        calls["timeout"] = timeout
        return FakeStripeResponse(
            200,
            {
                "id": "bps_test_123",
                "object": "billing_portal.session",
                "url": "https://billing.stripe.com/session/test",
                "livemode": False,
                "customer": "cus_test_123456",
                "return_url": "https://mightylink-app.com/billing",
            },
        )

    payload = {"customer": "cus_test_123456", "return_url": "https://mightylink-app.com/billing"}
    session = create_customer_portal_session(
        secret_key="test_secret_key",
        payload=payload,
        timeout_seconds=7,
        post=fake_post,
    )

    assert calls["url"].endswith("/v1/billing_portal/sessions")
    assert calls["data"] == payload
    assert calls["headers"]["Authorization"] == "Bearer test_secret_key"
    assert calls["timeout"] == 7
    assert session["url"] == "https://billing.stripe.com/session/test"


def test_create_customer_portal_session_raises_sanitized_error():
    def fake_post(url, data, headers, timeout):
        return FakeStripeResponse(
            400,
            {"error": {"message": "No such customer.", "code": "resource_missing"}},
        )

    with pytest.raises(StripePortalError) as excinfo:
        create_customer_portal_session(
            secret_key="sk_test_123",
            payload={"customer": "cus_missing", "return_url": "https://mightylink-app.com/billing"},
            post=fake_post,
        )

    assert "No such customer" in str(excinfo.value)
    assert "test_secret_key" not in str(excinfo.value)


def test_billing_page_renders(client):
    response = client.get("/billing")

    assert response.status_code == 200
    assert "Billing Portal" in response.text
    assert "customer-id" in response.text


def test_billing_portal_dry_run_does_not_require_secret(client, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_CUSTOMER_PORTAL_ENABLED", raising=False)

    response = client.post(
        "/api/billing/customer-portal/session",
        json={
            "customer_id": "cus_test_123456",
            "return_url": "https://mightylink-app.com/billing",
            "flow_type": "payment_method_update",
            "dry_run": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "preview"
    assert body["mode"] == "dry_run"
    assert body["stripe_secret_configured"] is False
    assert body["payload"]["customer"] == "cus_...3456"
    assert "cus_test_123456" not in response.text


def test_billing_portal_live_route_uses_configured_stripe_factory(client, monkeypatch):
    captured = {}

    def fake_create_customer_portal_session(*, secret_key, payload):
        captured["secret_key"] = secret_key
        captured["payload"] = payload
        return {
            "id": "bps_test_123",
            "url": "https://billing.stripe.com/session/test",
            "livemode": False,
            "return_url": payload["return_url"],
        }

    monkeypatch.setenv("STRIPE_CUSTOMER_PORTAL_ENABLED", "1")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "test_secret_key")
    monkeypatch.setattr(app, "create_customer_portal_session", fake_create_customer_portal_session)

    response = client.post(
        "/api/billing/customer-portal/session",
        json={
            "customer_id": "cus_test_123456",
            "return_url": "https://mightylink-app.com/billing",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["url"] == "https://billing.stripe.com/session/test"
    assert captured["secret_key"] == "test_secret_key"
    assert captured["payload"]["customer"] == "cus_test_123456"
