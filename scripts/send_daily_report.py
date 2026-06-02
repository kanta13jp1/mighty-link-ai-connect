#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate and sync the Daily Work Report to Google Drive and local reports.

This script parses data/WBS.tsv, calculates completion statistics, gathers
recent and upcoming tasks, and compiles a comprehensive daily work report.
The report is saved locally under reports/ and automatically uploaded as a
native Google Doc in Google Drive under k-umezawa@ml-mightylink.com.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
WBS_FILE = DATA_DIR / "WBS.tsv"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from upload_notebooklm_docs_to_drive import (
    EXPECTED_GOOGLE_ACCOUNT,
    get_file,
    load_credentials,
    upload_as_google_doc,
    verify_workspace_owner,
)


def jst_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))


def read_wbs_rows() -> list[dict[str, str]]:
    if not WBS_FILE.exists():
        raise FileNotFoundError(f"Missing WBS file: {WBS_FILE}")
    with WBS_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def get_wbs_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    total = len(rows)
    done = sum(1 for r in rows if r.get("ステータス") == "完了")
    active = sum(1 for r in rows if r.get("ステータス") == "実行中")
    todo = sum(1 for r in rows if r.get("ステータス") == "未着手")
    
    # Calculate phase statistics
    phases: dict[str, dict[str, int]] = {}
    for r in rows:
        ph = r.get("大フェーズ", "その他")
        status = r.get("ステータス", "未着手")
        if ph not in phases:
            phases[ph] = {"total": 0, "done": 0, "active": 0, "todo": 0}
        phases[ph]["total"] += 1
        if status == "完了":
            phases[ph]["done"] += 1
        elif status == "実行中":
            phases[ph]["active"] += 1
        else:
            phases[ph]["todo"] += 1

    return {
        "total": total,
        "done": done,
        "active": active,
        "todo": todo,
        "rate": round((done / total) * 100) if total else 0,
        "phases": phases,
    }


def compile_report(rows: list[dict[str, str]], summary: dict[str, Any], date_str: str) -> str:
    # Gather completed and upcoming tasks
    completed_tasks = []
    active_tasks = []
    upcoming_tasks = []

    for r in rows:
        status = r.get("ステータス")
        if status == "完了":
            completed_tasks.append(r)
        elif status == "実行中":
            active_tasks.append(r)
        elif status == "未着手":
            upcoming_tasks.append(r)

    # Sort upcoming by start date
    upcoming_tasks = sorted([t for t in upcoming_tasks if t.get("開始日")], key=lambda x: x["開始日"])[:7]

    phase_rows_str = ""
    for name, stats in sorted(summary["phases"].items()):
        rate = round((stats["done"] / stats["total"]) * 100) if stats["total"] else 0
        phase_rows_str += f"| {name} | {stats['total']} | {stats['done']} | {stats['active']} | {stats['todo']} | {rate}% |\n"

    upcoming_rows_str = ""
    for t in upcoming_tasks:
        upcoming_rows_str += f"- **{t.get('タスクID')}** ({t.get('小フェーズ')}): {t.get('タスク名')} (担当: {t.get('担当')}, 予定: {t.get('開始日')} 〜 {t.get('終了予定日')})\n"

    active_rows_str = ""
    for t in active_tasks:
        active_rows_str += f"- **{t.get('タスクID')}** ({t.get('小フェーズ')}): {t.get('タスク名')} (担当: {t.get('担当')})\n"
    if not active_rows_str:
        active_rows_str = "- 現在実行中のタスクはありません（順次次タスクへ着手します）。\n"

    completed_recent = completed_tasks[-5:]
    completed_rows_str = ""
    for t in reversed(completed_recent):
        completed_rows_str += f"- **{t.get('タスクID')}**: {t.get('タスク名')} (担当: {t.get('担当')}, 成果: {t.get('Sheets Live 連携アクション')})\n"

    report_content = f"""# Mighty Skill-Bridge デイリー作業レポート ({date_str})

作成日時: {jst_now().strftime('%Y-%m-%d %H:%M:%S %Z')}
対象アカウント: `{EXPECTED_GOOGLE_ACCOUNT}`

---

## 📊 WBS 進捗サマリ

- **全体タスク数**: {summary['total']} 件
- **完了済み**: {summary['done']} 件
- **進行中 (実行中)**: {summary['active']} 件
- **未着手**: {summary['todo']} 件
- **総合進捗率**: **{summary['rate']}%**

### 📂 フェーズ別詳細

| フェーズ名 | 総タスク数 | 完了 | 実行中 | 未着手 | 進捗率 |
| :--- | :---: | :---: | :---: | :---: | :---: |
{phase_rows_str}

---

## 🛠️ 直近の作業実績（直近完了5件）

{completed_rows_str}

---

## 🏃 現在進行中のタスク

{active_rows_str}

---

## 📅 次回着手予定のタスク（直近7件）

{upcoming_rows_str}

---

## 💡 AIエージェントからの本日のコメント・次の一手
- 本日、デイリーレポートの自動生成およびGoogle Drive連携機能（`T737`）が実装・デプロイされました。
- 次回は、WBSの日程計画に従い、ホスティング先およびDBインフラの最終選定調査（`T730`）に着手します。
- 1日1時間の持続可能な人間レビュー体制にレバレッジをかけ、6/16の本番リリースに向けて安全かつ高速に開発を推進してまいります。
"""
    return report_content


def main() -> None:
    print("[*] Mighty-Link AI Connect: Generating Daily Work Report...")
    rows = read_wbs_rows()
    summary = get_wbs_summary(rows)
    
    date_str = jst_now().strftime("%Y-%m-%d")
    report_md = compile_report(rows, summary, date_str)
    
    # Save locally
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    local_path = REPORTS_DIR / f"daily_report_{date_str}.md"
    local_path.write_text(report_md, encoding="utf-8")
    print(f"[+] Saved local report to: {local_path}")
    
    # Upload to Google Drive
    print("[*] Uploading report to Google Drive...")
    try:
        credentials = load_credentials()
        title = f"Mighty Skill-Bridge Daily Report {date_str}"
        
        # Check if we uploaded a report for this day previously to overwrite/update it
        manifest_file = REPORTS_DIR / "reports_manifest.json"
        manifest = {}
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            
        previous_id = manifest.get(date_str, {}).get("id")
        existing = get_file(credentials, previous_id) if previous_id else None
        existing_id = existing["id"] if existing else None
        
        result = upload_as_google_doc(
            credentials,
            title=title,
            content=report_md,
            existing_file_id=existing_id,
        )
        verify_workspace_owner(result)
        
        url = result.get("webViewLink") or f"https://docs.google.com/document/d/{result['id']}/edit"
        manifest[date_str] = {
            "id": result["id"],
            "name": result["name"],
            "url": url,
            "updated_at": jst_now().isoformat()
        }
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        
        print(f"[+] Daily Report successfully uploaded to Google Drive!")
        print(f"[*] Google Doc URL: {url}")
        
    except Exception as exc:
        print(f"[-] Google Drive upload failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
