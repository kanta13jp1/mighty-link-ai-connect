"""Stripe Customer Portal helpers.

The app only creates short-lived Stripe-hosted portal sessions. It does not
store Stripe secrets, customer IDs, or subscription IDs in project artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

import requests


STRIPE_PORTAL_SESSION_URL = "https://api.stripe.com/v1/billing_portal/sessions"
ALLOWED_FLOW_TYPES = {
    "",
    None,
    "payment_method_update",
    "subscription_cancel",
    "subscription_update",
}
SUBSCRIPTION_SCOPED_FLOWS = {"subscription_cancel", "subscription_update"}


@dataclass
class StripePortalError(Exception):
    """Raised when Stripe cannot create a Customer Portal session."""

    message: str
    status_code: Optional[int] = None
    code: Optional[str] = None

    def __str__(self) -> str:
        suffixes = []
        if self.status_code is not None:
            suffixes.append(f"status={self.status_code}")
        if self.code:
            suffixes.append(f"code={self.code}")
        if not suffixes:
            return self.message
        return f"{self.message} ({', '.join(suffixes)})"


def _require_non_empty(name: str, value: Optional[str]) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{name} is required.")
    return normalized


def _require_http_url(name: str, value: Optional[str]) -> str:
    normalized = _require_non_empty(name, value)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{name} must be an http or https URL.")
    return normalized


def normalize_flow_type(flow_type: Optional[str]) -> str:
    flow = (flow_type or "").strip()
    if flow not in ALLOWED_FLOW_TYPES:
        allowed = ", ".join(sorted(item for item in ALLOWED_FLOW_TYPES if item))
        raise ValueError(f"flow_type must be empty or one of: {allowed}.")
    return flow


def build_customer_portal_payload(
    *,
    customer_id: str,
    return_url: str,
    configuration_id: Optional[str] = None,
    flow_type: Optional[str] = None,
    subscription_id: Optional[str] = None,
    locale: Optional[str] = None,
) -> Dict[str, str]:
    """Build Stripe's x-www-form-urlencoded Customer Portal payload."""

    customer = _require_non_empty("customer_id", customer_id)
    portal_return_url = _require_http_url("return_url", return_url)
    flow = normalize_flow_type(flow_type)

    payload: Dict[str, str] = {
        "customer": customer,
        "return_url": portal_return_url,
    }

    if configuration_id:
        payload["configuration"] = configuration_id.strip()
    if locale:
        payload["locale"] = locale.strip()

    if not flow:
        return payload

    payload["flow_data[type]"] = flow
    payload["flow_data[after_completion][type]"] = "redirect"
    payload["flow_data[after_completion][redirect][return_url]"] = portal_return_url

    if flow in SUBSCRIPTION_SCOPED_FLOWS:
        subscription = _require_non_empty("subscription_id", subscription_id)
        payload[f"flow_data[{flow}][subscription]"] = subscription

    return payload


def mask_identifier(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = value.strip()
    if len(normalized) <= 8:
        return "***"
    return f"{normalized[:4]}...{normalized[-4:]}"


def sanitized_payload(payload: Dict[str, str]) -> Dict[str, str]:
    """Return a log-safe payload preview."""

    sanitized: Dict[str, str] = {}
    for key, value in payload.items():
        if key == "customer" or key.endswith("[subscription]"):
            sanitized[key] = mask_identifier(value)
        else:
            sanitized[key] = value
    return sanitized


def create_customer_portal_session(
    *,
    secret_key: str,
    payload: Dict[str, str],
    timeout_seconds: int = 15,
    post: Callable[..., Any] = requests.post,
) -> Dict[str, Any]:
    """Create a Stripe Customer Portal session and return selected fields."""

    key = _require_non_empty("secret_key", secret_key)
    try:
        response = post(
            STRIPE_PORTAL_SESSION_URL,
            data=payload,
            headers={"Authorization": f"Bearer {key}"},
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise StripePortalError("Stripe Customer Portal request failed.") from exc

    try:
        response_data = response.json()
    except ValueError as exc:
        raise StripePortalError(
            "Stripe Customer Portal response was not JSON.",
            status_code=getattr(response, "status_code", None),
        ) from exc

    if getattr(response, "status_code", 500) >= 400:
        error = response_data.get("error", {}) if isinstance(response_data, dict) else {}
        raise StripePortalError(
            str(error.get("message") or "Stripe Customer Portal session creation failed."),
            status_code=getattr(response, "status_code", None),
            code=error.get("code") or error.get("type"),
        )

    url = response_data.get("url") if isinstance(response_data, dict) else None
    if not url:
        raise StripePortalError(
            "Stripe Customer Portal session response did not include a URL.",
            status_code=getattr(response, "status_code", None),
        )

    return {
        "id": response_data.get("id"),
        "url": url,
        "livemode": response_data.get("livemode"),
        "customer": response_data.get("customer"),
        "configuration": response_data.get("configuration"),
        "return_url": response_data.get("return_url"),
        "flow": response_data.get("flow"),
    }
