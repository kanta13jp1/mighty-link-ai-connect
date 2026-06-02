---
name: sync-wbs
description: Synchronize WBS data from data/WBS.tsv to Google Sheets and Google Calendar.
triggers:
  - "sync wbs"
  - "sync sheets"
  - "sync calendar"
---

# Sync WBS Skill

Use this skill when you need to synchronize the WBS timeline, summary, task statuses, issues tracker, and QA tracker to Google Sheets and Google Calendar.

## Execution Steps

Run the following commands in the PowerShell terminal:

```powershell
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```

## Expectations

- Google Workspace authentication is executed via the `authorized_user.json` file for `k-umezawa@ml-mightylink.com`.
- WBS entries are synced. WBS tasks marked as completed (完了) are automatically deleted from Google Calendar.
