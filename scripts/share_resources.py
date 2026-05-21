#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: Resource Sharing Automation Tool
Author: Antigravity 2.0 (AI Agent)

This script automatically shares:
1. The custom Google Calendar "Mighty Skill-Bridge 開発計画"
2. The Google Spreadsheet (WBS)
with the CEO's Google Account: kobayashi-masami@ml-mightylink.com
"""

import os
import sys
import json
import requests
from google.oauth2.credentials import Credentials as UserCredentials
import google.auth.transport.requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Configuration
AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
USER_EMAIL = "k-umezawa@ml-mightylink.com"
CEO_EMAIL = "kobayashi-masami@ml-mightylink.com"
SPREADSHEET_ID = "1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

from google_workspace_account import assert_expected_google_account

def get_access_token():
    """Retrieves standard Access Token from authorized_user.json."""
    if not os.path.exists(AUTHORIZED_USER_FILE):
        raise FileNotFoundError(f"[-] Credentials file '{AUTHORIZED_USER_FILE}' not found.")
        
    with open(AUTHORIZED_USER_FILE, "r", encoding="utf-8") as f:
        info = json.load(f)
        
    creds = UserCredentials.from_authorized_user_info(info, scopes=SCOPES)
    assert_expected_google_account(creds, USER_EMAIL)
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return creds.token

def share_google_calendar(access_token):
    """Finds the custom calendar and adds the CEO as a reader/writer."""
    print("[*] Accessing Google Calendar API...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 1. Find Calendar ID
    print("[*] Checking for custom 'Mighty Skill-Bridge 開発計画' calendar...")
    list_url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    res = requests.get(list_url, headers=headers)
    
    if res.status_code != 200:
        print(f"[-] Failed to fetch calendar list: {res.text}")
        return False
        
    calendars = res.json().get("items", [])
    target_calendar_id = None
    for cal in calendars:
        if cal.get("summary") == "Mighty Skill-Bridge 開発計画":
            target_calendar_id = cal.get("id")
            break
            
    if not target_calendar_id:
        print("[-] Custom calendar 'Mighty Skill-Bridge 開発計画' not found in your list.")
        return False
        
    print(f"[+] Found custom calendar. ID: {target_calendar_id}")
    
    # 2. Add ACL rule for CEO (role: 'writer' so that the CEO can edit if needed, or 'reader')
    # Let's give 'writer' role so the CEO can manage schedule together.
    acl_url = f"https://www.googleapis.com/calendar/v3/calendars/{target_calendar_id}/acl"
    acl_body = {
        "role": "writer",
        "scope": {
            "type": "user",
            "value": CEO_EMAIL
        }
    }
    
    print(f"[*] Adding {CEO_EMAIL} to Calendar ACL as 'writer'...")
    acl_res = requests.post(acl_url, headers=headers, json=acl_body)
    
    if acl_res.status_code in [200, 201]:
        print(f"[+] Successfully shared calendar with {CEO_EMAIL}!")
        return True
    else:
        # Fallback to 'reader' if 'writer' fails or try again
        print(f"[-] Failed to add writer ACL: {acl_res.text}")
        print("[*] Retrying with 'reader' role...")
        acl_body["role"] = "reader"
        acl_res_retry = requests.post(acl_url, headers=headers, json=acl_body)
        if acl_res_retry.status_code in [200, 201]:
            print(f"[+] Successfully shared calendar with {CEO_EMAIL} as 'reader'!")
            return True
        else:
            print(f"[-] Failed to add reader ACL: {acl_res_retry.text}")
            return False

def share_google_spreadsheet(access_token):
    """Shares the Google Spreadsheet with the CEO as a writer."""
    print("[*] Accessing Google Drive API to share Spreadsheet...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Drive API v3 Permissions create endpoint
    perm_url = f"https://www.googleapis.com/drive/v3/files/{SPREADSHEET_ID}/permissions?sendNotificationEmail=true"
    perm_body = {
        "role": "writer",
        "type": "user",
        "emailAddress": CEO_EMAIL
    }
    
    print(f"[*] Adding {CEO_EMAIL} as 'writer' permission on Spreadsheet {SPREADSHEET_ID}...")
    res = requests.post(perm_url, headers=headers, json=perm_body)
    
    if res.status_code in [200, 201]:
        print(f"[+] Successfully shared Spreadsheet with {CEO_EMAIL}!")
        return True
    else:
        print(f"[-] Failed to share Spreadsheet: {res.text}")
        return False

def main():
    # Setup stdout encoding
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    print("="*60)
    print("[*] Mighty-Link AI Connect: CEO Resource Sharing Tool")
    print("="*60)
    
    try:
        token = get_access_token()
        
        # Share Calendar
        calendar_success = share_google_calendar(token)
        print()
        
        # Share Spreadsheet
        sheets_success = share_google_spreadsheet(token)
        
        print("="*60)
        if calendar_success and sheets_success:
            print(f"[🎉] SUCCESS! Shared both Calendar and Spreadsheet with {CEO_EMAIL}.")
        else:
            print("[⚠️] PARTIAL SUCCESS or FAILURE. Please review details above.")
        print("="*60)
        
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
