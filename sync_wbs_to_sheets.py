#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: WBS Google Sheets Sync Script
Author: Antigravity 2.0 (AI Agent)

This script parses WBS.tsv and pushes the tasks directly to a specified Google Spreadsheet
via the Google Sheets API. It automatically applies professional visual styling using the
Mighty-Link brand colors (deep blue header, centered columns, and status color highlights).
"""

import os
import sys
import csv
import json

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
CREDENTIALS_FILE = "credentials.json"
TSV_FILE = "WBS.tsv"

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
    print("🚀 Mighty-Link AI Connect: WBS Google Sheets Sync Tool")
    print("="*60)

    # 1. Check for API Credentials
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[-] ERROR: Google API credentials file '{CREDENTIALS_FILE}' not found.")
        print(f"\n[💡 Setup Instructions]")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a project and enable both 'Google Sheets API' and 'Google Drive API'.")
        print("3. Go to Credentials -> Create Credentials -> Service Account.")
        print("4. Under Actions for that service account, select Keys -> Add Key -> Create New Key (JSON).")
        print("5. Save that downloaded JSON file as 'credentials.json' in this project folder.")
        print("6. IMPORTANT: Share your Google Sheet with the client_email address inside the JSON!")
        sys.exit(1)

    # 2. Get Spreadsheet ID from args or env
    spreadsheet_id = None
    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
    else:
        spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    if not spreadsheet_id:
        print("\n[*] SPREADSHEET_ID not provided via command line argument or environment variable.")
        spreadsheet_id = input("👉 Please enter your Google Spreadsheet ID (or full URL): ").strip()
        
    if not spreadsheet_id:
        print("[-] Spreadsheet ID is required to continue. Exiting.")
        sys.exit(1)

    # Extract ID if URL is provided
    if "docs.google.com/spreadsheets" in spreadsheet_id:
        try:
            parts = spreadsheet_id.split("/d/")
            if len(parts) > 1:
                spreadsheet_id = parts[1].split("/")[0]
        except Exception:
            pass

    # 3. Authenticate with Google API
    print("[*] Authenticating with Google Cloud Platform...")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        print("[+] Authentication Successful!")
    except Exception as e:
        print(f"[-] Authentication Failed: {e}")
        sys.exit(1)

    # 4. Open Spreadsheet
    print(f"[*] Connecting to Spreadsheet ID: {spreadsheet_id}...")
    try:
        sh = client.open_by_key(spreadsheet_id)
        print(f"[+] Connected! Spreadsheet Title: '{sh.title}'")
    except Exception as e:
        print(f"[-] Failed to open sheet. Ensure your service account email is shared with the spreadsheet. Error: {e}")
        sys.exit(1)

    # 5. Load data and setup Worksheet
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

    # 6. Upload Data
    print("[*] Uploading WBS data rows...")
    worksheet.update(values=wbs_data, range_name="A1")
    print(f"[+] Successfully wrote {len(wbs_data)} rows to the sheet!")

    # 7. Apply Professional Styles (Workspace AI Design Theme)
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
        # Header row height
        worksheet.set_row_height(1, 40)
        # Data rows heights
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
    # Header: タスクID, 大フェーズ, 小フェーズ, タスク名, 担当, 実行エンジン, Sheets Live 連携アクション, ステータス, 開始日, 終了予定日
    # Status is column 8 (H)
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
    # Establishes default readable widths
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
    print("🎉 Sync Completed Successfully!")
    print("👉 View your live WBS sheet now!")
    print("="*60)

if __name__ == "__main__":
    main()
