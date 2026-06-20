import os
import json
import subprocess
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import sync_docs_to_notebooklm as sync  # noqa: E402


def test_run_notebooklm_converts_timeout_to_completed_process(monkeypatch):
    monkeypatch.setattr(sync.shutil, "which", lambda name: "notebooklm.exe")

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=kwargs["timeout"],
            output="partial output",
            stderr=b"partial error",
        )

    monkeypatch.setattr(sync.subprocess, "run", fake_run)

    completed = sync.run_notebooklm(["ask", "question"], timeout=3)

    assert completed.returncode == 124
    assert completed.stdout == "partial output"
    assert "partial error" in completed.stderr
    assert "timed out after 3 seconds" in completed.stderr


def test_sync_notebooklm_sources_skip_asks_does_not_call_ask(monkeypatch):
    calls = []
    writes = {}

    monkeypatch.setattr(sync, "notebooklm_auth_status", lambda: {"available": True, "status": "ready"})
    monkeypatch.setattr(sync, "resolve_notebook", lambda previous: ("notebook-1", {"action": "used_existing"}))
    monkeypatch.setattr(sync, "existing_source_titles", lambda notebook_id: {})

    def fake_run_notebooklm(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")

    monkeypatch.setattr(sync, "run_notebooklm", fake_run_notebooklm)
    monkeypatch.setattr(sync, "write_text", lambda path, text: writes.__setitem__(path, text))
    monkeypatch.setattr(sync, "write_json", lambda path, payload: writes.__setitem__(path, payload))

    result = sync.sync_notebooklm_sources(
        {"doc": {"name": "Mighty Skill-Bridge docs/docs/example.md", "id": "drive-1"}},
        {},
        run_asks=False,
        ask_timeout_seconds=900,
    )

    assert result["status"] == "ready"
    assert result["ask_generation"]["status"] == "skipped"
    assert result["answer_returncode"] is None
    assert any(call[:2] == ["source", "add-drive"] for call in calls)
    assert not any(call and call[0] in {"ask", "summary"} for call in calls)
    agent_brief = writes[sync.AGENT_BRIEF_PATH]
    assert "source sync completed" in agent_brief.lower()
    assert "not ready yet" not in agent_brief


def test_sync_notebooklm_sources_can_skip_existing_source_refresh(monkeypatch):
    calls = []
    writes = {}

    monkeypatch.setattr(sync, "notebooklm_auth_status", lambda: {"available": True, "status": "ready"})
    monkeypatch.setattr(sync, "resolve_notebook", lambda previous: ("notebook-1", {"action": "used_existing"}))
    monkeypatch.setattr(
        sync,
        "existing_source_titles",
        lambda notebook_id: {"Mighty Skill-Bridge docs/docs/example.md": "source-1"},
    )

    def fake_run_notebooklm(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")

    monkeypatch.setattr(sync, "run_notebooklm", fake_run_notebooklm)
    monkeypatch.setattr(sync, "write_text", lambda path, text: writes.__setitem__(path, text))
    monkeypatch.setattr(sync, "write_json", lambda path, payload: writes.__setitem__(path, payload))

    result = sync.sync_notebooklm_sources(
        {"doc": {"name": "Mighty Skill-Bridge docs/docs/example.md", "id": "drive-1"}},
        {},
        run_asks=False,
        refresh_existing_sources=False,
    )

    assert result["source_results"][0]["action"] == "skipped_existing_refresh"
    assert result["source_sync"]["refresh_existing_sources"] is False
    assert not any(call[:2] == ["source", "refresh"] for call in calls)


def test_resolve_notebook_reuses_existing_title_before_create(monkeypatch):
    calls = []

    def fake_run_notebooklm(args, **kwargs):
        calls.append(args)
        if args == ["list", "--json"]:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "notebooks": [
                            {
                                "id": "existing-notebook",
                                "title": sync.NOTEBOOK_TITLE,
                                "index": 1,
                            }
                        ]
                    }
                ),
                stderr="",
            )
        if args == ["use", "existing-notebook"]:
            return subprocess.CompletedProcess(args, 0, stdout="using existing", stderr="")
        raise AssertionError(f"unexpected notebooklm call: {args}")

    monkeypatch.setattr(sync, "run_notebooklm", fake_run_notebooklm)

    notebook_id, info = sync.resolve_notebook({})

    assert notebook_id == "existing-notebook"
    assert info["action"] == "used_title_match"
    assert ["create", sync.NOTEBOOK_TITLE, "--json"] not in calls
