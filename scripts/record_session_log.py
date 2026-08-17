#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Official Session Log Recorder Hook.

Implements the official Google Antigravity Hooks specification for the 'Stop' lifecycle event:
- Location: .agents/hooks.json
- Event: Stop
- Input Contract: Reads JSON payload on stdin (conversationId, transcriptPath, workspacePaths, etc.)
- Output Contract: Emits pure JSON on stdout (e.g., {})
- Security: Automatic redaction/masking of API keys, tokens, credentials, and sensitive data.
- Precision: Session-scoped and workspace-isolated log generation into docs/sessions/ and Obsidian Vault.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
SESSIONS_DIR = DOCS_DIR / "sessions"
OBSIDIAN_MEETINGS_DIR = PROJECT_ROOT / "exports" / "knowledge_flow" / "obsidian_vault" / "30_Meetings"
BRAIN_DIR = Path(os.path.expanduser("~/.gemini/antigravity/brain"))
JST = timezone(timedelta(hours=9))

# Secret redaction patterns
SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"AIzaSy[a-zA-Z0-9_\-]{30,}", re.IGNORECASE), "[REDACTED_GEMINI_KEY]"),
    (re.compile(r"ghp_[a-zA-Z0-9]{30,}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\.\-]{20,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"(api[_\-]?key|secret|password|passwd|token)\s*[:=]\s*['\"]?[^\s'\",;]+['\"]?", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"credentials\.json|client_secret\.json|\.env(\.local)?", re.IGNORECASE), "[PROTECTED_CONFIG_FILE]"),
]


def redact_secrets(text: str) -> str:
    """Mask sensitive tokens, API keys, passwords, and secret files from text."""
    if not text:
        return ""
    res = text
    for pattern, repl in SECRET_PATTERNS:
        res = pattern.sub(repl, res)
    return res


def normalize_file_path(path_str: str, base_dir: Path | None = None) -> str:
    """Clean and normalize a file path string."""
    if not path_str:
        return ""
    # Strip quotes, backticks, trailing/leading whitespace
    clean = path_str.strip('\'"` \t\r\n')
    try:
        p = Path(clean)
        if base_dir and p.is_absolute():
            try:
                return p.relative_to(base_dir).as_posix()
            except ValueError:
                pass
        return p.as_posix()
    except Exception:
        return clean.replace("\\", "/")


def parse_transcript_file(transcript_path: Path, workspace_root: Path) -> dict[str, Any]:
    """Parse Antigravity JSONL transcript extracting sanitized user prompts, tool actions, and modified files."""
    user_inputs: list[str] = []
    tool_actions: list[str] = []
    modified_files: set[str] = set()
    start_time: str | None = None
    end_time: str | None = None

    if not transcript_path.exists():
        return {
            "user_inputs": user_inputs,
            "tool_actions": tool_actions,
            "modified_files": [],
            "start_time": None,
            "end_time": None,
        }

    try:
        with transcript_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
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
                        # Extract clean user prompt and redact
                        clean_msg = content.split("<ADDITIONAL_METADATA>")[0].strip()
                        clean_msg = re.sub(r"<[^>]+>", "", clean_msg).strip()
                        if clean_msg:
                            user_inputs.append(redact_secrets(clean_msg))

                # Collect tool calls and file operations
                tool_calls = step.get("tool_calls", [])
                for tc in tool_calls:
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                    summary = args.get("toolSummary") or args.get("toolAction") or name
                    if name:
                        tool_actions.append(f"`{name}`: {redact_secrets(str(summary))}")

                    # Detect modified files from write/edit tools
                    for key in ["TargetFile", "target_file", "FilePath", "file_path", "AbsolutePath"]:
                        if key in args and args[key]:
                            norm = normalize_file_path(str(args[key]), workspace_root)
                            if norm and not norm.startswith("[PROTECTED"):
                                modified_files.add(norm)
    except Exception as e:
        sys.stderr.write(f"[!] Warning reading transcript {transcript_path}: {e}\n")

    return {
        "user_inputs": user_inputs,
        "tool_actions": tool_actions,
        "modified_files": sorted(list(modified_files)),
        "start_time": start_time,
        "end_time": end_time,
    }


def get_git_status(workspace_root: Path) -> str:
    """Get clean git status summary for current workspace."""
    try:
        res = subprocess.run(
            ["git", "status", "--short"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = res.stdout.strip()
        return redact_secrets(output)
    except Exception:
        return ""


def process_session_log(
    conversation_id: str,
    transcript_path: Path | None,
    workspace_root: Path,
    termination_reason: str = "stop",
) -> dict[str, Any]:
    """Generate structured markdown log and write to docs/sessions, Obsidian Vault, and SESSION_LOG.md."""
    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    date_slug = datetime.now(JST).strftime("%Y%m%d_%H%M%S")
    date_day = datetime.now(JST).strftime("%Y-%m-%d")

    data = (
        parse_transcript_file(transcript_path, workspace_root)
        if transcript_path and transcript_path.exists()
        else {
            "user_inputs": [],
            "tool_actions": [],
            "modified_files": [],
            "start_time": None,
            "end_time": None,
        }
    )

    short_id = conversation_id[:8] if conversation_id else "session"
    session_file_name = f"SESSION_{date_slug}_{short_id}.md"
    
    sessions_dir = workspace_root / "docs" / "sessions"
    obsidian_dir = workspace_root / "exports" / "knowledge_flow" / "obsidian_vault" / "30_Meetings"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    obsidian_dir.mkdir(parents=True, exist_ok=True)

    session_file_path = sessions_dir / session_file_name
    obsidian_file_path = obsidian_dir / f"{date_day} Antigravity Session {short_id}.md"

    content = [
        f"# 📝 Antigravity Session Log: {short_id}",
        "",
        f"- **記録日時 (JST)**: {now_jst}",
        f"- **Conversation ID**: `{conversation_id}`",
        f"- **終了区分 (Termination Reason)**: `{termination_reason}`",
        f"- **担当レーン**: Antigravity + Gemini",
        "",
        "## 1. ユーザーからの指示・ゴール (User Requests)",
    ]

    if data["user_inputs"]:
        for idx, u in enumerate(data["user_inputs"], 1):
            short_u = u[:400] + ("..." if len(u) > 400 else "")
            content.append(f"{idx}. {short_u}")
    else:
        content.append("- (明示的なプロンプトなし / バックグラウンド実行)")

    content.extend([
        "",
        "## 2. 変更・作成対象ファイル (Target Files)",
    ])
    if data["modified_files"]:
        for f in data["modified_files"]:
            content.append(f"- `{f}`")
    else:
        content.append("- (セッション内の直接ファイル編集記録なし)")

    content.extend([
        "",
        "## 3. 実行された主なアクション (Executed Tool Actions)",
    ])
    if data["tool_actions"]:
        unique_actions = list(dict.fromkeys(data["tool_actions"]))
        for a in unique_actions[:20]:
            content.append(f"- {a}")
        if len(unique_actions) > 20:
            content.append(f"- ... 他 {len(unique_actions) - 20} 件のアクション")
    else:
        content.append("- (ツール実行なし)")

    git_summary = get_git_status(workspace_root)
    if git_summary:
        content.extend([
            "",
            "## 4. Git 変更ステータス (Working Tree Status)",
            "```text",
            git_summary,
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

    # Write files
    session_file_path.write_text(log_text, encoding="utf-8")
    obsidian_file_path.write_text(log_text, encoding="utf-8")

    # Update master ledger docs/SESSION_LOG.md
    master_log = workspace_root / "docs" / "SESSION_LOG.md"
    header = "# Antigravity 開発セッション記録一覧 (Session Logs)\n\n全セッションの作業履歴・実行内容・変更ファイルが自動記録されるログ台帳です。\n\n"
    if not master_log.exists():
        master_log.write_text(header, encoding="utf-8")

    current_master = master_log.read_text(encoding="utf-8")
    last_prompt = data["user_inputs"][-1][:120] if data["user_inputs"] else "N/A"
    mod_files_summary = ", ".join(data["modified_files"][:5]) if data["modified_files"] else "None"
    entry_summary = (
        f"\n### [{now_jst}] Session `{short_id}`\n"
        f"- **詳細ログ**: [{session_file_name}](sessions/{session_file_name})\n"
        f"- **主な指示**: {last_prompt}\n"
        f"- **変更ファイル**: {mod_files_summary}\n"
    )

    if session_file_name not in current_master:
        master_log.write_text(current_master + entry_summary, encoding="utf-8")

    sys.stderr.write(f"[+] Recorded session log {session_file_name} for conversation {conversation_id}\n")
    return {
        "status": "success",
        "session_file": str(session_file_path),
        "obsidian_file": str(obsidian_file_path),
        "conversation_id": conversation_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Antigravity Session Log Recorder Hook")
    parser.add_argument("--conversation-id", default=None, help="Explicit conversation ID")
    parser.add_argument("--transcript-path", default=None, help="Explicit path to transcript.jsonl")
    parser.add_argument("--workspace-dir", default=None, help="Explicit workspace directory")
    args, _ = parser.parse_known_args()

    # Read stdin if available (official hook protocol)
    payload: dict[str, Any] = {}
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                payload = json.loads(stdin_data)
        except Exception as e:
            sys.stderr.write(f"[!] Warning parsing hook stdin JSON: {e}\n")

    conversation_id = args.conversation_id or payload.get("conversationId") or "unknown-session"
    raw_transcript_path = args.transcript_path or payload.get("transcriptPath")
    workspace_paths = payload.get("workspacePaths") or []
    termination_reason = payload.get("terminationReason") or "stop"

    # Determine workspace root
    if args.workspace_dir:
        workspace_root = Path(args.workspace_dir).resolve()
    elif workspace_paths:
        workspace_root = Path(workspace_paths[0]).resolve()
    else:
        workspace_root = PROJECT_ROOT

    # Determine transcript path
    transcript_path: Path | None = None
    if raw_transcript_path:
        transcript_path = Path(raw_transcript_path).resolve()
    elif conversation_id != "unknown-session" and BRAIN_DIR.exists():
        cand = BRAIN_DIR / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
        if cand.exists():
            transcript_path = cand

    # Process and record log
    try:
        process_session_log(
            conversation_id=conversation_id,
            transcript_path=transcript_path,
            workspace_root=workspace_root,
            termination_reason=termination_reason,
        )
    except Exception as e:
        sys.stderr.write(f"[!] Error recording session log: {e}\n")

    # MUST output valid JSON to stdout as required by Antigravity Hook Specification
    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
