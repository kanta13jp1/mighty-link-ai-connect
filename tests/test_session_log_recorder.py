# -*- coding: utf-8 -*-
"""
Rigorous tests for Antigravity Session Log Recorder Hook and .agents/hooks.json specification.
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


def test_hook_stdin_stdout_contract_and_json_output(tmp_path: Path):
    """Verify script accepts official JSON payload on stdin and emits pure JSON on stdout."""
    mock_workspace = tmp_path / "mock_workspace"
    mock_workspace.mkdir()
    
    mock_transcript = tmp_path / "transcript.jsonl"
    mock_steps = [
        {
            "step_index": 1,
            "type": "USER_INPUT",
            "content": "Add attendance export feature with key sk-proj-1234567890abcdef1234567890",
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
    
    # Verify stdout is strictly valid JSON
    stdout_trimmed = proc.stdout.strip()
    assert stdout_trimmed, "stdout must not be empty"
    parsed_stdout = json.loads(stdout_trimmed)
    assert isinstance(parsed_stdout, dict), "stdout must be a valid JSON dictionary"

    # Verify generated session log in mock workspace
    sessions_dir = mock_workspace / "docs" / "sessions"
    assert sessions_dir.exists(), "docs/sessions must be created in mock workspace"
    session_files = list(sessions_dir.glob("*.md"))
    assert len(session_files) == 1, "Exactly one session log file should be generated"

    log_content = session_files[0].read_text(encoding="utf-8")
    assert "test-conv-12345678-abcd" in log_content
    assert "src/attendance.py" in log_content


def test_secret_and_pii_redaction(tmp_path: Path):
    """Verify secrets, credentials, and API keys are automatically masked."""
    mock_workspace = tmp_path / "mock_workspace"
    mock_workspace.mkdir()
    
    mock_transcript = tmp_path / "transcript_secrets.jsonl"
    mock_steps = [
        {
            "step_index": 1,
            "type": "USER_INPUT",
            "content": "Connect to OpenAI sk-abcdef1234567890abcdef12345 and Gemini AIzaSyD123456789012345678901234567890 and GitHub ghp_123456789012345678901234567890123456 with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.secret",
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
        "terminationReason": "model_stop"
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

    # Assert raw secrets are NOT present
    assert "sk-abcdef1234567890abcdef12345" not in log_content
    assert "AIzaSyD123456789012345678901234567890" not in log_content
    assert "ghp_123456789012345678901234567890123456" not in log_content
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in log_content

    # Assert redaction placeholders ARE present
    assert "[REDACTED_API_KEY]" in log_content
    assert "[REDACTED_GEMINI_KEY]" in log_content
    assert "[REDACTED_GITHUB_TOKEN]" in log_content
    assert "Bearer [REDACTED_TOKEN]" in log_content
