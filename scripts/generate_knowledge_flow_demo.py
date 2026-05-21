#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate CEO-facing demo artifacts for the development knowledge flow.

This does not call external APIs or send messages. It produces concrete files
that can be shown, imported, or pasted into NotebookLM, Slack, Notion, and
Obsidian without exposing credentials.
"""

import csv
import datetime as dt
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
EXPORT_DIR = PROJECT_ROOT / "exports" / "knowledge_flow"
OBSIDIAN_DIR = EXPORT_DIR / "obsidian_vault"

WBS_FILE = DATA_DIR / "WBS.tsv"

SOURCE_DOCS = [
    "README.md",
    "docs/CEO_PRESENTATION_PREP_2026-06-02.md",
    "docs/CEO_PRESENTATION_DECISION_PACK_2026-06-02.md",
    "docs/DEVELOPMENT_KNOWLEDGE_FLOW.md",
    "docs/BACKEND_AI_PIPELINE.md",
    "docs/WBS.md",
    "docs/SETUP_GUIDE.md",
]


def jst_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))


def read_wbs_rows() -> list[dict]:
    with WBS_FILE.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def wbs_summary(rows: list[dict]) -> dict:
    total = len(rows)
    done = sum(1 for row in rows if row.get("ステータス") == "完了")
    active = sum(1 for row in rows if row.get("ステータス") == "実行中")
    todo = sum(1 for row in rows if row.get("ステータス") == "未着手")
    phase6 = [row for row in rows if row.get("大フェーズ") == "6. 社長プレゼン準備"]
    return {
        "total": total,
        "done": done,
        "active": active,
        "todo": todo,
        "completion_rate": round((done / total) * 100) if total else 0,
        "phase6_total": len(phase6),
        "phase6_done": sum(1 for row in phase6 if row.get("ステータス") == "完了"),
        "phase6_active": sum(1 for row in phase6 if row.get("ステータス") == "実行中"),
        "phase6_todo": sum(1 for row in phase6 if row.get("ステータス") == "未着手"),
    }


def knowledge_tasks(rows: list[dict]) -> list[dict]:
    return [
        row for row in rows
        if row.get("タスクID", "").startswith("T6")
        and (
            "NotebookLM" in row.get("タスク名", "")
            or "Slack" in row.get("タスク名", "")
            or "Notion" in row.get("タスク名", "")
            or "Obsidian" in row.get("タスク名", "")
            or "連携" in row.get("小フェーズ", "")
            or "開発フロー" in row.get("小フェーズ", "")
            or "権限" in row.get("小フェーズ", "")
        )
    ]


def read_source_excerpt(path: str, limit: int = 5000) -> str:
    target = PROJECT_ROOT / path
    if not target.exists():
        return ""
    text = target.read_text(encoding="utf-8", errors="replace")
    return text[:limit].rstrip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def build_notebooklm_pack(rows: list[dict], summary: dict) -> str:
    tasks = knowledge_tasks(rows)
    task_lines = "\n".join(
        f"- {row['タスクID']}: {row['小フェーズ']} / {row['タスク名']} / {row['ステータス']} / {row['開始日']} - {row['終了予定日']}"
        for row in tasks
    )
    sources = "\n".join(
        f"## Source: {path}\n\n{read_source_excerpt(path)}\n"
        for path in SOURCE_DOCS
        if read_source_excerpt(path)
    )
    return f"""# Mighty Skill-Bridge NotebookLM Source Pack

Generated: {jst_now().strftime('%Y-%m-%d %H:%M:%S %Z')}

## Purpose

This source pack is designed for NotebookLM before the 2026-06-02 CEO meeting.
Use it to generate concise explanations, likely CEO questions, and decision
points about the prototype, WBS, Google Workspace sync, and knowledge-flow tools.

## Current WBS Snapshot

- Total tasks: {summary['total']}
- Done: {summary['done']}
- In progress: {summary['active']}
- Not started: {summary['todo']}
- Completion rate: {summary['completion_rate']}%
- CEO presentation phase tasks: {summary['phase6_total']}
- CEO presentation phase done: {summary['phase6_done']}

## Knowledge Flow Tasks

{task_lines}

## Recommended NotebookLM Questions

1. 6/2の社長打ち合わせで、最初に説明すべき到達点を3分で要約してください。
2. NotebookLM / Slack / Notion / Obsidian の導入優先順位を比較してください。
3. 社長が確認すべきリスク、権限、情報管理ルールを一覧化してください。
4. 6/2後にWBSへ反映すべき次アクション候補を出してください。
5. このプロトタイプをサービス化する場合に、決めるべき事項と決めなくてよい事項を分けてください。

{sources}
"""


def build_slack_update(summary: dict) -> str:
    return f"""# Slack投稿案: 6/2 社長プレゼン準備進捗

投稿先候補: #mighty-skill-bridge / #dev-progress / 社長レビュー用チャンネル

```text
【Mighty Skill-Bridge 進捗共有】
6/2社長打ち合わせに向け、NotebookLM / Slack / Notion / Obsidian を使った開発ナレッジ連携デモを準備しました。

■ WBS状況
- 全体: {summary['total']}タスク / 完了{summary['done']} / 実行中{summary['active']} / 未着手{summary['todo']} / 完了率{summary['completion_rate']}%
- 社長プレゼン準備: {summary['phase6_total']}タスク / 完了{summary['phase6_done']} / 実行中{summary['phase6_active']} / 未着手{summary['phase6_todo']}

■ 見せられる状態
- NotebookLM投入用資料パックを生成済み
- Slack投稿文案を生成済み
- Notionインポート用CSVを生成済み
- Obsidian vault雛形を生成済み

■ 6/2で確認したいこと
- 4ツールのうち、どれを正式運用へ進めるか
- Slack/Notionに社長確認事項を流す範囲
- 個人情報・認証情報を外部ツールに入れないルール
```
"""


def write_notion_csvs(rows: list[dict]) -> None:
    decisions = [
        {
            "Name": "NotebookLMを社長説明前の資料要約に使うか",
            "Type": "Decision",
            "Status": "Needs CEO Decision",
            "Owner": "Human + Codex",
            "Related WBS": "T617",
            "Decision Needed": "Use / Hold / Later",
            "Due Date": "2026-06-02",
            "Notes": "docsとWBSを投入し、想定QA生成に使う候補。",
        },
        {
            "Name": "Slack通知を社長共有まで含めるか",
            "Type": "Decision",
            "Status": "Needs CEO Decision",
            "Owner": "Human + Codex",
            "Related WBS": "T618",
            "Decision Needed": "Team only / CEO included / Hold",
            "Due Date": "2026-06-02",
            "Notes": "WBS同期、GitHub Actions、公開URL検証結果を短文で共有する候補。",
        },
        {
            "Name": "Notionを議事録・意思決定DBの公式台帳にするか",
            "Type": "Decision",
            "Status": "Needs CEO Decision",
            "Owner": "Human + Codex",
            "Related WBS": "T619",
            "Decision Needed": "Official / Reference / Hold",
            "Due Date": "2026-06-02",
            "Notes": "6/2決定事項と次アクションをNotion DB化する候補。",
        },
        {
            "Name": "Obsidianをローカル開発メモとして採用するか",
            "Type": "Decision",
            "Status": "Needs CEO Decision",
            "Owner": "Codex",
            "Related WBS": "T620",
            "Decision Needed": "Local memo / Not use / Later",
            "Due Date": "2026-06-02",
            "Notes": "ADR、プロンプト、未整理アイデアをローカルで蓄積する候補。",
        },
    ]
    backlog = [
        {
            "Task": row["タスク名"],
            "WBS ID": row["タスクID"],
            "Phase": row["小フェーズ"],
            "Status": row["ステータス"],
            "Owner": row["担当"],
            "Start": row["開始日"],
            "Due": row["終了予定日"],
            "Notes": row["Sheets Live 連携アクション"],
        }
        for row in knowledge_tasks(rows)
    ]
    write_csv(EXPORT_DIR / "notion_decision_log.csv", decisions)
    write_csv(EXPORT_DIR / "notion_backlog_import.csv", backlog)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_obsidian_vault(summary: dict) -> None:
    write_text(
        OBSIDIAN_DIR / "Mighty Skill-Bridge Home.md",
        f"""# Mighty Skill-Bridge Home

## Current Status

- WBS total: {summary['total']}
- Done: {summary['done']}
- In progress: {summary['active']}
- Completion: {summary['completion_rate']}%

## Key Notes

- [[Meetings/2026-06-02 CEO Meeting]]
- [[ADR/ADR-0001-knowledge-flow]]
- [[Prompts/NotebookLM Source Prompt]]

## Rule

Keep private thoughts here. Promote only approved notes back to `docs/` and WBS.
""",
    )
    write_text(
        OBSIDIAN_DIR / "ADR" / "ADR-0001-knowledge-flow.md",
        """# ADR-0001: Knowledge Flow Demo Before CEO Decision

## Status

Proposed for 2026-06-02 CEO review.

## Context

The project needs a visible development workflow using NotebookLM, Slack,
Notion, and Obsidian, while the actual service concept remains undecided until
the CEO meeting.

## Decision

Create demo artifacts first:

- NotebookLM source pack
- Slack update draft
- Notion decision/backlog CSV
- Obsidian local vault starter

Do not send external messages or store secrets in third-party tools before CEO
approval.

## Consequences

The CEO can see the workflow in action without locking the product plan.
""",
    )
    write_text(
        OBSIDIAN_DIR / "Meetings" / "2026-06-02 CEO Meeting.md",
        """# 2026-06-02 CEO Meeting

## Decisions

- Service direction:
- First target user:
- Priority feature:
- Knowledge-flow tools to adopt:
- Sharing scope:

## Knowledge Flow Review

- NotebookLM:
- Slack:
- Notion:
- Obsidian:

## Next Actions

- WBS updates:
- Calendar updates:
- Git commit:
- CEO shared material:
""",
    )
    write_text(
        OBSIDIAN_DIR / "Prompts" / "NotebookLM Source Prompt.md",
        """# NotebookLM Source Prompt

Use the NotebookLM source pack to answer:

1. What should be explained first to the CEO?
2. What decisions are needed on 2026-06-02?
3. What are the risks of each knowledge-flow tool?
4. Which items should become WBS tasks after the meeting?
""",
    )
    write_text(
        OBSIDIAN_DIR / ".obsidian" / "app.json",
        """{
  "alwaysUpdateLinks": true,
  "promptDelete": false,
  "newFileLocation": "current",
  "attachmentFolderPath": "Attachments"
}
""",
    )
    write_text(
        OBSIDIAN_DIR / ".obsidian" / "appearance.json",
        """{
  "accentColor": "#1a73e8",
  "cssTheme": "",
  "baseFontSize": 16,
  "enabledCssSnippets": []
}
""",
    )


def build_demo_guide() -> str:
    return """# CEO Knowledge Flow Demo Guide

## Demo Order

1. Open `notebooklm_source_pack.md` and `notebooklm_source_pack.txt`; the TXT version can be uploaded to Google Drive as a native Google Doc and then used as a NotebookLM source.
2. Open `slack_ceo_update.md` and show the ready-to-post progress update.
3. Open `notion_decision_log.csv` and `notion_backlog_import.csv` as Notion import sources.
4. Open `obsidian_vault/Mighty Skill-Bridge Home.md` as a local Obsidian vault entry point.
5. Explain that no credentials or private customer data are included.

## CEO Decision

Ask which tools should become official after 2026-06-02:

- NotebookLM for source reading and QA generation
- Slack for progress notifications
- Notion for decisions and backlog
- Obsidian for local developer knowledge
"""


def generate() -> dict:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_wbs_rows()
    summary = wbs_summary(rows)

    artifacts = [
        EXPORT_DIR / "notebooklm_source_pack.md",
        EXPORT_DIR / "notebooklm_source_pack.txt",
        EXPORT_DIR / "slack_ceo_update.md",
        EXPORT_DIR / "notion_decision_log.csv",
        EXPORT_DIR / "notion_backlog_import.csv",
        EXPORT_DIR / "CEO_KNOWLEDGE_FLOW_DEMO_GUIDE.md",
        EXPORT_DIR / "integration_evidence.md",
        OBSIDIAN_DIR / "Mighty Skill-Bridge Home.md",
        OBSIDIAN_DIR / "ADR" / "ADR-0001-knowledge-flow.md",
        OBSIDIAN_DIR / "Meetings" / "2026-06-02 CEO Meeting.md",
        OBSIDIAN_DIR / "Prompts" / "NotebookLM Source Prompt.md",
        OBSIDIAN_DIR / ".obsidian" / "app.json",
        OBSIDIAN_DIR / ".obsidian" / "appearance.json",
    ]

    notebooklm_pack = build_notebooklm_pack(rows, summary)
    write_text(artifacts[0], notebooklm_pack)
    write_text(artifacts[1], notebooklm_pack)
    write_text(artifacts[2], build_slack_update(summary))
    write_notion_csvs(rows)
    build_obsidian_vault(summary)
    write_text(artifacts[5], build_demo_guide())

    manifest = {
        "generated_at_jst": jst_now().isoformat(timespec="seconds"),
        "summary": summary,
        "artifacts": [
            str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            for path in artifacts
            if path.exists()
        ],
        "notes": [
            "No external API calls were made.",
            "No credentials or authorized_user files were read.",
            "Artifacts are safe demo materials for CEO review.",
        ],
    }
    manifest_path = EXPORT_DIR / "manifest.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    manifest["artifacts"].append(str(manifest_path.relative_to(PROJECT_ROOT)).replace("\\", "/"))
    return manifest


def main() -> None:
    manifest = generate()
    print("[+] Knowledge flow demo artifacts generated.")
    print(f"[*] Output: {EXPORT_DIR}")
    for artifact in manifest["artifacts"]:
        print(f"  - {artifact}")


if __name__ == "__main__":
    main()
