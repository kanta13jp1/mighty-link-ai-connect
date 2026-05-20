#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: WBS Google Sheets Sync Script
Author: Antigravity 2.0 (AI Agent)

This script parses WBS.tsv and pushes the tasks directly to a specified Google Spreadsheet.
To bypass Google Cloud Service Account quota limitations, this script supports both:
1. OAuth 2.0 Desktop Authentication (via client_secret.json) -> Uses kanta13jp@gmail.com's own drive (No Quota Limits!)
2. Service Account Authentication (via credentials.json) -> Traditional fallback.
"""

import os
import sys
import csv
import json

# Force stdout/stderr to use utf-8 if possible
if sys.platform.startswith('win'):
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

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

# Configuration
CREDENTIALS_FILE = "credentials.json"     # Service Account
CLIENT_SECRET_FILE = "client_secret.json" # OAuth 2.0 Desktop client
TSV_FILE = "WBS.tsv"
USER_EMAIL = "kanta13jp@gmail.com"

# Mighty-Link Color Palette (Normalized to 0.0 - 1.0 for Sheets API)
COLORS = {
    "header_bg": {"red": 26/255, "green": 115/255, "blue": 232/255}, # #1A73E8 (Mighty Blue)
    "header_text": {"red": 1.0, "green": 1.0, "blue": 1.0},          # White
    "status_todo": {"red": 241/255, "green": 243/255, "blue": 244/255}, # Light Gray
    "status_working": {"red": 254/255, "green": 247/255, "blue": 224/255}, # Light Yellow
    "status_done": {"red": 230/255, "green": 244/255, "blue": 234/255}, # Light Green
    "border_gray": {"red": 218/255, "green": 220/255, "blue": 224/255}
}

def load_wbs_data(filepath):
    """Loads TSV data into a 2D list."""
    if not os.path.exists(filepath):
        print(f"[-] Error: Source WBS file '{filepath}' not found.")
        sys.exit(1)
        
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            data.append(row)
    return data

def main():
    print("="*60)
    print("[*] Mighty-Link AI Connect: WBS Google Sheets Sync Tool")
    print("="*60)

    client = None
    auth_mode = None

    # 1. Determine Authentication Mode (OAuth 2.0 has priority to bypass storage quotas)
    if os.path.exists(CLIENT_SECRET_FILE):
        print("[*] Found OAuth 2.0 client credentials. Launching Browser Authentication...")
        try:
            # Performs local OAuth authentication. Spawns browser on first run, saves authorized_user.json
            client = gspread.oauth(
                credentials_filename=CLIENT_SECRET_FILE,
                authorized_user_filename="authorized_user.json"
            )
            auth_mode = "OAuth 2.0 (User Drive)"
            print("[+] OAuth 2.0 Authentication Successful!")
        except Exception as e:
            print(f"[-] OAuth 2.0 Authentication Failed: {e}")
            print("[*] Falling back to Service Account check...")

    if not client:
        # Fallback to Service Account
        if os.path.exists(CREDENTIALS_FILE):
            print("[*] Authenticating via Google Cloud Service Account...")
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            try:
                creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
                client = gspread.authorize(creds)
                auth_mode = "Service Account (Robot)"
                print("[+] Service Account Authentication Successful!")
            except Exception as e:
                print(f"[-] Service Account Authentication Failed: {e}")
                sys.exit(1)
        else:
            print(f"[-] ERROR: Neither '{CLIENT_SECRET_FILE}' nor '{CREDENTIALS_FILE}' found.")
            print("\n[💡 Bypass & Setup Instructions (OAuth 2.0 Mode - Recommended)]")
            print("To completely bypass Drive storage quota limitations, use your personal Google Drive account:")
            print("1. Go to Google Cloud Console (https://console.cloud.google.com/) -> API & Services -> Credentials.")
            print("2. Click '+ Create Credentials' -> 'OAuth client ID'.")
            print("3. (If prompted) Click 'Configure Consent Screen', select 'External', input App Name ('Mighty WBS'), and save.")
            print("   * Under 'Test users', add 'kanta13jp@gmail.com'.")
            print("4. Go back to Credentials -> Create Credentials -> OAuth client ID.")
            print("5. Choose Application Type: 'Desktop App', name it, and click Create.")
            print("6. Download the JSON file and rename it to 'client_secret.json' in this folder.")
            sys.exit(1)

    # 2. Check for spreadsheet ID, if empty -> AUTO CREATE
    spreadsheet_id = None
    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
    else:
        spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    sh = None
    if not spreadsheet_id:
        # AUTO CREATION MODE
        sheet_title = "Mighty-Link AI Connect WBS"
        print(f"\n[*] SPREADSHEET_ID not provided. Entering [AUTO CREATE MODE]...")
        print(f"[*] Creating a brand new Google Spreadsheet: '{sheet_title}' under {auth_mode}...")
        try:
            sh = client.create(sheet_title)
            spreadsheet_id = sh.id
            print(f"[+] Spreadsheet created successfully! ID: {spreadsheet_id}")
            
            # If authenticated via Service account, we must share it with the user's Gmail
            if auth_mode == "Service Account (Robot)":
                print(f"[*] Sharing spreadsheet with '{USER_EMAIL}' as Editor...")
                sh.share(USER_EMAIL, perm_type="user", role="writer")
                print(f"[+] Successfully shared! It will appear in your 'Shared with me' Google Drive folder.")
            else:
                print(f"[+] The spreadsheet is directly owned by your account ({USER_EMAIL})!")
                print("[+] No manual sharing needed! It is located directly in your Google Drive.")
        except Exception as e:
            print(f"[-] Auto creation failed: {e}")
            if auth_mode == "Service Account (Robot)":
                print("\n[⚠️ Storage Quota Alert]")
                print("Your Service Account Drive quota is exceeded. To fix this automatically:")
                print(f"Please setup OAuth 2.0 by downloading 'client_secret.json' as detailed in the instructions above.")
            sys.exit(1)
    else:
        # Open existing sheet if ID is provided
        if "docs.google.com/spreadsheets" in spreadsheet_id:
            try:
                parts = spreadsheet_id.split("/d/")
                if len(parts) > 1:
                    spreadsheet_id = parts[1].split("/")[0]
            except Exception:
                pass
                
        print(f"[*] Connecting to existing Spreadsheet ID: {spreadsheet_id}...")
        try:
            sh = client.open_by_key(spreadsheet_id)
            print(f"[+] Connected! Spreadsheet Title: '{sh.title}'")
        except Exception as e:
            print(f"[-] Failed to open sheet. Ensure the sheet is shared if using Service Account. Error: {e}")
            sys.exit(1)

    # 3. Load data and setup Worksheet
    print("[*] Parsing local WBS.tsv...")
    wbs_data = load_wbs_data(TSV_FILE)
    if not wbs_data:
        print("[-] No WBS data found in TSV file. Exiting.")
        sys.exit(1)

    sheet_name = "Mighty-Link WBS"
    try:
        worksheet = sh.worksheet(sheet_name)
        print(f"[*] Found existing worksheet: '{sheet_name}'. Clearing content...")
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"[*] Worksheet '{sheet_name}' not found. Creating a new one...")
        worksheet = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
        print(f"[+] Worksheet '{sheet_name}' created successfully.")
        
        # Remove default Sheet1 if we created a new one to keep it clean
        try:
            default_sheet = sh.worksheet("Sheet1")
            sh.del_worksheet(default_sheet)
        except Exception:
            pass

    # 4. Upload Data
    print("[*] Uploading WBS data rows...")
    worksheet.update(values=wbs_data, range_name="A1")
    print(f"[+] Successfully wrote {len(wbs_data)} rows to the sheet!")

    # 5. Apply Professional Styles (Workspace AI Design Theme)
    print("[*] Applying Mighty-Link professional branding & styles...")
    num_rows = len(wbs_data)
    num_cols = len(wbs_data[0]) if num_rows > 0 else 0
    last_col_letter = chr(64 + num_cols) # 'J' if 10 columns

    # A. Format Header Row (Mighty Blue Background + White Bold Text)
    header_range = f"A1:{last_col_letter}1"
    worksheet.format(header_range, {
        "backgroundColor": COLORS["header_bg"],
        "textFormat": {
            "foregroundColor": COLORS["header_text"],
            "bold": True,
            "fontSize": 11
        },
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE"
    })

    # B. Set Row Heights (Header: 40px, Data Rows: 28px)
    try:
        worksheet.set_row_height(1, 40)
        for r in range(2, num_rows + 1):
            worksheet.set_row_height(r, 28)
    except Exception as e:
        print(f"[!] Warning while setting row heights: {e}")

    # C. Apply Borders and Center Alignments to Task IDs, Dates and Engine columns
    center_cols = ["A", "E", "F", "H", "I", "J"]  # IDs, Owner, Engine, Status, Dates
    for col in center_cols:
        col_range = f"{col}2:{col}{num_rows}"
        worksheet.format(col_range, {
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE"
        })

    # D. Colorize Status Column dynamically (Typically Column H / Index 8 in TSV)
    print("[*] Coloring WBS status cells dynamically...")
    status_col_index = 8
    for r in range(2, num_rows + 1):
        status_value = worksheet.cell(r, status_col_index).value
        cell_ref = f"H{r}"
        
        bg_color = COLORS["status_todo"]
        if status_value == "完了" or status_value == "Done" or status_value == "[Done]":
            bg_color = COLORS["status_done"]
        elif status_value == "実行中" or status_value == "Agent Working" or status_value == "Reviewing":
            bg_color = COLORS["status_working"]
            
        worksheet.format(cell_ref, {
            "backgroundColor": bg_color,
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER"
        })

    # E. Adjust Column Widths to fit content perfectly
    col_widths = {
        'A': 80,   # ID
        'B': 130,  # Big Phase
        'C': 130,  # Small Phase
        'D': 300,  # Task Name
        'E': 100,  # Owner
        'F': 130,  # Engine
        'G': 350,  # Sheets Live Sync
        'H': 120,  # Status
        'I': 110,  # Start Date
        'J': 110   # End Date
    }
    for col_letter, width in col_widths.items():
        try:
            worksheet.set_column_width(col_letter, width)
        except Exception:
            pass

    print("="*60)
    print("[+] Sync Completed Successfully!")
    print(f"[*] Spreadsheet URL: {sh.url}")
    print("="*60)

if __name__ == "__main__":
    main()
