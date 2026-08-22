# -*- coding: utf-8 -*-
"""
Rigorous comprehensive tests for Antigravity Session Log Recorder Hook.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON_PATH = PROJECT_ROOT / ".agents" / "hooks.json"
RECORDER_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "record_session_log.py"


def test_agents_hooks_json_specification_compliance():
    """Verify .agents/hooks.json matches the official Google Antigravity Hooks specification."""
    assert HOOKS_JSON_PATH.exists(), ".agents/hooks.json must exist in repository root"
    
    with HOOKS_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert isinstance(data, dict), "hooks.json root must be an object of named hooks"
    assert "session-log-recorder" in data, "session-log-recorder hook must be defined"
    
    hook = data["session-log-recorder"]
    assert "Stop" in hook, "Hook must listen to the official 'Stop' lifecycle event"
    assert isinstance(hook["Stop"], list), "'Stop' handlers must be a flat array of handler objects"
    assert len(hook["Stop"]) >= 1, "At least one Stop handler must be configured"
    
    handler = hook["Stop"][0]
    assert handler.get("type") == "command", "Handler type must be 'command'"
    assert "record_session_log.py" in handler.get("command", ""), "Handler command must execute record_session_log.py"
    assert handler.get("timeout", 0) > 0, "Handler should have an explicit timeout"


def test_configured_stop_hook_command_executes_from_agents_directory(tmp_path: Path):
    """Execute the configured command from Antigravity's observed .agents working directory."""
    mock_workspace = tmp_path / "mock_workspace"
    mock_workspace.mkdir()
    mock_transcript = tmp_path / "transcript_hook_command.jsonl"
    mock_transcript.write_text(
        json.dumps(
            {
                "step_index": 1,
                "type": "USER_INPUT",
                "content": "Verify the configured Stop hook command",
                "timestamp": "2026-08-22T01:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = {
        "executionNum": 1,
        "terminationReason": "model_stop",
        "fullyIdle": True,
        "conversationId": "configured-hook-command-1234",
        "workspacePaths": [str(mock_workspace)],
        "transcriptPath": str(mock_transcript),
        "artifactDirectoryPath": str(tmp_path / "artifacts"),
        "modelName": "test-model",
    }

    hook_data = json.loads(HOOKS_JSON_PATH.read_text(encoding="utf-8"))
    handler = hook_data["session-log-recorder"]["Stop"][0]
    command = handler["command"]

    normalized_command = command.replace("\\", "/").lower()
    assert PROJECT_ROOT.as_posix().lower() not in normalized_command, (
        "Hook command must not contain a machine-specific absolute project path"
    )

    proc = subprocess.run(
        command,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=HOOKS_JSON_PATH.parent,
        shell=True,
        timeout=handler["timeout"],
    )

    assert proc.returncode == 0, f"Configured Hook failed: {proc.stderr}"
    assert json.loads(proc.stdout.strip()).get("decision") == "allow"

    session_files = list((mock_workspace / "docs" / "sessions").glob("*.md"))
    assert len(session_files) == 1
    assert "configured-hook-command-1234" in session_files[0].read_text(encoding="utf-8")


def test_hook_stdin_stdout_contract_with_decision_allow(tmp_path: Path):
    """Verify script accepts official JSON payload on stdin and emits JSON with decision: allow on stdout."""
    mock_workspace = tmp_path / "mock_workspace"
    mock_workspace.mkdir()
    
    mock_transcript = tmp_path / "transcript.jsonl"
    mock_steps = [
        {
            "step_index": 1,
            "type": "USER_INPUT",
            "content": "Add attendance export feature",
            "timestamp": "2026-08-18T01:00:00Z"
        },
        {
            "step_index": 2,
            "type": "MODEL_RESPONSE",
            "tool_calls": [
                {
                    "name": "write_to_file",
                    "args": {
                        "TargetFile": str(mock_workspace / "src" / "attendance.py"),
                        "toolSummary": "Create attendance export module"
                    }
                }
            ]
        }
    ]
    with mock_transcript.open("w", encoding="utf-8") as f:
        for s in mock_steps:
            f.write(json.dumps(s) + "\n")

    input_payload = {
        "conversationId": "test-conv-12345678-abcd",
        "workspacePaths": [str(mock_workspace)],
        "transcriptPath": str(mock_transcript),
        "terminationReason": "model_stop",
        "fullyIdle": True
    }

    # Execute script feeding input_payload via stdin
    proc = subprocess.run(
        [sys.executable, str(RECORDER_SCRIPT_PATH)],
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT
    )

    assert proc.returncode == 0, f"Script failed with stderr: {proc.stderr}"
    
    # Verify stdout is strictly valid JSON containing decision: allow
    stdout_trimmed = proc.stdout.strip()
    assert stdout_trimmed, "stdout must not be empty"
    parsed_stdout = json.loads(stdout_trimmed)
    assert isinstance(parsed_stdout, dict), "stdout must be a valid JSON dictionary"
    assert parsed_stdout.get("decision") == "allow", "Stop hook must return decision: allow"

    # Verify generated session log in mock workspace
    sessions_dir = mock_workspace / "docs" / "sessions"
    assert sessions_dir.exists(), "docs/sessions must be created in mock workspace"
    session_files = list(sessions_dir.glob("*.md"))
    assert len(session_files) == 1, "Exactly one session log file should be generated"

    log_content = session_files[0].read_text(encoding="utf-8")
    assert "test-conv-12345678-abcd" in log_content
    assert "src/attendance.py" in log_content
    assert "fullyIdle=True" in log_content


def test_accurate_file_modification_and_exclusion(tmp_path: Path):
    """Verify read-only tools and external files are excluded from modified files list."""
    mock_workspace = tmp_path / "mock_workspace"
    mock_workspace.mkdir()
    
    mock_transcript = tmp_path / "transcript_tools.jsonl"
    mock_steps = [
        {
            "step_index": 1,
            "type": "USER_INPUT",
            "content": "Check files and edit code",
            "timestamp": "2026-08-18T01:00:00Z"
        },
        {
            "step_index": 2,
            "type": "MODEL_RESPONSE",
            "tool_calls": [
                {
                    "name": "view_file",
                    "args": {
                        "AbsolutePath": str(mock_workspace / "docs" / "readme.md"),
                        "toolSummary": "View readme.md"
                    }
                },
                {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": str(mock_workspace / "src" / "app.py"),
                        "toolSummary": "Update server config"
                    }
                },
                {
                    "name": "view_file",
                    "args": {
                        "AbsolutePath": "C:/Users/example/private.txt",
                        "toolSummary": "View private notes"
                    }
                }
            ]
        }
    ]
    with mock_transcript.open("w", encoding="utf-8") as f:
        for s in mock_steps:
            f.write(json.dumps(s) + "\n")

    input_payload = {
        "conversationId": "conv-file-check-1234",
        "workspacePaths": [str(mock_workspace)],
        "transcriptPath": str(mock_transcript),
        "terminationReason": "model_stop",
        "fullyIdle": True
    }

    proc = subprocess.run(
        [sys.executable, str(RECORDER_SCRIPT_PATH)],
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT
    )

    assert proc.returncode == 0
    sessions_dir = mock_workspace / "docs" / "sessions"
    log_content = list(sessions_dir.glob("*.md"))[0].read_text(encoding="utf-8")

    # Modified file must be present
    assert "src/app.py" in log_content
    # Viewed files must NOT be in target files section
    assert "docs/readme.md" not in log_content
    assert "private.txt" not in log_content


def test_comprehensive_secret_and_pii_redaction(tmp_path: Path):
    """Verify secrets, tokens, PII (email, phone), database passwords, and private keys are masked."""
    mock_workspace = tmp_path / "mock_workspace"
    mock_workspace.mkdir()
    
    mock_transcript = tmp_path / "transcript_secrets.jsonl"
    mock_steps = [
        {
            "step_index": 1,
            "type": "USER_INPUT",
            "content": (
                "Credentials: user email is kanta_umezawa@ml-mightylink.com, phone 090-1234-5678, "
                "AWS AKIAIOSFODNN7EXAMPLE, OpenAI sk-1234567890abcdef1234567890abcdef, "
                "Gemini AIzaSyD123456789012345678901234567890, GitHub PAT github_pat_11AAAAAAA0000000000000_1234567890, "
                "Slack xoxb-1234567890-1234567890-abcdef123456, DB postgresql://admin:SuperSecretPass123!@db.mightylink.com:5432/prod, "
                "Key: -----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----"
            ),
            "timestamp": "2026-08-18T01:00:00Z"
        }
    ]
    with mock_transcript.open("w", encoding="utf-8") as f:
        for s in mock_steps:
            f.write(json.dumps(s) + "\n")

    input_payload = {
        "conversationId": "secret-conv-9999",
        "workspacePaths": [str(mock_workspace)],
        "transcriptPath": str(mock_transcript),
        "terminationReason": "model_stop",
        "fullyIdle": True
    }

    proc = subprocess.run(
        [sys.executable, str(RECORDER_SCRIPT_PATH)],
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT
    )

    assert proc.returncode == 0
    sessions_dir = mock_workspace / "docs" / "sessions"
    log_content = list(sessions_dir.glob("*.md"))[0].read_text(encoding="utf-8")

    # Assert raw secrets and PII are NOT present
    assert "kanta_umezawa@ml-mightylink.com" not in log_content
    assert "090-1234-5678" not in log_content
    assert "AKIAIOSFODNN7EXAMPLE" not in log_content
    assert "sk-1234567890abcdef1234567890abcdef" not in log_content
    assert "AIzaSyD123456789012345678901234567890" not in log_content
    assert "github_pat_11AAAAAAA0000000000000_1234567890" not in log_content
    assert "xoxb-1234567890-1234567890-abcdef123456" not in log_content
    assert "SuperSecretPass123!" not in log_content
    assert "-----BEGIN RSA PRIVATE KEY-----" not in log_content

    # Assert redaction placeholders ARE present
    assert "[REDACTED_EMAIL]" in log_content
    assert "[REDACTED_PHONE]" in log_content
    assert "[REDACTED_AWS_KEY]" in log_content
    assert "[REDACTED_API_KEY]" in log_content
    assert "[REDACTED_GEMINI_KEY]" in log_content
    assert "[REDACTED_GITHUB_PAT]" in log_content
    assert "[REDACTED_SLACK_TOKEN]" in log_content
    assert "[REDACTED_DB_PASSWORD]" in log_content
    assert "[REDACTED_PRIVATE_KEY]" in log_content


def test_session_deduplication_and_in_place_update(tmp_path: Path):
    """Verify multiple Stop triggers for the same conversationId update the session log in-place without creating duplicate files."""
    mock_workspace = tmp_path / "mock_workspace"
    mock_workspace.mkdir()
    
    conv_id = "duplicate-check-conv-1111"
    mock_transcript = tmp_path / "transcript_dedup.jsonl"
    
    # Turn 1
    with mock_transcript.open("w", encoding="utf-8") as f:
        f.write(json.dumps({
            "step_index": 1,
            "type": "USER_INPUT",
            "content": "First turn request",
            "timestamp": "2026-08-18T01:00:00Z"
        }) + "\n")

    input_payload = {
        "conversationId": conv_id,
        "workspacePaths": [str(mock_workspace)],
        "transcriptPath": str(mock_transcript),
        "terminationReason": "model_stop",
        "fullyIdle": False
    }

    proc1 = subprocess.run(
        [sys.executable, str(RECORDER_SCRIPT_PATH)],
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT
    )
    assert proc1.returncode == 0
    sessions_dir = mock_workspace / "docs" / "sessions"
    assert len(list(sessions_dir.glob("*.md"))) == 1

    # Turn 2 with additional steps
    with mock_transcript.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "step_index": 2,
            "type": "USER_INPUT",
            "content": "Second turn request",
            "timestamp": "2026-08-18T01:05:00Z"
        }) + "\n")

    input_payload["fullyIdle"] = True
    proc2 = subprocess.run(
        [sys.executable, str(RECORDER_SCRIPT_PATH)],
        input=json.dumps(input_payload),
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT
    )
    assert proc2.returncode == 0
    
    # Must still have exactly 1 file (deduplicated by conversationId)
    session_files = list(sessions_dir.glob("*.md"))
    assert len(session_files) == 1, "Must update the same session file in-place"
    updated_content = session_files[0].read_text(encoding="utf-8")
    assert "Second turn request" in updated_content
    assert "fullyIdle=True" in updated_content
