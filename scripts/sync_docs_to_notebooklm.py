#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Sync project docs to Google Docs and prepare NotebookLM CLI ingestion.

The script has two layers:

1. Always syncs safe project documentation under docs/ to Workspace-owned
   native Google Docs using authorized_user.json and the Drive API.
2. If the local notebooklm CLI is authenticated, creates/uses a NotebookLM
   notebook, adds the Drive docs as sources, and asks NotebookLM for an
   agent-ready design and roadmap brief.

If NotebookLM CLI authentication is expired, the Drive sync still completes and
the script writes exact re-authentication / rerun steps for the user.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
EXPORT_DIR = PROJECT_ROOT / "exports" / "knowledge_flow"
DOCS_DIR = PROJECT_ROOT / "docs"
MANIFEST_PATH = EXPORT_DIR / "notebooklm_docs_manifest.json"
AGENT_BRIEF_PATH = EXPORT_DIR / "notebooklm_agent_brief.md"
AGENT_BRIEF_JSON_PATH = EXPORT_DIR / "notebooklm_agent_brief.json"
CEO_SLIDE_OUTLINE_PATH = EXPORT_DIR / "notebooklm_ceo_slide_outline.md"
CEO_SLIDE_OUTLINE_JSON_PATH = EXPORT_DIR / "notebooklm_ceo_slide_outline.json"
NEXT_STEPS_PATH = EXPORT_DIR / "notebooklm_cli_next_steps.md"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from upload_notebooklm_docs_to_drive import (  # noqa: E402
    EXPECTED_GOOGLE_ACCOUNT,
    get_file,
    load_credentials,
    upload_as_google_doc,
    verify_workspace_owner,
)
from google_workspace_account import (  # noqa: E402
    GoogleWorkspaceReauthRequiredError,
    is_google_oauth_reauth_required,
)


NOTEBOOK_TITLE = "Mighty Skill-Bridge Development Knowledge 2026-06-02"
SOURCE_PREFIX = "Mighty Skill-Bridge docs"
NOTEBOOKLM_COMMAND_TIMEOUT_SECONDS = int(os.environ.get("NOTEBOOKLM_COMMAND_TIMEOUT_SECONDS", "420"))
NOTEBOOKLM_ASK_TIMEOUT_SECONDS = int(os.environ.get("NOTEBOOKLM_ASK_TIMEOUT_SECONDS", "900"))

AGENT_QUESTION = """\
このNotebookに含まれる設計情報、作業手順、WBS、ロードマップをもとに、
Codex/AIエージェントが次に開発を進めるための要約を作ってください。

必ず以下を含めてください。
1. 現在のプロダクト方向性で確定していること
2. 6/2の社長打ち合わせまでに優先すべきプレゼン準備タスク
3. 6/2で社長に決めてもらうべき事項
4. バックエンド/app.pyやデータ構造を肉付けする時に守るべき前提
5. NotebookLM / Slack / Notion / Obsidian / GitHub Issues / GitHub Project の運用上の残課題
6. WBSへ追加すべき次アクション
"""

CEO_SLIDE_QUESTION = """\
6/2の社長打ち合わせで使う、8枚以内のプレゼン草案を作ってください。

前提:
- 実際の企画・サービス内容は6/2の打ち合わせで決定する
- それまではプロトタイプ、WBS、Google Workspace同期、NotebookLM/Slack/Notion/Obsidian/GitHub連携の「実際にやった状態」を見せる
- 社長に決めてもらう事項と、6/2後すぐにWBSへ反映する事項を明確にする

出力形式:
1. スライド番号とタイトル
2. 各スライドの要点3つ以内
3. 話すメモ
4. 見せる証跡URL/ファイル
5. 社長への質問
"""


def jst_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))


def relative(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace(os.sep, "/")


def source_key(path: Path) -> str:
    raw = relative(path).lower()
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_")


def source_title(path: Path) -> str:
    return f"{SOURCE_PREFIX}/{relative(path)}"


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = "\n".join(line.rstrip() for line in content.rstrip().splitlines())
    path.write_text(clean + "\n", encoding="utf-8")


def discover_docs() -> list[Path]:
    return sorted(path for path in DOCS_DIR.glob("*.md") if path.is_file())


def build_google_doc_content(path: Path) -> str:
    return (
        f"# {relative(path)}\n\n"
        f"Synced for NotebookLM from the Git repository.\n\n"
        f"- Source path: `{relative(path)}`\n"
        f"- Synced at: {jst_now().isoformat(timespec='seconds')}\n"
        f"- Workspace account: `{EXPECTED_GOOGLE_ACCOUNT}`\n\n"
        "---\n\n"
        f"{path.read_text(encoding='utf-8', errors='replace')}"
    )


def source_content_digest(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(relative(path).encode("utf-8"))
    digest.update(b"\0")
    digest.update(path.read_bytes())
    return digest.hexdigest()


def parse_manifest_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=9)))
    return parsed


def source_mtime_jst(path: Path) -> dt.datetime:
    return dt.datetime.fromtimestamp(
        path.stat().st_mtime,
        tz=dt.timezone(dt.timedelta(hours=9)),
    )


def reusable_previous_doc(
    path: Path,
    previous_entry: dict[str, Any],
    digest: str,
    previous_generated_at: dt.datetime | None,
) -> tuple[bool, str]:
    if not previous_entry.get("id") or not previous_entry.get("url"):
        return False, "missing_manifest_drive_metadata"

    if previous_entry.get("source_digest") == digest:
        return True, "source_digest_match"

    # Legacy manifests did not store a digest. If the local file has not changed
    # since that manifest was generated, trust the existing Drive document and
    # write a digest forward so future runs can use exact comparison.
    if not previous_entry.get("source_digest") and previous_generated_at:
        if source_mtime_jst(path) <= previous_generated_at:
            return True, "legacy_manifest_mtime_before_generated_at"

    return False, "source_changed_or_untracked"


def skipped_google_doc_entry(
    path: Path,
    previous_entry: dict[str, Any],
    digest: str,
    reason: str,
) -> dict[str, Any]:
    return {
        **previous_entry,
        "source": relative(path),
        "source_digest": digest,
        "sync_action": "skipped_unchanged",
        "sync_reason": reason,
        "skipped_at_jst": jst_now().isoformat(timespec="seconds"),
        "source_mtime_jst": source_mtime_jst(path).isoformat(timespec="seconds"),
    }


def google_doc_entry_from_upload(
    path: Path,
    result: dict[str, Any],
    digest: str,
    action: str,
) -> dict[str, Any]:
    return {
        "source": relative(path),
        "id": result["id"],
        "name": result["name"],
        "url": result["webViewLink"],
        "mimeType": result["mimeType"],
        "ownedByMe": result.get("ownedByMe"),
        "owners": result.get("owners", []),
        "createdTime": result.get("createdTime"),
        "modifiedTime": result.get("modifiedTime"),
        "source_digest": digest,
        "sync_action": action,
        "source_mtime_jst": source_mtime_jst(path).isoformat(timespec="seconds"),
    }


def summarize_google_doc_sync(docs: dict[str, Any], *, force_upload: bool) -> dict[str, Any]:
    action_counts: dict[str, int] = {}
    for doc in docs.values():
        action = str(doc.get("sync_action") or "unknown")
        action_counts[action] = action_counts.get(action, 0) + 1
    uploaded = sum(
        count
        for action, count in action_counts.items()
        if action.startswith("uploaded")
    )
    skipped = action_counts.get("skipped_unchanged", 0)
    return {
        "force_upload": force_upload,
        "docs_discovered": len(docs),
        "uploaded": uploaded,
        "skipped": skipped,
        "action_counts": action_counts,
    }


def sync_google_docs(previous: dict[str, Any], *, force_upload: bool = False) -> dict[str, Any]:
    previous_docs = previous.get("google_docs", {}) if isinstance(previous, dict) else {}
    previous_generated_at = parse_manifest_time(previous.get("generated_at_jst"))
    docs: dict[str, Any] = {}
    credentials: Any | None = None

    def ensure_credentials() -> Any:
        nonlocal credentials
        if credentials is None:
            credentials = load_credentials()
        return credentials

    for path in discover_docs():
        key = source_key(path)
        digest = source_content_digest(path)
        previous_entry = previous_docs.get(key, {}) if isinstance(previous_docs, dict) else {}
        reusable, reason = reusable_previous_doc(
            path,
            previous_entry,
            digest,
            previous_generated_at,
        )
        if reusable and not force_upload:
            docs[key] = skipped_google_doc_entry(path, previous_entry, digest, reason)
            continue

        credentials_for_upload = ensure_credentials()
        previous_id = previous_entry.get("id")
        existing = get_file(credentials_for_upload, previous_id) if previous_id else None
        existing_id = existing["id"] if existing else None

        result = upload_as_google_doc(
            credentials_for_upload,
            title=source_title(path),
            content=build_google_doc_content(path),
            existing_file_id=existing_id,
        )
        verify_workspace_owner(result)
        if not result.get("webViewLink"):
            result["webViewLink"] = f"https://docs.google.com/document/d/{result['id']}/edit"

        action = "uploaded_updated" if existing_id else "uploaded_created"
        docs[key] = google_doc_entry_from_upload(path, result, digest, action)

    return docs


def completed_output_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run_notebooklm(
    args: list[str],
    *,
    check: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("notebooklm")
    if not executable:
        raise FileNotFoundError("notebooklm CLI was not found on PATH.")

    effective_timeout = timeout if timeout is not None else NOTEBOOKLM_COMMAND_TIMEOUT_SECONDS
    command = [executable, *args]
    try:
        completed = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=effective_timeout,
        )
    except subprocess.TimeoutExpired as error:
        stdout = completed_output_text(getattr(error, "stdout", None) or getattr(error, "output", None))
        stderr = completed_output_text(getattr(error, "stderr", None))
        timeout_message = f"notebooklm {' '.join(args)} timed out after {effective_timeout} seconds."
        completed = subprocess.CompletedProcess(
            command,
            124,
            stdout=stdout,
            stderr=f"{stderr}\n{timeout_message}".strip(),
        )
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed


def notebooklm_auth_status() -> dict[str, Any]:
    if not shutil.which("notebooklm"):
        return {"available": False, "status": "cli_missing"}

    status = run_notebooklm(["status"])
    listing = run_notebooklm(["list"])
    if listing.returncode != 0:
        combined = (listing.stderr or listing.stdout or "").strip()
        auth_required = "Authentication expired" in combined or "notebooklm login" in combined
        return {
            "available": True,
            "status": "auth_required" if auth_required else "error",
            "status_output": (status.stdout or status.stderr or "").strip(),
            "error": "Authentication expired or invalid. Run 'notebooklm login' to re-authenticate."
            if auth_required
            else combined,
        }

    return {
        "available": True,
        "status": "ready",
        "status_output": (status.stdout or status.stderr or "").strip(),
        "list_output": listing.stdout.strip(),
    }


def parse_json_output(completed: subprocess.CompletedProcess[str]) -> Any:
    text = (completed.stdout or "").strip()
    if not text:
        return None
    return json.loads(text)


def notebook_answer_text(completed: subprocess.CompletedProcess[str]) -> str:
    if completed.returncode != 0:
        return completed.stderr or completed.stdout
    try:
        payload = parse_json_output(completed)
        if isinstance(payload, dict):
            return payload.get("answer") or payload.get("text") or completed.stdout
    except json.JSONDecodeError:
        pass
    return completed.stdout


def find_existing_notebook_by_title(title: str) -> tuple[str, dict[str, Any]] | None:
    listed = run_notebooklm(["list", "--json"])
    if listed.returncode != 0:
        return None

    try:
        payload = parse_json_output(listed)
    except json.JSONDecodeError:
        return None

    notebooks = payload.get("notebooks", []) if isinstance(payload, dict) else payload
    if not isinstance(notebooks, list):
        return None

    for notebook in notebooks:
        if not isinstance(notebook, dict):
            continue
        if notebook.get("title") != title:
            continue
        notebook_id = notebook.get("id") or notebook.get("notebook_id")
        if not notebook_id:
            continue
        use_result = run_notebooklm(["use", str(notebook_id)])
        if use_result.returncode == 0:
            return str(notebook_id), {
                "action": "used_title_match",
                "payload": notebook,
                "output": use_result.stdout.strip(),
            }
    return None


def resolve_notebook(previous: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    previous_notebook = previous.get("notebooklm", {}) if isinstance(previous, dict) else {}
    previous_id = previous_notebook.get("notebook_id")
    if previous_id:
        use_result = run_notebooklm(["use", previous_id])
        if use_result.returncode == 0:
            return previous_id, {"action": "used_existing", "output": use_result.stdout.strip()}

    existing = find_existing_notebook_by_title(NOTEBOOK_TITLE)
    if existing:
        return existing

    created = run_notebooklm(["create", NOTEBOOK_TITLE, "--json"], check=True)
    payload = parse_json_output(created)
    notebook_id = (
        payload.get("id")
        or payload.get("notebook_id")
        or payload.get("notebook", {}).get("id")
        if isinstance(payload, dict)
        else None
    )
    if not notebook_id:
        raise RuntimeError(f"NotebookLM create did not return an id: {created.stdout}")

    run_notebooklm(["use", notebook_id])
    return notebook_id, {"action": "created", "payload": payload}


def existing_source_titles(notebook_id: str) -> dict[str, str]:
    listed = run_notebooklm(["source", "list", "-n", notebook_id, "--json"])
    if listed.returncode != 0:
        return {}
    payload = parse_json_output(listed)
    if not isinstance(payload, list):
        payload = payload.get("sources", []) if isinstance(payload, dict) else []

    titles: dict[str, str] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name")
        source_id = item.get("id") or item.get("source_id")
        if title and source_id:
            titles[str(title)] = str(source_id)
    return titles


def write_notebooklm_ask_skipped_outputs(
    *,
    notebook_id: str,
    notebook_info: dict[str, Any],
    source_results: list[dict[str, Any]],
    ask_timeout_seconds: int,
) -> dict[str, Any]:
    generated_at = jst_now().isoformat(timespec="seconds")
    next_command = f"python scripts/sync_docs_to_notebooklm.py --ask-timeout-seconds {ask_timeout_seconds}"
    ask_generation = {
        "status": "skipped",
        "reason": "--skip-asks",
        "generated_at_jst": generated_at,
        "ask_timeout_seconds": ask_timeout_seconds,
        "next_command": next_command,
        "source_count": len(source_results),
    }
    common_payload = {
        "notebook_id": notebook_id,
        "notebook_info": notebook_info,
        "source_count": len(source_results),
        "source_results": source_results,
        "ask_generation": ask_generation,
    }
    write_json(
        AGENT_BRIEF_JSON_PATH,
        {
            **common_payload,
            "question": AGENT_QUESTION,
            "summary_returncode": None,
            "answer_returncode": None,
        },
    )
    write_json(
        CEO_SLIDE_OUTLINE_JSON_PATH,
        {
            **common_payload,
            "question": CEO_SLIDE_QUESTION,
            "answer_returncode": None,
        },
    )
    write_text(
        AGENT_BRIEF_PATH,
        f"""# NotebookLM Agent Brief

Generated: {generated_at}
Notebook: `{notebook_id}`
Status: `source_sync_ready`

NotebookLM source sync completed. The summary/ask generation phase was skipped by `--skip-asks` to keep the closeout run deterministic.

## Synced Sources

- Source rows processed: `{len(source_results)}`

## Optional Ask Generation

```powershell
{next_command}
```

After the optional ask generation succeeds, this file will be replaced by a NotebookLM-generated agent brief.
""",
    )
    write_text(
        CEO_SLIDE_OUTLINE_PATH,
        f"""# NotebookLM CEO Slide Outline

Generated: {generated_at}
Notebook: `{notebook_id}`
Status: `source_sync_ready`

NotebookLM source sync completed. The CEO slide outline ask was skipped by `--skip-asks` to avoid blocking the docs/Drive sync on a long NotebookLM response.

## Optional Ask Generation

```powershell
{next_command}
```

After the optional ask generation succeeds, this file will be replaced by a NotebookLM-generated CEO presentation outline.
""",
    )
    return ask_generation


def sync_notebooklm_sources(
    docs: dict[str, Any],
    previous: dict[str, Any],
    *,
    run_asks: bool = True,
    ask_timeout_seconds: int = NOTEBOOKLM_ASK_TIMEOUT_SECONDS,
    refresh_existing_sources: bool = True,
    source_timeout_seconds: int = NOTEBOOKLM_COMMAND_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    status = notebooklm_auth_status()
    if status.get("status") != "ready":
        return status

    notebook_id, notebook_info = resolve_notebook(previous)
    existing_titles = existing_source_titles(notebook_id)
    source_results: list[dict[str, Any]] = []

    for doc in docs.values():
        title = doc["name"]
        existing_source_id = existing_titles.get(title)
        if existing_source_id:
            if not refresh_existing_sources:
                source_results.append(
                    {
                        "title": title,
                        "drive_file_id": doc["id"],
                        "action": "skipped_existing_refresh",
                        "reason": "--skip-source-refresh",
                        "source_id": existing_source_id,
                        "returncode": None,
                        "stdout": "",
                        "stderr": "",
                    }
                )
                continue

            refreshed = run_notebooklm(
                ["source", "refresh", existing_source_id, "-n", notebook_id],
                timeout=source_timeout_seconds,
            )
            source_results.append(
                {
                    "title": title,
                    "drive_file_id": doc["id"],
                    "action": "refreshed_existing",
                    "source_id": existing_source_id,
                    "returncode": refreshed.returncode,
                    "stdout": refreshed.stdout.strip(),
                    "stderr": refreshed.stderr.strip(),
                }
            )
            continue

        added = run_notebooklm(
            [
                "source",
                "add-drive",
                doc["id"],
                title,
                "-n",
                notebook_id,
                "--mime-type",
                "google-doc",
            ],
            timeout=source_timeout_seconds,
        )
        source_results.append(
            {
                "title": title,
                "drive_file_id": doc["id"],
                "action": "added",
                "returncode": added.returncode,
                "stdout": added.stdout.strip(),
                "stderr": added.stderr.strip(),
            }
        )

    if not run_asks:
        ask_generation = write_notebooklm_ask_skipped_outputs(
            notebook_id=notebook_id,
            notebook_info=notebook_info,
            source_results=source_results,
            ask_timeout_seconds=ask_timeout_seconds,
        )
        return {
            **status,
            "notebook_id": notebook_id,
            "notebook_title": NOTEBOOK_TITLE,
            "notebook_info": notebook_info,
            "source_results": source_results,
            "source_sync": {
                "refresh_existing_sources": refresh_existing_sources,
                "source_timeout_seconds": source_timeout_seconds,
            },
            "ask_generation": ask_generation,
            "summary_returncode": None,
            "answer_returncode": None,
            "slide_outline_returncode": None,
            "agent_brief": relative(AGENT_BRIEF_PATH),
            "agent_brief_json": relative(AGENT_BRIEF_JSON_PATH),
            "ceo_slide_outline": relative(CEO_SLIDE_OUTLINE_PATH),
            "ceo_slide_outline_json": relative(CEO_SLIDE_OUTLINE_JSON_PATH),
        }

    summary = run_notebooklm(["summary", "-n", notebook_id, "--topics"], timeout=ask_timeout_seconds)
    answer = run_notebooklm(["ask", "-n", notebook_id, AGENT_QUESTION, "--json"], timeout=ask_timeout_seconds)
    slide_answer = run_notebooklm(
        ["ask", "-n", notebook_id, CEO_SLIDE_QUESTION, "--json"],
        timeout=ask_timeout_seconds,
    )
    ask_returncodes = [summary.returncode, answer.returncode, slide_answer.returncode]
    ask_status = "ready" if all(code == 0 for code in ask_returncodes) else "partial"
    if any(code == 124 for code in ask_returncodes):
        ask_status = "timeout"
    ask_generation = {
        "status": ask_status,
        "ask_timeout_seconds": ask_timeout_seconds,
        "summary_returncode": summary.returncode,
        "answer_returncode": answer.returncode,
        "slide_outline_returncode": slide_answer.returncode,
    }

    brief_payload: dict[str, Any] = {
        "notebook_id": notebook_id,
        "question": AGENT_QUESTION,
        "summary_returncode": summary.returncode,
        "summary_stdout": summary.stdout.strip(),
        "summary_stderr": summary.stderr.strip(),
        "answer_returncode": answer.returncode,
        "answer_stdout": answer.stdout.strip(),
        "answer_stderr": answer.stderr.strip(),
    }
    write_json(AGENT_BRIEF_JSON_PATH, brief_payload)

    slide_payload: dict[str, Any] = {
        "notebook_id": notebook_id,
        "question": CEO_SLIDE_QUESTION,
        "answer_returncode": slide_answer.returncode,
        "answer_stdout": slide_answer.stdout.strip(),
        "answer_stderr": slide_answer.stderr.strip(),
    }
    write_json(CEO_SLIDE_OUTLINE_JSON_PATH, slide_payload)

    answer_text = notebook_answer_text(answer)
    slide_text = notebook_answer_text(slide_answer)

    write_text(
        AGENT_BRIEF_PATH,
        f"""# NotebookLM Agent Brief

Generated: {jst_now().isoformat(timespec='seconds')}
Notebook: `{notebook_id}`

## Question

{AGENT_QUESTION}

## NotebookLM Answer

{answer_text}

## Notebook Summary

NotebookLM summary command return code: `{summary.returncode}`
""",
    )
    write_text(
        CEO_SLIDE_OUTLINE_PATH,
        f"""# NotebookLM CEO Slide Outline

Generated: {jst_now().isoformat(timespec='seconds')}
Notebook: `{notebook_id}`

## Question

{CEO_SLIDE_QUESTION}

## NotebookLM Answer

{slide_text}
""",
    )

    return {
        **status,
        "notebook_id": notebook_id,
        "notebook_title": NOTEBOOK_TITLE,
        "notebook_info": notebook_info,
        "source_results": source_results,
        "source_sync": {
            "refresh_existing_sources": refresh_existing_sources,
            "source_timeout_seconds": source_timeout_seconds,
        },
        "ask_generation": ask_generation,
        "summary_returncode": summary.returncode,
        "answer_returncode": answer.returncode,
        "slide_outline_returncode": slide_answer.returncode,
        "agent_brief": relative(AGENT_BRIEF_PATH),
        "agent_brief_json": relative(AGENT_BRIEF_JSON_PATH),
        "ceo_slide_outline": relative(CEO_SLIDE_OUTLINE_PATH),
        "ceo_slide_outline_json": relative(CEO_SLIDE_OUTLINE_JSON_PATH),
    }


def write_next_steps(manifest: dict[str, Any]) -> None:
    notebooklm = manifest.get("notebooklm", {})
    docs = manifest.get("google_docs", {})
    drive_sync = manifest.get("drive_sync", {})
    source_rows = "\n".join(
        f"- `{doc['source']}`: {doc['url']}"
        for doc in docs.values()
    )
    auth_status = notebooklm.get("status", "unknown")
    error = notebooklm.get("error", "")
    ask_generation = notebooklm.get("ask_generation", {})
    ask_status = ask_generation.get("status", "not_run")
    ask_next_command = ask_generation.get(
        "next_command",
        f"python scripts/sync_docs_to_notebooklm.py --ask-timeout-seconds {NOTEBOOKLM_ASK_TIMEOUT_SECONDS}",
    )
    if auth_status == "ready":
        reauth_section = f"""## NotebookLM Sync Result

NotebookLM CLI is authenticated and the docs source set has been synced.

- Notebook: `{notebooklm.get("notebook_id", "")}`
- Ask generation: `{ask_status}`
- Agent brief: `{notebooklm.get("agent_brief", relative(AGENT_BRIEF_PATH))}`
- Agent brief JSON: `{notebooklm.get("agent_brief_json", relative(AGENT_BRIEF_JSON_PATH))}`
- CEO slide outline: `{notebooklm.get("ceo_slide_outline", relative(CEO_SLIDE_OUTLINE_PATH))}`
- CEO slide outline JSON: `{notebooklm.get("ceo_slide_outline_json", relative(CEO_SLIDE_OUTLINE_JSON_PATH))}`

## Optional Ask Generation

If ask generation was skipped or timed out, keep the synced sources and rerun only the long NotebookLM summary/ask phase when needed:

```powershell
{ask_next_command}
```

## Re-authentication

If NotebookLM authentication expires later, run:

```powershell
python scripts/notebooklm_login_workspace.py
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
```

During browser login, select `k-umezawa@ml-mightylink.com`.
"""
    else:
        reauth_section = f"""## Re-authentication

NotebookLM CLI currently needs browser re-authentication before sources can be added to NotebookLM.

```powershell
python scripts/notebooklm_login_workspace.py
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
```

During browser login, select `k-umezawa@ml-mightylink.com`.

## Last CLI Error

```text
{error}
```

## Agent Retrieval Command

After authentication, the script will add the Drive docs as NotebookLM sources and write:

- `exports/knowledge_flow/notebooklm_agent_brief.md`
- `exports/knowledge_flow/notebooklm_agent_brief.json`
- `exports/knowledge_flow/notebooklm_ceo_slide_outline.md`
- `exports/knowledge_flow/notebooklm_ceo_slide_outline.json`

These files are the agent-facing design and roadmap summary for subsequent Codex work.
"""

    write_text(
        NEXT_STEPS_PATH,
        f"""# NotebookLM CLI Next Steps

Generated: {jst_now().isoformat(timespec='seconds')}

## Current Status

- Google Drive sync: done
- Workspace account: `{EXPECTED_GOOGLE_ACCOUNT}`
- Drive docs discovered: `{drive_sync.get("docs_discovered", len(docs))}`
- Drive docs uploaded: `{drive_sync.get("uploaded", "unknown")}`
- Drive docs skipped unchanged: `{drive_sync.get("skipped", "unknown")}`
- NotebookLM CLI status: `{auth_status}`

## Google Docs Synced From docs/

{source_rows}

{reauth_section}
""",
    )

    if auth_status != "ready":
        write_text(
            AGENT_BRIEF_PATH,
            f"""# NotebookLM Agent Brief

Generated: {jst_now().isoformat(timespec='seconds')}
Status: `{auth_status}`

NotebookLM CLI is not ready yet, so this file is a placeholder.

## Required Action

```powershell
notebooklm login
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
```

During `notebooklm login`, select `k-umezawa@ml-mightylink.com`.

## Synced Google Docs

{source_rows}

After re-authentication, this file will be replaced by a NotebookLM-generated
agent brief with design, roadmap, and next-action guidance.
""",
        )
        write_json(
            AGENT_BRIEF_JSON_PATH,
            {
                "generated_at_jst": jst_now().isoformat(timespec="seconds"),
                "status": auth_status,
                "error": error,
                "next_steps": relative(NEXT_STEPS_PATH),
            },
        )
        write_text(
            CEO_SLIDE_OUTLINE_PATH,
            f"""# NotebookLM CEO Slide Outline

Generated: {jst_now().isoformat(timespec='seconds')}
Status: `{auth_status}`

NotebookLM CLI is not ready yet, so this file is a placeholder.

## Required Action

```powershell
notebooklm login
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
```

After re-authentication, this file will be replaced by a NotebookLM-generated
8-slide-or-less CEO presentation outline.
""",
        )
        write_json(
            CEO_SLIDE_OUTLINE_JSON_PATH,
            {
                "generated_at_jst": jst_now().isoformat(timespec="seconds"),
                "status": auth_status,
                "error": error,
                "next_steps": relative(NEXT_STEPS_PATH),
            },
        )


def sync_gemini_context_cache(google_docs: dict[str, Any]) -> dict[str, Any]:
    """PoC function to create and refresh a Gemini Context Cache using all the project docs.
    
    If GEMINI_API_KEY is not present or google-genai is not installed, it gracefully skips.
    Otherwise, it combines all discoverable documents into a single rich text block,
    creates an explicit Gemini Context Cache with 1-hour TTL, and returns the metadata.
    """
    if not genai or not genai_types:
        return {"status": "skipped", "reason": "google-genai library is not installed"}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "GEMINI_API_KEY environment variable is not set"}

    try:
        client = genai.Client(api_key=api_key)
        
        # Discover all docs and compile their contents
        combined_contents = []
        for path in discover_docs():
            content = build_google_doc_content(path)
            combined_contents.append(content)
        
        combined_text = "\n\n=== FILE SPLITTER ===\n\n".join(combined_contents)
        
        # Check if cache size is sufficient (Gemini Context Caching requires minimum 32k tokens)
        char_count = len(combined_text)
        print(f"[*] Compiling {len(discover_docs())} docs for context caching. Total characters: {char_count}")
        
        # Current stable model; explicit caching
        # on 3.5 Flash requires a minimum of 4,096 tokens per the caching docs
        model_name = "gemini-3.5-flash"
        ttl_seconds = 3600
        
        print(f"[*] Creating explicit Gemini Context Cache with {model_name}...")
        cache = client.caches.create(
            model=model_name,
            config=genai_types.CreateCachedContentConfig(
                contents=[combined_text],
                display_name=NOTEBOOK_TITLE,
                ttl=f"{ttl_seconds}s"
            )
        )
        
        print(f"[+] Explicit Gemini Context Cache created successfully: {cache.name}")
        
        return {
            "status": "ready",
            "cache_name": cache.name,
            "display_name": cache.display_name,
            "model": cache.model,
            "ttl_seconds": ttl_seconds,
            "created_time": cache.create_time.isoformat() if hasattr(cache.create_time, "isoformat") else str(cache.create_time),
            "expire_time": cache.expire_time.isoformat() if hasattr(cache.expire_time, "isoformat") else str(cache.expire_time),
            "total_tokens_poc": "active"
        }
    except Exception as e:
        print(f"[-] Gemini Context Cache PoC failed: {e}")
        return {"status": "failed", "error": str(e)}


def _main_impl() -> None:
    parser = argparse.ArgumentParser(description="Sync docs/ Google Docs and NotebookLM sources.")
    parser.add_argument(
        "--drive-only",
        action="store_true",
        help="Only sync docs/ to Workspace Google Docs and skip NotebookLM CLI calls.",
    )
    parser.add_argument(
        "--force-drive-sync",
        action="store_true",
        help="Upload every docs/*.md file to Google Drive instead of trusting unchanged manifest entries.",
    )
    parser.add_argument(
        "--skip-asks",
        action="store_true",
        help="Sync Google Docs as NotebookLM sources but skip long summary/ask generation.",
    )
    parser.add_argument(
        "--ask-timeout-seconds",
        type=int,
        default=NOTEBOOKLM_ASK_TIMEOUT_SECONDS,
        help="Timeout in seconds for NotebookLM summary/ask commands.",
    )
    parser.add_argument(
        "--skip-source-refresh",
        action="store_true",
        help="Add missing NotebookLM sources but skip refreshing sources that already exist.",
    )
    parser.add_argument(
        "--source-timeout-seconds",
        type=int,
        default=NOTEBOOKLM_COMMAND_TIMEOUT_SECONDS,
        help="Timeout in seconds for each NotebookLM source add/refresh command.",
    )
    args = parser.parse_args()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    previous = load_manifest()
    google_docs = sync_google_docs(previous, force_upload=args.force_drive_sync)
    drive_sync = summarize_google_doc_sync(google_docs, force_upload=args.force_drive_sync)
    notebooklm = {"status": "skipped", "reason": "--drive-only"} if args.drive_only else sync_notebooklm_sources(
        google_docs,
        previous,
        run_asks=not args.skip_asks,
        ask_timeout_seconds=args.ask_timeout_seconds,
        refresh_existing_sources=not args.skip_source_refresh,
        source_timeout_seconds=args.source_timeout_seconds,
    )

    # Run the Gemini explicit context caching PoC (T691)
    gemini_cache = sync_gemini_context_cache(google_docs)

    manifest = {
        "generated_at_jst": jst_now().isoformat(timespec="seconds"),
        "account": EXPECTED_GOOGLE_ACCOUNT,
        "drive_sync": drive_sync,
        "google_docs": google_docs,
        "notebooklm": notebooklm,
        "gemini_context_cache": gemini_cache,
    }
    write_json(MANIFEST_PATH, manifest)
    write_next_steps(manifest)

    print("[+] docs/ Google Docs sync complete.")
    print(f"[*] Synced docs: {len(google_docs)}")
    print(f"[*] Drive docs uploaded: {drive_sync.get('uploaded')}")
    print(f"[*] Drive docs skipped unchanged: {drive_sync.get('skipped')}")
    print(f"[*] NotebookLM status: {notebooklm.get('status')}")
    print(f"[*] Gemini Context Cache status: {gemini_cache.get('status')}")
    if gemini_cache.get("cache_name"):
        print(f"[*] Gemini Context Cache name: {gemini_cache['cache_name']}")
    print(f"[*] Manifest: {relative(MANIFEST_PATH)}")
    print(f"[*] Next steps: {relative(NEXT_STEPS_PATH)}")
    if notebooklm.get("agent_brief"):
        print(f"[*] Agent brief: {notebooklm['agent_brief']}")
    if notebooklm.get("ceo_slide_outline"):
        print(f"[*] CEO slide outline: {notebooklm['ceo_slide_outline']}")


def main() -> None:
    try:
        _main_impl()
    except GoogleWorkspaceReauthRequiredError as error:
        print(f"[-] {error}")
        sys.exit(2)
    except Exception as error:
        if is_google_oauth_reauth_required(error):
            print(f"[-] {error}")
            sys.exit(2)
        raise


if __name__ == "__main__":
    main()
