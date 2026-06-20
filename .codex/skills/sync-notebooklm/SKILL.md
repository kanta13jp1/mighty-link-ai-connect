---
name: sync-notebooklm
description: Sync docs/ to Workspace Google Docs and Google Drive.
triggers:
  - "sync notebooklm"
  - "sync drive"
  - "sync docs to drive"
---

# Sync NotebookLM Skill

Use this skill when you need to upload and synchronize the project documents under `docs/` to Workspace Google Docs (Google Drive) for NotebookLM ingestion.

## Execution Steps

Run the following command in the PowerShell terminal:

```powershell
python scripts/sync_docs_to_notebooklm.py --drive-only
```

When NotebookLM CLI is authenticated and source ingestion should be updated
without waiting for long NotebookLM answer generation, run:

```powershell
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
```

Run the full ask generation only when the agent brief or CEO slide outline needs
fresh NotebookLM answers:

```powershell
python scripts/sync_docs_to_notebooklm.py --ask-timeout-seconds 900
```

## Expectations

- All `docs/*.md` files are parsed and uploaded to Google Drive.
- The manifest file `exports/knowledge_flow/notebooklm_docs_manifest.json` is updated.
- `--skip-asks` keeps NotebookLM source sync deterministic and writes explicit
  placeholders for the optional NotebookLM-generated brief files.
- `--skip-source-refresh` keeps closeout fast by adding missing sources but not
  forcing every existing source to refresh during the same session.
- Re-generation of the presentation deck PPTX and upload to Google Drive are triggered subsequently by running `scripts/generate_ceo_presentation_deck.py` and `scripts/upload_notebooklm_docs_to_drive.py`.
