#!/usr/bin/env python3
"""Run a secret-safe production onboarding UAT against mightylink-app.com.

The report records only HTTP statuses and boolean contract checks. Basic Auth
credentials, account identifiers, session tokens, response bodies, and raw
pseudonyms are intentionally excluded from both stdout and the JSON artifact.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_URL = "https://mightylink-app.com/"
DEFAULT_REPORT = Path("exports/production_onboarding_uat_report.json")
ALLOWED_HOSTS = {"mightylink-app.com"}


def _base_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("UAT URL must be the approved HTTPS production host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("UAT URL must not contain credentials, query, or fragment")
    return value.rstrip("/")


def _auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    auth_header: str | None = None,
    timeout: int = 20,
) -> tuple[int, dict[str, Any]]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mighty-Link-Production-Onboarding-UAT/1.0",
    }
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if auth_header:
        headers["Authorization"] = auth_header
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 -- host is allowlisted.
            status = response.status
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    try:
        decoded = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        decoded = {}
    return status, decoded if isinstance(decoded, dict) else {}


def run_uat(base_url: str, username: str, password: str, run_id: str) -> dict[str, Any]:
    base = _base_url(base_url)
    auth = _auth_header(username, password)
    state_url = f"{base}/api/onboarding/state"
    progress_url = f"{base}/api/onboarding/progress"
    activate_url = f"{base}/api/onboarding/activate"

    unauth_status, _ = _request(state_url)
    state_status, state = _request(state_url, auth_header=auth)
    required_ids = state.get("required_step_ids") or [
        item.get("id")
        for item in state.get("steps", [])
        if isinstance(item, dict) and item.get("required")
    ]
    required_ids = [value for value in required_ids if isinstance(value, str) and value]
    legal_version = state.get("legal_consent_version")
    flow_version = state.get("flow_version")

    progress_status, progress = _request(
        progress_url,
        method="POST",
        payload={"completed_step_ids": required_ids},
        auth_header=auth,
    )
    identifier = f"github-actions-uat-{run_id}"
    common = {
        "account_identifier": identifier,
        "completed_step_ids": required_ids,
        "legal_consent_accepted": True,
        "source": "production_uat",
        "page_url": f"{base}/",
        "session_id": f"production-onboarding-uat-{run_id}",
    }
    stale_status, _ = _request(
        activate_url,
        method="POST",
        payload={**common, "legal_consent_version": "MSB-LEGAL-STALE-UAT"},
        auth_header=auth,
    )
    activate_status, activated = _request(
        activate_url,
        method="POST",
        payload={**common, "legal_consent_version": legal_version},
        auth_header=auth,
    )

    checks = {
        "unauthenticated_state_is_401": unauth_status == 401,
        "authenticated_state_is_200": state_status == 200,
        "canonical_required_steps_present": bool(required_ids),
        "legal_consent_version_present": isinstance(legal_version, str) and bool(legal_version),
        "progress_is_activatable": progress_status == 200 and progress.get("can_activate") is True,
        "stale_legal_consent_is_rejected": stale_status == 400,
        "activation_succeeds": (
            activate_status == 200
            and activated.get("activated") is True
            and activated.get("auth_status") == "authenticated"
        ),
        "raw_identifier_not_echoed": identifier not in json.dumps(activated, ensure_ascii=False),
        "session_token_issued": isinstance(activated.get("session_token"), str)
        and activated.get("session_token", "").startswith("sess_onb_"),
    }
    return {
        "task_id": "T1001",
        "target_host": urllib.parse.urlparse(base).hostname,
        "run_id": str(run_id),
        "flow_version": flow_version if isinstance(flow_version, str) else None,
        "statuses": {
            "state_unauthenticated": unauth_status,
            "state_authenticated": state_status,
            "progress_authenticated": progress_status,
            "activate_stale_consent": stale_status,
            "activate_authenticated": activate_status,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "sensitive_fields_recorded": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    username = os.environ.get("BASIC_AUTH_USERNAME", "")
    password = os.environ.get("BASIC_AUTH_PASSWORD", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    if not username or not password:
        print("[!] Required production credentials are unavailable.", file=sys.stderr)
        return 2

    report: dict[str, Any] = {
        "task_id": "T1001",
        "target_host": urllib.parse.urlparse(_base_url(args.url)).hostname,
        "run_id": str(run_id),
        "passed": False,
        "sensitive_fields_recorded": False,
    }
    exit_code = 1
    try:
        report = run_uat(args.url, username, password, run_id)
        exit_code = 0 if report["passed"] else 1
    except Exception as exc:
        report["error_type"] = type(exc).__name__
        exit_code = 1
    finally:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"[{'+' if exit_code == 0 else '!'}] Production onboarding UAT: {'PASS' if exit_code == 0 else 'FAIL'}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())