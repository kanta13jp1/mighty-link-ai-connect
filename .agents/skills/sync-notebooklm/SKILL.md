---
name: sync-notebooklm
description: Synchronize documentation from docs/ to Google Drive, NotebookLM sources, and generate CEO presentation deck PPTX.
triggers:
  - "sync notebooklm"
  - "sync drive"
  - "sync docs to drive"
  - "generate presentation"
license: Apache-2.0
metadata:
  version: v2
  publisher: mighty-link
---

# Sync NotebookLM & Presentation Deck Generation Skill

Use this skill when documentation under `docs/` has been created or updated, or when fresh CEO presentation decks need to be compiled and uploaded to Google Drive.

---

## 1. Execution Commands (PowerShell)

### Fast Document Sync (Drive & Manifest Only)
```powershell
python scripts/sync_docs_to_notebooklm.py --drive-only
```

### Deterministic Sync (Skip Long Q&A Generation)
```powershell
python scripts/sync_docs_to_notebooklm.py --skip-asks --skip-source-refresh --source-timeout-seconds 60
```

### Presentation Deck Compilation & Upload
Run these commands after doc sync when presentation decks need updating:

```powershell
# Generate CEO Presentation Deck (PPTX)
python scripts/generate_ceo_presentation_deck.py

# Upload generated docs and slides to Google Drive
python scripts/upload_notebooklm_docs_to_drive.py
```

---

## 2. Key Manifest & Output Locations

- **Docs Manifest**: `exports/knowledge_flow/notebooklm_docs_manifest.json`
- **Presentation Deck**: `exports/presentation/ceo_deck_latest.pptx`
- **Target Drive Folder**: Managed automatically via Google OAuth token (`k-umezawa@ml-mightylink.com`).
