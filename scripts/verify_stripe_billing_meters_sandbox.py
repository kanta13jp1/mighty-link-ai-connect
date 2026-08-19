"""Stripe Billing Meters API Sandbox Verification Guard & Test Harness (T958 / T791).

Validates:
1. Meter event payload structure complies with Stripe Billing Meters API specifications.
2. Zero-PII policy: No raw customer email, CV content, or raw email body in event payloads.
3. Idempotency & deduplication keys (identifier) are properly generated and handled.
4. Webhook event signatures (stripe-signature header) are strictly validated with tolerance window.
5. Sandbox / test-mode execution safety: live keys and customer real card data are forbidden.
6. 10 Hypotheses are evaluated and exported to exports/stripe_billing_meters_sandbox_audit.{json,md}.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = PROJECT_ROOT / "exports" / "stripe_billing_meters_sandbox_audit.json"
DEFAULT_MD = PROJECT_ROOT / "exports" / "stripe_billing_meters_sandbox_audit.md"

VALID_EVENT_NAMES = {
    "analysis_run",
    "sales_email_match_run",
    "admin_export_run",
}

FORBIDDEN_PII_KEYS = {
    "email",
    "password",
    "raw_body",
    "sender_email",
    "candidate_name",
    "card_number",
    "cvv",
}
ALLOWED_EVENT_KEYS = {"event_name", "payload", "identifier", "timestamp"}
ALLOWED_PAYLOAD_KEYS = {"stripe_customer_id", "value"}
EMAIL_LIKE = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
SECRET_LIKE = re.compile(r"\b(?:sk|rk|whsec)_(?:live|test)_[A-Za-z0-9_]+\b", re.I)


def build_meter_event_payload(
    event_name: str,
    stripe_customer_id: str,
    value: int = 1,
    idempotency_key: str | None = None,
    timestamp: int | None = None,
) -> dict[str, Any]:
    """Construct a compliant Stripe Meter Event payload."""
    if event_name not in VALID_EVENT_NAMES:
        raise ValueError(f"Invalid meter event_name: {event_name}")
    if not stripe_customer_id.startswith("cus_"):
        raise ValueError("stripe_customer_id must use a Stripe test customer ID")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("value must be a positive integer")

    ts = int(time.time()) if timestamp is None else timestamp
    if not isinstance(ts, int) or ts <= 0:
        raise ValueError("timestamp must be a positive Unix timestamp")
    key = idempotency_key or f"meter_{uuid.uuid4().hex}"

    return {
        "event_name": event_name,
        "payload": {
            "stripe_customer_id": stripe_customer_id,
            "value": str(value),
        },
        "identifier": key,
        "timestamp": ts,
    }


def validate_meter_event(event: dict[str, Any]) -> tuple[bool, str]:
    """Validate that the meter event complies with zero-PII and format constraints."""
    if not isinstance(event, dict):
        return False, "Event is not a dict"

    extra_event_keys = set(event) - ALLOWED_EVENT_KEYS
    if extra_event_keys:
        return False, f"Unexpected event keys: {sorted(extra_event_keys)}"

    event_name = event.get("event_name")
    if event_name not in VALID_EVENT_NAMES:
        return False, f"Invalid event_name: {event_name}"

    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        return False, "Payload is not a dict"

    extra_payload_keys = set(payload) - ALLOWED_PAYLOAD_KEYS
    if extra_payload_keys:
        return False, f"Unexpected payload keys: {sorted(extra_payload_keys)}"
    if any(str(key).lower() in FORBIDDEN_PII_KEYS for key in payload):
        return False, "Forbidden PII key detected in meter payload"

    customer_id = payload.get("stripe_customer_id")
    if not isinstance(customer_id, str) or not customer_id.startswith("cus_"):
        return False, "Missing or invalid stripe_customer_id in payload"
    value = payload.get("value")
    if not isinstance(value, str) or not value.isdigit() or int(value) <= 0:
        return False, "Meter value must be a positive integer string"
    if any(
        EMAIL_LIKE.search(str(item)) or SECRET_LIKE.search(str(item))
        for item in payload.values()
    ):
        return False, "PII or secret-shaped value detected in meter payload"

    identifier = event.get("identifier")
    if not isinstance(identifier, str) or len(identifier) < 8:
        return False, "Missing or invalid identifier (idempotency key)"
    timestamp = event.get("timestamp")
    if not isinstance(timestamp, int) or timestamp <= 0:
        return False, "Missing or invalid Unix timestamp"

    return True, "Valid"


def verify_stripe_webhook_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
    tolerance_seconds: int = 300,
    current_time: int | None = None,
) -> tuple[bool, str]:
    """Verify a Stripe-style webhook signature against the raw payload."""
    if not signature_header or not secret:
        return False, "Missing signature header or secret"
    if tolerance_seconds <= 0:
        return False, "tolerance_seconds must be greater than zero"

    timestamp_str: str | None = None
    v1_signatures: list[str] = []
    for item in signature_header.split(","):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            if k == "t":
                timestamp_str = v
            elif k == "v1":
                v1_signatures.append(v)

    if not timestamp_str or not v1_signatures:
        return False, "Malformed signature header (missing t or v1)"

    try:
        ts = int(timestamp_str)
    except ValueError:
        return False, "Invalid timestamp in signature header"

    now = int(time.time()) if current_time is None else current_time
    age = abs(now - ts)
    if age > tolerance_seconds:
        return False, f"Timestamp outside tolerance window ({age}s > {tolerance_seconds}s)"

    signed_payload = f"{timestamp_str}.".encode("utf-8") + payload
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not any(hmac.compare_digest(expected_sig, candidate) for candidate in v1_signatures):
        return False, "Signature mismatch"

    return True, "Signature verified successfully"


def stripe_key_mode(api_key: str | None) -> str:
    """Classify a Stripe key without returning or logging the key itself."""
    if not api_key:
        return "not_configured"
    if api_key.startswith("sk_test_"):
        return "sandbox"
    if api_key.startswith("sk_live_"):
        return "live"
    return "unknown"


def sandbox_environment_check(
    environment: dict[str, str] | None = None,
    *,
    require_sandbox_key: bool = False,
) -> tuple[bool, str]:
    """Fail closed when a live or unrecognized Stripe key is configured."""
    env = os.environ if environment is None else environment
    modes = {
        name: stripe_key_mode(env.get(name))
        for name in ("STRIPE_SECRET_KEY", "STRIPE_API_KEY")
    }
    configured = {mode for mode in modes.values() if mode != "not_configured"}
    if "live" in configured:
        return False, "Live Stripe credential detected; sandbox verification blocked"
    if "unknown" in configured:
        return False, "Unrecognized Stripe credential detected; fail closed"
    if require_sandbox_key and "sandbox" not in configured:
        return False, "Sandbox credential is required but not configured"
    if "sandbox" in configured:
        return True, "Sandbox credential boundary verified (credential value not logged)"
    return True, "Offline contract mode; no Stripe credential loaded and no API call made"


def _hyp(hid: str, title: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": hid, "title": title, "passed": bool(passed), "detail": detail}


def evaluate(*, require_sandbox_key: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    # H1: Valid event payload creation
    sample_evt = build_meter_event_payload("analysis_run", "cus_test123", value=1)
    is_valid, msg = validate_meter_event(sample_evt)
    results.append(_hyp("H1", "Billing Meterイベントペイロードが仕様に準拠", is_valid, msg))

    # H2: Zero-PII verification
    bad_evt = {
        "event_name": "analysis_run",
        "payload": {"stripe_customer_id": "cus_test123", "email": "user@example.com"},
        "identifier": "evt_123",
        "timestamp": int(time.time()),
    }
    pii_valid, _ = validate_meter_event(bad_evt)
    results.append(_hyp("H2", "要配慮個人情報・生メールアドレスのメーター送信を完全遮断", not pii_valid, "PII payload properly rejected"))

    # H3: Valid event names coverage
    all_names_ok = all(
        validate_meter_event(build_meter_event_payload(name, "cus_test123"))[0]
        for name in VALID_EVENT_NAMES
    )
    results.append(_hyp("H3", "全3種の定義済み課金メーター (analysis/sales_email/admin) の正常生成", all_names_ok, f"Events: {sorted(VALID_EVENT_NAMES)}"))

    # H4: Idempotency identifier stability
    evt_a = build_meter_event_payload("sales_email_match_run", "cus_test123", idempotency_key="idemp_fixed_1")
    results.append(_hyp("H4", "冪等性キー (identifier) の指定と重複防止構造", evt_a.get("identifier") == "idemp_fixed_1", "Idempotency key preserved"))

    # H5: Webhook signature verification
    secret = "whsec_test_secret_12345"
    payload = b'{"type": "meter.event_received", "id": "evt_001"}'
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"

    wh_ok, wh_msg = verify_stripe_webhook_signature(payload, header, secret)
    results.append(_hyp("H5", "Stripe Webhook 署名検証 (HMAC-SHA256) が正常動作", wh_ok, wh_msg))

    # H6: Webhook signature rejection on invalid secret
    wh_bad, _ = verify_stripe_webhook_signature(payload, header, "whsec_wrong_secret")
    results.append(_hyp("H6", "不正署名 Webhook リクエストを安全に拒絶", not wh_bad, "Invalid signature rejected"))

    # H7: Webhook timestamp tolerance window
    old_ts = ts - 600
    old_sig = hmac.new(secret.encode(), f"{old_ts}.".encode() + payload, hashlib.sha256).hexdigest()
    old_header = f"t={old_ts},v1={old_sig}"
    wh_expired, exp_msg = verify_stripe_webhook_signature(payload, old_header, secret, tolerance_seconds=300)
    results.append(_hyp("H7", "リプレイ攻撃対策 (Timestamp Tolerance 超過リクエストの遮断)", not wh_expired, exp_msg))

    # H8: Design document linkage
    design_doc = PROJECT_ROOT / "docs" / "STRIPE_BILLING_INTEGRATION_DESIGN.md"
    results.append(_hyp("H8", "Stripe Billing 統合設計書 (T776/T791) が実在し整合", design_doc.is_file(), str(design_doc.name)))

    # H9: Sandbox isolation policy
    sandbox_ok, sandbox_detail = sandbox_environment_check(
        require_sandbox_key=require_sandbox_key
    )
    results.append(_hyp(
        "H9",
        "Stripe Sandbox認証境界（liveキー検出時はfail-closed）",
        sandbox_ok,
        sandbox_detail,
    ))

    # H10: Overall status
    all_ok = all(r["passed"] for r in results)
    results.append(_hyp(
        "H10",
        "Stripe Billing Metersオフライン契約ハーネス総合判定",
        all_ok,
        "PASS (API未呼び出し)" if all_ok else "FAIL",
    ))

    return results


def render_markdown(results: list[dict[str, Any]]) -> str:
    passed = all(r["passed"] for r in results)
    lines = [
        "# Stripe Billing Meters API Sandbox 検証監査 (T958 / T791)",
        "",
        f"- **総合判定**: {'✅ PASS' if passed else '❌ FAIL'}",
        "- **検証モード**: オフライン契約検証（Stripe APIへの送信なし）",
        f"- **対象メトリクス**: `{sorted(VALID_EVENT_NAMES)}`",
        "",
        "## 10仮説の検証結果",
        "",
        "| 仮説 | 内容 | 判定 | 詳細 |",
        "| :-- | :-- | :-- | :-- |",
    ]
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['id']} | {r['title']} | {mark} | {r['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Stripe Billing Meters Sandbox Test Harness (T958)")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    parser.add_argument(
        "--require-sandbox-key",
        action="store_true",
        help="fail unless a test/sandbox Stripe key is configured",
    )
    args = parser.parse_args()

    results = evaluate(require_sandbox_key=args.require_sandbox_key)
    passed = all(r["passed"] for r in results)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps({"passed": passed, "hypotheses": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_content = render_markdown(results)
    args.md.write_text(md_content, encoding="utf-8")
    print(md_content)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
