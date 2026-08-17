#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Official Session Log Recorder Hook.

Implements the official Google Antigravity Hooks specification for the 'Stop' lifecycle event:
- Location: .agents/hooks.json
- Event: Stop
- Input Contract: Reads JSON payload on stdin (conversationId, transcriptPath, workspacePaths, fullyIdle, etc.)
- Output Contract: Emits JSON with {"decision": "allow"} on stdout.
- Security: Automatic redaction of PII (emails, phone numbers), API keys, tokens, passwords, private keys, and config files.
- Precision: Session-scoped (deduplicated by conversationId) and workspace-isolated log generation into docs/sessions/ and Obsidian Vault.
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

MODIFYING_TOOLS = frozenset({
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
    "generate_image",
})

READ_ONLY_TOOLS = frozenset({
    "view_file",
    "list_dir",
    "grep_search",
    "read_resource",
    "list_resources",
    "search_web",
    "read_url_content",
})

# Comprehensive PII and Secret redaction patterns
SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Private Keys (PEM)
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    # Database Connection Strings with Passwords
    (re.compile(r"(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis):\/\/([^:]+):([^@]+)@", re.IGNORECASE), r"\1://\2:[REDACTED_DB_PASSWORD]@"),
    # AWS Access Keys
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    # OpenAI Keys
    (re.compile(r"\bsk-[a-zA-Z0-9_\-]{20,}\b", re.IGNORECASE), "[REDACTED_API_KEY]"),
    # Gemini / Google API Keys
    (re.compile(r"\bAIzaSy[a-zA-Z0-9_\-]{30,}\b", re.IGNORECASE), "[REDACTED_GEMINI_KEY]"),
    # GitHub Classic & Fine-grained Tokens
    (re.compile(r"\bgithub_pat_[a-zA-Z0-9_]{22,}\b", re.IGNORECASE), "[REDACTED_GITHUB_PAT]"),
    (re.compile(r"\bghp_[a-zA-Z0-9]{30,}\b", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    # Slack Tokens
    (re.compile(r"\bxox[baprs]-[a-zA-Z0-9\-]{10,}\b", re.IGNORECASE), "[REDACTED_SLACK_TOKEN]"),
    # Bearer Tokens
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\.\-]{20,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # Email Addresses
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    # Phone Numbers (Japanese & International formats)
    (re.compile(r"\b(0\d{1,4}[- ]?\d{1,4}[- ]?\d{4}|\+?\d{1,3}[- ]?\d{2,4}[- ]?\d{3,4}[- ]?\d{3,4})\b"), "[REDACTED_PHONE]"),
    # Generic Key/Secret/Password assignments
    (re.compile(r"(api[_\-]?key|secret|password|passwd|auth_token)\s*[:=]\s*['\"]?[^\s'\",;]+['\"]?", re.IGNORECASE), r"\1=[REDACTED]"),
    # Sensitive Config File Names
    (re.compile(r"\b(credentials\.json|client_secret\.json|authorized_user\.json|\.env(\.[a-zA-Z0-9_\-]+)?)\b", re.IGNORECASE), "[PROTECTED_CONFIG_FILE]"),
]


def redact_secrets(text: str) -> str:
    """Mask sensitive tokens, API keys, passwords, PII, and secret files from text."""
    if not text:
        return ""
    res = text
    for pattern, repl in SECRET_PATTERNS:
        res = pattern.sub(repl, res)
    return res


def sanitize_and_normalize_path(path_str: str, workspace_root: Path) -> str | None:
    """Clean and normalize a file path string strictly within the workspace root."""
    if not path_str:
        return None
    # Strip quotes, backticks, whitespace
    clean = path_str.strip('\'"` \t\r\n')
    if not clean:
        return None
    
    # Exclude sensitive config file targets
    if re.search(r"(\.env|credentials\.json|client_secret\.json|authorized_user\.json)", clean, re.IGNORECASE):
        return "[PROTECTED_CONFIG_FILE]"

    try:
        p = Path(clean)
        # If absolute path, ensure it resides inside workspace_root
        if p.is_absolute():
            try:
                rel = p.resolve().relative_to(workspace_root.resolve())
                return rel.as_posix()
            except ValueError:
                # Path is outside workspace root (e.g. C:/Users/example/private.txt) - ignore
                return None
        else:
            return p.as_posix()
    except Exception:
        return None


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
                        # Extract clean user prompt and redact PII/secrets
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

                    # ONLY extract modified files from actual modifying tools
                    if name in MODIFYING_TOOLS:
                        for key in ["TargetFile", "target_file", "FilePath", "file_path"]:
                            if key in args and args[key]:
                                norm = sanitize_and_normalize_path(str(args[key]), workspace_root)
                                if norm:
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
    fully_idle: bool = True,
) -> dict[str, Any]:
    """Generate structured markdown log and write to docs/sessions, Obsidian Vault, and SESSION_LOG.md."""
    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
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
    # Deterministic file name based on conversation ID to avoid duplicate files per turn
    session_file_name = f"SESSION_{short_id}.md"
    
    sessions_dir = workspace_root / "docs" / "sessions"
    obsidian_dir = workspace_root / "exports" / "knowledge_flow" / "obsidian_vault" / "30_Meetings"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    obsidian_dir.mkdir(parents=True, exist_ok=True)

    session_file_path = sessions_dir / session_file_name
    obsidian_file_path = obsidian_dir / f"{date_day} Antigravity Session {short_id}.md"

    idle_status = "完了 (fullyIdle=True)" if fully_idle else "実行中タスクあり (fullyIdle=False)"

    content = [
        f"# 📝 Antigravity Session Log: {short_id}",
        "",
        f"- **最終更新 (JST)**: {now_jst}",
        f"- **Conversation ID**: `{conversation_id}`",
        f"- **セッション状態**: `{idle_status}`",
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

    # Write / update deterministic session log files
    session_file_path.write_text(log_text, encoding="utf-8")
    obsidian_file_path.write_text(log_text, encoding="utf-8")

    # Update master ledger docs/SESSION_LOG.md in-place
    master_log = workspace_root / "docs" / "SESSION_LOG.md"
    header = "# Antigravity 開発セッション記録一覧 (Session Logs)\n\n全セッションの作業履歴・実行内容・変更ファイルが自動記録されるログ台帳です。\n\n"
    if not master_log.exists():
        master_log.write_text(header, encoding="utf-8")

    current_master = master_log.read_text(encoding="utf-8")
    last_prompt = data["user_inputs"][-1][:120] if data["user_inputs"] else "N/A"
    mod_files_summary = ", ".join(data["modified_files"][:5]) if data["modified_files"] else "None"
    entry_summary = (
        f"### [{now_jst}] Session `{short_id}`\n"
        f"- **詳細ログ**: [{session_file_name}](sessions/{session_file_name})\n"
        f"- **主な指示**: {last_prompt}\n"
        f"- **変更ファイル**: {mod_files_summary}\n"
    )

    # Check if section for this session already exists in master log and replace it cleanly
    session_heading_pattern = rf"### \[.*?\] Session `{re.escape(short_id)}`\n- \*\*詳細ログ\*\*:.*?\n- \*\*主な指示\*\*:.*?\n- \*\*変更ファイル\*\*:.*?\n"
    if re.search(session_heading_pattern, current_master):
        updated_master = re.sub(session_heading_pattern, entry_summary, current_master)
    else:
        updated_master = current_master.rstrip() + "\n\n" + entry_summary

    master_log.write_text(updated_master, encoding="utf-8")

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
    fully_idle = payload.get("fullyIdle", True)

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
            fully_idle=fully_idle,
        )
    except Exception as e:
        sys.stderr.write(f"[!] Error recording session log: {e}\n")

    # MUST output valid JSON with decision: "allow" for official Stop lifecycle hook
    output_payload = {
        "decision": "allow"
    }
    print(json.dumps(output_payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
