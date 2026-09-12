"""Exercise real OAuth refresh and Workspace account checks without network."""

import json
from pathlib import Path
import sys
from urllib.parse import parse_qs

import pytest
import requests
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import google_workspace_account as workspace  # noqa: E402


EXPECTED_ACCOUNT = "k-umezawa@ml-mightylink.com"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_URL = "https://www.googleapis.com/drive/v3/about"
DUMMY_REFRESH_TOKEN = "test-only-refresh-token"
DUMMY_CLIENT_SECRET = "test-only-client-secret"
DUMMY_ACCESS_TOKEN = "test-only-refreshed-access-token"


def _expired_credentials():
    return Credentials.from_authorized_user_info(
        {
            "token": "test-only-expired-access-token",
            "refresh_token": DUMMY_REFRESH_TOKEN,
            "client_id": "test-only-client-id",
            "client_secret": DUMMY_CLIENT_SECRET,
            "expiry": "2000-01-01T00:00:00Z",
        },
        scopes=["https://www.googleapis.com/auth/drive"],
    )


def _intercept_oauth(monkeypatch, *, account=EXPECTED_ACCOUNT, invalid_grant=False):
    calls = []

    def request(_session, method, url, **kwargs):
        method = method.upper()
        calls.append((method, url))
        if (method, url) == ("POST", TOKEN_URL):
            body = kwargs["data"]
            form = parse_qs(body.decode("utf-8") if isinstance(body, bytes) else body)
            assert form["grant_type"] == ["refresh_token"]
            assert form["refresh_token"] == [DUMMY_REFRESH_TOKEN]
            assert form["client_id"] == ["test-only-client-id"]
            assert form["client_secret"] == [DUMMY_CLIENT_SECRET]
            if invalid_grant:
                status = 400
                payload = {
                    "error": "invalid_grant",
                    "error_description": "Token has been expired or revoked.",
                }
            else:
                status = 200
                payload = {
                    "access_token": DUMMY_ACCESS_TOKEN,
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }
        elif (method, url) == ("GET", DRIVE_URL):
            assert not invalid_grant, "Drive must not be queried after refresh failure"
            assert kwargs["headers"]["Authorization"] == f"Bearer {DUMMY_ACCESS_TOKEN}"
            status = 200
            payload = {"user": {"emailAddress": account, "displayName": "Test user"}}
        else:
            raise AssertionError(f"Unexpected HTTP request: {method} {url}")

        response = requests.Response()
        response.status_code = status
        response.url = url
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps(payload).encode("utf-8")
        return response

    # Keep the real google-auth Request adapter and refresh implementation;
    # replace the shared HTTP boundary used by both OAuth and the Drive check.
    monkeypatch.setattr(requests.sessions.Session, "request", request)
    return calls


@pytest.mark.parametrize(
    "account",
    [EXPECTED_ACCOUNT, "different-account@example.test"],
    ids=["expected-account", "wrong-account"],
)
def test_real_oauth_refresh_then_account_check(monkeypatch, account):
    calls = _intercept_oauth(monkeypatch, account=account)
    credentials = _expired_credentials()
    assert not credentials.valid

    if account == EXPECTED_ACCOUNT:
        assert workspace.assert_expected_google_account(credentials, EXPECTED_ACCOUNT) == EXPECTED_ACCOUNT
    else:
        with pytest.raises(workspace.GoogleWorkspaceAccountError, match="account mismatch"):
            workspace.assert_expected_google_account(credentials, EXPECTED_ACCOUNT)

    assert credentials.valid
    assert credentials.token == DUMMY_ACCESS_TOKEN
    assert calls == [("POST", TOKEN_URL), ("GET", DRIVE_URL)]


def test_real_invalid_grant_requires_reauth(monkeypatch):
    calls = _intercept_oauth(monkeypatch, invalid_grant=True)
    credentials = _expired_credentials()

    with pytest.raises(workspace.GoogleWorkspaceReauthRequiredError) as error:
        workspace.assert_expected_google_account(credentials, EXPECTED_ACCOUNT)

    assert isinstance(error.value.__cause__, RefreshError)
    assert "--reauth" in str(error.value)
    assert DUMMY_REFRESH_TOKEN not in str(error.value)
    assert DUMMY_CLIENT_SECRET not in str(error.value)
    assert not credentials.valid
    assert calls == [("POST", TOKEN_URL)]
