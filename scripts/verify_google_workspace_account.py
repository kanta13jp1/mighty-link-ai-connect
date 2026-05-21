#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Verify that authorized_user.json is connected to the expected Workspace account."""

import os
import sys

from google.oauth2.credentials import Credentials as UserCredentials


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from google_workspace_account import (  # noqa: E402
    EXPECTED_GOOGLE_ACCOUNT,
    assert_expected_google_account,
)


AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


def main() -> None:
    if not os.path.exists(AUTHORIZED_USER_FILE):
        print(f"[-] Missing {AUTHORIZED_USER_FILE}")
        sys.exit(1)

    credentials = UserCredentials.from_authorized_user_file(AUTHORIZED_USER_FILE, scopes=SCOPES)
    account = assert_expected_google_account(credentials, EXPECTED_GOOGLE_ACCOUNT)
    print(f"[+] authorized_user.json is linked to {account}")


if __name__ == "__main__":
    main()
