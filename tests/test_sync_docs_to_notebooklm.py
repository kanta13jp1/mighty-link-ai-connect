import os
import json
import subprocess
import sys
import datetime as dt


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


def test_sync_google_docs_skips_unchanged_manifest_entries(tmp_path, monkeypatch):
    doc = tmp_path / "example.md"
    doc.write_text("# Example\n\nunchanged\n", encoding="utf-8")
    monkeypatch.setattr(sync, "DOCS_DIR", tmp_path)
    monkeypatch.setattr(sync, "discover_docs", lambda: [doc])
    monkeypatch.setattr(sync, "relative", lambda path: f"docs/{path.name}")
    monkeypatch.setattr(sync, "load_credentials", lambda: (_ for _ in ()).throw(AssertionError("no auth needed")))

    digest = sync.source_content_digest(doc)
    previous = {
        "generated_at_jst": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(),
        "google_docs": {
            "docs_example_md": {
                "source": "docs/example.md",
                "id": "drive-1",
                "name": "Mighty Skill-Bridge docs/docs/example.md",
                "url": "https://docs.google.com/document/d/drive-1/edit",
                "mimeType": "application/vnd.google-apps.document",
                "source_digest": digest,
            }
        },
    }

    docs = sync.sync_google_docs(previous)

    assert docs["docs_example_md"]["sync_action"] == "skipped_unchanged"
    assert docs["docs_example_md"]["sync_reason"] == "source_digest_match"
    summary = sync.summarize_google_doc_sync(docs, force_upload=False)
    assert summary["uploaded"] == 0
    assert summary["skipped"] == 1


def test_sync_google_docs_skips_legacy_manifest_when_mtime_is_old(tmp_path, monkeypatch):
    doc = tmp_path / "legacy.md"
    doc.write_text("# Legacy\n\nold content\n", encoding="utf-8")
    old_mtime = 1_700_000_000
    os.utime(doc, (old_mtime, old_mtime))
    monkeypatch.setattr(sync, "DOCS_DIR", tmp_path)
    monkeypatch.setattr(sync, "discover_docs", lambda: [doc])
    monkeypatch.setattr(sync, "relative", lambda path: f"docs/{path.name}")
    monkeypatch.setattr(sync, "load_credentials", lambda: (_ for _ in ()).throw(AssertionError("no auth needed")))

    generated_at = dt.datetime.fromtimestamp(
        old_mtime + 60,
        tz=dt.timezone(dt.timedelta(hours=9)),
    ).isoformat()
    previous = {
        "generated_at_jst": generated_at,
        "google_docs": {
            "docs_legacy_md": {
                "source": "docs/legacy.md",
                "id": "drive-legacy",
                "name": "Mighty Skill-Bridge docs/docs/legacy.md",
                "url": "https://docs.google.com/document/d/drive-legacy/edit",
                "mimeType": "application/vnd.google-apps.document",
            }
        },
    }

    docs = sync.sync_google_docs(previous)

    assert docs["docs_legacy_md"]["sync_action"] == "skipped_unchanged"
    assert docs["docs_legacy_md"]["sync_reason"] == "legacy_manifest_mtime_before_generated_at"
    assert docs["docs_legacy_md"]["source_digest"] == sync.source_content_digest(doc)


def test_sync_google_docs_uploads_changed_docs_and_force_uploads(tmp_path, monkeypatch):
    doc = tmp_path / "changed.md"
    doc.write_text("# Changed\n\nnew content\n", encoding="utf-8")
    monkeypatch.setattr(sync, "DOCS_DIR", tmp_path)
    monkeypatch.setattr(sync, "discover_docs", lambda: [doc])
    monkeypatch.setattr(sync, "relative", lambda path: f"docs/{path.name}")
    monkeypatch.setattr(sync, "load_credentials", lambda: "credentials")
    monkeypatch.setattr(sync, "get_file", lambda credentials, file_id: {"id": file_id})

    uploads = []

    def fake_upload_as_google_doc(credentials, *, title, content, existing_file_id):
        uploads.append(
            {
                "credentials": credentials,
                "title": title,
                "content": content,
                "existing_file_id": existing_file_id,
            }
        )
        return {
            "id": existing_file_id or "drive-created",
            "name": title,
            "webViewLink": "https://docs.google.com/document/d/drive-changed/edit",
            "mimeType": "application/vnd.google-apps.document",
            "ownedByMe": True,
            "owners": [{"emailAddress": sync.EXPECTED_GOOGLE_ACCOUNT}],
        }

    monkeypatch.setattr(sync, "upload_as_google_doc", fake_upload_as_google_doc)
    monkeypatch.setattr(sync, "verify_workspace_owner", lambda result: None)

    previous = {
        "generated_at_jst": "2026-06-21T00:00:00+09:00",
        "google_docs": {
            "docs_changed_md": {
                "source": "docs/changed.md",
                "id": "drive-existing",
                "name": "Mighty Skill-Bridge docs/docs/changed.md",
                "url": "https://docs.google.com/document/d/drive-existing/edit",
                "mimeType": "application/vnd.google-apps.document",
                "source_digest": "old-digest",
            }
        },
    }

    docs = sync.sync_google_docs(previous)

    assert uploads
    assert uploads[0]["credentials"] == "credentials"
    assert uploads[0]["existing_file_id"] == "drive-existing"
    assert docs["docs_changed_md"]["sync_action"] == "uploaded_updated"
    assert docs["docs_changed_md"]["source_digest"] == sync.source_content_digest(doc)
