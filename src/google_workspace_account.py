"""Google Workspace account guardrails for OAuth-backed integrations."""

from __future__ import annotations

import os
from typing import Any

import requests
from google.auth.transport.requests import Request


EXPECTED_GOOGLE_ACCOUNT = os.getenv(
    "MIGHTY_GOOGLE_ACCOUNT",
    "k-umezawa@ml-mightylink.com",
)


class GoogleWorkspaceAccountError(RuntimeError):
    """Raised when OAuth credentials do not belong to the expected account."""


def _refresh_if_needed(credentials: Any) -> None:
    if not getattr(credentials, "valid", False):
        credentials.refresh(Request())


def fetch_drive_user(credentials: Any) -> dict:
    """Return the Drive API user profile for the authenticated OAuth account."""
    if credentials is None:
        raise GoogleWorkspaceAccountError("Google OAuth credentials were not available for verification.")

    _refresh_if_needed(credentials)
    token = getattr(credentials, "token", None)
    if not token:
        raise GoogleWorkspaceAccountError("Google OAuth access token was not available after refresh.")

    response = requests.get(
        "https://www.googleapis.com/drive/v3/about",
        params={"fields": "user(emailAddress,displayName,permissionId)"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if response.status_code != 200:
        raise GoogleWorkspaceAccountError(
            f"Unable to verify Google Workspace account via Drive API: {response.status_code} {response.text[:300]}"
        )

    return response.json().get("user", {})


def assert_expected_google_account(
    credentials: Any,
    expected_email: str = EXPECTED_GOOGLE_ACCOUNT,
) -> str:
    """Verify OAuth credentials are connected to the expected Workspace account."""
    user = fetch_drive_user(credentials)
    actual_email = (user.get("emailAddress") or "").strip()
    display_name = (user.get("displayName") or "").strip()

    if actual_email.lower() != expected_email.lower():
        raise GoogleWorkspaceAccountError(
            "Google OAuth account mismatch. "
            f"Expected '{expected_email}', but authenticated as '{actual_email or 'unknown'}'. "
            "Delete or regenerate authorized_user.json using the expected Workspace account."
        )

    label = f"{actual_email} ({display_name})" if display_name else actual_email
    print(f"[+] Verified Google Workspace account: {label}")
    return actual_email


def credentials_from_gspread_client(client: Any) -> Any:
    """Extract OAuth credentials from supported gspread client versions."""
    direct = getattr(client, "auth", None)
    if direct is not None:
        return direct

    http_client = getattr(client, "http_client", None)
    if http_client is not None:
        nested = getattr(http_client, "auth", None)
        if nested is not None:
            return nested

    return None
