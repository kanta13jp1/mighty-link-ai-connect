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
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


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


NOTEBOOK_TITLE = "Mighty Skill-Bridge Development Knowledge 2026-06-02"
SOURCE_PREFIX = "Mighty Skill-Bridge docs"

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


def sync_google_docs(previous: dict[str, Any]) -> dict[str, Any]:
    credentials = load_credentials()
    previous_docs = previous.get("google_docs", {}) if isinstance(previous, dict) else {}
    docs: dict[str, Any] = {}

    for path in discover_docs():
        key = source_key(path)
        previous_id = previous_docs.get(key, {}).get("id")
        existing = get_file(credentials, previous_id) if previous_id else None
        existing_id = existing["id"] if existing else None

        result = upload_as_google_doc(
            credentials,
            title=source_title(path),
            content=build_google_doc_content(path),
            existing_file_id=existing_id,
        )
        verify_workspace_owner(result)
        if not result.get("webViewLink"):
            result["webViewLink"] = f"https://docs.google.com/document/d/{result['id']}/edit"

        docs[key] = {
            "source": relative(path),
            "id": result["id"],
            "name": result["name"],
            "url": result["webViewLink"],
            "mimeType": result["mimeType"],
            "ownedByMe": result.get("ownedByMe"),
            "owners": result.get("owners", []),
            "createdTime": result.get("createdTime"),
            "modifiedTime": result.get("modifiedTime"),
        }

    return docs


def run_notebooklm(args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("notebooklm")
    if not executable:
        raise FileNotFoundError("notebooklm CLI was not found on PATH.")

    completed = subprocess.run(
        [executable, *args],
        cwd=str(PROJECT_ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
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


def resolve_notebook(previous: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    previous_notebook = previous.get("notebooklm", {}) if isinstance(previous, dict) else {}
    previous_id = previous_notebook.get("notebook_id")
    if previous_id:
        use_result = run_notebooklm(["use", previous_id])
        if use_result.returncode == 0:
            return previous_id, {"action": "used_existing", "output": use_result.stdout.strip()}

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


def sync_notebooklm_sources(
    docs: dict[str, Any],
    previous: dict[str, Any],
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
            refreshed = run_notebooklm(["source", "refresh", existing_source_id, "-n", notebook_id])
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
            ]
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

    summary = run_notebooklm(["summary", "-n", notebook_id, "--topics"])
    answer = run_notebooklm(["ask", "-n", notebook_id, AGENT_QUESTION, "--json"])
    slide_answer = run_notebooklm(["ask", "-n", notebook_id, CEO_SLIDE_QUESTION, "--json"])

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
    source_rows = "\n".join(
        f"- `{doc['source']}`: {doc['url']}"
        for doc in docs.values()
    )
    auth_status = notebooklm.get("status", "unknown")
    error = notebooklm.get("error", "")
    if auth_status == "ready":
        reauth_section = f"""## NotebookLM Sync Result

NotebookLM CLI is authenticated and the docs source set has been synced.

- Notebook: `{notebooklm.get("notebook_id", "")}`
- Agent brief: `{notebooklm.get("agent_brief", relative(AGENT_BRIEF_PATH))}`
- Agent brief JSON: `{notebooklm.get("agent_brief_json", relative(AGENT_BRIEF_JSON_PATH))}`
- CEO slide outline: `{notebooklm.get("ceo_slide_outline", relative(CEO_SLIDE_OUTLINE_PATH))}`
- CEO slide outline JSON: `{notebooklm.get("ceo_slide_outline_json", relative(CEO_SLIDE_OUTLINE_JSON_PATH))}`

## Re-authentication

If NotebookLM authentication expires later, run:

```powershell
python scripts/notebooklm_login_workspace.py
python scripts/sync_docs_to_notebooklm.py
```

During browser login, select `k-umezawa@ml-mightylink.com`.
"""
    else:
        reauth_section = f"""## Re-authentication

NotebookLM CLI currently needs browser re-authentication before sources can be added to NotebookLM.

```powershell
python scripts/notebooklm_login_workspace.py
python scripts/sync_docs_to_notebooklm.py
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
python scripts/sync_docs_to_notebooklm.py
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
python scripts/sync_docs_to_notebooklm.py
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync docs/ Google Docs and NotebookLM sources.")
    parser.add_argument(
        "--drive-only",
        action="store_true",
        help="Only sync docs/ to Workspace Google Docs and skip NotebookLM CLI calls.",
    )
    args = parser.parse_args()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    previous = load_manifest()
    google_docs = sync_google_docs(previous)
    notebooklm = {"status": "skipped", "reason": "--drive-only"} if args.drive_only else sync_notebooklm_sources(
        google_docs,
        previous,
    )

    manifest = {
        "generated_at_jst": jst_now().isoformat(timespec="seconds"),
        "account": EXPECTED_GOOGLE_ACCOUNT,
        "google_docs": google_docs,
        "notebooklm": notebooklm,
    }
    write_json(MANIFEST_PATH, manifest)
    write_next_steps(manifest)

    print("[+] docs/ Google Docs sync complete.")
    print(f"[*] Synced docs: {len(google_docs)}")
    print(f"[*] NotebookLM status: {notebooklm.get('status')}")
    print(f"[*] Manifest: {relative(MANIFEST_PATH)}")
    print(f"[*] Next steps: {relative(NEXT_STEPS_PATH)}")
    if notebooklm.get("agent_brief"):
        print(f"[*] Agent brief: {notebooklm['agent_brief']}")
    if notebooklm.get("ceo_slide_outline"):
        print(f"[*] CEO slide outline: {notebooklm['ceo_slide_outline']}")


if __name__ == "__main__":
    main()
