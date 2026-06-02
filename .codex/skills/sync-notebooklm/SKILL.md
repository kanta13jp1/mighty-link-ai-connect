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

## Expectations

- All `docs/*.md` files are parsed and uploaded to Google Drive.
- The manifest file `exports/knowledge_flow/notebooklm_docs_manifest.json` is updated.
- Re-generation of the presentation deck PPTX and upload to Google Drive are triggered subsequently by running `scripts/generate_ceo_presentation_deck.py` and `scripts/upload_notebooklm_docs_to_drive.py`.
