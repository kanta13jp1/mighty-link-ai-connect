---
name: sync-wbs
description: Comprehensive session closeout and WBS synchronization to GitHub Issues/Projects, Google Sheets, and Google Calendar.
triggers:
  - "sync wbs"
  - "sync sheets"
  - "sync calendar"
  - "session closeout"
license: Apache-2.0
metadata:
  version: v2
  publisher: mighty-link
---

# Sync WBS & Session Closeout Skill

Use this skill to execute the required session closeout flow: run preflight checks, regenerate demo flows, synchronize updated WBS tasks to GitHub Issues/Project #1, and sync status to Google Sheets and Google Calendar.

---

## 1. Required Session Closeout Workflow

Execute the following commands sequentially in the PowerShell terminal:

### Step 1: Preflight Integrity Check (Mandatory First)
```powershell
python scripts/run_lane_preflight.py --full
```
*Never commit or sync if the working tree fails preflight.*

### Step 2: Knowledge Flow & Demo Generation
```powershell
python scripts/generate_knowledge_flow_demo.py
```

### Step 3: Targeted WBS Synchronization
Replace `TXXX` with every WBS task completed or materially updated during the session (e.g. `T301`, `T302`):

```powershell
# Dry run first to verify issue mapping
python scripts/sync_wbs_to_github.py TXXX --dry-run

# Commit sync to GitHub Issues & Project
python scripts/sync_wbs_to_github.py TXXX --report exports/github_wbs_sync_report.json

# Sync to Google Sheets (課題管理表 & QA表)
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8

# Sync to Google Calendar (Completed tasks are deleted automatically)
python scripts/sync_wbs_to_calendar.py
```

---

## 2. Authentication & Environment Pre-requisites

- **Google Workspace**: `k-umezawa@ml-mightylink.com` OAuth token must be active. Run `python scripts/verify_google_workspace_account.py` if authentication fails.
- **GitHub CLI**: `gh auth status` must show active authentication for issue/project manipulation.
- **WBS Source of Truth**: Always edit `data/WBS.tsv` before running sync commands.
