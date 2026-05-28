#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: Apply CEO Decisions to WBS Script
Author: Antigravity 2.0 (AI Agent)

This script parses docs/CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md
based on the chosen direction (A, B, C, or D) and appends the appropriate
Phase 7 tasks directly into data/WBS.tsv.
"""

import os
import sys
import re
import csv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
TSV_FILE = os.path.join(DATA_DIR, "WBS.tsv")
ROADMAP_MD = os.path.join(DOCS_DIR, "CEO_PRESENTATION_POST_DECISION_ROADMAP_2026-06-02.md")

DIRECTIONS = {
    "A": {
        "title": "## 方向性 A: AI フィット診断支援 (Phase 7-A)",
        "subphase": "AIフィット診断"
    },
    "B": {
        "title": "## 方向性 B: Workspace 連携型 PM 支援 (Phase 7-B)",
        "subphase": "PM支援連携"
    },
    "C": {
        "title": "## 方向性 C: AI PoC 高速構築支援 (Phase 7-C)",
        "subphase": "AI PoC構築"
    },
    "D": {
        "title": "## 方向性 D: 保留 (5-7 営業日以内の追加面談で再決定)",
        "subphase": "保留対応"
    }
}

COMMON_TITLE = "## 共通: 全方向性で着手するタスク (Phase 7-common)"

def parse_dates(date_str):
    """Parses date string from markdown table and returns YYYY-MM-DD tuples."""
    # Matches patterns like "6/2 18:00 - 6/3 12:00" or "6/3 - 6/9" or "6/4 - 6/5"
    matches = re.findall(r"(\d+)/(\d+)", date_str)
    if len(matches) >= 2:
        m1, d1 = matches[0]
        m2, d2 = matches[1]
        return f"2026-{int(m1):02d}-{int(d1):02d}", f"2026-{int(m2):02d}-{int(d2):02d}"
    elif len(matches) == 1:
        m1, d1 = matches[0]
        return f"2026-{int(m1):02d}-{int(d1):02d}", f"2026-{int(m1):02d}-{int(d1):02d}"
    
    # Fallbacks
    if "追加面談" in date_str:
        return "2026-06-03", "2026-06-04"
    return "2026-06-03", "2026-06-03"

def determine_engine(assignee):
    """Determines execution engine based on assignee."""
    assignee_lower = assignee.lower()
    if "codex" in assignee_lower:
        return "VSCode + Codex"
    elif "claude" in assignee_lower:
        return "VSCode + Claude Code"
    elif "antigravity" in assignee_lower:
        return "Antigravity 2.0"
    return "Gemini API 現行モデル"

def extract_table_rows(md_content, section_title):
    """Extracts table rows falling under a specific section title."""
    # Regex to find the section and grab the first table text block after it
    pattern = re.escape(section_title) + r".*?\n(\|.*?\n\|.*?\n(?:\|.*?\n)+)"
    match = re.search(pattern, md_content, re.DOTALL)
    if not match:
        print(f"[-] Warning: Section '{section_title}' not found in roadmap markdown.")
        return []
    
    table_text = match.group(1)
    rows = []
    for line in table_text.strip().split("\n"):
        if "---" in line or "ID" in line:
            continue  # Skip header and divider lines
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 5:
            rows.append(parts)
    return rows

def main():
    print("="*60)
    print("[*] Mighty-Link AI Connect: CEO Decision WBS Ingest Tool")
    print("="*60)

    # 1. Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python scripts/apply_ceo_decisions.py <A/B/C/D>")
        print("Directions:")
        print("  A: AI Fit Assessment Support (AIフィット診断支援)")
        print("  B: Workspace Integrated PM Support (Workspace連携型PM支援)")
        print("  C: AI PoC Fast-track Build Support (AI PoC高速構築支援)")
        print("  D: Deferred / Follow-up Meeting (保留/追加面談)")
        sys.exit(1)
    
    choice = sys.argv[1].upper()
    if choice not in DIRECTIONS:
        print(f"[-] Error: Invalid choice '{choice}'. Must be A, B, C, or D.")
        sys.exit(1)

    direction_info = DIRECTIONS[choice]
    print(f"[*] Applying Option {choice}: {direction_info['title'][3:]}")

    # 2. Check roadmap file
    if not os.path.exists(ROADMAP_MD):
        print(f"[-] Error: Roadmap markdown not found at {ROADMAP_MD}")
        sys.exit(1)
    
    with open(ROADMAP_MD, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 3. Extract table rows
    print("[*] Extracting Phase 7-common tasks...")
    common_rows = extract_table_rows(md_content, COMMON_TITLE)
    print(f"[+] Found {len(common_rows)} common tasks.")

    print(f"[*] Extracting Phase 7-{choice} tasks...")
    choice_rows = extract_table_rows(md_content, direction_info["title"])
    print(f"[+] Found {len(choice_rows)} specific tasks.")

    if not common_rows and not choice_rows:
        print("[-] Error: No tasks found. Please verify the markdown format.")
        sys.exit(1)

    # 4. Read existing WBS data
    if not os.path.exists(TSV_FILE):
        print(f"[-] Error: WBS.tsv not found at {TSV_FILE}")
        sys.exit(1)

    existing_rows = []
    with open(TSV_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            existing_rows.append(row)

    # Remove any existing T7XX rows to avoid duplicates on re-runs
    header = existing_rows[0]
    cleaned_rows = [header]
    removed_count = 0
    for row in existing_rows[1:]:
        if row and row[0].startswith("T7"):
            removed_count += 1
            continue
        cleaned_rows.append(row)
    
    if removed_count > 0:
        print(f"[*] Removed {removed_count} existing Phase 7 task rows from current WBS list.")

    # 5. Format and append new rows
    new_task_count = 0
    
    # 5a. Process common rows
    for r in common_rows:
        task_id = r[0]
        name = r[1]
        assignee = r[2]
        dates = r[3]
        notes = r[4]
        
        start_date, end_date = parse_dates(dates)
        engine = determine_engine(assignee)
        
        cleaned_rows.append([
            task_id,
            "7. 決定後実行",
            "共通管理",
            name,
            assignee,
            engine,
            notes,
            "未着手",
            start_date,
            end_date
        ])
        new_task_count += 1

    # 5b. Process choice rows
    for r in choice_rows:
        task_id = r[0]
        name = r[1]
        assignee = r[2]
        dates = r[3]
        notes = r[4]
        
        start_date, end_date = parse_dates(dates)
        engine = determine_engine(assignee)
        
        cleaned_rows.append([
            task_id,
            "7. 決定後実行",
            direction_info["subphase"],
            name,
            assignee,
            engine,
            notes,
            "未着手",
            start_date,
            end_date
        ])
        new_task_count += 1

    # 6. Write back to WBS.tsv
    with open(TSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(cleaned_rows)

    print(f"[+] Successfully wrote {new_task_count} Phase 7 tasks into {os.path.relpath(TSV_FILE, PROJECT_ROOT)}")
    print("\n[*] Next Steps:")
    print("1. Sync to Google Sheets: python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8")
    print("2. Sync to Google Calendar: python scripts/sync_wbs_to_calendar.py")
    print("="*60)

if __name__ == "__main__":
    main()
