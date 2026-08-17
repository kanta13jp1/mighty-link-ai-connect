#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Session Log Recorder Hook Script.

Automatically parses the latest conversation transcript from Antigravity Brain,
extracts user prompts, executed tool calls, modified files, and git changes,
and records a structured session log in docs/SESSION_LOG.md and Obsidian Vault (30_Meetings).
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
SESSIONS_DIR = DOCS_DIR / "sessions"
OBSIDIAN_MEETINGS_DIR = PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "30_Meetings"
BRAIN_DIR = Path(os.path.expanduser("~/.gemini/antigravity/brain"))
JST = timezone(timedelta(hours=9))


def get_latest_conversation() -> tuple[str, Path] | None:
    if not BRAIN_DIR.exists():
        return None
    conv_dirs = [
        d for d in BRAIN_DIR.iterdir()
        if d.is_dir() and (d / ".system_generated" / "logs" / "transcript.jsonl").exists()
    ]
    if not conv_dirs:
        return None
    conv_dirs.sort(key=lambda d: (d / ".system_generated" / "logs" / "transcript.jsonl").stat().st_mtime, reverse=True)
    latest = conv_dirs[0]
    return latest.name, latest / ".system_generated" / "logs" / "transcript.jsonl"


def parse_transcript(log_path: Path) -> dict:
    user_inputs = []
    tool_actions = []
    modified_files = set()
    start_time = None
    end_time = None

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                except Exception:
                    continue

                ts = step.get("timestamp")
                if ts:
                    if not start_time:
                        start_time = ts
                    end_time = ts

                step_type = step.get("type")
                if step_type == "USER_INPUT":
                    content = step.get("content", "").strip()
                    if content and not content.startswith("{{ CHECKPOINT"):
                        # Extract clean user message
                        clean_msg = content.split("<ADDITIONAL_METADATA>")[0].strip()
                        clean_msg = re.sub(r"<[^>]+>", "", clean_msg).strip()
                        if clean_msg:
                            user_inputs.append(clean_msg)

                # Collect tool calls
                tool_calls = step.get("tool_calls", [])
                for tc in tool_calls:
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                    summary = args.get("toolSummary") or args.get("toolAction") or name
                    if name:
                        tool_actions.append(f"`{name}`: {summary}")
                    
                    # Track edited files
                    if name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
                        target = args.get("TargetFile")
                        if target:
                            modified_files.add(Path(target).name)
    except Exception as e:
        print(f"[!] Warning reading transcript: {e}")

    return {
        "user_inputs": user_inputs,
        "tool_actions": tool_actions,
        "modified_files": sorted(list(modified_files)),
        "start_time": start_time,
        "end_time": end_time,
    }


def get_git_diff_summary() -> str:
    try:
        res = subprocess.run(
            ["git", "status", "--short"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )
        return res.stdout.strip()
    except Exception:
        return ""


def record_session_log():
    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now(JST).strftime("%Y%m%d_%H%M%S")
    
    conv_info = get_latest_conversation()
    conv_id = conv_info[0] if conv_info else "unknown-session"
    transcript_path = conv_info[1] if conv_info else None
    
    data = parse_transcript(transcript_path) if transcript_path else {
        "user_inputs": [],
        "tool_actions": [],
        "modified_files": [],
    }

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    session_file_name = f"SESSION_{date_str}_{conv_id[:8]}.md"
    session_file_path = SESSIONS_DIR / session_file_name
    obsidian_file_path = OBSIDIAN_MEETINGS_DIR / f"{datetime.now(JST).strftime('%Y-%m-%d')} Antigravity Session {conv_id[:8]}.md"

    # Build Markdown Content
    content = [
        f"# 📝 Antigravity Session Log: {conv_id[:8]}",
        "",
        f"- **記録日時 (JST)**: {now_jst}",
        f"- **Conversation ID**: `{conv_id}`",
        f"- **担当レーン**: Antigravity + Gemini",
        "",
        "## 1. ユーザーからの指示・ゴール (User Requests)",
    ]
    
    if data["user_inputs"]:
        for idx, u in enumerate(data["user_inputs"], 1):
            short_u = u[:300] + ("..." if len(u) > 300 else "")
            content.append(f"{idx}. {short_u}")
    else:
        content.append("- (明示的なユーザー指示なし / 自動同期セッション)")

    content.extend([
        "",
        "## 2. 変更・作成されたファイル (Modified Files)",
    ])
    if data["modified_files"]:
        for f in data["modified_files"]:
            content.append(f"- `{f}`")
    else:
        content.append("- (セッション内の直接ファイル編集なし)")

    content.extend([
        "",
        "## 3. 実行された主なアクション (Executed Tool Actions)",
    ])
    if data["tool_actions"]:
        # Group or limit unique tool actions
        unique_actions = list(dict.fromkeys(data["tool_actions"]))
        for a in unique_actions[:15]:
            content.append(f"- {a}")
        if len(unique_actions) > 15:
            content.append(f"- ... 他 {len(unique_actions) - 15} 件のアクション")
    else:
        content.append("- (ツール実行なし)")

    diff_summary = get_git_diff_summary()
    if diff_summary:
        content.extend([
            "",
            "## 4. Git 変更ステータス (Working Tree Diff)",
            "```text",
            diff_summary,
            "```",
        ])

    content.extend([
        "",
        "---",
        "## 5. 関連リンク",
        "- [WBS Management Table](../WBS.md)",
        "- [Master Knowledge Graph Index](../MASTER_KNOWLEDGE_GRAPH.md)",
        "- [[Mighty Skill-Bridge Home]]",
    ])

    log_text = "\n".join(content) + "\n"

    # Write individual session log
    session_file_path.write_text(log_text, encoding="utf-8")
    print(f"[+] Saved individual session log to: {session_file_path.relative_to(PROJECT_ROOT)}")

    # Write to Obsidian Vault 30_Meetings
    obsidian_file_path.write_text(log_text, encoding="utf-8")
    print(f"[+] Synced session log to Obsidian Vault: {obsidian_file_path.relative_to(PROJECT_ROOT)}")

    # Append to Master SESSION_LOG.md
    master_log = DOCS_DIR / "SESSION_LOG.md"
    header = "# Antigravity 開発セッション記録一覧 (Session Logs)\n\n全セッションの作業履歴・実行内容・変更ファイルが自動記録されるログ台帳です。\n\n"
    if not master_log.exists():
        master_log.write_text(header, encoding="utf-8")

    current_master = master_log.read_text(encoding="utf-8")
    entry_summary = f"\n### [{now_jst}] Session `{conv_id[:8]}`\n- **詳細ログ**: [{session_file_name}](sessions/{session_file_name})\n- **主な指示**: {data['user_inputs'][-1][:120] if data['user_inputs'] else 'N/A'}\n- **変更ファイル**: {', '.join(data['modified_files'][:5]) if data['modified_files'] else 'None'}\n"
    
    if session_file_name not in current_master:
        master_log.write_text(current_master + entry_summary, encoding="utf-8")
        print(f"[+] Appended session entry to: {master_log.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    record_session_log()
