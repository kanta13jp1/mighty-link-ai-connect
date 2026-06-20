import os
import sys

import pytest
from google.auth.exceptions import RefreshError


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from google_workspace_account import (  # noqa: E402
    EXPECTED_GOOGLE_ACCOUNT,
    GoogleWorkspaceReauthRequiredError,
    fetch_drive_user,
    google_workspace_reauth_message,
    is_google_oauth_reauth_required,
)


class ExpiredCredentials:
    valid = False

    def refresh(self, request):
        raise RefreshError("invalid_grant: Token has been expired or revoked.")


def test_expired_oauth_refresh_prompts_reauth():
    with pytest.raises(GoogleWorkspaceReauthRequiredError) as excinfo:
        fetch_drive_user(ExpiredCredentials())

    message = str(excinfo.value)
    assert "--reauth" in message
    assert EXPECTED_GOOGLE_ACCOUNT in message
    assert "Do not commit" in message


def test_reauth_detector_recognizes_google_invalid_grant():
    error = RefreshError("invalid_grant: Token has been expired or revoked.")

    assert is_google_oauth_reauth_required(error)


def test_reauth_message_does_not_include_secret_material():
    message = google_workspace_reauth_message()

    assert "token=" not in message
    assert "password" not in message.lower()
