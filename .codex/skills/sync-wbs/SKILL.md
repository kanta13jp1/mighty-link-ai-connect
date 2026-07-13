---
name: sync-wbs
description: Synchronize selected WBS data to GitHub Issues/Project, Google Sheets, and Google Calendar.
triggers:
  - "sync wbs"
  - "sync sheets"
  - "sync calendar"
---

# Sync WBS Skill

Use this skill when you need to synchronize selected WBS tasks to GitHub Issues/Project and synchronize the WBS timeline, summary, task statuses, issues tracker, and QA tracker to Google Sheets and Google Calendar.

## Execution Steps

Run the following commands in the PowerShell terminal:

```powershell
python scripts/sync_wbs_to_github.py TXXX --dry-run
python scripts/sync_wbs_to_github.py TXXX --report exports/github_wbs_sync_report.json
python scripts/sync_wbs_to_sheets.py 1L99HCBHr4IsVUWqnUuG6OgoUmxEQUdfaYQim1n6etB8
python scripts/sync_wbs_to_calendar.py
```

Replace `TXXX` with every WBS task completed or materially updated in the session. Never synchronize the whole historical WBS implicitly.

## Expectations

- Google Workspace authentication is executed via the `authorized_user.json` file for `k-umezawa@ml-mightylink.com`.
- GitHub Issues are opened/closed from WBS status and added to Project #1 with Status, Start date, and Target date.
- WBS entries are synced. WBS tasks marked as completed (完了) are automatically deleted from Google Calendar.
