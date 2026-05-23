#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Upload NotebookLM demo inputs as native Google Docs with Workspace OAuth.

This script intentionally uses the local authorized_user.json OAuth token rather
than a Codex/MCP Google Drive connector. The connector may be authenticated as a
different Google account, while the project must keep demo documents under the
Workspace account configured in src/google_workspace_account.py.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from google_workspace_account import (  # noqa: E402
    EXPECTED_GOOGLE_ACCOUNT,
    assert_expected_google_account,
)


AUTHORIZED_USER_FILE = PROJECT_ROOT / "authorized_user.json"
EXPORT_DIR = PROJECT_ROOT / "exports" / "knowledge_flow"
OUTPUT_FILE = EXPORT_DIR / "google_drive_workspace_docs.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

DOC_SOURCES = [
    {
        "key": "notebooklm_source_pack",
        "title": "Mighty Skill-Bridge NotebookLM Source Pack 2026-06-02 (Workspace)",
        "source": EXPORT_DIR / "notebooklm_source_pack.txt",
    },
    {
        "key": "notebooklm_presentation_brief",
        "title": "Mighty Skill-Bridge CEO Presentation Brief 2026-06-02 (Workspace)",
        "source": EXPORT_DIR / "notebooklm_presentation_brief.txt",
    },
    {
        "key": "notebooklm_agent_brief",
        "title": "Mighty Skill-Bridge NotebookLM Agent Brief 2026-06-02 (Workspace)",
        "source": EXPORT_DIR / "notebooklm_agent_brief.md",
    },
    {
        "key": "notebooklm_ceo_slide_outline",
        "title": "Mighty Skill-Bridge NotebookLM CEO Slide Outline 2026-06-02 (Workspace)",
        "source": EXPORT_DIR / "notebooklm_ceo_slide_outline.md",
    },
]

FILE_SOURCES = [
    {
        "key": "ceo_presentation_pptx",
        "title": "Mighty Skill-Bridge CEO Presentation Deck 2026-06-02.pptx",
        "source": EXPORT_DIR / "mighty_skill_bridge_ceo_presentation_2026-06-02.pptx",
        "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    {
        "key": "ceo_presentation_pptx_branded",
        "title": "Mighty Skill-Bridge CEO Presentation Deck 2026-06-02 (Branded).pptx",
        "source": EXPORT_DIR / "mighty_skill_bridge_ceo_presentation_2026-06-02_branded.pptx",
        "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    {
        "key": "ui_wireframes_pptx",
        "title": "Mighty Skill-Bridge UI Wireframes — 10 Patterns 2026-06-02.pptx",
        "source": EXPORT_DIR / "mighty_skill_bridge_ui_wireframes_2026-06-02.pptx",
        "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    {
        "key": "ui_wireframes_canva_pptx",
        "title": "Mighty Skill-Bridge UI Wireframes — 10 Patterns 2026-06-02 (Canva, Branded).pptx",
        "source": PROJECT_ROOT / "exports" / "mighty_skill_bridge_wireframes_v2.pptx",
        "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
]


def load_credentials() -> UserCredentials:
    if not AUTHORIZED_USER_FILE.exists():
        raise FileNotFoundError(f"Missing OAuth file: {AUTHORIZED_USER_FILE}")

    credentials = UserCredentials.from_authorized_user_file(
        str(AUTHORIZED_USER_FILE),
        scopes=SCOPES,
    )
    assert_expected_google_account(credentials, EXPECTED_GOOGLE_ACCOUNT)
    if not credentials.valid:
        credentials.refresh(Request())
    return credentials


def api_headers(credentials: UserCredentials) -> dict[str, str]:
    if not credentials.valid:
        credentials.refresh(Request())
    return {"Authorization": f"Bearer {credentials.token}"}


def multipart_body(metadata: dict[str, Any], content: str) -> tuple[bytes, str]:
    boundary = f"mighty-drive-boundary-{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata, ensure_ascii=False)}\r\n"
        f"--{boundary}\r\n"
        "Content-Type: text/plain; charset=UTF-8\r\n\r\n"
        f"{content}\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    return body, boundary


def multipart_binary_body(
    metadata: dict[str, Any],
    content: bytes,
    *,
    content_type: str,
) -> tuple[bytes, str]:
    boundary = f"mighty-drive-boundary-{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{json.dumps(metadata, ensure_ascii=False)}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def request_json(
    credentials: UserCredentials,
    method: str,
    url: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> dict[str, Any]:
    request_headers = api_headers(credentials)
    if headers:
        request_headers.update(headers)

    response = None
    transient_statuses = {429, 500, 502, 503, 504}
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            response = requests.request(
                method,
                url,
                params=params,
                headers=request_headers,
                data=data,
                timeout=90,
            )
        except requests.RequestException as exc:
            if attempt == max_attempts - 1:
                raise RuntimeError(f"Drive API {method} failed after retries: {exc}") from exc
            time.sleep(min(2 ** attempt, 8))
            continue

        if response.status_code not in transient_statuses:
            break
        if attempt < max_attempts - 1:
            time.sleep(min(2 ** attempt, 8))

    assert response is not None
    if response.status_code >= 400:
        raise RuntimeError(f"Drive API {method} failed: {response.status_code} {response.text[:500]}")
    return response.json()


def get_file(credentials: UserCredentials, file_id: str) -> dict[str, Any] | None:
    try:
        return request_json(
            credentials,
            "GET",
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={
                "fields": "id,name,mimeType,webViewLink,createdTime,modifiedTime,ownedByMe,owners(emailAddress,displayName)",
                "supportsAllDrives": "true",
            },
        )
    except RuntimeError as exc:
        if " 404 " in str(exc) or "File not found" in str(exc):
            return None
        raise


def upload_as_google_doc(
    credentials: UserCredentials,
    *,
    title: str,
    content: str,
    existing_file_id: str | None,
) -> dict[str, Any]:
    metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
    }
    body, boundary = multipart_body(metadata, content)
    params = {
        "uploadType": "multipart",
        "fields": "id,name,mimeType,webViewLink,createdTime,modifiedTime,ownedByMe,owners(emailAddress,displayName)",
        "supportsAllDrives": "true",
    }
    headers = {"Content-Type": f"multipart/related; boundary={boundary}"}

    if existing_file_id:
        return request_json(
            credentials,
            "PATCH",
            f"https://www.googleapis.com/upload/drive/v3/files/{existing_file_id}",
            params=params,
            headers=headers,
            data=body,
        )

    return request_json(
        credentials,
        "POST",
        "https://www.googleapis.com/upload/drive/v3/files",
        params=params,
        headers=headers,
        data=body,
    )


def upload_binary_file(
    credentials: UserCredentials,
    *,
    title: str,
    content: bytes,
    mime_type: str,
    existing_file_id: str | None,
) -> dict[str, Any]:
    metadata = {
        "name": title,
        "mimeType": mime_type,
    }
    body, boundary = multipart_binary_body(metadata, content, content_type=mime_type)
    params = {
        "uploadType": "multipart",
        "fields": "id,name,mimeType,webViewLink,webContentLink,createdTime,modifiedTime,ownedByMe,owners(emailAddress,displayName)",
        "supportsAllDrives": "true",
    }
    headers = {"Content-Type": f"multipart/related; boundary={boundary}"}

    if existing_file_id:
        return request_json(
            credentials,
            "PATCH",
            f"https://www.googleapis.com/upload/drive/v3/files/{existing_file_id}",
            params=params,
            headers=headers,
            data=body,
        )

    return request_json(
        credentials,
        "POST",
        "https://www.googleapis.com/upload/drive/v3/files",
        params=params,
        headers=headers,
        data=body,
    )


def load_previous_metadata() -> dict[str, Any]:
    if not OUTPUT_FILE.exists():
        return {}
    return json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))


def owner_emails(file_metadata: dict[str, Any]) -> list[str]:
    return [
        (owner.get("emailAddress") or "").strip()
        for owner in file_metadata.get("owners", [])
        if owner.get("emailAddress")
    ]


def verify_workspace_owner(file_metadata: dict[str, Any]) -> None:
    owners = owner_emails(file_metadata)
    owned_by_me = bool(file_metadata.get("ownedByMe"))
    if owners and EXPECTED_GOOGLE_ACCOUNT.lower() not in [owner.lower() for owner in owners]:
        raise RuntimeError(
            f"Unexpected Drive owner for {file_metadata.get('name')}: {owners}. "
            f"Expected {EXPECTED_GOOGLE_ACCOUNT}."
        )
    if not owners and not owned_by_me:
        raise RuntimeError(
            f"Drive did not confirm ownership for {file_metadata.get('name')}. "
            "Refusing to record the document."
        )


def main() -> None:
    credentials = load_credentials()
    previous = load_previous_metadata()
    previous_docs = previous.get("documents", {}) if isinstance(previous, dict) else {}
    previous_files = previous.get("files", {}) if isinstance(previous, dict) else {}

    documents: dict[str, Any] = {}
    for source in DOC_SOURCES:
        source_path = source["source"]
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source file: {source_path}")

        previous_id = previous_docs.get(source["key"], {}).get("id")
        existing = get_file(credentials, previous_id) if previous_id else None
        existing_id = existing["id"] if existing else None

        result = upload_as_google_doc(
            credentials,
            title=source["title"],
            content=source_path.read_text(encoding="utf-8"),
            existing_file_id=existing_id,
        )
        verify_workspace_owner(result)
        if not result.get("webViewLink"):
            result["webViewLink"] = f"https://docs.google.com/document/d/{result['id']}/edit"

        documents[source["key"]] = {
            "id": result["id"],
            "name": result["name"],
            "url": result["webViewLink"],
            "mimeType": result["mimeType"],
            "ownedByMe": result.get("ownedByMe"),
            "owners": result.get("owners", []),
            "createdTime": result.get("createdTime"),
            "modifiedTime": result.get("modifiedTime"),
            "source": str(source_path.relative_to(PROJECT_ROOT)).replace(os.sep, "/"),
        }

    files: dict[str, Any] = {}
    for source in FILE_SOURCES:
        source_path = source["source"]
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source file: {source_path}")

        previous_id = previous_files.get(source["key"], {}).get("id")
        existing = get_file(credentials, previous_id) if previous_id else None
        existing_id = existing["id"] if existing else None

        result = upload_binary_file(
            credentials,
            title=source["title"],
            content=source_path.read_bytes(),
            mime_type=source["mimeType"],
            existing_file_id=existing_id,
        )
        verify_workspace_owner(result)
        if not result.get("webViewLink"):
            result["webViewLink"] = f"https://drive.google.com/file/d/{result['id']}/view"

        files[source["key"]] = {
            "id": result["id"],
            "name": result["name"],
            "url": result["webViewLink"],
            "downloadUrl": result.get("webContentLink"),
            "mimeType": result["mimeType"],
            "ownedByMe": result.get("ownedByMe"),
            "owners": result.get("owners", []),
            "createdTime": result.get("createdTime"),
            "modifiedTime": result.get("modifiedTime"),
            "source": str(source_path.relative_to(PROJECT_ROOT)).replace(os.sep, "/"),
        }

    metadata = {
        "account": EXPECTED_GOOGLE_ACCOUNT,
        "auth_file": str(AUTHORIZED_USER_FILE.relative_to(PROJECT_ROOT)).replace(os.sep, "/"),
        "documents": documents,
        "files": files,
    }
    OUTPUT_FILE.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("[+] Workspace Google Docs are ready.")
    print(f"[*] Account: {EXPECTED_GOOGLE_ACCOUNT}")
    for key, doc in documents.items():
        print(f"  - {key}: {doc['url']}")
    for key, item in files.items():
        print(f"  - {key}: {item['url']}")
    print(f"[*] Metadata: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
