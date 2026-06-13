#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Create recurrent Google Calendar event for bi-weekly regular review.

This script creates the decided recurrent bi-weekly review meetings on Google
Calendar using the custom calendar ID and existing OAuth credentials.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import requests

try:
    from google.oauth2.credentials import Credentials as UserCredentials
    from google.auth.transport.requests import Request
except ImportError:
    print("[-] Google Auth libraries are not installed.")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
AUTHORIZED_USER_FILE = PROJECT_ROOT / "authorized_user.json"

CALENDAR_ID = "c_148e9a1be60982dab1792a5f5da8d64deaeee325b3951765ab2fbd3d0561ec02@group.calendar.google.com"
GOOGLE_API_TIMEOUT_SECONDS = 30


def load_credentials() -> UserCredentials:
    if not AUTHORIZED_USER_FILE.exists():
        raise FileNotFoundError(f"Missing OAuth file: {AUTHORIZED_USER_FILE}")
    credentials = UserCredentials.from_authorized_user_file(
        str(AUTHORIZED_USER_FILE),
        scopes=[
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ],
    )
    if not credentials.valid:
        credentials.refresh(Request())
    return credentials


def build_recurrent_event() -> dict:
    event_body = {
        "summary": "【定例】Mighty Skill-Bridge 開発レビューミーティング",
        "description": (
            "持続可能な開発体制（休日を除く1日1時間目安）における、開発の進捗確認、デモ検証、"
            "および次回スプリント方針決定のための隔週定例レビューミーティングです。\n"
            "初次: 2026年6月17日 17:30〜18:00 (JST)\n"
            "主催: 寛太梅澤"
        ),
        "start": {
            "dateTime": "2026-06-17T17:30:00",
            "timeZone": "Asia/Tokyo"
        },
        "end": {
            "dateTime": "2026-06-17T18:00:00",
            "timeZone": "Asia/Tokyo"
        },
        "recurrence": [
            "RRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=10"
        ]
    }
    return event_body


def main() -> None:
    print("[*] Mighty-Link AI Connect: Creating Recurrent Calendar Invite...")
    
    try:
        credentials = load_credentials()
        headers = {"Authorization": f"Bearer {credentials.token}"}
        
        # Check if recurrent event is already created (to avoid duplicates)
        list_url = f"https://www.googleapis.com/calendar/v3/calendars/{CALENDAR_ID}/events"
        params = {
            "q": "【定例】Mighty Skill-Bridge 開発レビューミーティング",
            "singleEvents": "false",
        }
        
        res = requests.get(list_url, headers=headers, params=params, timeout=GOOGLE_API_TIMEOUT_SECONDS)
        existing_items = res.json().get("items", []) if res.status_code == 200 else []
        
        event_body = build_recurrent_event()
        
        if existing_items:
            print("[*] Found existing recurrent invite. Updating it to avoid duplicates...")
            event_id = existing_items[0]["id"]
            update_url = f"{list_url}/{event_id}"
            res = requests.put(update_url, headers=headers, json=event_body, timeout=GOOGLE_API_TIMEOUT_SECONDS)
        else:
            print("[*] Creating brand new recurrent invite...")
            res = requests.post(list_url, headers=headers, json=event_body, timeout=GOOGLE_API_TIMEOUT_SECONDS)
            
        if res.status_code not in [200, 204]:
            raise RuntimeError(f"Calendar API call failed: {res.status_code} {res.text}")
            
        result_json = res.json()
        print(f"[+] Recurrent regular review meeting successfully scheduled!")
        print(f"[*] Summary: {result_json.get('summary')}")
        print(f"[*] Recurrence: {result_json.get('recurrence')}")
        print(f"[*] Calendar Event URL: {result_json.get('htmlLink')}")
        
        # Save local report
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        manifest_file = REPORTS_DIR / "reports_manifest.json"
        manifest = {}
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            
        manifest["recurrent_calendar_invite"] = {
            "id": result_json.get("id"),
            "summary": result_json.get("summary"),
            "recurrence": result_json.get("recurrence"),
            "url": result_json.get("htmlLink"),
            "updated_at": result_json.get("updated")
        }
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        
    except Exception as exc:
        print(f"[-] Recurrent calendar invite creation failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
