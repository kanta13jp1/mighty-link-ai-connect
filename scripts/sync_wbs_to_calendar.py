#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: WBS Google Calendar Sync Script
Author: Antigravity 2.0 (AI Agent)

This script:
1. Generates an 'exports/mighty_development_plan.ics' file for offline import.
2. Synchronizes WBS milestones and the CEO meeting to Google Calendar using:
   - OAuth 2.0 (via client_secret.json) -> Creates a custom "Mighty Skill-Bridge 開発計画" calendar on user's drive.
   - Service Account (via credentials.json) -> Falls back to writing directly to user's calendar or sharing events.
"""

import os
import sys
import datetime
import uuid
import json
import hashlib
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "exports")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def install_and_import(package):
    """Dynamically checks and instructs how to install dependencies if missing."""
    try:
        __import__(package)
    except ImportError:
        print(f"[-] Required library '{package}' is not installed.")
        print(f"[*] Please install it by running: pip install -r requirements.txt")
        sys.exit(1)

# Ensure dependencies are available
install_and_import("gspread")
install_and_import("google.oauth2")

import gspread
from google.oauth2.service_account import Credentials
import google.auth.transport.requests
from google_workspace_account import (
    GoogleWorkspaceAccountError,
    assert_expected_google_account,
    credentials_from_gspread_client,
)

# Configuration
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")       # Service Account
CLIENT_SECRET_FILE = os.path.join(PROJECT_ROOT, "client_secret.json")   # OAuth 2.0 Desktop client
AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
USER_EMAIL = "k-umezawa@ml-mightylink.com"

# WBS Schedule definitions (Parsed from docs/WBS.md / data/WBS.tsv)
SCHEDULE_EVENTS = [
    {
        "summary": "【Mighty Skill-Bridge】フェーズ1: 企画・設計（要件定義 & DB設計）",
        "description": "開発の土台となる要件定義(requirements.md)およびDB設計(database.md)の策定・合意。",
        "start_date": "2026-05-20",
        "end_date": "2026-05-22", # 2 days (exclusive end date is 22nd)
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ2: フロント開発（UI/UX実装）",
        "description": "プレミアムなガラスモフィズム調UI、ドラッグ＆ドロップパネル、Chart.js連携の実装。",
        "start_date": "2026-05-22",
        "end_date": "2026-05-25", # 3 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ3: バックエンド & AI（Gemini 3.5 & Omni 連携API）",
        "description": "FastAPIを用いたマルチモーダルパースAPI、4次元分析API、Google Sheets同期エンジン、構造化プロファイル抽出・4軸スコアリングfallback基盤、AI判定監査ログ(JSONL)・recent audit API、GitHub Pages公開デモ保護ガード、CATS型WBSスプレッドシートUIの開発。",
        "start_date": "2026-05-25",
        "end_date": "2026-05-28", # 3 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ4: テスト & デバッグ（Browser Agent & Code Mender）",
        "description": "Browser Agentによる自律UIテスト、Code Menderによるセキュリティ診断・デバッグ。",
        "start_date": "2026-05-28",
        "end_date": "2026-05-30", # 2 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ5: 本番公開（CI/CDデプロイ & プレスリリース）",
        "description": "GitHub ActionsによるCI/CD環境構築、リリース、およびプレスリリース告知文の自動生成・公開。",
        "start_date": "2026-05-30",
        "end_date": "2026-06-01", # 2 days
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】フェーズ6: 社長プレゼン準備（6/2判断材料・デモ・想定QA）",
        "description": "6/2の社長打ち合わせに向け、サービス内容を決め打ちせず、公開デモ、WBS、Google Workspace連携、論点、選択肢、判断マトリクス、議事録テンプレート、想定QA、決定後の反映手順を準備します。",
        "start_date": "2026-05-21",
        "end_date": "2026-06-02",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】社長プレゼン判断材料レビュー",
        "description": "スライド構成、判断マトリクス、想定質問、デモバックアップ導線を確認し、6/2で決める事項と保留事項を分離します。",
        "start_time": "2026-05-30T10:00:00",
        "end_time": "2026-05-30T11:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】社長向け事前共有メモ作成",
        "description": "社長へ事前共有する確認ポイント、当日アジェンダ、公開デモURL、WBS/Calendar確認導線の短文ドラフトを作成します。",
        "start_date": "2026-05-30",
        "end_date": "2026-06-01",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】開発ナレッジ連携フロー整理",
        "description": "NotebookLM、Slack、Notion、Obsidianを6/2の社長判断材料として整理し、正式実装前に役割・情報管理・導入優先順位を確認します。",
        "start_date": "2026-05-24",
        "end_date": "2026-05-29",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】連携ツール採用判断レビュー",
        "description": "NotebookLM/Slack/Notion/Obsidianの採用・保留・後回し、共有範囲、権限ルール、6/2以降の実装候補をレビューします。",
        "start_time": "2026-05-28T14:00:00",
        "end_time": "2026-05-28T15:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】開発ナレッジ連携デモ確認",
        "description": "NotebookLM投入資料、Slack投稿案、Notion CSV、Obsidian vault、公開デモUI、FastAPI生成APIを確認し、社長に見せる順番を固めます。",
        "start_time": "2026-05-29T15:00:00",
        "end_time": "2026-05-29T16:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】CLI/MCP連携証跡レビュー",
        "description": "GitHub Issues、Google Docs化したNotebookLM source pack、Notion証跡ページ、Obsidian vault、Slack投稿案、GitHub Project権限課題を確認し、6/2で見せる順番を決めます。",
        "start_time": "2026-05-23T11:00:00",
        "end_time": "2026-05-23T12:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】GitHub Project権限復旧チェック",
        "description": "gh auth refresh -s read:project 実行後にProject board取得/作成とIssue #1-#6の配置可否を確認します。",
        "start_time": "2026-05-24T10:00:00",
        "end_time": "2026-05-24T11:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLMプレゼン草案作成",
        "description": "NotebookLMへSource PackとPresentation Briefを投入し、6/2社長説明用の8枚以内スライド構成、話す要点、想定QAを生成します。",
        "start_time": "2026-05-22T15:00:00",
        "end_time": "2026-05-22T16:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】Slack投稿先・送信権限確認",
        "description": "Slack投稿案を実送信するため、投稿先チャンネル、社長共有範囲、Slack connector/CLIの利用可否を確認します。",
        "start_time": "2026-05-24T11:00:00",
        "end_time": "2026-05-24T11:30:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】Google Workspace OAuthアカウント固定確認",
        "description": "authorized_user.jsonがk-umezawa@ml-mightylink.comに紐づいていることをDrive APIで確認し、Sheets/Calendar/API同期前の誤アカウント防止ガードを追加します。",
        "start_date": "2026-05-21",
        "end_date": "2026-05-22",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】Workspace Google Docs再作成確認",
        "description": "NotebookLM用Source PackとPresentation BriefをLocal OAuth Drive APIでk-umezawa@ml-mightylink.com所有のGoogle Docsとして再作成し、Google Docsホームに表示される状態を確認します。",
        "start_date": "2026-05-22",
        "end_date": "2026-05-23",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】docs NotebookLM同期・Google Docs化",
        "description": "docs/*.md 14件をLocal OAuth Drive APIでk-umezawa@ml-mightylink.com所有のGoogle Docsへ同期し、NotebookLM CLI source add-drive用manifestを作成します。",
        "start_date": "2026-05-22",
        "end_date": "2026-05-23",
        "is_all_day": True
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLM CLI再認証・Source追加",
        "description": "notebooklm loginでk-umezawa@ml-mightylink.comを選択し、sync_docs_to_notebooklm.pyを再実行してNotebookLMへdocs sourceを追加します。",
        "start_time": "2026-05-23T10:00:00",
        "end_time": "2026-05-23T10:30:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】NotebookLM Agent Brief取得",
        "description": "NotebookLM ask/summaryで設計情報・ロードマップ・6/2前タスクを要約し、AIエージェントの次回開発入力としてnotebooklm_agent_brief.mdへ保存します。",
        "start_time": "2026-05-23T10:30:00",
        "end_time": "2026-05-23T11:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】社長プレゼン最終リハーサル",
        "description": "公開URL、ローカルAPI、Google Sheets WBS、Calendar同期、説明資料、想定QA、バックアップ手順を最終確認します。",
        "start_time": "2026-06-01T16:00:00",
        "end_time": "2026-06-01T17:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    },
    {
        "summary": "【Mighty Skill-Bridge】第1回 社長報告会（プロジェクト方針決定）",
        "description": "「Mighty Skill-Bridge」の公開デモ、WBS、Google Workspace連携、6/2以降の企画・サービス内容・優先機能・開発方針を確認し、決定します。",
        "start_time": "2026-06-02T13:00:00",
        "end_time": "2026-06-02T14:00:00",
        "time_zone": "Asia/Tokyo",
        "is_all_day": False
    }
]

def generate_ics_file():
    """Generates standard iCalendar (.ics) file for 1-click import."""
    print("[*] Generating iCalendar (.ics) file...")
    
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Mighty-Link//AI Connect Calendar Sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Mighty Skill-Bridge 開発計画",
        "X-WR-TIMEZONE:Asia/Tokyo"
    ]
    
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    for ev in SCHEDULE_EVENTS:
        ics_lines.append("BEGIN:VEVENT")
        stable_uid = uuid.uuid5(uuid.NAMESPACE_URL, ev["summary"])
        ics_lines.append(f"UID:{stable_uid}@mighty-link.ai")
        ics_lines.append(f"DTSTAMP:{now_str}")
        ics_lines.append(f"SUMMARY:{ev['summary']}")
        ics_lines.append(f"DESCRIPTION:{ev['description']}")
        
        if ev["is_all_day"]:
            start = ev["start_date"].replace("-", "")
            end = ev["end_date"].replace("-", "")
            ics_lines.append(f"DTSTART;VALUE=DATE:{start}")
            ics_lines.append(f"DTEND;VALUE=DATE:{end}")
        else:
            # Format: 2026-06-02T13:00:00 -> 20260602T130000
            start = ev["start_time"].replace("-", "").replace(":", "")
            end = ev["end_time"].replace("-", "").replace(":", "")
            ics_lines.append(f"DTSTART;TZID=Asia/Tokyo:{start}")
            ics_lines.append(f"DTEND;TZID=Asia/Tokyo:{end}")
            
        ics_lines.append("END:VEVENT")
        
    ics_lines.append("END:VCALENDAR")
    
    ics_content = "\r\n".join(ics_lines) + "\r\n"
    
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    filepath = os.path.join(EXPORTS_DIR, "mighty_development_plan.ics")
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(ics_content)
        
    print(f"[+] iCalendar (.ics) file generated successfully: {os.path.abspath(filepath)}")
    print("[*] You can import this file directly into Google Calendar, Outlook, or Apple Calendar.")
    return filepath

from google.oauth2.credentials import Credentials as UserCredentials

def get_google_auth_token(auth_mode):
    """Retrieves standard Access Token directly from JSON files depending on auth_mode."""
    scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ]
    if "OAuth" in auth_mode:
        if os.path.exists(AUTHORIZED_USER_FILE):
            with open(AUTHORIZED_USER_FILE, "r", encoding="utf-8") as f:
                info = json.load(f)
            creds = UserCredentials.from_authorized_user_info(info)
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            return creds.token
    elif "Service Account" in auth_mode:
        if os.path.exists(CREDENTIALS_FILE):
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            auth_req = google.auth.transport.requests.Request()
            creds.refresh(auth_req)
            return creds.token
    raise Exception("No valid credentials found to extract access token.")

def build_event_body(ev):
    """Builds a deterministic Calendar API event payload."""
    event_body = {
        "summary": ev["summary"],
        "description": ev["description"],
        "extendedProperties": {
            "private": {
                "syncSource": "mighty-link-ai-connect",
                "syncKey": hashlib.sha1(ev["summary"].encode("utf-8")).hexdigest()
            }
        }
    }

    if ev["is_all_day"]:
        event_body["start"] = {"date": ev["start_date"]}
        event_body["end"] = {"date": ev["end_date"]}
    else:
        event_body["start"] = {"dateTime": ev["start_time"], "timeZone": ev["time_zone"]}
        event_body["end"] = {"dateTime": ev["end_time"], "timeZone": ev["time_zone"]}

    return event_body

def event_window_params(ev):
    """Returns a small search window for finding existing calendar events."""
    if ev["is_all_day"]:
        start = datetime.date.fromisoformat(ev["start_date"]) - datetime.timedelta(days=1)
        end = datetime.date.fromisoformat(ev["end_date"]) + datetime.timedelta(days=1)
        return {
            "timeMin": f"{start.isoformat()}T00:00:00+09:00",
            "timeMax": f"{end.isoformat()}T23:59:59+09:00"
        }

    start_dt = datetime.datetime.fromisoformat(ev["start_time"]) - datetime.timedelta(hours=6)
    end_dt = datetime.datetime.fromisoformat(ev["end_time"]) + datetime.timedelta(hours=6)
    return {
        "timeMin": f"{start_dt.isoformat()}+09:00",
        "timeMax": f"{end_dt.isoformat()}+09:00"
    }

def event_matches(existing_event, desired_event):
    """Checks summary and start/end values so re-sync updates instead of duplicating."""
    if existing_event.get("summary") != desired_event.get("summary"):
        return False
    existing_start = existing_event.get("start", {})
    existing_end = existing_event.get("end", {})
    desired_start = desired_event.get("start", {})
    desired_end = desired_event.get("end", {})
    return event_time_value(existing_start) == event_time_value(desired_start) and event_time_value(existing_end) == event_time_value(desired_end)

def event_time_value(event_time):
    if "date" in event_time:
        return event_time["date"]
    # Google may return 2026-06-02T13:00:00+09:00 while the request uses
    # dateTime plus a timeZone field. Compare the local timestamp portion.
    return event_time.get("dateTime", "")[:19]

def find_existing_event(headers, calendar_id, ev, desired_event):
    list_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    params = {
        "q": ev["summary"],
        "singleEvents": "true",
        "orderBy": "startTime",
        **event_window_params(ev)
    }
    res = requests.get(list_url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"  [!] Could not check existing events for {ev['summary']}: {res.text}")
        return None

    matches = []
    for item in res.json().get("items", []):
        if event_matches(item, desired_event):
            matches.append(item)

    if len(matches) > 1:
        for duplicate in matches[1:]:
            delete_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{duplicate['id']}"
            delete_res = requests.delete(delete_url, headers=headers)
            if delete_res.status_code in [200, 204]:
                print(f"  [*] Removed duplicate event: {ev['summary']}")
            else:
                print(f"  [!] Failed to remove duplicate event {duplicate['id']}: {delete_res.text}")

    return matches[0] if matches else None

def sync_to_google_calendar(access_token, auth_mode):
    """Creates events in Google Calendar via HTTP REST API."""
    print(f"[*] Starting API Sync (Auth Mode: {auth_mode})...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 1. Determine which Calendar to write to
    target_calendar_id = "primary"
    
    # If OAuth 2.0 (User Drive), we can list and create custom calendars!
    if "OAuth" in auth_mode:
        print("[*] Checking for existing custom 'Mighty Skill-Bridge 開発計画' calendar...")
        list_url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
        res = requests.get(list_url, headers=headers)
        
        if res.status_code == 200:
            calendars = res.json().get("items", [])
            for cal in calendars:
                if cal.get("summary") == "Mighty Skill-Bridge 開発計画":
                    target_calendar_id = cal.get("id")
                    print(f"[+] Found existing custom calendar. ID: {target_calendar_id}")
                    break
            
            if target_calendar_id == "primary":
                print("[*] Custom calendar not found. Creating a new one...")
                create_url = "https://www.googleapis.com/calendar/v3/calendars"
                cal_body = {"summary": "Mighty Skill-Bridge 開発計画", "timeZone": "Asia/Tokyo"}
                c_res = requests.post(create_url, headers=headers, json=cal_body)
                
                if c_res.status_code == 200:
                    target_calendar_id = c_res.json().get("id")
                    print(f"[+] Successfully created new custom calendar! ID: {target_calendar_id}")
                else:
                    print(f"[-] Failed to create custom calendar ({c_res.status_code}). Using Primary calendar instead.")
        else:
            print(f"[-] Failed to fetch calendar list. Using Primary calendar.")

    # 2. In Service Account Mode, we attempt to write to USER_EMAIL
    if "Service Account" in auth_mode:
        target_calendar_id = USER_EMAIL
        print(f"[*] Service Account mode: Writing to {USER_EMAIL} (Requires manual calendar sharing configured).")

    # 3. Create Events
    success_count = 0
    fail_count = 0
    update_count = 0
    
    for ev in SCHEDULE_EVENTS:
        event_body = build_event_body(ev)
        existing_event = find_existing_event(headers, target_calendar_id, ev, event_body)

        if existing_event:
            event_url = f"https://www.googleapis.com/calendar/v3/calendars/{target_calendar_id}/events/{existing_event['id']}"
            res = requests.patch(event_url, headers=headers, json=event_body)
            action_label = "Updated"
        else:
            insert_url = f"https://www.googleapis.com/calendar/v3/calendars/{target_calendar_id}/events"
            res = requests.post(insert_url, headers=headers, json=event_body)
            action_label = "Created"
        
        if res.status_code in [200, 201]:
            print(f"  [+] {action_label} event: {ev['summary']}")
            success_count += 1
            if existing_event:
                update_count += 1
        else:
            print(f"  [-] Failed to sync event: {ev['summary']} | Error: {res.text}")
            fail_count += 1
            
    print("="*60)
    print(f"[+] API Sync Complete! Success: {success_count}, Updated: {update_count}, Failed: {fail_count}")
    
    if fail_count > 0 and "Service Account" in auth_mode:
        print("[!] Note: Google Service Accounts cannot write to your calendar by default.")
        print(f"    Please share your calendar with the service account email with 'Make changes' permission,")
        print("    or import the generated 'exports/mighty_development_plan.ics' file.")
    print("="*60)

def main():
    # Configure stdout/stderr encoding to UTF-8 to prevent encoding errors on Windows terminal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    print("="*60)
    print("[*] Mighty-Link AI Connect: WBS Google Calendar Sync Tool")
    print("="*60)

    # Always generate the .ics file first (failsafe & convenient)
    generate_ics_file()
    
    client = None
    auth_mode = None

    # 1. OAuth 2.0 Desktop Authentication (Priority)
    if os.path.exists(CLIENT_SECRET_FILE):
        print("[*] Found OAuth 2.0 client credentials. Authenticating...")
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events"
            ]
            client = gspread.oauth(
                scopes=scopes,
                credentials_filename=CLIENT_SECRET_FILE,
                authorized_user_filename=AUTHORIZED_USER_FILE
            )
            assert_expected_google_account(credentials_from_gspread_client(client), USER_EMAIL)
            auth_mode = "OAuth 2.0 (User Drive)"
            print("[+] OAuth 2.0 Authentication Successful!")
        except GoogleWorkspaceAccountError as e:
            print(f"[-] OAuth 2.0 Workspace Account Verification Failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[-] OAuth 2.0 Authentication Failed: {e}")
            print("[*] Falling back to Service Account check...")

    # 2. Service Account Fallback
    if not client and os.path.exists(CREDENTIALS_FILE):
        print("[*] Authenticating via Google Cloud Service Account...")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ]
        try:
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
            client = gspread.authorize(creds)
            auth_mode = "Service Account"
            print("[+] Service Account Authentication Successful!")
        except Exception as e:
            print(f"[-] Service Account Authentication Failed: {e}")

    # 3. Perform Sync if Client authenticated
    if client:
        try:
            access_token = get_google_auth_token(auth_mode)
            sync_to_google_calendar(access_token, auth_mode)
        except Exception as e:
            print(f"[-] API Execution failed: {e}")
            print("[*] Please import the generated 'exports/mighty_development_plan.ics' file manually.")
    else:
        print("[-] API Authentication credentials not found.")
        print("[*] Synchronized WBS via iCalendar file successfully. Please import the .ics file manually.")

if __name__ == "__main__":
    main()
