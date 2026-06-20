#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Verify that authorized_user.json is connected to the expected Workspace account."""

import argparse
import os
import sys

import gspread
from google.oauth2.credentials import Credentials as UserCredentials


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from google_workspace_account import (  # noqa: E402
    EXPECTED_GOOGLE_ACCOUNT,
    GoogleWorkspaceAccountError,
    GoogleWorkspaceReauthRequiredError,
    assert_expected_google_account,
    credentials_from_gspread_client,
    google_workspace_reauth_message,
)


CLIENT_SECRET_FILE = os.path.join(PROJECT_ROOT, "client_secret.json")
AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


def reauth() -> None:
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"[-] Missing {CLIENT_SECRET_FILE}")
        print("[*] Download an OAuth Desktop client secret as client_secret.json before reauth.")
        sys.exit(1)

    if os.path.exists(AUTHORIZED_USER_FILE):
        os.remove(AUTHORIZED_USER_FILE)
        print(f"[*] Removed stale {AUTHORIZED_USER_FILE}")

    print("[*] Launching Google OAuth reauthentication...")
    print(f"[*] Sign in as {EXPECTED_GOOGLE_ACCOUNT}")
    client = gspread.oauth(
        scopes=SCOPES,
        credentials_filename=CLIENT_SECRET_FILE,
        authorized_user_filename=AUTHORIZED_USER_FILE,
    )
    account = assert_expected_google_account(
        credentials_from_gspread_client(client),
        EXPECTED_GOOGLE_ACCOUNT,
    )
    print(f"[+] authorized_user.json was refreshed for {account}")
    print("[!] Keep authorized_user.json, client_secret.json, and OAuth tokens local-only.")


def verify() -> None:
    if not os.path.exists(AUTHORIZED_USER_FILE):
        print(f"[-] Missing {AUTHORIZED_USER_FILE}")
        print(f"[*] {google_workspace_reauth_message(EXPECTED_GOOGLE_ACCOUNT)}")
        sys.exit(1)

    credentials = UserCredentials.from_authorized_user_file(AUTHORIZED_USER_FILE, scopes=SCOPES)
    account = assert_expected_google_account(credentials, EXPECTED_GOOGLE_ACCOUNT)
    print(f"[+] authorized_user.json is linked to {account}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify or refresh the Google Workspace OAuth user account."
    )
    parser.add_argument(
        "--reauth",
        action="store_true",
        help="Delete stale authorized_user.json and launch the OAuth browser flow.",
    )
    args = parser.parse_args()

    try:
        if args.reauth:
            reauth()
        else:
            verify()
    except GoogleWorkspaceReauthRequiredError as error:
        print(f"[-] {error}")
        sys.exit(2)
    except GoogleWorkspaceAccountError as error:
        print(f"[-] {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
