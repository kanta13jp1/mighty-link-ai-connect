#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mighty-Link AI Connect: WBS Google Sheets Sync Script
Author: Antigravity 2.0 (AI Agent)

This script parses data/WBS.tsv and pushes the tasks directly to a specified Google Spreadsheet.
To bypass Google Cloud Service Account quota limitations, this script supports both:
1. OAuth 2.0 Desktop Authentication (via client_secret.json) -> Uses the Workspace user's own drive.
2. Service Account Authentication (via credentials.json) -> Traditional fallback.
"""

import os
import sys
import csv
import json
import re
import datetime
from collections import OrderedDict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# sys.stdout/stderr override removed to avoid logging capture interference


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
from google_workspace_account import (
    GoogleWorkspaceAccountError,
    assert_expected_google_account,
    credentials_from_gspread_client,
)

# Configuration
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")       # Service Account
CLIENT_SECRET_FILE = os.path.join(PROJECT_ROOT, "client_secret.json")   # OAuth 2.0 Desktop client
AUTHORIZED_USER_FILE = os.path.join(PROJECT_ROOT, "authorized_user.json")
TSV_FILE = os.path.join(DATA_DIR, "WBS.tsv")
ISSUES_TSV_FILE = os.path.join(DATA_DIR, "issues_tracker.tsv")
QA_TSV_FILE = os.path.join(DATA_DIR, "qa_tracker.tsv")
TEST_TSV_FILE = os.path.join(DATA_DIR, "test_results.tsv")
SECURITY_TSV_FILE = os.path.join(DATA_DIR, "security_log.tsv")
DEPLOY_TSV_FILE = os.path.join(DATA_DIR, "deploy_log.tsv")
USER_EMAIL = "k-umezawa@ml-mightylink.com"
WBS_SHEET_NAME = "Mighty-Link WBS"
SUMMARY_SHEET_NAME = "WBS Summary"
TIMELINE_SHEET_NAME = "WBS Timeline"
ISSUES_SHEET_NAME = "課題管理表"
QA_SHEET_NAME = "QA表"
TEST_SHEET_NAME = "テスト結果"
SECURITY_SHEET_NAME = "セキュリティ"
DEPLOY_SHEET_NAME = "デプロイ結果"
DATA_START_ROW = 8

# Mighty-Link Color Palette (Normalized to 0.0 - 1.0 for Sheets API)
COLORS = {
    "header_bg": {"red": 26/255, "green": 115/255, "blue": 232/255}, # #1A73E8 (Mighty Blue)
    "header_text": {"red": 1.0, "green": 1.0, "blue": 1.0},          # White
    "title_bg": {"red": 11/255, "green": 57/255, "blue": 84/255},
    "group_bg": {"red": 34/255, "green": 84/255, "blue": 130/255},
    "subheader_bg": {"red": 217/255, "green": 226/255, "blue": 243/255}, # CATS-like light blue
    "phase_bg": {"red": 226/255, "green": 239/255, "blue": 251/255},
    "summary_bg": {"red": 239/255, "green": 246/255, "blue": 255/255},
    "status_todo": {"red": 241/255, "green": 243/255, "blue": 244/255}, # Light Gray
    "status_working": {"red": 254/255, "green": 247/255, "blue": 224/255}, # Light Yellow
    "status_done": {"red": 230/255, "green": 244/255, "blue": 234/255}, # Light Green
    "status_alert": {"red": 252/255, "green": 228/255, "blue": 214/255},
    "warning_bg": {"red": 255/255, "green": 242/255, "blue": 204/255},
    "white": {"red": 1.0, "green": 1.0, "blue": 1.0},
    "black": {"red": 0.0, "green": 0.0, "blue": 0.0},
    "border_gray": {"red": 218/255, "green": 220/255, "blue": 224/255}
}

ENHANCED_HEADERS = [
    "WBS#",
    "Lv",
    "WP",
    "大フェーズ",
    "小フェーズ",
    "タスク名",
    "タスク内容・コメント",
    "状態",
    "主管/担当",
    "実行エンジン",
    "予定開始日",
    "予定終了日",
    "予定工数(日)",
    "進捗率",
    "アラート",
    "備考",
]

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


def load_tracker_data(filepath):
    """Loads an optional tracker TSV and pads rows to a rectangular grid."""
    if not os.path.exists(filepath):
        print(f"[!] Tracker source not found, skipping: {os.path.relpath(filepath, PROJECT_ROOT)}")
        return []

    rows = []
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row and any(cell.strip() for cell in row):
                rows.append(row)

    if not rows:
        return []

    width = max(len(row) for row in rows)
    return [row + [""] * (width - len(row)) for row in rows]


def normalize_status(status):
    status = (status or "").strip()
    if status in ["完了", "Done", "[Done]"]:
        return "完了"
    if status in ["実行中", "対応中", "Agent Working", "Reviewing"]:
        return "実行中"
    return "未着手"


def status_progress(status):
    status = normalize_status(status)
    if status == "完了":
        return "100%"
    if status == "実行中":
        return "50%"
    return "0%"


def extract_phase_no(phase, fallback):
    match = re.match(r"\s*(\d+)", phase or "")
    return match.group(1) if match else str(fallback)


def safe_cell(row, index, default=""):
    return row[index] if index < len(row) else default


def formula_quote(sheet_name):
    return f"'{sheet_name}'"


def ensure_worksheet(sh, title, rows=120, cols=20):
    try:
        worksheet = sh.worksheet(title)
        print(f"[*] Found existing worksheet: '{title}'. Clearing content...")
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"[*] Worksheet '{title}' not found. Creating a new one...")
        worksheet = sh.add_worksheet(title=title, rows=rows, cols=cols)
        print(f"[+] Worksheet '{title}' created successfully.")
    worksheet.resize(rows=rows, cols=cols)
    return worksheet


def parse_date_value(value):
    value = (value or "").strip()
    if not value:
        return ""
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return value


def build_enhanced_wbs(wbs_data):
    """Expands the simple TSV into a CATS-like hierarchical WBS grid."""
    phase_groups = OrderedDict()
    for row in wbs_data[1:]:
        if not row or not safe_cell(row, 0):
            continue
        phase_groups.setdefault(safe_cell(row, 1), []).append(row)

    data_rows = []
    task_rows = []

    for phase_idx, (phase, tasks) in enumerate(phase_groups.items(), start=1):
        phase_no = extract_phase_no(phase, phase_idx)
        starts = [parse_date_value(safe_cell(task, 8)) for task in tasks if safe_cell(task, 8)]
        ends = [parse_date_value(safe_cell(task, 9)) for task in tasks if safe_cell(task, 9)]
        phase_start = min(starts) if starts else ""
        phase_end = max(ends) if ends else ""
        task_start_row = DATA_START_ROW + len(data_rows) + 1
        task_end_row = task_start_row + len(tasks) - 1
        phase_sheet_row = DATA_START_ROW + len(data_rows)
        statuses = [normalize_status(safe_cell(task, 7)) for task in tasks]
        if all(status == "完了" for status in statuses):
            phase_status = "完了"
        elif all(status == "未着手" for status in statuses):
            phase_status = "未着手"
        else:
            phase_status = "実行中"

        data_rows.append([
            phase_no,
            1,
            "Phase",
            phase,
            "",
            phase,
            f"{len(tasks)} tasks / {phase_start} - {phase_end}",
            phase_status,
            "",
            "",
            phase_start,
            phase_end,
            f"=SUM(M{task_start_row}:M{task_end_row})",
            f"=IFERROR(AVERAGE(N{task_start_row}:N{task_end_row}),0%)",
            f'=IF(N{phase_sheet_row}=1,"完了",IF(N{phase_sheet_row}=0,"未着手","進行中"))',
            "",
        ])

        for seq, task in enumerate(tasks, start=1):
            sheet_row = DATA_START_ROW + len(data_rows)
            status = normalize_status(safe_cell(task, 7))
            row = [
                f"{phase_no}.{seq}",
                2,
                safe_cell(task, 0),
                phase,
                safe_cell(task, 2),
                safe_cell(task, 3),
                safe_cell(task, 6),
                status,
                safe_cell(task, 4),
                safe_cell(task, 5),
                parse_date_value(safe_cell(task, 8)),
                parse_date_value(safe_cell(task, 9)),
                f'=IF(AND(K{sheet_row}<>"",L{sheet_row}<>""),L{sheet_row}-K{sheet_row}+1,"")',
                status_progress(status),
                f'=IFS(H{sheet_row}="完了","完了",AND(K{sheet_row}<>"",TODAY()>K{sheet_row},N{sheet_row}=0),"着手遅れ",AND(L{sheet_row}<>"",TODAY()>L{sheet_row},N{sheet_row}<1),"終了遅れ",N{sheet_row}>0,"着手済",TRUE,"未着手")',
                "",
            ]
            data_rows.append(row)
            task_rows.append(row)

    last_data_row = DATA_START_ROW + len(data_rows) - 1
    report_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheet_values = [
        ["Mighty-Link AI Connect WBS 管理表"] + [""] * (len(ENHANCED_HEADERS) - 1),
        [f"参照テンプレート: 【次期CATS】WBS_分析計画工程(後半).xlsx / Last Sync: {report_time}"] + [""] * (len(ENHANCED_HEADERS) - 1),
        [""] * len(ENHANCED_HEADERS),
        [
            "総タスク", f"=COUNTIF(B{DATA_START_ROW}:B{last_data_row},2)",
            "完了", f'=COUNTIFS(B{DATA_START_ROW}:B{last_data_row},2,H{DATA_START_ROW}:H{last_data_row},"完了")',
            "実行中", f'=COUNTIFS(B{DATA_START_ROW}:B{last_data_row},2,H{DATA_START_ROW}:H{last_data_row},"実行中")',
            "未着手", f'=COUNTIFS(B{DATA_START_ROW}:B{last_data_row},2,H{DATA_START_ROW}:H{last_data_row},"未着手")',
            "完了率", f"=IFERROR(D4/B4,0%)",
            "対象期間", f'=TEXT(MIN(K{DATA_START_ROW}:K{last_data_row}),"yyyy/mm/dd")&" - "&TEXT(MAX(L{DATA_START_ROW}:L{last_data_row}),"yyyy/mm/dd")',
            "", "", "", ""
        ],
        [""] * len(ENHANCED_HEADERS),
        ["WBS階層"] + [""] * 5 + ["タスク管理"] + [""] * 3 + ["予定・進捗"] + [""] * 4 + ["メモ"],
        ENHANCED_HEADERS,
    ] + data_rows
    return sheet_values, data_rows, task_rows, last_data_row


def build_summary_sheet(phase_names, last_data_row):
    q_sheet = formula_quote(WBS_SHEET_NAME)
    values = [
        ["Mighty-Link AI Connect WBS 集計"] + [""] * 8,
        ["フェーズ別のタスク状態・完了率・期間を自動集計"] + [""] * 8,
        [""] * 9,
        ["大フェーズ", "総数", "完了", "実行中", "未着手", "完了率", "開始日", "終了日", "ステータス"],
    ]
    for idx, phase in enumerate(phase_names, start=5):
        phase_cell = f"A{idx}"
        values.append([
            phase,
            f'=COUNTIFS({q_sheet}!$D${DATA_START_ROW}:$D${last_data_row},{phase_cell},{q_sheet}!$B${DATA_START_ROW}:$B${last_data_row},2)',
            f'=COUNTIFS({q_sheet}!$D${DATA_START_ROW}:$D${last_data_row},{phase_cell},{q_sheet}!$B${DATA_START_ROW}:$B${last_data_row},2,{q_sheet}!$H${DATA_START_ROW}:$H${last_data_row},"完了")',
            f'=COUNTIFS({q_sheet}!$D${DATA_START_ROW}:$D${last_data_row},{phase_cell},{q_sheet}!$B${DATA_START_ROW}:$B${last_data_row},2,{q_sheet}!$H${DATA_START_ROW}:$H${last_data_row},"実行中")',
            f'=COUNTIFS({q_sheet}!$D${DATA_START_ROW}:$D${last_data_row},{phase_cell},{q_sheet}!$B${DATA_START_ROW}:$B${last_data_row},2,{q_sheet}!$H${DATA_START_ROW}:$H${last_data_row},"未着手")',
            f"=IFERROR(C{idx}/B{idx},0%)",
            f'=IFERROR(MINIFS({q_sheet}!$K${DATA_START_ROW}:$K${last_data_row},{q_sheet}!$D${DATA_START_ROW}:$D${last_data_row},{phase_cell},{q_sheet}!$B${DATA_START_ROW}:$B${last_data_row},2),"")',
            f'=IFERROR(MAXIFS({q_sheet}!$L${DATA_START_ROW}:$L${last_data_row},{q_sheet}!$D${DATA_START_ROW}:$D${last_data_row},{phase_cell},{q_sheet}!$B${DATA_START_ROW}:$B${last_data_row},2),"")',
            f'=IF(F{idx}=1,"完了",IF(F{idx}=0,"未着手","進行中"))',
        ])
    summary_start_row = 5
    summary_end_row = summary_start_row + len(phase_names) - 1
    values.append([""] * 9)
    total_row = summary_end_row + 2
    values.append([
        "合計",
        f"=SUM(B{summary_start_row}:B{summary_end_row})",
        f"=SUM(C{summary_start_row}:C{summary_end_row})",
        f"=SUM(D{summary_start_row}:D{summary_end_row})",
        f"=SUM(E{summary_start_row}:E{summary_end_row})",
        f"=IFERROR(C{total_row}/B{total_row},0%)",
        f'=IFERROR(MIN(G{summary_start_row}:G{summary_end_row}),"")',
        f'=IFERROR(MAX(H{summary_start_row}:H{summary_end_row}),"")',
        f'=IF(F{total_row}=1,"完了",IF(F{total_row}=0,"未着手","進行中"))',
    ])
    return values


def build_timeline_sheet(task_rows):
    """Builds a visual Gantt-style timeline grid for the WBS Timeline tab."""
    base_cols = 10
    header_rows = 5
    today = datetime.date.today()

    def parse_iso_date(value):
        try:
            return datetime.date.fromisoformat((value or "").strip())
        except ValueError:
            return None

    def day_range(start_date, end_date):
        current = start_date
        while current <= end_date:
            yield current
            current += datetime.timedelta(days=1)

    def delay_state(row, start_date, end_date):
        progress = str(row[13]).strip()
        if progress == "100%":
            return "on_track"
        if end_date and end_date < today:
            return "overdue_end"
        if progress == "0%" and start_date and start_date < today:
            return "overdue_start"
        if end_date and 0 <= (end_date - today).days <= 1:
            return "due_soon"
        return "on_track"

    def delay_label(state):
        labels = {
            "overdue_end": "終了遅れ",
            "overdue_start": "着手遅れ",
            "due_soon": "期限間近",
            "on_track": "正常",
        }
        return labels.get(state, "正常")

    def task_kind(row, state):
        progress = str(row[13]).strip()
        if progress == "100%":
            return "done"
        if state in ["overdue_end", "overdue_start"]:
            return "overdue"
        if state == "due_soon":
            return "due_soon"
        if progress == "50%":
            return "working"
        return "todo"

    entries = []
    valid_dates = []
    for row in task_rows:
        start_date = parse_iso_date(row[10])
        end_date = parse_iso_date(row[11])
        if start_date and end_date and end_date < start_date:
            start_date, end_date = end_date, start_date
        if start_date:
            valid_dates.append(start_date)
        if end_date:
            valid_dates.append(end_date)
        state = delay_state(row, start_date, end_date)
        entries.append({
            "row": row,
            "start": start_date,
            "end": end_date,
            "delay": state,
            "kind": task_kind(row, state),
        })

    if valid_dates:
        start_date = min(valid_dates) - datetime.timedelta(days=2)
        end_date = max(valid_dates) + datetime.timedelta(days=3)
    else:
        start_date = today - datetime.timedelta(days=7)
        end_date = today + datetime.timedelta(days=14)

    # Keep the sheet readable if future WBS data grows beyond the current 6/2 prep window.
    max_days = 120
    if (end_date - start_date).days + 1 > max_days:
        end_date = start_date + datetime.timedelta(days=max_days - 1)

    date_columns = list(day_range(start_date, end_date))
    date_index = {date_value: idx for idx, date_value in enumerate(date_columns)}
    total_cols = base_cols + len(date_columns)
    report_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    title = "Mighty-Link AI Connect WBS Timeline"
    description = f"Gantt-style schedule view generated from data/WBS.tsv / Last Sync: {report_time}"
    legend = "Legend: orange=late, yellow=due soon, gray=done, green=active, white=planned, blue line=today"
    month_row = [""] * total_cols
    metadata_headers = ["分類", "WBS#", "WP", "タスク", "状態", "担当", "開始", "終了", "進捗", "遅延"]
    day_header_row = metadata_headers + [str(date_value.day) for date_value in date_columns]

    month_spans = []
    current_month_key = None
    current_month_start = None
    for idx, date_value in enumerate(date_columns):
        month_key = (date_value.year, date_value.month)
        if month_key != current_month_key:
            if current_month_key is not None:
                month_spans.append((base_cols + current_month_start, base_cols + idx))
            current_month_key = month_key
            current_month_start = idx
            month_row[base_cols + idx] = f"'{date_value.year}年{date_value.month}月"
    if current_month_key is not None:
        month_spans.append((base_cols + current_month_start, base_cols + len(date_columns)))

    values = [
        [title] + [""] * (total_cols - 1),
        [description] + [""] * (total_cols - 1),
        [legend] + [""] * (total_cols - 1),
        month_row,
        day_header_row,
    ]

    bar_ranges = []
    delay_rows = []
    for entry in entries:
        row = entry["row"]
        start = entry["start"]
        end = entry["end"]
        delay = entry["delay"]
        sheet_row_idx = len(values)
        values_row = [
            row[3],
            row[0],
            row[2],
            row[5],
            row[7],
            row[8],
            row[10],
            row[11],
            row[13],
            delay_label(delay),
        ] + [""] * len(date_columns)
        if delay != "on_track":
            delay_rows.append({"row": sheet_row_idx, "delay": delay})

        if start and end:
            clipped_start = max(start, start_date)
            clipped_end = min(end, end_date)
            if clipped_start <= clipped_end and clipped_start in date_index and clipped_end in date_index:
                start_offset = date_index[clipped_start]
                end_offset = date_index[clipped_end]
                start_col = base_cols + start_offset
                end_col = base_cols + end_offset + 1
                label = f"{row[0]} {row[5]} ・ {row[7]}"
                values_row[start_col] = label[:64]
                bar_ranges.append({
                    "row": sheet_row_idx,
                    "start_col": start_col,
                    "end_col": end_col,
                    "kind": entry["kind"],
                    "delay": delay,
                })
        values.append(values_row)

    weekend_cols = [
        base_cols + idx
        for idx, date_value in enumerate(date_columns)
        if date_value.weekday() >= 5
    ]
    today_col = base_cols + date_index[today] if today in date_index else None

    meta = {
        "base_cols": base_cols,
        "header_rows": header_rows,
        "month_spans": month_spans,
        "weekend_cols": weekend_cols,
        "today_col": today_col,
        "bar_ranges": bar_ranges,
        "delay_rows": delay_rows,
    }
    return values, meta


def gantt_color(kind):
    if kind == "done":
        return {"red": 183/255, "green": 183/255, "blue": 183/255}
    if kind == "overdue":
        return {"red": 244/255, "green": 180/255, "blue": 0/255}
    if kind == "due_soon":
        return {"red": 251/255, "green": 188/255, "blue": 5/255}
    if kind == "working":
        return {"red": 217/255, "green": 234/255, "blue": 211/255}
    return {"red": 1.0, "green": 1.0, "blue": 1.0}


def delay_row_color(delay):
    if delay in ["overdue_end", "overdue_start"]:
        return COLORS["status_alert"]
    if delay == "due_soon":
        return COLORS["warning_bg"]
    return COLORS["white"]


def apply_gantt_timeline_styles(sh, worksheet, num_rows, num_cols, meta):
    print("[*] Applying Gantt-style WBS timeline styles...")
    sheet_id = worksheet.id
    base_cols = meta["base_cols"]
    header_rows = meta["header_rows"]
    requests = cleanup_sheet_requests(sh, worksheet, max(num_rows, 80), max(num_cols, 20))

    requests.extend([
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {
                        "frozenRowCount": header_rows,
                        "frozenColumnCount": base_cols,
                        "hideGridlines": False,
                    },
                },
                "fields": "gridProperties(frozenRowCount,frozenColumnCount,hideGridlines)",
            }
        },
        {"mergeCells": {"range": grid_range(sheet_id, 0, 1, 0, base_cols), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": grid_range(sheet_id, 1, 2, 0, base_cols), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": grid_range(sheet_id, 2, 3, 0, base_cols), "mergeType": "MERGE_ALL"}},
        repeat_format(sheet_id, 0, 1, 0, num_cols, {
            "backgroundColor": COLORS["title_bg"],
            "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True, "fontSize": 16},
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
        }),
        repeat_format(sheet_id, 1, 2, 0, num_cols, {
            "backgroundColor": COLORS["summary_bg"],
            "textFormat": {"fontSize": 9},
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
        }),
        repeat_format(sheet_id, 2, 3, 0, num_cols, {
            "backgroundColor": COLORS["white"],
            "textFormat": {"fontSize": 9, "bold": True},
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
        }),
        repeat_format(sheet_id, 3, 4, 0, num_cols, {
            "backgroundColor": COLORS["subheader_bg"],
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, 4, 5, 0, num_cols, {
            "backgroundColor": COLORS["header_bg"],
            "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True, "fontSize": 9},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, header_rows, num_rows, 0, base_cols, {
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, header_rows, num_rows, base_cols, num_cols, {
            "verticalAlignment": "MIDDLE",
            "horizontalAlignment": "CENTER",
            "wrapStrategy": "CLIP",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, header_rows, num_rows, 6, 8, {
            "numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"},
            "horizontalAlignment": "CENTER",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"),
        repeat_format(sheet_id, header_rows, num_rows, 8, 9, {
            "numberFormat": {"type": "PERCENT", "pattern": "0%"},
            "horizontalAlignment": "CENTER",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"),
        {
            "setBasicFilter": {
                "filter": {"range": grid_range(sheet_id, header_rows - 1, num_rows, 0, num_cols)}
            }
        },
    ])

    for start_col, end_col in meta["month_spans"]:
        if end_col - start_col > 1:
            requests.append({"mergeCells": {"range": grid_range(sheet_id, 3, 4, start_col, end_col), "mergeType": "MERGE_ALL"}})

    col_widths = [180, 72, 80, 260, 90, 120, 92, 92, 68, 92]
    for col_idx, width in enumerate(col_widths):
        requests.append(set_column_width_request(sheet_id, col_idx, width))
    for col_idx in range(base_cols, num_cols):
        requests.append(set_column_width_request(sheet_id, col_idx, 28))

    for row_idx, height in {0: 38, 1: 28, 2: 26, 3: 26, 4: 34}.items():
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": row_idx, "endIndex": row_idx + 1},
                "properties": {"pixelSize": height},
                "fields": "pixelSize",
            }
        })
    if num_rows > header_rows:
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": header_rows, "endIndex": num_rows},
                "properties": {"pixelSize": 30},
                "fields": "pixelSize",
            }
        })

    weekend_bg = {"red": 248/255, "green": 249/255, "blue": 250/255}
    for col_idx in meta["weekend_cols"]:
        requests.append(repeat_format(sheet_id, 3, num_rows, col_idx, col_idx + 1, {
            "backgroundColor": weekend_bg,
            "borders": border_format(),
        }, "userEnteredFormat(backgroundColor,borders)"))

    for delayed in meta["delay_rows"]:
        requests.append(repeat_format(sheet_id, delayed["row"], delayed["row"] + 1, 0, num_cols, {
            "backgroundColor": delay_row_color(delayed["delay"]),
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }, "userEnteredFormat(backgroundColor,verticalAlignment,wrapStrategy,borders)"))

    for bar in meta["bar_ranges"]:
        requests.append(repeat_format(sheet_id, bar["row"], bar["row"] + 1, bar["start_col"], bar["end_col"], {
            "backgroundColor": gantt_color(bar["kind"]),
            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": COLORS["black"]},
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "CLIP",
            "borders": border_format(),
        }, "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,borders)"))

    if meta["today_col"] is not None:
        today_border = {"style": "SOLID_THICK", "width": 2, "color": COLORS["header_bg"]}
        requests.extend([
            repeat_format(sheet_id, 3, 5, meta["today_col"], meta["today_col"] + 1, {
                "backgroundColor": {"red": 232/255, "green": 240/255, "blue": 254/255},
                "textFormat": {"bold": True},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
            }, "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"),
            {
                "updateBorders": {
                    "range": grid_range(sheet_id, 3, num_rows, meta["today_col"], meta["today_col"] + 1),
                    "left": today_border,
                    "right": today_border,
                }
            },
        ])

    requests.extend([
        add_text_conditional(sheet_id, header_rows, num_rows, 4, "完了", COLORS["status_done"]),
        add_text_conditional(sheet_id, header_rows, num_rows, 4, "実行中", COLORS["status_working"]),
        add_text_conditional(sheet_id, header_rows, num_rows, 4, "未着手", COLORS["status_todo"]),
        add_text_conditional(sheet_id, header_rows, num_rows, 9, "終了遅れ", COLORS["status_alert"]),
        add_text_conditional(sheet_id, header_rows, num_rows, 9, "着手遅れ", COLORS["status_alert"]),
        add_text_conditional(sheet_id, header_rows, num_rows, 9, "期限間近", COLORS["warning_bg"]),
    ])
    sh.batch_update({"requests": requests})


def build_timeline_sheet_legacy(task_rows):
    values = [
        ["Mighty-Link AI Connect WBS Timeline"] + [""] * 8,
        ["予定開始日・終了日・進捗率を横断確認するための軽量タイムライン"] + [""] * 8,
        [""] * 9,
        ["WBS#", "タスクID", "大フェーズ", "タスク名", "状態", "予定開始日", "予定終了日", "予定工数(日)", "進捗率"],
    ]
    for row in task_rows:
        timeline_row = len(values) + 1
        values.append([
            row[0],
            row[2],
            row[3],
            row[5],
            row[7],
            row[10],
            row[11],
            f'=IF(AND(F{timeline_row}<>"",G{timeline_row}<>""),G{timeline_row}-F{timeline_row}+1,"")',
            row[13],
        ])
    return values


def build_tracker_sheet(title, description, rows):
    if not rows:
        return []
    width = max(len(row) for row in rows)
    report_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    padded_rows = [row + [""] * (width - len(row)) for row in rows]
    return [
        [title] + [""] * (width - 1),
        [f"{description} / Last Sync: {report_time}"] + [""] * (width - 1),
        [""] * width,
        padded_rows[0],
    ] + padded_rows[1:]


def get_sheet_metadata(sh, sheet_id):
    metadata = sh.fetch_sheet_metadata(params={"includeGridData": False})
    for sheet in metadata.get("sheets", []):
        if sheet.get("properties", {}).get("sheetId") == sheet_id:
            return sheet
    return {}


def cleanup_sheet_requests(sh, worksheet, row_count, col_count):
    sheet_meta = get_sheet_metadata(sh, worksheet.id)
    requests = []
    if sheet_meta.get("basicFilter"):
        requests.append({"clearBasicFilter": {"sheetId": worksheet.id}})
    for _ in range(len(sheet_meta.get("conditionalFormats", []))):
        requests.append({"deleteConditionalFormatRule": {"sheetId": worksheet.id, "index": 0}})
    requests.append({
        "unmergeCells": {
            "range": {
                "sheetId": worksheet.id,
                "startRowIndex": 0,
                "endRowIndex": row_count,
                "startColumnIndex": 0,
                "endColumnIndex": col_count,
            }
        }
    })
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": worksheet.id,
                "startRowIndex": 0,
                "endRowIndex": row_count,
                "startColumnIndex": 0,
                "endColumnIndex": col_count,
            },
            "cell": {"userEnteredFormat": {}},
            "fields": "userEnteredFormat",
        }
    })
    return requests


def grid_range(sheet_id, start_row, end_row, start_col, end_col):
    return {
        "sheetId": sheet_id,
        "startRowIndex": start_row,
        "endRowIndex": end_row,
        "startColumnIndex": start_col,
        "endColumnIndex": end_col,
    }


def repeat_format(sheet_id, start_row, end_row, start_col, end_col, fmt, fields=None):
    return {
        "repeatCell": {
            "range": grid_range(sheet_id, start_row, end_row, start_col, end_col),
            "cell": {"userEnteredFormat": fmt},
            "fields": fields or "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,numberFormat,borders)",
        }
    }


def border_format():
    border = {"style": "SOLID", "width": 1, "color": COLORS["border_gray"]}
    return {"top": border, "bottom": border, "left": border, "right": border}


def set_column_width_request(sheet_id, col_idx, width):
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": col_idx,
                "endIndex": col_idx + 1,
            },
            "properties": {"pixelSize": width},
            "fields": "pixelSize",
        }
    }


def add_text_conditional(sheet_id, start_row, end_row, col_idx, text, bg_color, font_color=None):
    fmt = {"backgroundColor": bg_color, "textFormat": {"bold": True}}
    if font_color:
        fmt["textFormat"]["foregroundColor"] = font_color
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [grid_range(sheet_id, start_row, end_row, col_idx, col_idx + 1)],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_EQ",
                        "values": [{"userEnteredValue": text}],
                    },
                    "format": fmt,
                },
            },
            "index": 0,
        }
    }


def apply_wbs_styles(sh, worksheet, num_rows, num_cols, last_data_row):
    print("[*] Applying CATS-like hierarchical WBS styles...")
    requests = cleanup_sheet_requests(sh, worksheet, max(num_rows, 80), max(num_cols, 16))

    sheet_id = worksheet.id
    requests.extend([
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {
                        "frozenRowCount": 7,
                        "hideGridlines": True,
                    },
                },
                "fields": "gridProperties(frozenRowCount,hideGridlines)",
            }
        },
        {"mergeCells": {"range": grid_range(sheet_id, 0, 1, 0, num_cols), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": grid_range(sheet_id, 1, 2, 0, num_cols), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": grid_range(sheet_id, 5, 6, 0, 6), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": grid_range(sheet_id, 5, 6, 6, 10), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": grid_range(sheet_id, 5, 6, 10, 15), "mergeType": "MERGE_ALL"}},
        repeat_format(sheet_id, 0, 1, 0, num_cols, {
            "backgroundColor": COLORS["title_bg"],
            "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True, "fontSize": 16},
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
        }),
        repeat_format(sheet_id, 1, 2, 0, num_cols, {
            "backgroundColor": COLORS["summary_bg"],
            "textFormat": {"foregroundColor": COLORS["black"], "fontSize": 9},
            "horizontalAlignment": "LEFT",
            "verticalAlignment": "MIDDLE",
        }),
        repeat_format(sheet_id, 3, 4, 0, num_cols, {
            "backgroundColor": COLORS["warning_bg"],
            "textFormat": {"bold": True, "fontSize": 10},
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, 5, 6, 0, num_cols, {
            "backgroundColor": COLORS["group_bg"],
            "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, 6, 7, 0, num_cols, {
            "backgroundColor": COLORS["subheader_bg"],
            "textFormat": {"bold": True, "fontSize": 10},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, DATA_START_ROW - 1, last_data_row, 0, num_cols, {
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, DATA_START_ROW - 1, last_data_row, 0, 3, {
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
        }, "userEnteredFormat(horizontalAlignment,verticalAlignment)"),
        repeat_format(sheet_id, DATA_START_ROW - 1, last_data_row, 7, 15, {
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
        }, "userEnteredFormat(horizontalAlignment,verticalAlignment)"),
        repeat_format(sheet_id, DATA_START_ROW - 1, last_data_row, 10, 12, {
            "numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"},
            "horizontalAlignment": "CENTER",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"),
        repeat_format(sheet_id, DATA_START_ROW - 1, last_data_row, 12, 13, {
            "numberFormat": {"type": "NUMBER", "pattern": "0"},
            "horizontalAlignment": "RIGHT",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"),
        repeat_format(sheet_id, DATA_START_ROW - 1, last_data_row, 13, 14, {
            "numberFormat": {"type": "PERCENT", "pattern": "0%"},
            "horizontalAlignment": "CENTER",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"),
        repeat_format(sheet_id, 3, 4, 9, 10, {
            "numberFormat": {"type": "PERCENT", "pattern": "0%"},
            "horizontalAlignment": "CENTER",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"),
        {
            "setBasicFilter": {
                "filter": {
                    "range": grid_range(sheet_id, 6, last_data_row, 0, num_cols),
                }
            }
        },
        {
            "setDataValidation": {
                "range": grid_range(sheet_id, DATA_START_ROW - 1, last_data_row, 7, 8),
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [
                            {"userEnteredValue": "完了"},
                            {"userEnteredValue": "実行中"},
                            {"userEnteredValue": "未着手"},
                        ],
                    },
                    "showCustomUi": True,
                    "strict": False,
                },
            }
        },
    ])

    col_widths = [78, 42, 86, 150, 125, 280, 360, 90, 110, 140, 105, 105, 85, 78, 110, 180]
    for col_idx, width in enumerate(col_widths):
        requests.append(set_column_width_request(sheet_id, col_idx, width))

    row_heights = {0: 38, 1: 28, 3: 34, 5: 30, 6: 38}
    for row_idx, height in row_heights.items():
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": row_idx, "endIndex": row_idx + 1},
                "properties": {"pixelSize": height},
                "fields": "pixelSize",
            }
        })
    requests.append({
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": DATA_START_ROW - 1, "endIndex": last_data_row},
            "properties": {"pixelSize": 32},
            "fields": "pixelSize",
        }
    })

    # Phase rows and status/alert colors.
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [grid_range(sheet_id, DATA_START_ROW - 1, last_data_row, 0, num_cols)],
                "booleanRule": {
                    "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": f"=$B{DATA_START_ROW}=1"}]},
                    "format": {"backgroundColor": COLORS["phase_bg"], "textFormat": {"bold": True}},
                },
            },
            "index": 0,
        }
    })
    requests.extend([
        add_text_conditional(sheet_id, DATA_START_ROW - 1, last_data_row, 7, "完了", COLORS["status_done"]),
        add_text_conditional(sheet_id, DATA_START_ROW - 1, last_data_row, 7, "実行中", COLORS["status_working"]),
        add_text_conditional(sheet_id, DATA_START_ROW - 1, last_data_row, 7, "未着手", COLORS["status_todo"]),
        add_text_conditional(sheet_id, DATA_START_ROW - 1, last_data_row, 14, "完了", COLORS["status_done"]),
        add_text_conditional(sheet_id, DATA_START_ROW - 1, last_data_row, 14, "着手済", COLORS["status_working"]),
        add_text_conditional(sheet_id, DATA_START_ROW - 1, last_data_row, 14, "着手遅れ", COLORS["status_alert"]),
        add_text_conditional(sheet_id, DATA_START_ROW - 1, last_data_row, 14, "終了遅れ", COLORS["status_alert"]),
    ])

    sh.batch_update({"requests": requests})


def apply_simple_table_styles(sh, worksheet, num_rows, num_cols, freeze_rows=4, percent_cols=None, date_cols=None, col_widths=None):
    percent_cols = percent_cols if percent_cols is not None else [5]
    date_cols = date_cols if date_cols is not None else [(6, 8)]
    sheet_id = worksheet.id
    requests = cleanup_sheet_requests(sh, worksheet, max(num_rows, 60), max(num_cols, 12))
    requests.extend([
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": freeze_rows, "hideGridlines": True},
                },
                "fields": "gridProperties(frozenRowCount,hideGridlines)",
            }
        },
        {"mergeCells": {"range": grid_range(sheet_id, 0, 1, 0, num_cols), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": grid_range(sheet_id, 1, 2, 0, num_cols), "mergeType": "MERGE_ALL"}},
        repeat_format(sheet_id, 0, 1, 0, num_cols, {
            "backgroundColor": COLORS["title_bg"],
            "textFormat": {"foregroundColor": COLORS["header_text"], "bold": True, "fontSize": 14},
            "verticalAlignment": "MIDDLE",
        }),
        repeat_format(sheet_id, 1, 2, 0, num_cols, {
            "backgroundColor": COLORS["summary_bg"],
            "textFormat": {"fontSize": 9},
            "verticalAlignment": "MIDDLE",
        }),
        repeat_format(sheet_id, freeze_rows - 1, freeze_rows, 0, num_cols, {
            "backgroundColor": COLORS["subheader_bg"],
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }),
        repeat_format(sheet_id, freeze_rows, num_rows, 0, num_cols, {
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP",
            "borders": border_format(),
        }),
        {
            "setBasicFilter": {
                "filter": {"range": grid_range(sheet_id, freeze_rows - 1, num_rows, 0, num_cols)}
            }
        },
    ])
    widths = col_widths or [220, 72, 72, 72, 72, 82, 110, 110, 90, 140, 140, 140]
    for col_idx, width in enumerate(widths):
        if col_idx < num_cols:
            requests.append(set_column_width_request(sheet_id, col_idx, width))
    for col_idx in percent_cols:
        if col_idx >= num_cols:
            continue
        requests.append(repeat_format(sheet_id, freeze_rows, num_rows, col_idx, col_idx + 1, {
            "numberFormat": {"type": "PERCENT", "pattern": "0%"},
            "horizontalAlignment": "CENTER",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"))
    for start_col, end_col in date_cols:
        if start_col >= num_cols:
            continue
        requests.append(repeat_format(sheet_id, freeze_rows, num_rows, start_col, min(end_col, num_cols), {
            "numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"},
            "horizontalAlignment": "CENTER",
        }, "userEnteredFormat(numberFormat,horizontalAlignment)"))
    sh.batch_update({"requests": requests})


def apply_tracker_styles(sh, worksheet, num_rows, num_cols, tracker_type):
    if tracker_type == "issues":
        col_widths = [90, 110, 80, 110, 260, 300, 360, 120, 105, 105, 145, 260, 110, 320, 105]
        date_cols = [(8, 10), (14, 15)]
    elif tracker_type == "qa":
        col_widths = [95, 130, 300, 380, 320, 120, 260, 150, 100, 105]
        date_cols = [(9, 10)]
    elif tracker_type == "test":
        col_widths = [90, 110, 160, 300, 85, 120, 80, 80, 145]
        date_cols = []
    elif tracker_type == "security":
        col_widths = [90, 100, 180, 300, 350, 90, 145, 145]
        date_cols = []
    elif tracker_type == "deploy":
        col_widths = [90, 120, 350, 120, 140, 145]
        date_cols = []
    else:
        col_widths = [120] * num_cols
        date_cols = []

    apply_simple_table_styles(
        sh,
        worksheet,
        num_rows,
        num_cols,
        freeze_rows=4,
        percent_cols=[],
        date_cols=date_cols,
        col_widths=col_widths,
    )

    data_start = 4
    requests = []
    sheet_id = worksheet.id
    if tracker_type == "issues":
        requests.extend([
            add_text_conditional(sheet_id, data_start, num_rows, 2, "HIGH", COLORS["status_alert"]),
            add_text_conditional(sheet_id, data_start, num_rows, 2, "MED", COLORS["status_working"]),
            add_text_conditional(sheet_id, data_start, num_rows, 2, "LOW", COLORS["status_done"]),
            add_text_conditional(sheet_id, data_start, num_rows, 3, "open", COLORS["white"]),
            add_text_conditional(sheet_id, data_start, num_rows, 3, "in_progress", COLORS["status_working"]),
            add_text_conditional(sheet_id, data_start, num_rows, 3, "resolved", COLORS["status_done"]),
            add_text_conditional(sheet_id, data_start, num_rows, 3, "wont_fix", COLORS["status_todo"]),
            add_text_conditional(sheet_id, data_start, num_rows, 3, "deferred", COLORS["phase_bg"]),
        ])
    elif tracker_type == "qa":
        requests.extend([
            add_text_conditional(sheet_id, data_start, num_rows, 8, "保留中", COLORS["status_working"]),
            add_text_conditional(sheet_id, data_start, num_rows, 8, "回答済", COLORS["status_done"]),
            add_text_conditional(sheet_id, data_start, num_rows, 8, "想定済", COLORS["white"]),
            add_text_conditional(sheet_id, data_start, num_rows, 8, "解決不要", COLORS["status_todo"]),
        ])
    elif tracker_type == "test":
        requests.extend([
            add_text_conditional(sheet_id, data_start, num_rows, 4, "PASS", COLORS["status_done"]),
            add_text_conditional(sheet_id, data_start, num_rows, 4, "FAIL", COLORS["status_alert"]),
        ])
    elif tracker_type == "security":
        requests.extend([
            add_text_conditional(sheet_id, data_start, num_rows, 1, "HIGH", COLORS["status_alert"]),
            add_text_conditional(sheet_id, data_start, num_rows, 1, "MED", COLORS["status_working"]),
            add_text_conditional(sheet_id, data_start, num_rows, 1, "LOW", COLORS["status_todo"]),
            add_text_conditional(sheet_id, data_start, num_rows, 5, "FIXED", COLORS["status_done"]),
        ])
    elif tracker_type == "deploy":
        requests.extend([
            add_text_conditional(sheet_id, data_start, num_rows, 3, "SUCCESS", COLORS["status_done"]),
            add_text_conditional(sheet_id, data_start, num_rows, 3, "FAILED", COLORS["status_alert"]),
        ])
    if requests:
        sh.batch_update({"requests": requests})

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
            print("\n[*] Bypass & Setup Instructions (OAuth 2.0 Mode - Recommended)")
            print("To bypass Drive storage quota limitations, use the Workspace Google Drive account:")
            print("1. Go to Google Cloud Console (https://console.cloud.google.com/) -> API & Services -> Credentials.")
            print("2. Click '+ Create Credentials' -> 'OAuth client ID'.")
            print("3. (If prompted) Click 'Configure Consent Screen', select 'External', input App Name ('Mighty WBS'), and save.")
            print(f"   * Under 'Test users', add '{USER_EMAIL}'.")
            print("4. Go back to Credentials -> Create Credentials -> OAuth client ID.")
            print("5. Choose Application Type: 'Desktop App', name it, and click Create.")
            print("6. Download the JSON file and rename it to 'client_secret.json' in the project root folder.")
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
                print("\n[!] Storage Quota Alert")
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

    # 3. Load data and setup Worksheets
    print(f"[*] Parsing local {os.path.relpath(TSV_FILE, PROJECT_ROOT)}...")
    wbs_data = load_wbs_data(TSV_FILE)
    if not wbs_data:
        print("[-] No WBS data found in TSV file. Exiting.")
        sys.exit(1)

    enhanced_values, enhanced_rows, task_rows, last_data_row = build_enhanced_wbs(wbs_data)
    phase_names = [row[3] for row in enhanced_rows if row[1] == 1]
    summary_values = build_summary_sheet(phase_names, last_data_row)
    timeline_values, timeline_meta = build_timeline_sheet(task_rows)
    issue_source_rows = load_tracker_data(ISSUES_TSV_FILE)
    qa_source_rows = load_tracker_data(QA_TSV_FILE)
    test_source_rows = load_tracker_data(TEST_TSV_FILE)
    security_source_rows = load_tracker_data(SECURITY_TSV_FILE)
    deploy_source_rows = load_tracker_data(DEPLOY_TSV_FILE)
    issue_values = build_tracker_sheet(
        "Mighty-Link 課題管理表",
        "6/2社長プレゼン準備と開発運用で発生した課題・ブロッカーを管理",
        issue_source_rows,
    )
    qa_values = build_tracker_sheet(
        "Mighty-Link QA表",
        "社長・顧客からの想定質問、保留時対応、回答状況を管理",
        qa_source_rows,
    )
    test_values = build_tracker_sheet(
        "Mighty-Link テスト実行結果",
        "Browser Agentによる自律UI/UXテストおよび機能検証ログ",
        test_source_rows,
    )
    security_values = build_tracker_sheet(
        "Mighty-Link セキュリティ・監査ログ",
        "Code Menderによる自律脆弱性自動修正およびコード監査ログ",
        security_source_rows,
    )
    deploy_values = build_tracker_sheet(
        "Mighty-Link デプロイ実行結果",
        "GitHub Pagesおよびローカル環境へのデプロイ実行ログ",
        deploy_source_rows,
    )

    wbs_rows = max(len(enhanced_values) + 20, 120)
    wbs_cols = len(ENHANCED_HEADERS)
    worksheet = ensure_worksheet(sh, WBS_SHEET_NAME, rows=wbs_rows, cols=wbs_cols)
    summary_sheet = ensure_worksheet(sh, SUMMARY_SHEET_NAME, rows=max(len(summary_values) + 20, 60), cols=9)
    timeline_cols = len(timeline_values[0]) if timeline_values else 9
    timeline_sheet = ensure_worksheet(sh, TIMELINE_SHEET_NAME, rows=max(len(timeline_values) + 20, 80), cols=timeline_cols)
    issue_sheet = None
    qa_sheet = None
    test_sheet = None
    security_sheet = None
    if issue_values:
        issue_sheet = ensure_worksheet(
            sh,
            ISSUES_SHEET_NAME,
            rows=max(len(issue_values) + 20, 80),
            cols=len(issue_values[0]),
        )
    if qa_values:
        qa_sheet = ensure_worksheet(
            sh,
            QA_SHEET_NAME,
            rows=max(len(qa_values) + 20, 90),
            cols=len(qa_values[0]),
        )
    if test_values:
        test_sheet = ensure_worksheet(
            sh,
            TEST_SHEET_NAME,
            rows=max(len(test_values) + 20, 80),
            cols=len(test_values[0]),
        )
    if security_values:
        security_sheet = ensure_worksheet(
            sh,
            SECURITY_SHEET_NAME,
            rows=max(len(security_values) + 20, 80),
            cols=len(security_values[0]),
        )
    deploy_sheet = None
    if deploy_values:
        deploy_sheet = ensure_worksheet(
            sh,
            DEPLOY_SHEET_NAME,
            rows=max(len(deploy_values) + 20, 80),
            cols=len(deploy_values[0]),
        )

    # Remove default Sheet1 if present to keep the workbook clean.
    try:
        default_sheet = sh.worksheet("Sheet1")
        protected_sheet_ids = [worksheet.id, summary_sheet.id, timeline_sheet.id]
        if issue_sheet:
            protected_sheet_ids.append(issue_sheet.id)
        if qa_sheet:
            protected_sheet_ids.append(qa_sheet.id)
        if test_sheet:
            protected_sheet_ids.append(test_sheet.id)
        if security_sheet:
            protected_sheet_ids.append(security_sheet.id)
        if deploy_sheet:
            protected_sheet_ids.append(deploy_sheet.id)
        if default_sheet.id not in protected_sheet_ids:
            sh.del_worksheet(default_sheet)
    except Exception:
        pass

    # 4. Upload Data
    print("[*] Uploading enhanced CATS-like WBS views...")
    worksheet.update(values=enhanced_values, range_name="A1", value_input_option="USER_ENTERED")
    summary_sheet.update(values=summary_values, range_name="A1", value_input_option="USER_ENTERED")
    timeline_sheet.update(values=timeline_values, range_name="A1", value_input_option="USER_ENTERED")
    if issue_sheet:
        issue_sheet.update(values=issue_values, range_name="A1", value_input_option="USER_ENTERED")
    if qa_sheet:
        qa_sheet.update(values=qa_values, range_name="A1", value_input_option="USER_ENTERED")
    if test_sheet:
        test_sheet.update(values=test_values, range_name="A1", value_input_option="USER_ENTERED")
    if security_sheet:
        security_sheet.update(values=security_values, range_name="A1", value_input_option="USER_ENTERED")
    if deploy_sheet:
        deploy_sheet.update(values=deploy_values, range_name="A1", value_input_option="USER_ENTERED")
    print(f"[+] Successfully wrote {len(wbs_data)} source rows into {len(enhanced_values)} hierarchical WBS display rows.")
    if issue_values:
        print(f"[+] Successfully wrote {max(len(issue_values) - 4, 0)} issue tracker rows into '{ISSUES_SHEET_NAME}'.")
    if qa_values:
        print(f"[+] Successfully wrote {max(len(qa_values) - 4, 0)} QA tracker rows into '{QA_SHEET_NAME}'.")
    if test_values:
        print(f"[+] Successfully wrote {max(len(test_values) - 4, 0)} test tracker rows into '{TEST_SHEET_NAME}'.")
    if security_values:
        print(f"[+] Successfully wrote {max(len(security_values) - 4, 0)} security tracker rows into '{SECURITY_SHEET_NAME}'.")
    if deploy_values:
        print(f"[+] Successfully wrote {max(len(deploy_values) - 4, 0)} deploy tracker rows into '{DEPLOY_SHEET_NAME}'.")

    # 5. Apply Professional Styles (CATS-inspired WBS Design)
    try:
        apply_wbs_styles(sh, worksheet, len(enhanced_values), len(ENHANCED_HEADERS), last_data_row)
        apply_simple_table_styles(sh, summary_sheet, len(summary_values), 9, freeze_rows=4, percent_cols=[5], date_cols=[(6, 8)])
        apply_gantt_timeline_styles(sh, timeline_sheet, len(timeline_values), timeline_cols, timeline_meta)
        if issue_sheet:
            apply_tracker_styles(sh, issue_sheet, len(issue_values), len(issue_values[0]), "issues")
        if qa_sheet:
            apply_tracker_styles(sh, qa_sheet, len(qa_values), len(qa_values[0]), "qa")
        if test_sheet:
            apply_tracker_styles(sh, test_sheet, len(test_values), len(test_values[0]), "test")
        if security_sheet:
            apply_tracker_styles(sh, security_sheet, len(security_values), len(security_values[0]), "security")
        if deploy_sheet:
            apply_tracker_styles(sh, deploy_sheet, len(deploy_values), len(deploy_values[0]), "deploy")
        print("[+] CATS-like hierarchy, summary, timeline, tracker tabs, filters, freeze panes, and status colors applied.")
    except Exception as e:
        print(f"[!] Warning while setting styles/dimensions: {e}")

    print("="*60)
    print("[+] Sync Completed Successfully!")
    print(f"[*] Spreadsheet URL: {sh.url}")
    print("="*60)

if __name__ == "__main__":
    main()
