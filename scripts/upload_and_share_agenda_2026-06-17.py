#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Upload the 2026-06-17 meeting agenda PPTX to Google Drive and share it with the CEO.

This script checks if the file already exists on Drive under the same name.
If it does, it updates the existing file (maintaining the same URL).
If not, it uploads a new file and grants 'reader' access to the CEO.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
import requests
from pathlib import Path
from google.oauth2.credentials import Credentials as UserCredentials
import google.auth.transport.requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from google_workspace_account import assert_expected_google_account

AUTHORIZED_USER_FILE = PROJECT_ROOT / "authorized_user.json"
PPTX_FILE = PROJECT_ROOT / "exports" / "mighty_skill_bridge_agenda_2026-06-17.pptx"

USER_EMAIL = "k-umezawa@ml-mightylink.com"
CEO_EMAIL = "kobayashi-masami@ml-mightylink.com"
FILE_NAME = "Mighty Skill-Bridge CEO Meeting Agenda 2026-06-17.pptx"
MIME_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]
TIMEOUT = 30


def get_access_token() -> str:
    if not AUTHORIZED_USER_FILE.exists():
        raise FileNotFoundError(f"Missing OAuth credentials file: {AUTHORIZED_USER_FILE}")

    info = json.loads(AUTHORIZED_USER_FILE.read_text(encoding="utf-8"))
    creds = UserCredentials.from_authorized_user_info(info, scopes=SCOPES)
    assert_expected_google_account(creds, USER_EMAIL)

    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds.token


def find_existing_file(token: str) -> str | None:
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": f"name = '{FILE_NAME}' and trashed = false",
        "spaces": "drive",
        "fields": "files(id, name)",
        "supportsAllDrives": "true",
        "includeItemsFromTrash": "false",
    }
    res = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
    if res.status_code != 200:
        print(f"[-] Search API failed: {res.text}")
        return None

    files = res.json().get("files", [])
    if files:
        return files[0]["id"]
    return None


def multipart_binary_body(metadata: dict, content: bytes, content_type: str) -> tuple[bytes, str]:
    boundary = f"mighty-drive-boundary-{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata, ensure_ascii=False)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def upload_file(token: str, file_id: str | None) -> dict:
    content = PPTX_FILE.read_bytes()
    metadata = {
        "name": FILE_NAME,
        "mimeType": MIME_TYPE,
    }
    body, boundary = multipart_binary_body(metadata, content, MIME_TYPE)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/related; boundary={boundary}",
    }
    params = {
        "uploadType": "multipart",
        "fields": "id,name,webViewLink,ownedByMe",
        "supportsAllDrives": "true",
    }

    if file_id:
        url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
        print(f"[*] Updating existing file on Google Drive (ID: {file_id})...")
        res = requests.patch(url, headers=headers, params=params, data=body, timeout=TIMEOUT)
    else:
        url = "https://www.googleapis.com/upload/drive/v3/files"
        print("[*] Uploading new file to Google Drive...")
        res = requests.post(url, headers=headers, params=params, data=body, timeout=TIMEOUT)

    if res.status_code not in [200, 201]:
        raise RuntimeError(f"Upload failed: {res.status_code} {res.text}")

    return res.json()


def share_file_with_ceo(token: str, file_id: str) -> bool:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions"
    params = {"sendNotificationEmail": "true"}
    body = {
        "role": "reader",
        "type": "user",
        "emailAddress": CEO_EMAIL
    }
    print(f"[*] Sharing file with CEO ({CEO_EMAIL}) as 'reader'...")
    res = requests.post(url, headers=headers, params=params, json=body, timeout=TIMEOUT)
    if res.status_code in [200, 201]:
        print(f"[+] Successfully shared file with {CEO_EMAIL}!")
        return True
    else:
        print(f"[-] Failed to share file: {res.text}")
        return False


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not PPTX_FILE.exists():
        print(f"[-] PPTX file not found: {PPTX_FILE}")
        sys.exit(1)

    try:
        token = get_access_token()

        # Check if file already exists to avoid duplicates
        existing_id = find_existing_file(token)
        if existing_id:
            print(f"[+] Found existing file on Drive. ID: {existing_id}")

        result = upload_file(token, existing_id)
        file_id = result["id"]
        web_link = result.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
        print(f"[+] File uploaded successfully! Link: {web_link}")

        # Share permission
        share_success = share_file_with_ceo(token, file_id)

        print("\n" + "="*60)
        if share_success:
            print(f"[+] SUCCESS! Shared today's Agenda PPTX with {CEO_EMAIL}.")
            print(f"[*] Link: {web_link}")
        else:
            print("[!] File uploaded, but sharing failed. Please review log.")
        print("="*60)

    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
